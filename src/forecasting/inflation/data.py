"""Load the verified CPI target and construct auditable FX forecast inputs."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from statsmodels.tsa.arima.model import ARIMA

ROOT = Path(__file__).resolve().parents[3]
CPI_DATA = ROOT / "data" / "processed" / "cpi_monthly_clean.csv"
FEATURE_PANEL = ROOT / "data" / "processed" / "features" / "research_master_feature_panel.csv"
STAGE1_PREDICTIONS = (
    ROOT / "artifacts" / "predictions" / "exchange_rate" / "stage1_exchange_rate_predictions.csv"
)


def load_published_cpi_target(path: Path = CPI_DATA) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Return the longest contiguous segment of the published All-India CPI inflation rate.

    The CPI index is never used as a substitute target. Disjoint published-rate
    segments are reported in metadata rather than concatenated across missing periods.
    """
    source = pd.read_csv(path)
    required = {"date", "state", "sector", "division", "inflation_value", "series_label"}
    missing_columns = required.difference(source.columns)
    if missing_columns:
        raise ValueError(f"CPI source is missing required columns: {sorted(missing_columns)}")

    cpi = source.loc[
        source["state"].eq("All India")
        & source["sector"].eq("Combined")
        & source["division"].eq("CPI (General)")
    ].copy()
    cpi["date"] = pd.to_datetime(cpi["date"], errors="coerce")
    cpi["published_inflation"] = pd.to_numeric(cpi["inflation_value"], errors="coerce")
    cpi = cpi.dropna(subset=["date"]).sort_values("date").reset_index(drop=True)
    periods = cpi["date"].dt.to_period("M")
    if periods.duplicated().any():
        raise ValueError("The selected CPI General series contains duplicate months.")

    published = cpi.dropna(subset=["published_inflation"]).copy()
    published["period"] = published["date"].dt.to_period("M")
    if published.empty:
        raise ValueError("No published CPI inflation observations are available.")
    group_id = published["period"].astype("int64").diff().ne(1).cumsum()
    segments = [group.copy() for _, group in published.groupby(group_id, sort=True)]
    selected_index = max(range(len(segments)), key=lambda index: len(segments[index]))
    selected = segments[selected_index].copy().reset_index(drop=True)
    target = selected[["date", "published_inflation"]].rename(
        columns={"published_inflation": "cpi_inflation"}
    )

    segment_summary = [
        {
            "start": group["date"].min().date().isoformat(),
            "end": group["date"].max().date().isoformat(),
            "observations": len(group),
        }
        for group in segments
    ]
    metadata: dict[str, Any] = {
        "source_file": str(path),
        "source_rows": len(cpi),
        "source_date_start": cpi["date"].min().date().isoformat(),
        "source_date_end": cpi["date"].max().date().isoformat(),
        "published_observations": len(published),
        "published_missing": int(cpi["published_inflation"].isna().sum()),
        "published_series_segments": segment_summary,
        "selected_segment": segment_summary[selected_index],
        "selected_target_column": "inflation_value (published)",
        "selected_target_observations": len(target),
        "index_substitution": False,
    }
    return target, metadata


def load_feature_panel(path: Path = FEATURE_PANEL) -> pd.DataFrame:
    """Load verified engineered features without modifying their source file."""
    panel = pd.read_csv(path)
    if "date" not in panel:
        raise ValueError("The verified feature panel has no date column.")
    panel["date"] = pd.to_datetime(panel["date"], errors="coerce")
    panel = panel.dropna(subset=["date"]).sort_values("date").reset_index(drop=True)
    if panel["date"].duplicated().any():
        raise ValueError("The verified feature panel contains duplicate dates.")
    return panel


def _stage1_arima_predictions() -> pd.DataFrame:
    columns = ["forecast_origin", "target_date", "horizon", "predicted"]
    if not STAGE1_PREDICTIONS.exists():
        return pd.DataFrame(columns=columns)
    predictions = pd.read_csv(STAGE1_PREDICTIONS)
    predictions["forecast_origin"] = pd.to_datetime(predictions["forecast_origin"])
    predictions["target_date"] = pd.to_datetime(predictions["target_date"])
    return predictions


