"""Tests for feature-engineering output generation and formulas."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from src.features.feature_engineering import (
    build_brent_features,
    build_brent_inr_proxy_features,
    build_cpi_features,
    build_exchange_rate_features,
    build_wpi_features,
    generate_feature_outputs,
)


def test_exchange_rate_features_partition_depreciation_and_appreciation() -> None:
    exchange = pd.DataFrame(
        {
            "date": pd.to_datetime(["2024-01-01", "2024-02-01", "2024-03-01", "2024-04-01"]),
            "usd_inr_monthly": [80.0, 82.0, 81.0, 84.0],
        }
    )
    features = build_exchange_rate_features(exchange)

    assert features["usd_inr_mom_change"].iloc[1] == pytest.approx(2.0)
    assert features["usd_inr_mom_pct_change"].iloc[1] == pytest.approx(2.5)
    assert features["usd_inr_depreciation_log_change"].iloc[1] > 0
    assert features["usd_inr_appreciation_log_change"].iloc[2] > 0
    assert features["usd_inr_3m_cumulative_change_pct"].iloc[3] == pytest.approx(
        ((84.0 / 80.0) - 1.0) * 100.0
    )


def test_brent_inr_proxy_matches_product_of_underlying_series() -> None:
    brent = pd.DataFrame(
        {
            "date": pd.to_datetime(["2024-01-01", "2024-02-01", "2024-03-01"]),
            "brent_usd_per_barrel": [70.0, 72.0, 75.0],
        }
    )
    exchange = pd.DataFrame(
        {
            "date": pd.to_datetime(["2024-01-01", "2024-02-01", "2024-03-01"]),
            "usd_inr_monthly": [80.0, 81.0, 82.0],
        }
    )
    features = build_brent_inr_proxy_features(brent, exchange)
    assert features["brent_inr_proxy_level"].tolist() == pytest.approx([5600.0, 5832.0, 6150.0])
    assert features["brent_inr_proxy_mom_pct_change"].iloc[1] == pytest.approx(
        ((5832.0 / 5600.0) - 1.0) * 100.0
    )


def test_cpi_features_keep_published_inflation_separate() -> None:
    months = pd.date_range("2023-01-01", periods=13, freq="MS")
    cpi = pd.DataFrame(
        {
            "date": months,
            "index_value": [100.0 + i for i in range(13)],
            "inflation_value": [
                None,
                1.2,
                2.8,
                None,
                3.0,
                3.1,
                None,
                2.6,
                2.4,
                None,
                3.2,
                3.8,
                None,
            ],
        }
    )
    features = build_cpi_features(cpi)
    assert features["cpi_12m_index_inflation"].iloc[-1] == pytest.approx(
        ((112.0 / 100.0) - 1.0) * 100.0
    )
    assert pd.isna(features["cpi_published_inflation"].iloc[0])
    assert pd.isna(features["cpi_1m_index_lag"].iloc[0])


def test_wpi_features_preserve_all_commodities_and_weights() -> None:
    wpi = pd.DataFrame(
        {
            "date": pd.to_datetime(["2024-01-01", "2024-01-01", "2024-02-01", "2024-02-01"]),
            "comm_name": [
                "All commodities",
                "Primary Articles",
                "All commodities",
                "Primary Articles",
            ],
            "comm_code": [1000000000, 1100000000, 1000000000, 1100000000],
            "comm_wt": [100.0, 45.0, 100.0, 45.0],
            "index_value": [104.7, 103.4, 105.2, 103.9],
        }
    )
    features = build_wpi_features(wpi)
    assert "wpi_all_commodities_index" in features.columns
    assert features["wpi_all_commodities_index"].iloc[0] == pytest.approx(104.7)
    assert features["wpi_all_commodities_mom_change"].iloc[1] == pytest.approx(0.5)


def test_generate_feature_outputs_creates_expected_files() -> None:
    project_root = Path(__file__).resolve().parents[1]
    outputs = generate_feature_outputs(project_root)
    assert set(outputs) == {
        "exchange_rate_features",
        "brent_features",
        "brent_inr_proxy_features",
        "cpi_features",
        "repo_rate_features",
        "neer_reer_features",
        "wpi_features",
        "research_master_feature_panel",
    }


def test_master_feature_panel_has_unique_feature_names() -> None:
    project_root = Path(__file__).resolve().parents[1]
    panel = generate_feature_outputs(project_root)["research_master_feature_panel"]
    assert not panel.columns.duplicated().any()
    assert "usd_inr_monthly" in panel.columns
    assert "usd_inr_monthly_x" not in panel.columns
    assert "usd_inr_monthly_y" not in panel.columns


def test_brent_rolling_volatility_is_past_window_only() -> None:
    brent = pd.DataFrame(
        {
            "date": pd.to_datetime(
                [
                    "2024-01-01",
                    "2024-02-01",
                    "2024-03-01",
                    "2024-04-01",
                    "2024-05-01",
                    "2024-06-01",
                ]
            ),
            "brent_usd_per_barrel": [70.0, 72.0, 75.0, 74.0, 76.0, 80.0],
        }
    )
    features = build_brent_features(brent)
    assert pd.isna(features["brent_6m_rolling_volatility"].iloc[0])
    assert pd.isna(features["brent_6m_rolling_volatility"].iloc[1])
    assert pd.notna(features["brent_6m_rolling_volatility"].iloc[3])
    assert features["brent_6m_rolling_volatility"].iloc[3] > 0
