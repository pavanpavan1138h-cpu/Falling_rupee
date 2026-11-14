"""Monthly alignment helpers for multi-source research panels."""

from __future__ import annotations

import pandas as pd


def build_monthly_macro_panel(
    brent_df: pd.DataFrame,
    usd_inr_monthly_df: pd.DataFrame,
    repo_df: pd.DataFrame,
    neer_df: pd.DataFrame,
    cpi_df: pd.DataFrame,
    wpi_df: pd.DataFrame,
) -> pd.DataFrame:
    """Merge monthly source tables on a common monthly date index."""
    merged = brent_df.rename(columns={"date": "date"}).copy()
    merged = merged.merge(
        usd_inr_monthly_df.rename(columns={"date": "date"}),
        on="date",
        how="outer",
    )
    merged = merged.merge(repo_df.rename(columns={"date": "date"}), on="date", how="outer")
    merged = merged.merge(neer_df.rename(columns={"date": "date"}), on="date", how="outer")
    merged = merged.merge(
        cpi_df.rename(columns={"date": "date", "index_value": "cpi_general_index"}),
        on="date",
        how="outer",
    )
    merged = merged.merge(
        wpi_df.rename(columns={"date": "date", "index_value": "wpi_all_commodities_index"}),
        on="date",
        how="outer",
    )
    merged = merged.sort_values("date").reset_index(drop=True)
    return merged


def build_monthly_imported_inflation_panel(
    brent_df: pd.DataFrame,
    usd_inr_monthly_df: pd.DataFrame,
    repo_df: pd.DataFrame,
    neer_df: pd.DataFrame,
    cpi_df: pd.DataFrame,
    wpi_df: pd.DataFrame,
) -> pd.DataFrame:
    """Create a panel for imported-inflation analysis with explicit source coverage metadata."""
    monthly = build_monthly_macro_panel(
        brent_df=brent_df,
        usd_inr_monthly_df=usd_inr_monthly_df,
        repo_df=repo_df,
        neer_df=neer_df,
        cpi_df=cpi_df,
        wpi_df=wpi_df,
    )
    monthly["has_brent"] = monthly.get("brent_usd_per_barrel", pd.NA).notna()
    monthly["has_usd_inr"] = monthly.get("usd_inr_monthly", pd.NA).notna()
    monthly["has_repo_rate"] = monthly.get("repo_rate", pd.NA).notna()
    monthly["has_neer_reer"] = (
        monthly.get("Trade_NEER", pd.NA).notna()
        | monthly.get("Trade_REER", pd.NA).notna()
        | monthly.get("Export_NEER", pd.NA).notna()
        | monthly.get("Export_REER", pd.NA).notna()
    )
    monthly["has_cpi"] = monthly.get("cpi_general_index", pd.NA).notna()
    monthly["has_wpi"] = monthly.get("wpi_all_commodities_index", pd.NA).notna()
    return monthly.sort_values("date").reset_index(drop=True)


def build_daily_exchange_rate_panel(daily_df: pd.DataFrame) -> pd.DataFrame:
    """Create a clean daily exchange-rate panel."""
    panel = daily_df.rename(columns={"date": "date", "DEXINUS": "usd_inr_daily"}).copy()
    panel = panel.sort_values("date").reset_index(drop=True)
    return panel
