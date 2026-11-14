"""Unit tests for deterministic Stage 3 feature construction."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.pass_through.features import build_stage3_features


def _source_panel() -> pd.DataFrame:
    dates = pd.date_range("2013-01-01", "2015-03-01", freq="MS")
    values = np.arange(len(dates), dtype=float)
    fx = 100.0 + values
    fx[12] = 110.0
    fx[13] = 99.0
    return pd.DataFrame(
        {
            "date": dates,
            "usd_inr_monthly": fx,
            "cpi_index": 100.0 + values,
            "cpi_published_inflation": 5.0 + values / 10.0,
            "wpi_all_commodities_index": 100.0 + values * 0.8,
            "wpi_fuel_power_index": 100.0 + values * 0.9,
            "wpi_manufactured_index": 100.0 + values * 0.7,
            "brent_usd_per_barrel": 50.0 + values * 0.2,
            "repo_rate": 6.0 + values * 0.01,
            "Trade_NEER": 100.0 + values * 0.1,
            "Trade_REER": 100.0 + values * 0.2,
            "Export_NEER": 100.0 + values * 0.3,
            "Export_REER": 100.0 + values * 0.4,
        }
    )


def test_depreciation_appreciation_signs_and_partial_sum_initialization() -> None:
    panel = build_stage3_features(
        _source_panel(), pd.Timestamp("2014-01-01"), pd.Timestamp("2015-03-01")
    )

    assert panel.loc[0, "fx_log_change_pct"] == pytest.approx(100 * np.log(110 / 111))
    assert panel.loc[0, "depreciation"] == pytest.approx(0.0)
    assert panel.loc[0, "appreciation"] == pytest.approx(panel.loc[0, "fx_log_change_pct"])
    assert panel.loc[1, "depreciation"] == 0.0
    assert panel.loc[1, "appreciation"] < 0
    assert panel.loc[0, "fx_positive_partial_sum"] == pytest.approx(0.0)
    assert panel.loc[0, "fx_negative_partial_sum"] == pytest.approx(panel.loc[0, "appreciation"])
    assert (panel["fx_positive_partial_sum"].diff().fillna(0) >= 0).all()
    assert (panel["fx_negative_partial_sum"].diff().fillna(0) <= 0).all()


def test_annual_inflation_uses_exact_12_month_lag_and_positive_pairs_only() -> None:
    source = _source_panel()
    source.loc[source["date"].eq("2014-12-01"), "cpi_index"] = 0.0
    source.loc[source["date"].eq("2015-01-01"), "wpi_all_commodities_index"] = -1.0
    panel = build_stage3_features(source, pd.Timestamp("2014-01-01"), pd.Timestamp("2015-03-01"))

    january_2014 = panel.loc[panel["date"].eq("2014-01-01")].iloc[0]
    expected = 100 * np.log(112 / 100)
    assert january_2014["cpi_annual_log_inflation"] == pytest.approx(expected)
    assert panel.loc[panel["date"].eq("2014-12-01"), "cpi_annual_log_inflation"].isna().all()
    assert (
        panel.loc[
            panel["date"].eq("2015-01-01"),
            "wpi_all_commodities_annual_log_inflation",
        ]
        .isna()
        .all()
    )


def test_future_changes_do_not_revise_prior_features() -> None:
    original = _source_panel()
    changed = original.copy()
    changed.loc[changed["date"].gt("2014-12-01"), "usd_inr_monthly"] *= 2.0
    changed.loc[changed["date"].gt("2014-12-01"), "cpi_index"] *= 2.0

    base_features = build_stage3_features(
        original, pd.Timestamp("2014-01-01"), pd.Timestamp("2015-03-01")
    )
    changed_features = build_stage3_features(
        changed, pd.Timestamp("2014-01-01"), pd.Timestamp("2015-03-01")
    )
    past = base_features["date"].le("2014-12-01")
    compare_columns = [
        "fx_log_change_pct",
        "depreciation",
        "appreciation",
        "cpi_annual_log_inflation",
        "fx_positive_partial_sum",
        "fx_negative_partial_sum",
    ]

    pd.testing.assert_frame_equal(
        base_features.loc[past, compare_columns].reset_index(drop=True),
        changed_features.loc[past, compare_columns].reset_index(drop=True),
    )


def test_nonpositive_usd_inr_is_rejected() -> None:
    source = _source_panel()
    source.loc[source["date"].eq("2014-02-01"), "usd_inr_monthly"] = 0.0

    with pytest.raises(ValueError, match="strictly positive"):
        build_stage3_features(source, pd.Timestamp("2014-01-01"), pd.Timestamp("2015-03-01"))