def build_fx_forecast_archive(
    origins: pd.Series,
    feature_panel: pd.DataFrame,
    horizons: tuple[int, ...] = (1, 3, 6),
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Create origin-safe FX forecasts, reusing Stage 1 ARIMA forecasts where available.

    Historical gaps are filled with fixed ARIMA(0,1,1) rolling-origin forecasts.
    A random-walk forecast is retained as a distinct benchmark series. No future
    exchange-rate observation is passed to either forecast.
    """
    fx = feature_panel[["date", "usd_inr_monthly"]].dropna().copy()
    fx["date"] = pd.to_datetime(fx["date"])
    fx["usd_inr_monthly"] = pd.to_numeric(fx["usd_inr_monthly"], errors="coerce")
    fx = fx.dropna().sort_values("date").reset_index(drop=True)
    periods = fx["date"].dt.to_period("M")
    if periods.duplicated().any():
        raise ValueError("FX source has more than one observation per month.")

    requested_origins = pd.to_datetime(origins).drop_duplicates().sort_values()
    stage1 = _stage1_arima_predictions()
    stage1_arima = stage1.loc[stage1["model"].eq("arima")].copy()
    stage1_random_walk = stage1.loc[stage1["model"].eq("random_walk")].copy()
    archive_rows: list[dict[str, Any]] = []
    reused_arima = 0
    reused_random_walk = 0
    order = (0, 1, 1)

    for origin in requested_origins:
        origin_period = origin.to_period("M")
        history = fx.loc[fx["date"].dt.to_period("M") <= origin_period]
        if history.empty:
            continue
        origin_value = float(history.iloc[-1]["usd_inr_monthly"])
        if history["date"].max().to_period("M") != origin_period:
            continue

        model = ARIMA(
            history["usd_inr_monthly"].astype(float),
            order=order,
            enforce_stationarity=False,
            enforce_invertibility=False,
        ).fit()
        arima_path = np.asarray(model.forecast(steps=max(horizons)), dtype=float)

        for horizon in horizons:
            target_date = (origin_period + horizon).to_timestamp()
            stage1_match = stage1_arima.loc[
                (stage1_arima["forecast_origin"].dt.to_period("M") == origin_period)
                & (stage1_arima["target_date"].dt.to_period("M") == target_date.to_period("M"))
                & stage1_arima["horizon"].eq(horizon)
            ]
            if not stage1_match.empty:
                arima_value = float(stage1_match.iloc[0]["predicted"])
                arima_source = "stage1_out_of_sample_arima"
                reused_arima += 1
            else:
                arima_value = float(arima_path[horizon - 1])
                arima_source = "historical_rolling_origin_arima_0_1_1"

            rw_match = stage1_random_walk.loc[
                (stage1_random_walk["forecast_origin"].dt.to_period("M") == origin_period)
                & (
                    stage1_random_walk["target_date"].dt.to_period("M")
                    == target_date.to_period("M")
                )
                & stage1_random_walk["horizon"].eq(horizon)
            ]
            if not rw_match.empty:
                random_walk_value = float(rw_match.iloc[0]["predicted"])
                rw_source = "stage1_out_of_sample_random_walk"
                reused_random_walk += 1
            else:
                random_walk_value = origin_value
                rw_source = "historical_origin_random_walk"

            archive_rows.extend(
                [
                    {
                        "forecast_origin": origin,
                        "target_date": target_date,
                        "horizon": horizon,
                        "model": "arima_0_1_1",
                        "predicted_usd_inr": arima_value,
                        "origin_usd_inr": origin_value,
                        "provenance": arima_source,
                    },
                    {
                        "forecast_origin": origin,
                        "target_date": target_date,
                        "horizon": horizon,
                        "model": "random_walk",
                        "predicted_usd_inr": random_walk_value,
                        "origin_usd_inr": origin_value,
                        "provenance": rw_source,
                    },
                ]
            )

    archive = pd.DataFrame(archive_rows)
    if archive.empty:
        raise ValueError("No origin-safe FX forecasts could be constructed.")
    if archive.duplicated(["forecast_origin", "target_date", "horizon", "model"]).any():
        raise ValueError("FX forecast archive contains duplicate origin/target/model rows.")
    if not archive["predicted_usd_inr"].map(np.isfinite).all():
        raise ValueError("FX forecast archive contains non-finite predictions.")
    metadata = {
        "stage1_arima_order_verified": order,
        "stage1_predictions_reused_arima": reused_arima,
        "stage1_predictions_reused_random_walk": reused_random_walk,
        "generated_historical_arima_rows": int(
            archive.loc[archive["provenance"].eq("historical_rolling_origin_arima_0_1_1")].shape[0]
        ),
        "forecast_origin_count": int(archive["forecast_origin"].nunique()),
        "horizons": horizons,
        "generated_as_retrospective_not_real_time": True,
    }
    return archive, metadata
