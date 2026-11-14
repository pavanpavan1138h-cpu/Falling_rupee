"""Complementary unit-root and stationarity tests for Stage 3 series."""

from __future__ import annotations

import warnings
from typing import Any

import numpy as np
import pandas as pd
from statsmodels.tsa.stattools import adfuller, kpss

LEVEL_TREND_SERIES = {
    "usd_inr_monthly",
    "cpi_index",
    "wpi_all_commodities_index",
    "wpi_fuel_power_index",
    "wpi_manufactured_index",
    "brent_usd_per_barrel",
    "brent_inr_proxy_level",
    "fx_positive_partial_sum",
    "fx_negative_partial_sum",
    "repo_rate",
    "trade_neer",
    "trade_reer",
    "export_neer",
    "export_reer",
}

SERIES_TO_TEST = (
    "usd_inr_monthly",
    "fx_log_change_pct",
    "depreciation",
    "appreciation",
    "fx_positive_partial_sum",
    "fx_negative_partial_sum",
    "cpi_index",
    "cpi_annual_log_inflation",
    "cpi_published_inflation",
    "wpi_all_commodities_index",
    "wpi_all_commodities_annual_log_inflation",
    "wpi_fuel_power_index",
    "wpi_fuel_power_annual_log_inflation",
    "wpi_manufactured_index",
    "wpi_manufactured_annual_log_inflation",
    "brent_usd_per_barrel",
    "brent_log_change_pct",
    "brent_inr_proxy_level",
    "brent_inr_proxy_log_change_pct",
    "repo_rate",
    "repo_change_pp",
    "trade_neer",
    "trade_neer_log_change_pct",
    "trade_reer",
    "trade_reer_log_change_pct",
    "export_neer",
    "export_neer_log_change_pct",
    "export_reer",
    "export_reer_log_change_pct",
)


def _test_one(series: pd.Series, name: str, difference: int) -> dict[str, Any]:
    """Run ADF and KPSS with declared deterministic terms and captured warnings."""
    values = pd.to_numeric(series, errors="coerce").replace([np.inf, -np.inf], np.nan).dropna()
    if len(values) < 30:
        raise ValueError(f"{name} has only {len(values)} values for stationarity testing.")
    deterministic = "ct" if difference == 0 and name in LEVEL_TREND_SERIES else "c"
    captured: list[str] = []
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        adf = adfuller(
            values.to_numpy(dtype=float),
            regression=deterministic,
            autolag="AIC",
            result_object=True,
        )
        kpss_result = kpss(
            values.to_numpy(dtype=float),
            regression=deterministic,
            nlags="auto",
            result_object=True,
        )
    captured.extend(f"{item.category.__name__}: {item.message}" for item in caught)
    return {
        "series": name,
        "difference_order": difference,
        "observations": int(len(values)),
        "start": str(values.index.min()) if isinstance(values.index, pd.DatetimeIndex) else "",
        "end": str(values.index.max()) if isinstance(values.index, pd.DatetimeIndex) else "",
        "deterministic": deterministic,
        "adf_statistic": float(adf.statistic),
        "adf_pvalue": float(adf.pvalue),
        "adf_used_lag": int(adf.lags),
        "adf_nobs": int(adf.nobs),
        "adf_aic": float(adf.icbest),
        "adf_critical_1pct": float(adf.critical_values["1%"]),
        "adf_critical_5pct": float(adf.critical_values["5%"]),
        "adf_critical_10pct": float(adf.critical_values["10%"]),
        "kpss_statistic": float(kpss_result.statistic),
        "kpss_pvalue": float(kpss_result.pvalue),
        "kpss_lags": int(kpss_result.lags),
        "kpss_critical_1pct": float(kpss_result.critical_values["1%"]),
        "kpss_critical_5pct": float(kpss_result.critical_values["5%"]),
        "kpss_critical_10pct": float(kpss_result.critical_values["10%"]),
        "warnings": " | ".join(captured),
    }


def _stationary_evidence(result: dict[str, Any]) -> bool:
    """Require both tests to support stationarity at the 5% level."""
    return bool(result["adf_pvalue"] <= 0.05 and result["kpss_pvalue"] > 0.05)


def classify_integration(results: pd.DataFrame) -> pd.DataFrame:
    """Provide cautious I(0)/I(1)/possible-I(2) labels from paired tests."""
    rows: list[dict[str, Any]] = []
    for name, group in results.groupby("series", sort=False):
        by_order = group.set_index("difference_order").to_dict("index")
        level = by_order.get(0)
        first = by_order.get(1)
        second = by_order.get(2)
        if level and _stationary_evidence(level):
            classification = "I(0)-consistent"
        elif first and _stationary_evidence(first):
            classification = "I(1)-consistent"
        elif second and _stationary_evidence(second):
            classification = "possible I(2); verify"
        else:
            classification = "ambiguous / tests disagree"
        rows.append(
            {
                "series": name,
                "classification": classification,
                "level_adf_pvalue": level["adf_pvalue"] if level else np.nan,
                "level_kpss_pvalue": level["kpss_pvalue"] if level else np.nan,
                "first_diff_adf_pvalue": first["adf_pvalue"] if first else np.nan,
                "first_diff_kpss_pvalue": first["kpss_pvalue"] if first else np.nan,
                "second_diff_adf_pvalue": second["adf_pvalue"] if second else np.nan,
                "second_diff_kpss_pvalue": second["kpss_pvalue"] if second else np.nan,
                "interpretation_note": (
                    "Unit-root tests have low power in this short sample; "
                    "classification is indicative, not proof."
                ),
            }
        )
    return pd.DataFrame(rows)


def run_stationarity_tests(panel: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Test levels and up to second differences for all pre-specified variables."""
    absent = set(SERIES_TO_TEST).difference(panel.columns)
    if absent:
        raise ValueError(f"Stationarity panel is missing series: {sorted(absent)}")
    results: list[dict[str, Any]] = []
    for name in SERIES_TO_TEST:
        values = pd.to_numeric(panel[name], errors="coerce")
        for difference in range(3):
            transformed = values.copy()
            for _ in range(difference):
                transformed = transformed.diff()
            results.append(_test_one(transformed, name, difference))
    result_frame = pd.DataFrame(results)
    observed_warnings = sorted(
        {warning for warning in result_frame["warnings"].astype(str) if warning}
    )
    for message in observed_warnings:
        warnings.warn(
            f"Observed stationarity-test warning: {message}",
            RuntimeWarning,
            stacklevel=2,
        )
    return result_frame, classify_integration(result_frame)
