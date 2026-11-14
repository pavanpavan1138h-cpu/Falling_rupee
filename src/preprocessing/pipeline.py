"""Execution pipeline for the POME EL preprocessing stage."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from config.settings import PROJECT_PATHS

from .cleaning import clean_simple_series
from .cpi_processing import combine_cpi_series, load_cpi_series
from .date_handling import ensure_date_column
from .loaders import read_csv_dataset, read_neer_reer_dataset
from .monthly_alignment import (
    build_daily_exchange_rate_panel,
    build_monthly_imported_inflation_panel,
    build_monthly_macro_panel,
)
from .wpi_processing import read_wpi_monthly_long

OUTPUT_FILES = {
    "brent_monthly_clean": "brent_monthly_clean.csv",
    "usd_inr_daily_clean": "usd_inr_daily_clean.csv",
    "usd_inr_monthly_clean": "usd_inr_monthly_clean.csv",
    "repo_rate_clean": "repo_rate_clean.csv",
    "neer_reer_monthly_clean": "neer_reer_monthly_clean.csv",
    "cpi_current_series_clean": "cpi_current_series_clean.csv",
    "cpi_back_series_clean": "cpi_back_series_clean.csv",
    "cpi_monthly_clean": "cpi_monthly_clean.csv",
    "wpi_monthly_clean": "wpi_monthly_clean.csv",
    "monthly_macro_panel": "monthly_macro_panel.csv",
    "monthly_imported_inflation_panel": "monthly_imported_inflation_panel.csv",
    "daily_exchange_rate_panel": "daily_exchange_rate_panel.csv",
}


def run_preprocessing(root: str | Path | None = None) -> dict[str, pd.DataFrame]:
    """Create processed research datasets from the raw read-only files."""
    project_root = Path(root) if root is not None else PROJECT_PATHS.root
    processed_dir = project_root / "data" / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)

    brent_df = read_csv_dataset(
        project_root / "data/raw/02_Brent_Crude_Oil_Spot_Price_Monthly_USD_per_Barrel.csv"
    )
    brent_df = brent_df.rename(columns={"observation_date": "date", "MCOILBRENTEU": "value"})
    brent_clean = clean_simple_series(brent_df, "date", "value", frequency="M")[["date", "value"]]
    brent_clean = brent_clean.rename(columns={"value": "brent_usd_per_barrel"})
    brent_clean.to_csv(processed_dir / OUTPUT_FILES["brent_monthly_clean"], index=False)

    daily_df = read_csv_dataset(project_root / "data/raw/03_USD_INR_Exchange_Rate_Daily.csv")
    daily_df = daily_df.rename(columns={"observation_date": "date", "DEXINUS": "usd_inr_daily"})
    daily_clean = clean_simple_series(daily_df, "date", "usd_inr_daily")
    daily_clean = daily_clean.rename(columns={"usd_inr_daily": "usd_inr_daily"})
    daily_clean.to_csv(processed_dir / OUTPUT_FILES["usd_inr_daily_clean"], index=False)

    monthly_df = read_csv_dataset(project_root / "data/raw/03_USD_INR_Exchange_Rate_Monthly.csv")
    monthly_df = monthly_df.rename(columns={"observation_date": "date", "EXINUS": "value"})
    month_clean = clean_simple_series(monthly_df, "date", "value", frequency="M")
    month_clean = month_clean.rename(columns={"value": "usd_inr_monthly"})
    month_clean.to_csv(processed_dir / OUTPUT_FILES["usd_inr_monthly_clean"], index=False)

    repo_df = read_csv_dataset(project_root / "data/raw/04_India_RBI_Policy_Repo_Rate_Monthly.csv")
    repo_df = repo_df.rename(columns={"period": "date", "value": "repo_rate"})
    repo_clean = clean_simple_series(repo_df, "date", "repo_rate")
    repo_clean = repo_clean.rename(columns={"repo_rate": "repo_rate"})
    repo_clean.to_csv(processed_dir / OUTPUT_FILES["repo_rate_clean"], index=False)

    neer_df = read_neer_reer_dataset(
        project_root / "data/raw/05_India_RBI_NEER_REER_40_Currency_Monthly.csv"
    )
    neer_df = neer_df.rename(columns={"Date": "date"})
    neer_df = ensure_date_column(neer_df, "date")
    for col in ["Trade_NEER", "Trade_REER", "Export_NEER", "Export_REER"]:
        if col in neer_df.columns:
            neer_df[col] = pd.to_numeric(neer_df[col], errors="coerce")
    neer_df = neer_df.drop_duplicates(subset=["date"]).sort_values("date").reset_index(drop=True)
    neer_df.to_csv(processed_dir / OUTPUT_FILES["neer_reer_monthly_clean"], index=False)

    current_df = load_cpi_series(
        project_root / "data/raw/06_India_CPI_General_Combined_Monthly_2024_Base.xlsx", "Current"
    )
    back_df = load_cpi_series(
        project_root / "data/raw/07_India_CPI_General_Combined_Back_Series_2024_Base.xlsx", "Back"
    )
    current_df = (
        current_df.drop_duplicates(subset=["observation_date"])
        .sort_values("observation_date")
        .reset_index(drop=True)
    )
    back_df = (
        back_df.drop_duplicates(subset=["observation_date"])
        .sort_values("observation_date")
        .reset_index(drop=True)
    )
    current_df.to_csv(processed_dir / OUTPUT_FILES["cpi_current_series_clean"], index=False)
    back_df.to_csv(processed_dir / OUTPUT_FILES["cpi_back_series_clean"], index=False)
    cpi_combined = combine_cpi_series(current_df, back_df)
    cpi_combined = cpi_combined.rename(columns={"observation_date": "date"})
    cpi_combined.to_csv(processed_dir / OUTPUT_FILES["cpi_monthly_clean"], index=False)

    wpi_long = read_wpi_monthly_long(
        project_root / "data/raw/08_India_WPI_Monthly_Index_2011_12_Base_Raw.xls"
    )
    wpi_long = wpi_long.rename(columns={"observation_date": "date", "index_value": "index_value"})
    wpi_long = (
        wpi_long.drop_duplicates(subset=["comm_name", "comm_code", "date"])
        .sort_values("date")
        .reset_index(drop=True)
    )
    wpi_long.to_csv(processed_dir / OUTPUT_FILES["wpi_monthly_clean"], index=False)

    wpi_all_commodities = wpi_long[
        wpi_long["comm_name"].astype(str).str.lower().str.contains("all commodities", na=False)
    ][["date", "index_value"]].rename(columns={"index_value": "wpi_all_commodities_index"})
    macro_panel = build_monthly_macro_panel(
        brent_df=brent_clean,
        usd_inr_monthly_df=month_clean,
        repo_df=repo_clean,
        neer_df=neer_df,
        cpi_df=cpi_combined[["date", "index_value"]].rename(
            columns={"index_value": "cpi_general_index"}
        ),
        wpi_df=wpi_all_commodities,
    )
    macro_panel = macro_panel.sort_values("date").reset_index(drop=True)
    macro_panel.to_csv(processed_dir / OUTPUT_FILES["monthly_macro_panel"], index=False)

    imported_panel = build_monthly_imported_inflation_panel(
        brent_df=brent_clean,
        usd_inr_monthly_df=month_clean,
        repo_df=repo_clean,
        neer_df=neer_df,
        cpi_df=cpi_combined[["date", "index_value"]].rename(
            columns={"index_value": "cpi_general_index"}
        ),
        wpi_df=wpi_all_commodities,
    )
    imported_panel = imported_panel.sort_values("date").reset_index(drop=True)
    imported_panel.to_csv(
        processed_dir / OUTPUT_FILES["monthly_imported_inflation_panel"], index=False
    )

    daily_panel = build_daily_exchange_rate_panel(
        daily_clean.rename(columns={"date": "date", "usd_inr_daily": "usd_inr_daily"})
    )
    daily_panel.to_csv(processed_dir / OUTPUT_FILES["daily_exchange_rate_panel"], index=False)

    validation_summary: dict[str, pd.DataFrame] = {
        "brent": brent_clean,
        "usd_inr_daily": daily_clean,
        "usd_inr_monthly": month_clean,
        "repo_rate": repo_clean,
        "neer_reer": neer_df,
        "cpi_current": current_df,
        "cpi_back": back_df,
        "cpi_combined": cpi_combined,
        "wpi": wpi_long,
        "monthly_macro_panel": macro_panel,
        "monthly_imported_inflation_panel": imported_panel,
        "daily_exchange_rate_panel": daily_panel,
    }
    return validation_summary
