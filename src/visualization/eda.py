"""Exploratory data analysis for the POME EL feature-engineering outputs."""

from __future__ import annotations

import warnings
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from statsmodels.tsa.stattools import adfuller, kpss

ROOT = Path(__file__).resolve().parents[2]
PROCESSED_DIR = ROOT / "data" / "processed"
FEATURE_DIR = PROCESSED_DIR / "features"
VISUALIZATION_DIR = ROOT / "visualizations" / "eda"
REPORT_DIR = ROOT / "reports" / "research"

sns.set_theme(style="whitegrid")


def _safe_numeric(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce")


def _as_date_frame(frame: pd.DataFrame, date_col: str = "date") -> pd.DataFrame:
    output = frame.copy()
    output[date_col] = pd.to_datetime(output[date_col], errors="coerce")
    output = output.dropna(subset=[date_col]).sort_values(date_col).reset_index(drop=True)
    return output


def _summary_row(category: str, variable: str, series: pd.Series) -> dict[str, object]:
    clean = _safe_numeric(series).dropna()
    if clean.empty:
        return {
            "category": category,
            "variable": variable,
            "n": 0,
            "mean": np.nan,
            "median": np.nan,
            "std": np.nan,
            "min": np.nan,
            "p25": np.nan,
            "p75": np.nan,
            "max": np.nan,
            "skew": np.nan,
            "kurtosis": np.nan,
            "missing": int(series.isna().sum()),
            "cv": np.nan,
        }

    mean = float(clean.mean())
    std = float(clean.std(ddof=1)) if len(clean) > 1 else 0.0
    cv = std / abs(mean) if mean != 0 else np.nan
    return {
        "category": category,
        "variable": variable,
        "n": int(clean.size),
        "mean": mean,
        "median": float(clean.median()),
        "std": std,
        "min": float(clean.min()),
        "p25": float(clean.quantile(0.25)),
        "p75": float(clean.quantile(0.75)),
        "max": float(clean.max()),
        "skew": float(clean.skew()),
        "kurtosis": float(clean.kurt()),
        "missing": int(series.isna().sum()),
        "cv": cv,
    }


def compute_descriptive_statistics() -> pd.DataFrame:
    """Create descriptive statistics for the core engineered-variable families."""
    exchange = pd.read_csv(FEATURE_DIR / "exchange_rate_features.csv")
    brent = pd.read_csv(FEATURE_DIR / "brent_features.csv")
    brent_proxy = pd.read_csv(FEATURE_DIR / "brent_inr_proxy_features.csv")
    cpi = pd.read_csv(FEATURE_DIR / "cpi_features.csv")
    repo = pd.read_csv(FEATURE_DIR / "repo_rate_features.csv")
    neer = pd.read_csv(FEATURE_DIR / "neer_reer_features.csv")
    wpi = pd.read_csv(FEATURE_DIR / "wpi_features.csv")

    variable_sets: dict[str, list[str]] = {
        "Exchange rate": [
            "usd_inr_level",
            "usd_inr_mom_change",
            "usd_inr_mom_pct_change",
            "usd_inr_log_change",
            "usd_inr_depreciation_log_change",
            "usd_inr_appreciation_log_change",
        ],
        "Brent price": [
            "brent_usd_per_barrel_level",
            "brent_mom_pct_change",
            "brent_6m_rolling_volatility",
        ],
        "Brent-INR proxy": [
            "brent_inr_proxy_level",
            "brent_inr_proxy_mom_pct_change",
            "brent_inr_proxy_log_change",
        ],
        "CPI": [
            "cpi_index_level",
            "cpi_published_inflation",
            "cpi_3m_index_inflation",
            "cpi_12m_index_inflation",
        ],
        "Repo rate": ["repo_rate_level", "repo_rate_change_pp"],
        "NEER/REER": [
            "Trade_NEER_level",
            "Trade_REER_level",
            "Trade_NEER_mom_pct_change",
            "Trade_REER_mom_pct_change",
        ],
        "WPI": [
            "wpi_all_commodities_index",
            "wpi_all_commodities_mom_change",
            "wpi_all_commodities_mom_pct_change",
            "wpi_all_commodities_yoy_inflation",
        ],
    }

    datasets = {
        "Exchange rate": exchange,
        "Brent price": brent,
        "Brent-INR proxy": brent_proxy,
        "CPI": cpi,
        "Repo rate": repo,
        "NEER/REER": neer,
        "WPI": wpi,
    }

    rows: list[dict[str, object]] = []
    for category, variable_list in variable_sets.items():
        frame = datasets[category]
        for variable in variable_list:
            if variable not in frame.columns:
                continue
            rows.append(_summary_row(category, variable, frame[variable]))

    output = pd.DataFrame(rows)
    output["n"] = output["n"].astype(int)
    output["missing"] = output["missing"].astype(int)
    return output.sort_values(["category", "variable"]).reset_index(drop=True)


def _ensure_output_dirs() -> None:
    for subdir in [
        "exchange_rate",
        "brent",
        "inflation",
        "pass_through",
        "wpi",
        "correlations",
        "diagnostics",
        "missingness",
    ]:
        (VISUALIZATION_DIR / subdir).mkdir(parents=True, exist_ok=True)


def plot_exchange_rate_summary() -> None:
    exchange = _as_date_frame(pd.read_csv(FEATURE_DIR / "exchange_rate_features.csv"))
    fig, axes = plt.subplots(2, 1, figsize=(12, 10))
    axes[0].plot(exchange["date"], exchange["usd_inr_level"], color="navy")
    axes[0].set_title("USD/INR monthly exchange-rate level")
    axes[0].set_ylabel("INR per USD")
    axes[0].grid(True, alpha=0.3)

    axes[1].bar(exchange["date"], exchange["usd_inr_mom_pct_change"], color="darkorange", width=20)
    axes[1].axhline(0, color="black", linewidth=1)
    axes[1].set_title("USD/INR monthly percentage change")
    axes[1].set_ylabel("Percent")
    axes[1].grid(True, alpha=0.3)
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(VISUALIZATION_DIR / "exchange_rate" / "usd_inr_overview.png", dpi=220)
    plt.close(fig)


def plot_brent_and_proxy() -> None:
    brent = _as_date_frame(pd.read_csv(FEATURE_DIR / "brent_features.csv"))
    proxy = _as_date_frame(pd.read_csv(FEATURE_DIR / "brent_inr_proxy_features.csv"))

    fig, axes = plt.subplots(2, 1, figsize=(12, 10))
    axes[0].plot(brent["date"], brent["brent_usd_per_barrel_level"], color="forestgreen")
    axes[0].set_title("Brent crude oil price")
    axes[0].set_ylabel("USD per barrel")
    axes[0].grid(True, alpha=0.3)

    axes[1].plot(proxy["date"], proxy["brent_inr_proxy_level"], color="darkred")
    axes[1].set_title("Brent-INR proxy (approximate INR per barrel)")
    axes[1].set_ylabel("Approximate INR per barrel")
    axes[1].grid(True, alpha=0.3)
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(VISUALIZATION_DIR / "brent" / "brent_and_proxy.png", dpi=220)
    plt.close(fig)


def plot_cpi_and_repo() -> None:
    cpi = _as_date_frame(pd.read_csv(FEATURE_DIR / "cpi_features.csv"))
    repo = _as_date_frame(pd.read_csv(FEATURE_DIR / "repo_rate_features.csv"))

    fig, axes = plt.subplots(2, 1, figsize=(12, 10))
    axes[0].plot(cpi["date"], cpi["cpi_index_level"], color="crimson")
    axes[0].set_title("CPI index level")
    axes[0].set_ylabel("Index")
    axes[0].grid(True, alpha=0.3)

    axes[1].plot(repo["date"], repo["repo_rate_level"], color="purple")
    axes[1].set_title("Policy repo rate")
    axes[1].set_ylabel("Percent")
    axes[1].grid(True, alpha=0.3)
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(VISUALIZATION_DIR / "inflation" / "cpi_and_repo.png", dpi=220)
    plt.close(fig)


def plot_neer_reer_and_wpi() -> None:
    neer = _as_date_frame(pd.read_csv(FEATURE_DIR / "neer_reer_features.csv"))
    wpi = _as_date_frame(pd.read_csv(FEATURE_DIR / "wpi_features.csv"))

    fig, axes = plt.subplots(2, 1, figsize=(12, 10))
    axes[0].plot(neer["date"], neer["Trade_NEER_level"], label="Trade NEER", color="tab:blue")
    axes[0].plot(neer["date"], neer["Trade_REER_level"], label="Trade REER", color="tab:orange")
    axes[0].set_title("NEER and REER indices")
    axes[0].set_ylabel("Index")
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)

    axes[1].plot(wpi["date"], wpi["wpi_all_commodities_index"], color="teal")
    axes[1].set_title("WPI All Commodities index")
    axes[1].set_ylabel("Index")
    axes[1].grid(True, alpha=0.3)
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(VISUALIZATION_DIR / "wpi" / "neer_reer_and_wpi.png", dpi=220)
    plt.close(fig)


