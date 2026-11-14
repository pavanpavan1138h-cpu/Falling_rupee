"""Basic data cleaning operations for the research pipeline."""

from __future__ import annotations

import pandas as pd

from .date_handling import ensure_date_column
from .validation import ensure_numeric


def clean_simple_series(
    df: pd.DataFrame,
    date_col: str,
    value_col: str,
    *,
    frequency: str | None = None,
) -> pd.DataFrame:
    """Sort and normalize a basic series while preserving source values and missing data."""
    output = df[[date_col, value_col]].copy()
    output = ensure_numeric(output, [value_col])
    output = ensure_date_column(output, date_col)
    if frequency == "M":
        output["period"] = output[date_col].dt.to_period("M").astype(str)
    output = output.drop_duplicates(subset=[date_col]).sort_values(date_col).reset_index(drop=True)
    return output


def clean_monthly_panel(df: pd.DataFrame, date_col: str) -> pd.DataFrame:
    """Standardize a monthly panel to an index column and chronological order."""
    output = ensure_date_column(df.copy(), date_col)
    output["month"] = output[date_col].dt.to_period("M").astype(str)
    output = output.sort_values(date_col).reset_index(drop=True)
    return output
