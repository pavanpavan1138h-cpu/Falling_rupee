"""Build auditable, origin-safe Stage 4 classification datasets."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
DATA_ROOT = ROOT / "data" / "processed"
FEATURE_COLUMNS: dict[str, list[str]] = {
    "C0": [
        "cpi_lag_1",
        "cpi_lag_3",
        "cpi_lag_6",
        "cpi_lag_12",
        "cpi_change_1m",
        "cpi_mean_3m",
        "cpi_volatility_6m",
    ],
    "C1": [
        "cpi_lag_1",
        "cpi_lag_3",
        "cpi_lag_6",
        "cpi_lag_12",
        "cpi_change_1m",
        "cpi_mean_3m",
        "cpi_volatility_6m",
        "fx_log_return_1m",
        "fx_cumulative_return_3m",
        "fx_volatility_6m",
    ],
    "C2": [
        "cpi_lag_1",
        "cpi_lag_3",
        "cpi_lag_6",
        "cpi_lag_12",
        "cpi_change_1m",
        "cpi_mean_3m",
        "cpi_volatility_6m",
        "fx_log_return_1m",
        "fx_cumulative_return_3m",
        "fx_volatility_6m",
        "brent_log_return_1m",
        "brent_cumulative_return_3m",
    ],
    "C3": [
        "cpi_lag_1",
        "cpi_lag_3",
        "cpi_lag_6",
        "cpi_lag_12",
        "cpi_change_1m",
        "cpi_mean_3m",
        "cpi_volatility_6m",
        "fx_log_return_1m",
        "fx_cumulative_return_3m",
        "fx_volatility_6m",
        "brent_inr_proxy_log_return_1m",
        "brent_inr_proxy_cumulative_return_3m",
    ],
}
HORIZONS = (1, 3, 6)


def _monthly_series(path: Path, value_column: str, output_name: str) -> pd.Series:
    """Load a unique monthly numeric series keyed to calendar-month starts."""
    data = pd.read_csv(path, usecols=["date", value_column])
    data["date"] = pd.to_datetime(data["date"], errors="coerce")
    data[value_column] = pd.to_numeric(data[value_column], errors="coerce")
    data = data.dropna(subset=["date"])
    data["period"] = data["date"].dt.to_period("M")
    if data["period"].duplicated().any():
        raise ValueError(f"{path.name} contains duplicate months.")
    data = data.dropna(subset=[value_column]).set_index("period").sort_index()
    return data[value_column].rename(output_name)


def load_stage4_sources() -> tuple[pd.DataFrame, dict[str, Any]]:
    """Load published CPI and source levels without modifying source files."""
    cpi_path = DATA_ROOT / "cpi_monthly_clean.csv"
    cpi_source = pd.read_csv(cpi_path)
    required = {"date", "state", "sector", "division", "inflation_value"}
    if missing := required.difference(cpi_source.columns):
        raise ValueError(f"CPI file lacks required columns: {sorted(missing)}")
    cpi = cpi_source.loc[
        cpi_source["state"].eq("All India")
        & cpi_source["sector"].eq("Combined")
        & cpi_source["division"].eq("CPI (General)")
    ].copy()
    cpi["date"] = pd.to_datetime(cpi["date"], errors="coerce")
    cpi["period"] = cpi["date"].dt.to_period("M")
    cpi["inflation_value"] = pd.to_numeric(cpi["inflation_value"], errors="coerce")
    if cpi["period"].dropna().duplicated().any():
        raise ValueError("Selected All India/Combined/CPI General CPI has duplicate months.")
    published = cpi.dropna(subset=["period", "inflation_value"]).sort_values("period")
    if published.empty:
        raise ValueError("No published CPI inflation observations were found.")
    group_id = published["period"].astype("int64").diff().ne(1).cumsum()
    segments = [group.copy() for _, group in published.groupby(group_id, sort=True)]
    segment = max(segments, key=len).copy()
    expected_periods = pd.period_range("2014-01", "2024-12", freq="M")
    if not segment["period"].reset_index(drop=True).equals(pd.Series(expected_periods)):
        raise ValueError(
            "The longest published CPI segment differs from the verified Jan 2014-Dec 2024 "
            "calendar; review source continuity before training."
        )
    target = segment[["period", "inflation_value"]].rename(
        columns={"inflation_value": "target_inflation"}
    )
    target["target_month"] = target["period"].dt.to_timestamp()

    fx = _monthly_series(
        DATA_ROOT / "usd_inr_monthly_clean.csv",
        "usd_inr_monthly",
        "usd_inr_level",
    )
    brent = _monthly_series(
        DATA_ROOT / "brent_monthly_clean.csv",
        "brent_usd_per_barrel",
        "brent_usd_level",
    )
    panel = pd.concat([fx, brent], axis=1).sort_index()
    panel = panel.reindex(expected_periods)
    if panel.isna().any().any():
        missing_months = panel.index[panel.isna().any(axis=1)].astype(str).tolist()
        raise ValueError(f"Market source levels are missing in the CPI window: {missing_months}")
    if (panel <= 0).any().any():
        raise ValueError("FX and Brent source levels must be strictly positive.")
    panel["brent_inr_proxy_level"] = panel["usd_inr_level"] * panel["brent_usd_level"]
    for source, prefix in (
        ("usd_inr_level", "fx"),
        ("brent_usd_level", "brent"),
        ("brent_inr_proxy_level", "brent_inr_proxy"),
    ):
        panel[f"{prefix}_log_return"] = 100.0 * np.log(panel[source]).diff()
    panel["fx_volatility_6m"] = panel["fx_log_return"].rolling(6, min_periods=6).std()
    panel["brent_volatility_6m"] = (
        panel["brent_log_return"].rolling(6, min_periods=6).std()
    )
    panel["brent_inr_proxy_volatility_6m"] = (
        panel["brent_inr_proxy_log_return"].rolling(6, min_periods=6).std()
    )
    target = target.set_index("period")
    target = target.reindex(expected_periods)
    metadata: dict[str, Any] = {
        "cpi_source": str(cpi_path.relative_to(ROOT)),
        "cpi_series": "All India / Combined / CPI (General) / inflation_value",
        "cpi_segment_start": str(expected_periods[0]),
        "cpi_segment_end": str(expected_periods[-1]),
        "cpi_observations": len(target),
        "cpi_index_used_as_target": False,
        "disconnected_2025_and_2026_segments_used": False,
        "market_source_files": [
            "data/processed/usd_inr_monthly_clean.csv",
            "data/processed/brent_monthly_clean.csv",
        ],
        "source_calendar_complete": True,
        "release_vintages_verified": False,
    }
    return target, panel, metadata


def _value(series: pd.Series, period: pd.Period) -> float:
    """Return one exact calendar-month value, failing rather than bridging gaps."""
    if period not in series.index:
        raise ValueError(f"Required source month {period} is unavailable.")
    result = series.loc[period]
    if not np.isfinite(float(result)):
        raise ValueError(f"Required source value at {period} is missing or non-finite.")
    return float(result)


def build_classification_frames(
    target: pd.DataFrame,
    market: pd.DataFrame,
    horizons: tuple[int, ...] = HORIZONS,
) -> tuple[dict[tuple[str, int], pd.DataFrame], dict[str, Any]]:
    """Build C0-C3 direct-horizon frames using source observations through t-1."""
    cpi = target["target_inflation"]
    frames: dict[tuple[str, int], pd.DataFrame] = {}
    coverage: dict[str, Any] = {}
    all_periods = target.index
    for horizon in horizons:
        rows: list[dict[str, Any]] = []
        for origin in pd.period_range("2015-01", "2024-12", freq="M"):
            target_period = origin + horizon
            if target_period not in all_periods:
                continue
            reference = origin - 1
            cpi_history = {
                lag: _value(cpi, reference - (lag - 1))
                for lag in (1, 2, 3, 6, 12)
            }
            row: dict[str, Any] = {
                "forecast_origin": origin.to_timestamp(),
                "target_month": target_period.to_timestamp(),
                "horizon_months": horizon,
                "target_inflation": _value(cpi, target_period),
                "elevated_target": int(_value(cpi, target_period) > 6.0),
                "feature_observation_end": reference.to_timestamp(),
                "cpi_lag_1": cpi_history[1],
                "cpi_lag_3": cpi_history[3],
                "cpi_lag_6": cpi_history[6],
                "cpi_lag_12": cpi_history[12],
                "cpi_change_1m": cpi_history[1] - cpi_history[2],
                "cpi_mean_3m": float(
                    np.mean([_value(cpi, reference - lag) for lag in range(3)])
                ),
                "cpi_volatility_6m": float(
                    np.std(
                        [_value(cpi, reference - lag) for lag in range(6)],
                        ddof=1,
                    )
                ),
                "fx_log_return_1m": _value(market["fx_log_return"], reference),
                "fx_cumulative_return_3m": sum(
                    _value(market["fx_log_return"], reference - lag) for lag in range(3)
                ),
                "fx_volatility_6m": float(
                    np.std(
                        [
                            _value(market["fx_log_return"], reference - lag)
                            for lag in range(6)
                        ],
                        ddof=1,
                    )
                ),
                "brent_log_return_1m": _value(market["brent_log_return"], reference),
                "brent_cumulative_return_3m": sum(
                    _value(market["brent_log_return"], reference - lag) for lag in range(3)
                ),
                "brent_inr_proxy_log_return_1m": _value(
                    market["brent_inr_proxy_log_return"], reference
                ),
                "brent_inr_proxy_cumulative_return_3m": sum(
                    _value(market["brent_inr_proxy_log_return"], reference - lag)
                    for lag in range(3)
                ),
            }
            if row["feature_observation_end"] >= row["forecast_origin"]:
                raise ValueError("A feature observation is not strictly before its origin.")
            if target_period != origin + horizon:
                raise ValueError("Forecast origin and target month are misaligned.")
            rows.append(row)

        base = pd.DataFrame(rows)
        if base.empty:
            raise ValueError(f"No eligible observations for horizon {horizon}.")
        for configuration, features in FEATURE_COLUMNS.items():
            frame = base[
                [
                    "forecast_origin",
                    "target_month",
                    "horizon_months",
                    "target_inflation",
                    "elevated_target",
                    "feature_observation_end",
                    *features,
                ]
            ].copy()
            if frame["forecast_origin"].duplicated().any():
                raise ValueError(f"{configuration} has duplicate origins at horizon {horizon}.")
            if frame[features].isna().any().any():
                raise ValueError(f"{configuration} has missing predictors at horizon {horizon}.")
            if not np.isfinite(frame[features].to_numpy(dtype=float)).all():
                raise ValueError(f"{configuration} has non-finite predictors.")
            frames[(configuration, horizon)] = frame.reset_index(drop=True)
            coverage[f"{configuration}_{horizon}m"] = {
                "observations": len(frame),
                "elevated": int(frame["elevated_target"].sum()),
                "non_elevated": int((frame["elevated_target"] == 0).sum()),
                "feature_count": len(features),
                "features": features,
                "origin_start": frame["forecast_origin"].min().date().isoformat(),
                "origin_end": frame["forecast_origin"].max().date().isoformat(),
                "target_start": frame["target_month"].min().date().isoformat(),
                "target_end": frame["target_month"].max().date().isoformat(),
            }
    for horizon in horizons:
        reference = frames[("C0", horizon)][["forecast_origin", "target_month"]]
        for configuration in FEATURE_COLUMNS:
            compared = frames[(configuration, horizon)][["forecast_origin", "target_month"]]
            if not compared.equals(reference):
                raise ValueError(f"{configuration} does not share the C0 sample at {horizon}m.")
    return frames, coverage
