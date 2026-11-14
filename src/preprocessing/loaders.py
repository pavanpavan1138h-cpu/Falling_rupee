"""Dataset loading utilities for raw POME EL inputs."""

from __future__ import annotations

from pathlib import Path

import pandas as pd


def read_csv_dataset(path: str | Path) -> pd.DataFrame:
    """Read a CSV dataset with a standard pandas path."""
    return pd.read_csv(path)


def read_excel_dataset(path: str | Path, sheet_name: str | int = 0) -> pd.DataFrame:
    """Read an Excel sheet using the project-supported engine."""
    return pd.read_excel(path, sheet_name=sheet_name)


def read_neer_reer_dataset(path: str | Path) -> pd.DataFrame:
    """Load the RBI NEER/REER table while skipping metadata rows ahead of the true header."""
    raw = pd.read_csv(path, header=None)
    for idx, row in raw.iterrows():
        values = row.astype(str).str.strip().tolist()
        if "Date" in values and "Trade_NEER" in values:
            header_row = idx
            break
    else:
        raise ValueError(f"Could not locate the NEER/REER table header in {path}.")

    df = pd.read_csv(path, header=header_row)
    return df


def read_wpi_dataset(path: str | Path) -> pd.DataFrame:
    """Load the WPI workbook and preserve the raw workbook structure before reshaping."""
    return pd.read_excel(path, sheet_name="MONTHLY_INDEX", header=0)