def plot_correlations() -> None:
    panel = _as_date_frame(pd.read_csv(FEATURE_DIR / "research_master_feature_panel.csv"))
    subset = panel[
        [
            "usd_inr_mom_pct_change",
            "brent_mom_pct_change",
            "cpi_published_inflation",
            "wpi_all_commodities_mom_pct_change",
            "repo_rate_change_pp",
            "Trade_NEER_mom_pct_change",
            "Trade_REER_mom_pct_change",
        ]
    ].dropna()
    corr = subset.corr(method="pearson")
    fig, ax = plt.subplots(figsize=(10, 8))
    sns.heatmap(corr, cmap="coolwarm", annot=True, fmt=".2f", linewidths=0.5, ax=ax)
    ax.set_title("Pearson correlation heatmap (common non-missing observations)")
    fig.tight_layout()
    fig.savefig(VISUALIZATION_DIR / "correlations" / "pearson_heatmap.png", dpi=220)
    plt.close(fig)


# A small set of additional diagnostics for EDA outputs.
def compute_correlation_results() -> pd.DataFrame:
    panel = _as_date_frame(pd.read_csv(FEATURE_DIR / "research_master_feature_panel.csv"))
    pairs = [
        ("usd_inr_mom_change", "cpi_published_inflation"),
        ("usd_inr_depreciation_log_change", "cpi_published_inflation"),
        ("usd_inr_appreciation_log_change", "cpi_published_inflation"),
        ("brent_mom_pct_change", "cpi_published_inflation"),
        ("brent_inr_proxy_mom_pct_change", "cpi_published_inflation"),
        ("Trade_NEER_mom_pct_change", "cpi_published_inflation"),
        ("Trade_REER_mom_pct_change", "cpi_published_inflation"),
        ("repo_rate_change_pp", "cpi_published_inflation"),
        ("wpi_all_commodities_mom_pct_change", "cpi_published_inflation"),
    ]

    rows: list[dict[str, object]] = []
    for left, right in pairs:
        merged = panel[["date", left, right]].dropna()
        pearson = merged[left].corr(merged[right], method="pearson")
        spearman = merged[left].corr(merged[right], method="spearman")
        rows.append(
            {
                "left_variable": left,
                "right_variable": right,
                "n_common": int(len(merged)),
                "pearson": pearson,
                "spearman": spearman,
            }
        )
    return pd.DataFrame(rows)


