"""Tests for exploratory-data-analysis calculations and outputs."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.visualization.eda import (
    compute_descriptive_statistics,
    compute_episode_summary,
    generate_eda_outputs,
)


def test_descriptive_statistics_include_key_moments() -> None:
    summary = compute_descriptive_statistics()
    required = {
        "category",
        "variable",
        "n",
        "mean",
        "median",
        "std",
        "min",
        "p25",
        "p75",
        "max",
        "skew",
        "kurtosis",
        "missing",
        "cv",
    }
    assert required.issubset(summary.columns)
    assert not summary.empty
    assert "Exchange rate" in summary["category"].unique()


def test_episode_summary_returns_threshold_based_rows() -> None:
    episodes = compute_episode_summary()
    assert isinstance(episodes, pd.DataFrame)
    required = {
        "episode_type",
        "start_date",
        "end_date",
        "duration_months",
        "threshold",
        "max_value",
    }
    assert required.issubset(episodes.columns)


def test_generate_eda_outputs_creates_reports_and_visuals() -> None:
    outputs = generate_eda_outputs()
    for target in outputs.values():
        assert Path(target).exists()
    assert (Path("visualizations") / "eda" / "exchange_rate" / "usd_inr_overview.png").exists()
    assert (Path("visualizations") / "eda" / "correlations" / "pearson_heatmap.png").exists()
