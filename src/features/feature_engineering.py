"""Feature engineering for the POME EL research pipeline.

These functions create economically interpretable time-series features from the
verified processed datasets while preserving the original source values and
avoid- ing forward-looking leakage. All calculations are based only on current and
past observations within the same series.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


def _prepare_time_series(df: pd.DataFrame, date_col: str) -> pd.DataFrame:
    """Standardize a time series to a sorted date index with valid dates only."""
    output = df.copy()
    output[date_col] = pd.to_datetime(output[date_col], errors="coerce")
    output = output.dropna(subset=[date_col]).sort_values(date_col).reset_index(drop=True)
    return output


def _pct_change(series: pd.Series) -> pd.Series:
    """Return percentage change in decimal units times 100."""
    return series.pct_change().mul(100.0)


def _log_change(series: pd.Series) -> pd.Series:
    """Return log difference times 100, preserving missing values."""
    numeric = pd.to_numeric(series, errors="coerce")
    positive = numeric[numeric > 0]
    result = pd.Series(np.nan, index=numeric.index, dtype=float)
    if positive.empty:
        return result
    result.loc[positive.index] = np.log(positive).diff().mul(100.0)
    return result.reindex(numeric.index)


def _period_cumulative_change(series: pd.Series, periods: int) -> pd.Series:
    """Return cumulative percentage change over a horizon in percentage points."""
    return ((series / series.shift(periods)) - 1.0).mul(100.0)


def build_exchange_rate_features(monthly_df: pd.DataFrame) -> pd.DataFrame:
    """Construct monthly USD/INR exchange-rate features.

    A rise in INR per USD indicates rupee depreciation. Features explicitly keep the
    sign of exchange-rate movements so depreciation and appreciation remain
    separately identifiable.
    """
    df = _prepare_time_series(monthly_df, "date")
    df = df[["date", "usd_inr_monthly"]].copy()
    df = df.rename(columns={"usd_inr_monthly": "usd_inr_level"})

    df["usd_inr_mom_change"] = df["usd_inr_level"].diff()
    df["usd_inr_mom_pct_change"] = _pct_change(df["usd_inr_level"])
    df["usd_inr_log_change"] = _log_change(df["usd_inr_level"])
    df["usd_inr_depreciation_log_change"] = df["usd_inr_log_change"].clip(lower=0)
    df["usd_inr_appreciation_log_change"] = (-df["usd_inr_log_change"]).clip(lower=0)

    for periods in (3, 6, 12):
        df[f"usd_inr_{periods}m_cumulative_change_pct"] = _period_cumulative_change(
            df["usd_inr_level"], periods
        )
        df[f"usd_inr_{periods}m_level_change"] = df["usd_inr_level"].diff(periods)

    return df


def build_brent_features(brent_df: pd.DataFrame) -> pd.DataFrame:
    """Construct monthly Brent crude-oil features."""
    df = _prepare_time_series(brent_df, "date")
    df = df[["date", "brent_usd_per_barrel"]].copy()
    df = df.rename(columns={"brent_usd_per_barrel": "brent_usd_per_barrel_level"})

    df["brent_mom_pct_change"] = _pct_change(df["brent_usd_per_barrel_level"])
    df["brent_log_change"] = _log_change(df["brent_usd_per_barrel_level"])
    for periods in (3, 6, 12):
        df[f"brent_{periods}m_cumulative_change_pct"] = _period_cumulative_change(
            df["brent_usd_per_barrel_level"], periods
        )

    df["brent_6m_rolling_volatility"] = (
        df["brent_log_change"].rolling(window=6, min_periods=3).std().mul(100.0)
    )
    return df


def build_brent_inr_proxy_features(
    brent_df: pd.DataFrame,
    monthly_exchange_df: pd.DataFrame,
) -> pd.DataFrame:
    """Construct the exchange-rate-adjusted crude-oil proxy in INR per barrel."""
    brent = _prepare_time_series(brent_df, "date")[["date", "brent_usd_per_barrel"]].copy()
    exchange = _prepare_time_series(monthly_exchange_df, "date")[["date", "usd_inr_monthly"]].copy()
    merged = brent.merge(exchange, on="date", how="inner")

    merged["brent_inr_proxy_level"] = merged["brent_usd_per_barrel"] * merged["usd_inr_monthly"]
    merged["brent_inr_proxy_mom_pct_change"] = _pct_change(merged["brent_inr_proxy_level"])
    merged["brent_inr_proxy_log_change"] = _log_change(merged["brent_inr_proxy_level"])
    for periods in (3, 6, 12):
        merged[f"brent_inr_proxy_{periods}m_cumulative_change_pct"] = _period_cumulative_change(
            merged["brent_inr_proxy_level"], periods
        )
    return merged


def build_cpi_features(cpi_df: pd.DataFrame) -> pd.DataFrame:
    """Construct CPI index and inflation features while preserving source labels."""
    df = _prepare_time_series(cpi_df, "date")
    df = df[["date", "index_value", "inflation_value"]].copy()

    df["cpi_index_level"] = pd.to_numeric(df["index_value"], errors="coerce")
    df["cpi_published_inflation"] = pd.to_numeric(df["inflation_value"], errors="coerce")
    df["cpi_mom_change_index"] = df["cpi_index_level"].diff()
    df["cpi_mom_pct_change_index"] = _pct_change(df["cpi_index_level"])

    for periods in (3, 6, 12):
        df[f"cpi_{periods}m_index_inflation"] = _period_cumulative_change(
            df["cpi_index_level"], periods
        )
        df[f"cpi_{periods}m_index_lag"] = df["cpi_index_level"].shift(periods)

    df["cpi_1m_index_lag"] = df["cpi_index_level"].shift(1)
    df["cpi_2m_index_lag"] = df["cpi_index_level"].shift(2)
    df["cpi_3m_index_lag"] = df["cpi_index_level"].shift(3)
    df["cpi_6m_index_lag"] = df["cpi_index_level"].shift(6)
    df["cpi_12m_index_lag"] = df["cpi_index_level"].shift(12)

    df["cpi_1m_inflation_lag"] = df["cpi_published_inflation"].shift(1)
    df["cpi_2m_inflation_lag"] = df["cpi_published_inflation"].shift(2)
    df["cpi_3m_inflation_lag"] = df["cpi_published_inflation"].shift(3)
    df["cpi_6m_inflation_lag"] = df["cpi_published_inflation"].shift(6)
    df["cpi_12m_inflation_lag"] = df["cpi_published_inflation"].shift(12)

    return df


def build_repo_rate_features(repo_rate_df: pd.DataFrame) -> pd.DataFrame:
    """Construct repo-rate features while preserving the original policy-rate convention."""
    df = _prepare_time_series(repo_rate_df, "date")
    df = df[["date", "repo_rate"]].copy()
    df["repo_rate_level"] = pd.to_numeric(df["repo_rate"], errors="coerce")
    df["repo_rate_change_pp"] = df["repo_rate_level"].diff()
    df["repo_rate_3m_change_pp"] = df["repo_rate_level"].diff(3)
    df["repo_rate_6m_change_pp"] = df["repo_rate_level"].diff(6)
    df["repo_rate_change_indicator"] = df["repo_rate_change_pp"].ne(0).astype(int)
    return df


def _series_change_features(
    df: pd.DataFrame, series_name: str, periods: tuple[int, ...]
) -> pd.DataFrame:
    """Add percentage and cumulative changes for a single index series."""
    for period in periods:
        df[f"{series_name}_{period}m_pct_change"] = _pct_change(df[series_name])
        df[f"{series_name}_{period}m_cumulative_change_pct"] = _period_cumulative_change(
            df[series_name], period
        )
    return df


def build_neer_reer_features(neer_reer_df: pd.DataFrame) -> pd.DataFrame:
    """Construct NEER/REER percentage and cumulative changes while keeping series separate."""
    df = _prepare_time_series(neer_reer_df, "date")
    series = [
        "Trade_NEER",
        "Trade_REER",
        "Export_NEER",
        "Export_REER",
    ]
    for name in series:
        df[f"{name}_level"] = pd.to_numeric(df[name], errors="coerce")
        df[f"{name}_mom_pct_change"] = _pct_change(df[f"{name}_level"])
        df[f"{name}_log_change"] = _log_change(df[f"{name}_level"])
        for periods in (3, 6, 12):
            df[f"{name}_{periods}m_cumulative_change_pct"] = _period_cumulative_change(
                df[f"{name}_level"], periods
            )
    return df


def build_wpi_features(wpi_df: pd.DataFrame) -> pd.DataFrame:
    """Construct headline WPI features from the commodity-long workbook."""
    df = _prepare_time_series(wpi_df, "date")
    all_commodities = df[
        df["comm_name"].astype(str).str.strip().str.lower() == "all commodities"
    ].copy()
    categories = {
        "primary_articles": "Primary Articles",
        "fuel_and_power": "Fuel & Power",
        "manufactured_products": "Manufactured Products",
    }

    output = all_commodities[["date", "comm_name", "comm_code", "comm_wt", "index_value"]].copy()
    output = output.rename(columns={"index_value": "wpi_all_commodities_index"})
    output["wpi_all_commodities_mom_change"] = output["wpi_all_commodities_index"].diff()
    output["wpi_all_commodities_mom_pct_change"] = _pct_change(output["wpi_all_commodities_index"])
    output["wpi_all_commodities_yoy_inflation"] = _period_cumulative_change(
        output["wpi_all_commodities_index"], 12
    )

    for key, value in categories.items():
        subset = df[df["comm_name"].astype(str).str.strip().str.lower() == value.lower()].copy()
        if subset.empty:
            continue
        series = subset[["date", "index_value"]].rename(columns={"index_value": f"wpi_{key}_index"})
        output = output.merge(series, on="date", how="outer")
        output[f"wpi_{key}_mom_change"] = output[f"wpi_{key}_index"].diff()
        output[f"wpi_{key}_mom_pct_change"] = _pct_change(output[f"wpi_{key}_index"])

    return output.sort_values("date").reset_index(drop=True)


def build_research_master_feature_panel(
    exchange_rate_features: pd.DataFrame,
    brent_features: pd.DataFrame,
    brent_inr_proxy_features: pd.DataFrame,
    cpi_features: pd.DataFrame,
    repo_rate_features: pd.DataFrame,
    neer_reer_features: pd.DataFrame,
    wpi_features: pd.DataFrame,
) -> pd.DataFrame:
    """Merge the defensible feature sets into a single research panel.

    The master panel is intentionally an outer merge keyed on date to preserve the
    original source coverage and explicit local missingness. No imputation is added.
    Raw series columns that duplicate engineered values are excluded to keep the
    master panel interpretable and single-source per variable.
    """
    exchange = exchange_rate_features.rename(columns={"usd_inr_level": "usd_inr_monthly"}).copy()
    brent = brent_features.copy()
    proxy = brent_inr_proxy_features.drop(
        columns=["brent_usd_per_barrel", "usd_inr_monthly"], errors="ignore"
    ).copy()
    cpi = cpi_features.drop(columns=["index_value", "inflation_value"], errors="ignore").copy()
    repo = repo_rate_features.drop(columns=["repo_rate"], errors="ignore").copy()
    neer_reer = neer_reer_features.drop(
        columns=[
            "Year",
            "Month",
            "Trade_NEER",
            "Trade_REER",
            "Export_NEER",
            "Export_REER",
        ],
        errors="ignore",
    ).copy()
    wpi = wpi_features.drop(columns=["comm_name", "comm_code", "comm_wt"], errors="ignore").copy()

    panel = exchange
    for frame in (brent, proxy, cpi, repo, neer_reer, wpi):
        panel = panel.merge(frame, on="date", how="outer")

    panel = panel.sort_values("date").reset_index(drop=True)
    if panel.columns.duplicated().any():
        duplicate_cols = panel.columns[panel.columns.duplicated()].tolist()
        raise ValueError(f"Duplicate feature names remain in the master panel: {duplicate_cols}")
    return panel


def generate_feature_outputs(root: str | Path | None = None) -> dict[str, pd.DataFrame]:
    """Construct all feature-engineering outputs under data/processed/features."""
    project_root = Path(root) if root is not None else Path(__file__).resolve().parents[2]
    processed_dir = project_root / "data" / "processed"
    feature_dir = processed_dir / "features"
    feature_dir.mkdir(parents=True, exist_ok=True)

    exchange_rate = pd.read_csv(processed_dir / "usd_inr_monthly_clean.csv")
    brent = pd.read_csv(processed_dir / "brent_monthly_clean.csv")
    cpi = pd.read_csv(processed_dir / "cpi_monthly_clean.csv")
    repo = pd.read_csv(processed_dir / "repo_rate_clean.csv")
    neer_reer = pd.read_csv(processed_dir / "neer_reer_monthly_clean.csv")
    wpi = pd.read_csv(processed_dir / "wpi_monthly_clean.csv")

    exchange_features = build_exchange_rate_features(exchange_rate)
    brent_features = build_brent_features(brent)
    brent_proxy_features = build_brent_inr_proxy_features(brent, exchange_rate)
    cpi_features = build_cpi_features(cpi)
    repo_features = build_repo_rate_features(repo)
    neer_reer_features = build_neer_reer_features(neer_reer)
    wpi_features = build_wpi_features(wpi)

    outputs = {
        "exchange_rate_features": exchange_features,
        "brent_features": brent_features,
        "brent_inr_proxy_features": brent_proxy_features,
        "cpi_features": cpi_features,
        "repo_rate_features": repo_features,
        "neer_reer_features": neer_reer_features,
        "wpi_features": wpi_features,
    }

    for name, frame in outputs.items():
        frame.to_csv(feature_dir / f"{name}.csv", index=False)

    master_panel = build_research_master_feature_panel(
        exchange_rate_features=exchange_features,
        brent_features=brent_features,
        brent_inr_proxy_features=brent_proxy_features,
        cpi_features=cpi_features,
        repo_rate_features=repo_features,
        neer_reer_features=neer_reer_features,
        wpi_features=wpi_features,
    )
    master_panel.to_csv(feature_dir / "research_master_feature_panel.csv", index=False)
    return outputs | {"research_master_feature_panel": master_panel}
