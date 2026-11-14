"""Date handling helpers for the preprocessing pipeline."""

from __future__ import annotations

import pandas as pd


def ensure_date_column(df: pd.DataFrame, date_col: str) -> pd.DataFrame:
    """Parse a date-like column to pandas datetime and sort by date."""
    output = df.copy()
    output[date_col] = pd.to_datetime(output[date_col], errors="coerce")
    output = output.dropna(subset=[date_col]).sort_values(date_col).reset_index(drop=True)
    return output


def as_monthly_date(value: str | object) -> pd.Timestamp | pd.NaT:
    """Convert a monthly representation to a first-of-month timestamp."""
    if pd.isna(value):
        return pd.NaT
    try:
        return pd.to_datetime(value, errors="coerce")
    except (TypeError, ValueError):
        return pd.NaT


def create_monthly_period(date_values: pd.Series) -> pd.Series:
    """Return a YYYY-MM period string for monthly series."""
    return pd.PeriodIndex(date_values, freq="M").astype(str)
