"""Regression tests for the Stage 2 CPI forecasting data and evaluation path."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.forecasting.inflation.data import (
    build_fx_forecast_archive,
    load_feature_panel,
    load_published_cpi_target,
)
from src.forecasting.inflation.evaluation import (
    build_episode_error_summary,
    forecast_metrics,
)
from src.forecasting.inflation.features import build_configuration_frames
from src.forecasting.inflation.forecasting import (
    ML_MODELS,
    _fit_tabular_model,
    _model_and_grid,
    _purged_cv_splits,
    split_train_validation_test,
)
from src.forecasting.inflation.run_experiments import _training_thresholds


@pytest.fixture(scope="module")
def observed_inputs() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict]:
    target, target_metadata = load_published_cpi_target()
    panel = load_feature_panel()
    archive, _ = build_fx_forecast_archive(target["date"], panel)
    return target, panel, archive, target_metadata


@pytest.fixture(scope="module")
def observed_frames(
    observed_inputs: tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict],
) -> dict[tuple[str, int], pd.DataFrame]:
    target, panel, archive, _ = observed_inputs
    frames, _ = build_configuration_frames(target, panel, archive)
    return frames


def test_published_cpi_uses_longest_contiguous_segment(
    observed_inputs: tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict],
) -> None:
    target, _, _, metadata = observed_inputs

    assert len(target) == 132
    assert metadata["selected_target_column"] == "inflation_value (published)"
    assert metadata["index_substitution"] is False
    assert metadata["selected_segment"] == {
        "start": "2014-01-01",
        "end": "2024-12-01",
        "observations": 132,
    }
    assert metadata["published_series_segments"][-1] == {
        "start": "2026-01-01",
        "end": "2026-09-01",
        "observations": 9,
    }


@pytest.mark.parametrize("horizon", [1, 3, 6])
def test_forecast_origin_target_horizon_and_lags_are_aligned(
    observed_inputs: tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict],
    observed_frames: dict[tuple[str, int], pd.DataFrame],
    horizon: int,
) -> None:
    target, panel, archive, _ = observed_inputs
    frame = observed_frames[("C3", horizon)]
    row = frame.iloc[20]
    target_period = row["forecast_origin"].to_period("M") + horizon
    target_actual = target.loc[
        target["date"].dt.to_period("M").eq(target_period), "cpi_inflation"
    ].iloc[0]
    assert row["target_date"].to_period("M") == target_period
    assert row["target_cpi_inflation"] == pytest.approx(target_actual)

    origin_period = row["forecast_origin"].to_period("M")
    for lag in (1, 2, 3, 6, 12):
        cpi_value = target.loc[
            target["date"].dt.to_period("M").eq(origin_period - lag),
            "cpi_inflation",
        ].iloc[0]
        proxy_value = panel.loc[
            panel["date"].dt.to_period("M").eq(origin_period - lag),
            "brent_inr_proxy_level",
        ].iloc[0]
        assert row[f"cpi_lag_{lag}"] == pytest.approx(cpi_value)
        assert row[f"brent_inr_proxy_level_lag_{lag}"] == pytest.approx(proxy_value)

    c2_row = (
        observed_frames[("C2", horizon)]
        .loc[lambda rows: rows["forecast_origin"].eq(row["forecast_origin"])]
        .iloc[0]
    )
    matching_fx = archive.loc[
        archive["model"].eq("arima_0_1_1")
        & archive["forecast_origin"].eq(c2_row["forecast_origin"])
        & archive["target_date"].eq(c2_row["target_date"])
        & archive["horizon"].eq(horizon),
        "predicted_usd_inr",
    ].iloc[0]
    assert c2_row["fx_predicted_level"] == pytest.approx(matching_fx)


def test_information_sets_do_not_include_unlagged_realized_macro_features(
    observed_frames: dict[tuple[str, int], pd.DataFrame],
) -> None:
    expected = {
        "C0": ("cpi_lag_",),
        "C1": (
            "cpi_lag_",
            "brent_usd_per_barrel_level_lag_",
            "brent_mom_pct_change_lag_",
        ),
        "C2": ("cpi_lag_", "fx_predicted_level", "fx_predicted_change_pct"),
        "C3": (
            "cpi_lag_",
            "brent_inr_proxy_level_lag_",
            "brent_inr_proxy_mom_pct_change_lag_",
        ),
    }
    for (configuration, horizon), frame in observed_frames.items():
        features = [
            column for column in frame if column.startswith(("cpi_lag_", "brent_", "fx_predicted_"))
        ]
        assert features
        assert all(
            any(column.startswith(prefix) for prefix in expected[configuration])
            for column in features
        )
        assert (frame["target_date"] > frame["forecast_origin"]).all()
        assert horizon in (1, 3, 6)


@pytest.mark.parametrize("horizon", [1, 3, 6])
def test_chronological_splits_and_cv_purge_future_targets(
    observed_frames: dict[tuple[str, int], pd.DataFrame],
    horizon: int,
) -> None:
    frame = observed_frames[("C0", horizon)]
    train_idx, validation_idx, test_idx = split_train_validation_test(frame)
    assert train_idx[-1] < validation_idx[0] < test_idx[0]

    training = frame.iloc[train_idx].reset_index(drop=True)
    for cv_train, cv_validation in _purged_cv_splits(training):
        first_validation_origin = training.iloc[cv_validation[0]]["forecast_origin"]
        assert (training.iloc[cv_train]["forecast_origin"] < first_validation_origin).all()
        assert (training.iloc[cv_train]["target_date"] < first_validation_origin).all()


def test_elastic_net_scaling_is_inside_model_pipeline_and_converges(
    observed_frames: dict[tuple[str, int], pd.DataFrame],
) -> None:
    frame = observed_frames[("C1", 1)]
    train_idx, _, _ = split_train_validation_test(frame)
    train = frame.iloc[train_idx].copy()
    feature_columns = [column for column in train if column.startswith(("cpi_lag_", "brent_"))]
    estimator, _ = _model_and_grid("elastic_net")
    assert estimator.named_steps["scaler"].__class__.__name__ == "StandardScaler"

    model = _fit_tabular_model(
        "elastic_net",
        {"alpha": 0.1, "l1_ratio": 0.5},
        train,
        feature_columns,
    )
    assert np.allclose(
        model.named_steps["scaler"].mean_,
        train[feature_columns].mean().to_numpy(),
    )
    assert np.max(model.named_steps["model"].n_iter_) < model.named_steps["model"].max_iter
    assert ML_MODELS == ("elastic_net", "random_forest", "xgboost")


def test_brent_episode_threshold_uses_purged_training_targets(
    observed_frames: dict[tuple[str, int], pd.DataFrame],
    observed_inputs: tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict],
) -> None:
    _, panel, _, _ = observed_inputs
    _, brent_thresholds, _ = _training_thresholds(observed_frames, panel)
    frame = observed_frames[("C0", 1)]
    train_idx, validation_idx, _ = split_train_validation_test(frame)
    first_validation_origin = frame.iloc[validation_idx[0]]["forecast_origin"]
    eligible = frame.iloc[train_idx].loc[
        frame.iloc[train_idx]["target_date"] < first_validation_origin
    ]
    target_dates = eligible["target_date"]
    expected = (
        panel.loc[panel["date"].isin(target_dates), "brent_mom_pct_change"].dropna().quantile(0.95)
    )
    assert brent_thresholds[1] == pytest.approx(expected)


def test_forecast_metrics_and_episode_runs_are_calculated_correctly(
    observed_inputs: tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict],
) -> None:
    target, _, _, _ = observed_inputs
    metrics = forecast_metrics(
        np.array([2.0, 4.0, 8.0]),
        np.array([3.0, 2.0, 10.0]),
    )
    assert metrics["mae"] == pytest.approx(5.0 / 3.0)
    assert metrics["rmse"] == pytest.approx(np.sqrt(3.0))
    assert metrics["bias"] == pytest.approx(1.0 / 3.0)
    assert metrics["r2"] == pytest.approx(1.0 - 27.0 / 56.0)
    assert metrics["mape"] == pytest.approx(np.mean([0.5, 0.5, 0.25]) * 100.0)

    selected = target.iloc[[0, 1, 3]]
    predictions = pd.DataFrame(
        {
            "horizon": 1,
            "configuration": "C0",
            "model": "autoregression",
            "target_date": selected["date"].to_numpy(),
            "actual": selected["cpi_inflation"].to_numpy(),
            "error": 0.0,
        }
    )
    episodes = build_episode_error_summary(
        predictions,
        {1: -100.0},
        "high_inflation",
    )
    assert episodes.iloc[0]["n_distinct_target_months"] == 3
    assert episodes.iloc[0]["n_episode_runs"] == 2
    no_episodes = build_episode_error_summary(
        predictions,
        {1: 100.0},
        "high_inflation",
    )
    assert no_episodes.iloc[0]["n_forecasts"] == 0
    assert no_episodes.iloc[0]["n_episode_runs"] == 0
    assert np.isnan(no_episodes.iloc[0]["mae"])
