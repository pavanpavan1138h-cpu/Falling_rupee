"""Validation utilities for preprocessing outputs."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


def summarize_numeric_issues(df: pd.DataFrame, value_cols: list[str]) -> dict[str, Any]:
    """Return counts of missing values, zeros, non-finite values, and duplicate dates."""
    summary: dict[str, Any] = {
        "missing_values": int(df[value_cols].isna().sum().sum()),
        "zero_values": int((df[value_cols] == 0).sum().sum()),
        "non_finite_values": int(
            df[value_cols]
            .apply(lambda col: np.isinf(pd.to_numeric(col, errors="coerce")).sum())
            .sum()
        ),
    }
    return summary


def check_duplicate_dates(df: pd.DataFrame, date_col: str) -> int:
    """Return the number of duplicate date entries in a dataset."""
    return int(df[date_col].duplicated().sum())


def check_ordering(df: pd.DataFrame, date_col: str) -> bool:
    """Return whether the dates are strictly sorted in ascending order without duplicates."""
    s = df[date_col].dropna()
    if s.empty:
        return True
    return bool(s.is_monotonic_increasing and not s.duplicated().any())


def validate_date_column(df: pd.DataFrame, date_col: str) -> dict[str, Any]:
    """Return a validation record for a date column."""
    return {
        "duplicate_dates": check_duplicate_dates(df, date_col),
        "chronological_order": check_ordering(df, date_col),
        "null_date_values": int(df[date_col].isna().sum()),
    }


def ensure_numeric(df: pd.DataFrame, value_cols: list[str]) -> pd.DataFrame:
    """Coerce a set of columns to numeric, preserving missing values."""
    output = df.copy()
    for col in value_cols:
        output[col] = pd.to_numeric(output[col], errors="coerce")
    return output
