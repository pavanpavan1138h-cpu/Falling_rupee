"""CPI preprocessing utilities."""

from __future__ import annotations

import pandas as pd

from .date_handling import ensure_date_column

MONTH_MAP = {
    "January": "01",
    "February": "02",
    "March": "03",
    "April": "04",
    "May": "05",
    "June": "06",
    "July": "07",
    "August": "08",
    "September": "09",
    "October": "10",
    "November": "11",
    "December": "12",
}


def load_cpi_series(path: str, series_name: str) -> pd.DataFrame:
    """Load a CPI workbook and retain the source-labeled series.

    The output keeps the index and inflation columns explicitly for downstream
    monthly alignment and audit reporting.
    """
    df = pd.read_excel(path, sheet_name="CPI Data")
    df = df.copy()
    df["observation_date"] = df["year"].astype(str) + "-" + df["month"].map(MONTH_MAP) + "-01"
    df["observation_date"] = pd.to_datetime(df["observation_date"], errors="coerce")
    df["series_label"] = series_name
    df["base_year"] = df.get("base_year", pd.Series([None] * len(df)))
    df["index_value"] = pd.to_numeric(df["index"], errors="coerce")
    df["inflation_value"] = pd.to_numeric(df["inflation"], errors="coerce")
    required = [
        "observation_date",
        "series_label",
        "base_year",
        "year",
        "month",
        "state",
        "sector",
        "division",
        "group",
        "class",
        "sub_class",
        "item",
        "code",
        "index_value",
        "inflation_value",
    ]
    return df[required].copy()


def combine_cpi_series(
    current_df: pd.DataFrame,
    back_df: pd.DataFrame,
) -> pd.DataFrame:
    """Combine CPI back and current series while preserving the source label."""
    combined = pd.concat([current_df, back_df], ignore_index=True)
    combined = ensure_date_column(combined, "observation_date")
    combined = combined.sort_values("observation_date").reset_index(drop=True)
    return combined


def cpi_overlap_check(
    current_df: pd.DataFrame,
    back_df: pd.DataFrame,
) -> dict[str, int | list[str] | bool]:
    """Return explicit overlap and continuity metadata for the CPI pair."""
    current_dates = set(current_df["observation_date"].tolist())
    back_dates = set(back_df["observation_date"].tolist())
    overlap = sorted(current_dates & back_dates)
    ordered = bool(
        current_df["observation_date"].dropna().max() > back_df["observation_date"].dropna().min()
        and not overlap
    )
    return {
        "overlap_count": len(overlap),
        "overlap_dates": [str(value) for value in overlap],
        "adjacent_series": ordered,
    }
