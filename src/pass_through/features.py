"""Deterministic, backward-looking Stage 3 variable construction."""

from __future__ import annotations

import numpy as np
import pandas as pd

SAMPLE_START = pd.Timestamp("2014-01-01")
SAMPLE_END = pd.Timestamp("2024-12-01")


def _numeric(series: pd.Series) -> pd.Series:
    """Convert a source field to numeric while retaining explicit missing values."""
    return pd.to_numeric(series, errors="coerce").astype(float)


def _log_change(level: pd.Series) -> pd.Series:
    """Calculate 100 times the first difference of log positive levels."""
    values = _numeric(level)
    valid = values.where(values.gt(0))
    return np.log(valid).diff().mul(100.0)


def _annual_log_inflation(index: pd.Series) -> pd.Series:
    """Calculate index-derived annual log inflation for positive index pairs only."""
    values = _numeric(index)
    valid = values.where(values.gt(0))
    lagged = valid.shift(12)
    result = (np.log(valid) - np.log(lagged)).mul(100.0)
    return result.where(valid.notna() & lagged.notna())


def _annual_simple_inflation(index: pd.Series) -> pd.Series:
    """Calculate the separately labelled simple annual index percentage change."""
    values = _numeric(index)
    lagged = values.shift(12)
    result = ((values / lagged) - 1.0).mul(100.0)
    return result.where(values.gt(0) & lagged.gt(0))


def build_stage3_features(
    source_panel: pd.DataFrame,
    sample_start: pd.Timestamp = SAMPLE_START,
    sample_end: pd.Timestamp = SAMPLE_END,
) -> pd.DataFrame:
    """Build auditable FX, inflation, imported-cost, and optional control variables.

    All differencing and annual changes use current and past observations only.
    Cumulative FX partial sums are initialized to zero immediately before the
    first in-sample exchange-rate change.
    """
    required = {
        "date",
        "usd_inr_monthly",
        "cpi_index",
        "cpi_published_inflation",
        "wpi_all_commodities_index",
        "wpi_fuel_power_index",
        "wpi_manufactured_index",
        "brent_usd_per_barrel",
        "repo_rate",
        "Trade_NEER",
        "Trade_REER",
        "Export_NEER",
        "Export_REER",
    }
    missing = required.difference(source_panel.columns)
    if missing:
        raise ValueError(f"Source panel is missing required fields: {sorted(missing)}")

    panel = source_panel.copy()
    panel["date"] = (
        pd.to_datetime(panel["date"], errors="raise").dt.to_period("M").dt.to_timestamp()
    )
    panel = panel.sort_values("date").reset_index(drop=True)
    periods = panel["date"].dt.to_period("M")
    if panel["date"].duplicated().any() or not periods.is_monotonic_increasing:
        raise ValueError("Stage 3 source panel must have unique, increasing monthly dates.")
    expected = pd.period_range(periods.iloc[0], periods.iloc[-1], freq="M")
    if not periods.reset_index(drop=True).equals(pd.Series(expected)):
        raise ValueError("Stage 3 source panel must have a complete monthly calendar.")

    numeric_columns = [column for column in required if column != "date"] + [
        "wpi_all_commodities_index_name",
        "wpi_all_commodities_index_code",
        "wpi_all_commodities_index_weight",
        "wpi_fuel_power_index_name",
        "wpi_fuel_power_index_code",
        "wpi_fuel_power_index_weight",
        "wpi_manufactured_index_name",
        "wpi_manufactured_index_code",
        "wpi_manufactured_index_weight",
    ]
    output = panel.copy()
    for column in numeric_columns:
        if column in output.columns and column not in {"cpi_published_inflation"}:
            output[column] = pd.to_numeric(output[column], errors="coerce")

    fx_level = _numeric(output["usd_inr_monthly"])
    if fx_level.le(0).any():
        raise ValueError("USD/INR levels must be strictly positive for log changes.")
    output["fx_log_change_pct"] = _log_change(fx_level)
    output["fx_simple_change_pct"] = fx_level.pct_change().mul(100.0)
    output["depreciation"] = output["fx_log_change_pct"].clip(lower=0.0)
    output["appreciation"] = output["fx_log_change_pct"].clip(upper=0.0)

    index_columns = {
        "cpi_index": "cpi",
        "wpi_all_commodities_index": "wpi_all_commodities",
        "wpi_fuel_power_index": "wpi_fuel_power",
        "wpi_manufactured_index": "wpi_manufactured",
    }
    for source, prefix in index_columns.items():
        output[f"{prefix}_annual_log_inflation"] = _annual_log_inflation(output[source])
        output[f"{prefix}_annual_simple_inflation"] = _annual_simple_inflation(output[source])
    output["cpi_published_inflation"] = _numeric(output["cpi_published_inflation"])

    output["brent_log_change_pct"] = _log_change(output["brent_usd_per_barrel"])
    output["brent_simple_change_pct"] = (
        _numeric(output["brent_usd_per_barrel"]).pct_change().mul(100.0)
    )
    output["brent_inr_proxy_level"] = _numeric(output["brent_usd_per_barrel"]) * fx_level
    output["brent_inr_proxy_log_change_pct"] = _log_change(output["brent_inr_proxy_level"])
    output["brent_inr_proxy_simple_change_pct"] = (
        output["brent_inr_proxy_level"].pct_change().mul(100.0)
    )

    output["repo_change_pp"] = _numeric(output["repo_rate"]).diff()
    for measure in ("Trade_NEER", "Trade_REER", "Export_NEER", "Export_REER"):
        output[measure.lower()] = _numeric(output[measure])
        output[f"{measure.lower()}_log_change_pct"] = _log_change(output[measure])
    in_sample = output["date"].between(sample_start, sample_end)
    output = output.loc[in_sample].copy().reset_index(drop=True)
    if output.empty:
        raise ValueError("The configured Stage 3 sample contains no source observations.")
    if output["date"].iloc[0] != sample_start or output["date"].iloc[-1] != sample_end:
        raise ValueError("The configured Stage 3 sample endpoints are not present in the sources.")

    output["fx_positive_partial_sum"] = output["depreciation"].fillna(0.0).cumsum()
    output["fx_negative_partial_sum"] = output["appreciation"].fillna(0.0).cumsum()
    return output
