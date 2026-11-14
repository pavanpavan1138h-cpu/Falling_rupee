"""Construct the four separate nested CPI forecast information sets."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

HORIZONS = (1, 3, 6)
CPI_LAGS = (1, 2, 3, 6, 12)
IMPORTED_LAGS = (1, 2, 3, 6, 12)
CONFIGURATIONS = ("C0", "C1", "C2", "C3")


def build_configuration_frames(
    cpi_target: pd.DataFrame,
    feature_panel: pd.DataFrame,
    fx_archive: pd.DataFrame,
    horizons: tuple[int, ...] = HORIZONS,
) -> tuple[dict[tuple[str, int], pd.DataFrame], dict[str, Any]]:
    """Build horizon-specific targets and non-overlapping C0/C1/C2/C3 features.

    All predictor lags are calculated backward from the forecast-origin month.
    C2's exchange-rate predictor is a forecast at that origin; C3's proxy uses
    only historical lagged proxy values from the verified engineered panel.
    """
    target = cpi_target[["date", "cpi_inflation"]].copy()
    target["date"] = pd.to_datetime(target["date"])
    target["cpi_inflation"] = pd.to_numeric(target["cpi_inflation"], errors="coerce")
    target = target.dropna().sort_values("date").reset_index(drop=True)
    target_periods = target["date"].dt.to_period("M")
    expected_periods = pd.period_range(target_periods.iloc[0], target_periods.iloc[-1], freq="M")
    if not target_periods.reset_index(drop=True).equals(pd.Series(expected_periods)):
        raise ValueError("The chosen published CPI target segment must be monthly and contiguous.")

    panel = feature_panel.copy()
    panel["date"] = pd.to_datetime(panel["date"])
    panel = panel.drop_duplicates("date").sort_values("date").reset_index(drop=True)
    required_macro = {
        "brent_usd_per_barrel_level",
        "brent_mom_pct_change",
        "brent_inr_proxy_level",
        "brent_inr_proxy_mom_pct_change",
        "usd_inr_monthly",
    }
    missing_macro = required_macro.difference(panel.columns)
    if missing_macro:
        raise ValueError(f"Verified feature panel lacks Stage 2 fields: {sorted(missing_macro)}")

    rows = target.merge(
        panel[
            [
                "date",
                "brent_usd_per_barrel_level",
                "brent_mom_pct_change",
                "brent_inr_proxy_level",
                "brent_inr_proxy_mom_pct_change",
                "usd_inr_monthly",
            ]
        ],
        on="date",
        how="left",
        validate="one_to_one",
    )

    for lag in CPI_LAGS:
        rows[f"cpi_lag_{lag}"] = rows["cpi_inflation"].shift(lag)
    for name in (
        "brent_usd_per_barrel_level",
        "brent_mom_pct_change",
    ):
        for lag in IMPORTED_LAGS:
            rows[f"{name}_lag_{lag}"] = rows[name].shift(lag)
    for name in (
        "brent_inr_proxy_level",
        "brent_inr_proxy_mom_pct_change",
    ):
        for lag in IMPORTED_LAGS:
            rows[f"{name}_lag_{lag}"] = rows[name].shift(lag)

    arima_fx = fx_archive.loc[fx_archive["model"].eq("arima_0_1_1")].copy()
    arima_fx["forecast_origin"] = pd.to_datetime(arima_fx["forecast_origin"])
    arima_fx["target_date"] = pd.to_datetime(arima_fx["target_date"])
    arima_fx = arima_fx.rename(
        columns={
            "forecast_origin": "date",
            "predicted_usd_inr": "fx_predicted_level",
            "origin_usd_inr": "fx_origin_level",
            "provenance": "fx_forecast_provenance",
        }
    )
    expected_pairs = pd.concat(
        [
            pd.DataFrame(
                {
                    "date": rows["date"],
                    "horizon": horizon,
                    "target_date": (rows["date"].dt.to_period("M") + horizon).dt.to_timestamp(),
                }
            )
            for horizon in horizons
        ],
        ignore_index=True,
    )
    fx_keyed = arima_fx[
        [
            "date",
            "target_date",
            "horizon",
            "fx_predicted_level",
            "fx_origin_level",
            "fx_forecast_provenance",
        ]
    ]
    fx_keyed = fx_keyed.rename(columns={"date": "forecast_origin"})
    fx_joined = expected_pairs.merge(
        fx_keyed,
        left_on=["date", "target_date", "horizon"],
        right_on=["forecast_origin", "target_date", "horizon"],
        how="left",
        validate="one_to_one",
    )
    if fx_joined["fx_predicted_level"].isna().any():
        raise ValueError(
            "C2 has missing origin/horizon FX forecasts; no actual FX substitution is allowed."
        )
    fx_joined["fx_predicted_change_pct"] = (
        (fx_joined["fx_predicted_level"] / fx_joined["fx_origin_level"]) - 1.0
    ) * 100.0

    c0_columns = [f"cpi_lag_{lag}" for lag in CPI_LAGS]
    c1_columns = c0_columns + [
        f"{name}_lag_{lag}"
        for name in ("brent_usd_per_barrel_level", "brent_mom_pct_change")
        for lag in IMPORTED_LAGS
    ]
    c3_columns = c0_columns + [
        f"{name}_lag_{lag}"
        for name in ("brent_inr_proxy_level", "brent_inr_proxy_mom_pct_change")
        for lag in IMPORTED_LAGS
    ]
    configurations: dict[str, list[str]] = {
        "C0": c0_columns,
        "C1": c1_columns,
        "C2": c0_columns + ["fx_predicted_level", "fx_predicted_change_pct"],
        "C3": c3_columns,
    }

    frames: dict[tuple[str, int], pd.DataFrame] = {}
    coverage: dict[str, Any] = {}
    for horizon in horizons:
        horizon_rows = rows.copy()
        horizon_rows["target_date"] = (target_periods + horizon).dt.to_timestamp()
        horizon_rows["target_cpi_inflation"] = horizon_rows["cpi_inflation"].shift(-horizon)
        horizon_fx = fx_joined.loc[fx_joined["horizon"].eq(horizon)].copy()
        horizon_fx = horizon_fx[
            [
                "date",
                "fx_predicted_level",
                "fx_predicted_change_pct",
                "fx_forecast_provenance",
            ]
        ]
        horizon_rows = horizon_rows.merge(
            horizon_fx,
            on="date",
            how="left",
            validate="one_to_one",
        )
        for config, feature_columns in configurations.items():
            columns = [
                "date",
                "target_date",
                "target_cpi_inflation",
                "cpi_inflation",
                *feature_columns,
            ]
            if config == "C2":
                columns.append("fx_forecast_provenance")
            selected = horizon_rows[columns].copy()
            selected = selected.rename(
                columns={"date": "forecast_origin", "cpi_inflation": "origin_cpi_inflation"}
            )
            selected = selected.dropna(
                subset=["target_cpi_inflation", "origin_cpi_inflation", *feature_columns]
            ).reset_index(drop=True)
            if not np.isfinite(selected[feature_columns].to_numpy(dtype=float)).all():
                raise ValueError(f"{config} has non-finite predictor values at horizon {horizon}.")
            frames[(config, horizon)] = selected
            coverage[f"{config}_{horizon}m"] = {
                "observations": len(selected),
                "origin_start": selected["forecast_origin"].min().date().isoformat(),
                "origin_end": selected["forecast_origin"].max().date().isoformat(),
                "target_start": selected["target_date"].min().date().isoformat(),
                "target_end": selected["target_date"].max().date().isoformat(),
                "feature_count": len(feature_columns),
                "feature_columns": feature_columns,
            }
    return frames, coverage
