"""Tests for the preprocessing pipeline validation layer."""

from __future__ import annotations

import pandas as pd

from src.preprocessing.cpi_processing import cpi_overlap_check
from src.preprocessing.monthly_alignment import build_monthly_macro_panel
from src.preprocessing.validation import validate_date_column


def test_validate_date_column_tracks_duplicates() -> None:
    df = pd.DataFrame(
        {
            "date": ["2024-01-01", "2024-01-02", "2024-01-02", "2024-01-04"],
            "value": [1.0, 2.0, 2.0, 4.0],
        }
    )
    result = validate_date_column(df.assign(date=pd.to_datetime(df["date"])), "date")
    assert result["duplicate_dates"] == 1
    assert result["chronological_order"] is False


def test_cpi_overlap_check_reports_no_overlap() -> None:
    current = pd.DataFrame({"observation_date": pd.to_datetime(["2025-01-01", "2025-02-01"])})
    back = pd.DataFrame({"observation_date": pd.to_datetime(["2024-01-01", "2024-02-01"])})
    result = cpi_overlap_check(current, back)
    assert result["overlap_count"] == 0
    assert result["adjacent_series"] is True


def test_build_monthly_macro_panel_keeps_unique_dates() -> None:
    brent = pd.DataFrame(
        {"date": pd.to_datetime(["2024-01-01", "2024-02-01"]), "brent_usd_per_barrel": [80.0, 81.0]}
    )
    usd_inr = pd.DataFrame(
        {"date": pd.to_datetime(["2024-01-01", "2024-02-01"]), "usd_inr_monthly": [82.0, 83.0]}
    )
    repo = pd.DataFrame(
        {"date": pd.to_datetime(["2024-01-01", "2024-02-01"]), "repo_rate": [6.25, 6.5]}
    )
    neer = pd.DataFrame(
        {"date": pd.to_datetime(["2024-01-01", "2024-02-01"]), "Trade_NEER": [100.0, 101.0]}
    )
    cpi = pd.DataFrame(
        {"date": pd.to_datetime(["2024-01-01", "2024-02-01"]), "cpi_general_index": [114.2, 115.0]}
    )
    wpi = pd.DataFrame(
        {
            "date": pd.to_datetime(["2024-01-01", "2024-02-01"]),
            "wpi_all_commodities_index": [120.1, 121.2],
        }
    )
    panel = build_monthly_macro_panel(brent, usd_inr, repo, neer, cpi, wpi)
    assert panel["date"].is_unique
    assert len(panel) == 2