def compute_stationarity_results() -> pd.DataFrame:
    exchange = _as_date_frame(pd.read_csv(FEATURE_DIR / "exchange_rate_features.csv"))
    brent = _as_date_frame(pd.read_csv(FEATURE_DIR / "brent_features.csv"))
    cpi = _as_date_frame(pd.read_csv(FEATURE_DIR / "cpi_features.csv"))
    wpi = _as_date_frame(pd.read_csv(FEATURE_DIR / "wpi_features.csv"))
    series_map = {
        "usd_inr_level": exchange["usd_inr_level"],
        "brent_usd_per_barrel_level": brent["brent_usd_per_barrel_level"],
        "cpi_index_level": cpi["cpi_index_level"],
        "wpi_all_commodities_index": wpi["wpi_all_commodities_index"],
        "Trade_NEER_level": pd.read_csv(FEATURE_DIR / "neer_reer_features.csv")["Trade_NEER_level"],
    }

    results: list[dict[str, object]] = []
    for name, series in series_map.items():
        clean = _safe_numeric(series).dropna()
        if clean.empty:
            continue
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=FutureWarning)
            warnings.filterwarnings("ignore", category=UserWarning)
            warnings.filterwarnings("ignore", category=RuntimeWarning)
            try:
                adf_result = adfuller(clean, autolag="AIC")
                adf_stat = float(adf_result[0])
                adf_pvalue = float(adf_result[1])
            except ValueError:
                adf_stat, adf_pvalue = np.nan, np.nan
            try:
                kpss_result = kpss(clean, regression="c", nlags="auto")
                kpss_stat = float(kpss_result[0])
                kpss_pvalue = float(kpss_result[1])
            except ValueError:
                kpss_stat, kpss_pvalue = np.nan, np.nan
        results.append(
            {
                "variable": name,
                "n": int(clean.size),
                "adf_stat": adf_stat,
                "adf_pvalue": adf_pvalue,
                "kpss_stat": kpss_stat,
                "kpss_pvalue": kpss_pvalue,
            }
        )
    return pd.DataFrame(results)


