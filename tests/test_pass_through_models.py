"""Unit tests for Stage 3 lag alignment and configuration separation."""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.pass_through.models import build_analysis_panel, build_model_design


def _model_panel() -> pd.DataFrame:
    dates = pd.date_range("2014-01-01", periods=48, freq="MS")
    values = np.arange(len(dates), dtype=float)
    return pd.DataFrame(
        {
            "date": dates,
            "outcome": np.sin(values / 4) + values / 10,
            "fx_log_change_pct": values / 20 - 1,
            "depreciation": np.maximum(values / 20 - 1, 0),
            "appreciation": np.minimum(values / 20 - 1, 0),
            "brent_log_change_pct": np.cos(values / 5),
            "brent_inr_proxy_log_change_pct": np.sin(values / 3),
        }
    )


def test_model_lags_and_target_months_are_aligned() -> None:
    panel = _model_panel()
    frame = build_analysis_panel(panel, "outcome")
    design = build_model_design(frame, p=2, q=1, kind="asymmetric")

    target_date = pd.Timestamp("2014-08-01")
    index = design.dates.index[design.dates.eq(target_date)][0]
    frame_index = frame.index[frame["date"].eq(target_date)][0]
    assert design.outcome.iloc[index] == panel.loc[panel["date"].eq(target_date), "outcome"].iloc[0]
    assert design.regressors.loc[index, "outcome_lag_1"] == frame.loc[frame_index, "outcome_lag_1"]
    assert (
        design.regressors.loc[index, "depreciation_lag_0"]
        == frame.loc[frame_index, "depreciation_lag_0"]
    )
    assert (
        design.regressors.loc[index, "appreciation_lag_1"]
        == frame.loc[frame_index, "appreciation_lag_1"]
    )


def test_future_observation_changes_do_not_enter_origin_regressors() -> None:
    original = _model_panel()
    altered = original.copy()
    altered.loc[altered["date"].eq("2016-01-01"), "fx_log_change_pct"] += 500
    altered.loc[altered["date"].eq("2016-01-01"), "depreciation"] += 500
    altered.loc[altered["date"].eq("2016-01-01"), "appreciation"] -= 500

    frame = build_analysis_panel(original, "outcome")
    altered_frame = build_analysis_panel(altered, "outcome")
    design = build_model_design(frame, p=2, q=1, kind="asymmetric")
    altered_design = build_model_design(altered_frame, p=2, q=1, kind="asymmetric")
    origin = pd.Timestamp("2015-12-01")
    row = design.dates.index[design.dates.eq(origin)][0]
    altered_row = altered_design.dates.index[altered_design.dates.eq(origin)][0]

    pd.testing.assert_series_equal(
        design.regressors.iloc[row],
        altered_design.regressors.iloc[altered_row],
    )


def test_proxy_alternative_does_not_contain_fx_split_terms() -> None:
    frame = build_analysis_panel(_model_panel(), "outcome")
    design = build_model_design(frame, p=1, q=0, kind="proxy", control="proxy")

    assert "proxy_lag_1" in design.regressors
    assert not any(
        "depreciation" in term or "appreciation" in term for term in design.feature_names
    )
    assert not any(term.startswith("fx_lag_") for term in design.feature_names)


def test_invalid_nonmonthly_series_is_rejected() -> None:
    panel = _model_panel().drop(index=10)

    try:
        build_analysis_panel(panel, "outcome")
    except ValueError as exc:
        assert "complete monthly calendar" in str(exc)
    else:
        raise AssertionError("A missing monthly row must be rejected.")
