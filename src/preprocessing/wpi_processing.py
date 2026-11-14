"""WPI preprocessing utilities."""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

from .date_handling import ensure_date_column


def read_wpi_monthly_long(path: str | Path) -> pd.DataFrame:
    """Reshape the raw WPI workbook from wide month columns into a long monthly table."""
    df = pd.read_excel(path, sheet_name="MONTHLY_INDEX", header=0)
    value_columns = [col for col in df.columns if col.startswith("INDX")]
    records: list[dict[str, object]] = []

    for _, row in df.iterrows():
        comm_name = row.get("COMM_NAME")
        comm_code = row.get("COMM_CODE")
        comm_wt = row.get("COMM_WT")
        for col in value_columns:
            match = re.match(r"INDX(\d{2})(\d{4})", col)
            if match is None:
                continue
            month_code, year = match.groups()
            date_value = pd.Timestamp(year=int(year), month=int(month_code), day=1)
            val = pd.to_numeric(row[col], errors="coerce")
            records.append(
                {
                    "comm_name": comm_name,
                    "comm_code": comm_code,
                    "comm_wt": comm_wt,
                    "observation_date": date_value,
                    "index_value": val,
                }
            )

    result = pd.DataFrame(records)
    if result.empty:
        return result
    result = ensure_date_column(result, "observation_date")
    result = result.sort_values("observation_date").reset_index(drop=True)
    return result


def build_wpi_aggregates(df: pd.DataFrame) -> pd.DataFrame:
    """Return a one-row-per-date aggregate table with key WPI summaries."""
    if df.empty:
        return df
    all_comm = df[
        df["comm_name"].astype(str).str.lower().str.contains("all commodities", na=False)
    ].copy()
    if all_comm.empty:
        return df
    all_comm = all_comm.groupby("observation_date", as_index=False)["index_value"].mean()
    all_comm = all_comm.rename(columns={"index_value": "all_commodities_index"})
    return all_comm.sort_values("observation_date").reset_index(drop=True)