def compute_episode_summary() -> pd.DataFrame:
    exchange = _as_date_frame(pd.read_csv(FEATURE_DIR / "exchange_rate_features.csv"))
    cpi = _as_date_frame(pd.read_csv(FEATURE_DIR / "cpi_features.csv"))
    brent = _as_date_frame(pd.read_csv(FEATURE_DIR / "brent_features.csv"))
    panel = exchange[["date", "usd_inr_mom_pct_change"]].merge(
        cpi[["date", "cpi_published_inflation"]], on="date", how="outer"
    ).merge(brent[["date", "brent_usd_per_barrel_level"]], on="date", how="outer")
    panel = panel.sort_values("date").reset_index(drop=True)

    dep_threshold = panel["usd_inr_mom_pct_change"].quantile(0.9)
    inflation_threshold = panel["cpi_published_inflation"].quantile(0.9)
    brent_threshold = panel["brent_usd_per_barrel_level"].quantile(0.9)

    rows: list[dict[str, object]] = []
    for category, column, threshold in [
        ("depreciation", "usd_inr_mom_pct_change", dep_threshold),
        ("inflation", "cpi_published_inflation", inflation_threshold),
        ("brent_high", "brent_usd_per_barrel_level", brent_threshold),
    ]:
        mask = panel[column].ge(threshold)
        if not mask.any():
            continue
        starts = panel.loc[mask & ~mask.shift(fill_value=False).fillna(False), "date"]
        ends = panel.loc[mask & ~mask.shift(-1, fill_value=False).fillna(False), "date"]
        for start, end in zip(starts, ends, strict=False):
            sub = panel[(panel["date"] >= start) & (panel["date"] <= end)]
            rows.append(
                {
                    "episode_type": category,
                    "start_date": start,
                    "end_date": end,
                    "duration_months": int((end - start).days / 30.4375) + 1,
                    "threshold": float(threshold),
                    "max_value": float(sub[column].max()),
                }
            )
    return pd.DataFrame(rows)


def create_missingness_summary() -> pd.DataFrame:
    panel = _as_date_frame(pd.read_csv(FEATURE_DIR / "research_master_feature_panel.csv"))
    missing = panel.isna().sum().sort_values(ascending=False)
    return missing.reset_index().rename(columns={"index": "variable", 0: "missing_count"})


def generate_eda_outputs() -> dict[str, Path]:
    """Generate EDA statistics, charts, and summary outputs."""
    _ensure_output_dirs()

    descriptive = compute_descriptive_statistics()
    descriptive.to_csv(REPORT_DIR / "EDA_DESCRIPTIVE_STATISTICS.csv", index=False)

    correlation_results = compute_correlation_results()
    correlation_results.to_csv(REPORT_DIR / "EDA_CORRELATION_RESULTS.csv", index=False)

    stationarity = compute_stationarity_results()
    stationarity.to_csv(REPORT_DIR / "EDA_STATIONARITY_RESULTS.csv", index=False)

    episodes = compute_episode_summary()
    episodes.to_csv(REPORT_DIR / "EDA_EPISODE_SUMMARY.csv", index=False)

    missing_summary = create_missingness_summary()
    missing_summary.to_csv(REPORT_DIR / "EDA_MISSINGNESS_SUMMARY.csv", index=False)

    plot_exchange_rate_summary()
    plot_brent_and_proxy()
    plot_cpi_and_repo()
    plot_neer_reer_and_wpi()
    plot_correlations()

    missing_heatmap = pd.read_csv(FEATURE_DIR / "research_master_feature_panel.csv")
    missing_heatmap = _as_date_frame(missing_heatmap)
    fig, ax = plt.subplots(figsize=(12, 8))
    heatmap = missing_heatmap.isna().astype(int)
    sns.heatmap(heatmap.iloc[:, 1:30], ax=ax, cmap="Blues", cbar_kws={"label": "missing indicator"})
    ax.set_title("Missingness heatmap for early feature columns")
    fig.tight_layout()
    fig.savefig(VISUALIZATION_DIR / "missingness" / "feature_missingness_heatmap.png", dpi=220)
    plt.close(fig)

    return {
        "descriptive": REPORT_DIR / "EDA_DESCRIPTIVE_STATISTICS.csv",
        "correlation": REPORT_DIR / "EDA_CORRELATION_RESULTS.csv",
        "stationarity": REPORT_DIR / "EDA_STATIONARITY_RESULTS.csv",
        "episodes": REPORT_DIR / "EDA_EPISODE_SUMMARY.csv",
    }
