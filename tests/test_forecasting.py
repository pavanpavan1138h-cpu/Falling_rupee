"""Tests for the exchange-rate forecasting experiment."""

from __future__ import annotations

import json

import numpy as np
import pandas as pd
import pytest

from src.forecasting.exchange_rate.forecasting import (
    EXCHANGE_DATA,
    MODELS_ROOT,
    PREDICTIONS_ROOT,
    _fit_final_estimator,
    _purged_cv_splits,
    build_horizon_frame,
    evaluate_predictions,
    load_stage1_dataset,
    random_walk_forecast,
    run_stage1_forecasting,
    split_train_validation_test,
)


def test_split_train_validation_test_preserves_chronology() -> None:
    panel = pd.DataFrame(
        {
            "date": pd.date_range("2020-01-01", periods=60, freq="MS"),
            "usd_inr_monthly": np.linspace(70.0, 90.0, 60),
        }
    )
    horizon_frame = build_horizon_frame(panel, horizon=1)
    train_idx, val_idx, test_idx = split_train_validation_test(horizon_frame)

    assert train_idx.is_monotonic_increasing
    assert val_idx.is_monotonic_increasing
    assert test_idx.is_monotonic_increasing
    assert train_idx[-1] < val_idx[0]
    assert val_idx[-1] < test_idx[0]
    assert len(train_idx) + len(val_idx) + len(test_idx) == len(horizon_frame)


def test_horizon_target_and_predictor_lags_are_calendar_aligned() -> None:
    panel = pd.DataFrame(
        {
            "date": pd.date_range("2020-01-01", periods=30, freq="MS"),
            "usd_inr_monthly": np.arange(70.0, 100.0),
            "brent_usd_per_barrel_level": np.arange(50.0, 80.0),
        }
    )
    frame = build_horizon_frame(panel, horizon=3)
    row = frame.loc[frame["forecast_origin"] == pd.Timestamp("2021-02-01")].iloc[0]

    assert row["target_date"] == pd.Timestamp("2021-05-01")
    assert row["target_level"] == pytest.approx(86.0)
    assert row["usd_inr_monthly_lag_0"] == pytest.approx(83.0)
    assert row["usd_inr_monthly_lag_1"] == pytest.approx(82.0)
    assert "brent_usd_per_barrel_level_lag_0" not in frame.columns
    assert "brent_usd_per_barrel_level_lag_1" in frame.columns


def test_horizon_frame_rejects_missing_calendar_months() -> None:
    panel = pd.DataFrame(
        {
            "date": pd.to_datetime(["2020-01-01", "2020-03-01", "2020-04-01"]),
            "usd_inr_monthly": [70.0, 72.0, 73.0],
        }
    )
    with pytest.raises(ValueError, match="complete monthly calendar"):
        build_horizon_frame(panel, horizon=1)


def test_target_month_information_is_not_in_origin_predictors() -> None:
    dates = pd.date_range("2020-01-01", periods=48, freq="MS")
    panel = pd.DataFrame(
        {
            "date": dates,
            "usd_inr_monthly": np.arange(48, dtype=float) + 70,
            "usd_inr_mom_change": np.arange(48, dtype=float),
            "brent_usd_per_barrel_level": np.arange(48, dtype=float) + 50,
        }
    )
    baseline = build_horizon_frame(panel, horizon=3)
    target_month = pd.Timestamp("2022-05-01")
    origin = pd.Timestamp("2022-02-01")
    altered_panel = panel.copy()
    altered_panel.loc[altered_panel["date"] == target_month, "usd_inr_monthly"] += 500
    altered_panel.loc[altered_panel["date"] == target_month, "brent_usd_per_barrel_level"] += 500
    altered = build_horizon_frame(altered_panel, horizon=3)

    baseline_row = baseline.loc[baseline["forecast_origin"] == origin].iloc[0]
    altered_row = altered.loc[altered["forecast_origin"] == origin].iloc[0]
    assert baseline_row["target_level"] != altered_row["target_level"]
    assert baseline_row[list(_feature_columns(baseline))].equals(
        altered_row[list(_feature_columns(altered))]
    )


def _feature_columns(frame: pd.DataFrame) -> list[str]:
    return [column for column in frame if "_lag_" in column]


def test_purged_cv_training_targets_precede_validation_origins() -> None:
    panel = pd.DataFrame(
        {
            "date": pd.date_range("2010-01-01", periods=100, freq="MS"),
            "usd_inr_monthly": np.linspace(45.0, 85.0, 100),
        }
    )
    frame = build_horizon_frame(panel, horizon=3)
    train_idx, _, _ = split_train_validation_test(frame)
    training = frame.iloc[train_idx].reset_index(drop=True)

    for training_indices, validation_indices in _purged_cv_splits(training):
        first_validation_origin = training.iloc[validation_indices[0]]["forecast_origin"]
        assert (
            training.iloc[training_indices]["target_date"] < first_validation_origin
        ).all()


def test_random_walk_uses_latest_observation_available_at_origin() -> None:
    history = pd.DataFrame(
        {
            "date": pd.date_range("2020-01-01", periods=6, freq="MS"),
            "usd_inr_monthly": [72.0, 73.0, 74.0, 75.0, 76.0, 77.0],
        }
    )
    forecast = random_walk_forecast(history, history["date"].iloc[4], horizon=6)
    assert forecast == pytest.approx(76.0)

    metrics = evaluate_predictions(
        np.array([1.0, 2.0, 3.0]),
        np.array([1.0, 1.0, 4.0]),
        np.array([1.0, 2.5, 2.0]),
    )
    assert metrics["mae"] == pytest.approx(0.6666666667)
    assert metrics["bias"] == pytest.approx(0.0)
    assert metrics["rmse"] == pytest.approx(np.sqrt(2.0 / 3.0))
    assert metrics["directional_accuracy"] == pytest.approx(1.0)


def test_training_only_scaler_and_elastic_net_converge() -> None:
    X_train = pd.DataFrame({"first": [0.0, 1.0, 2.0, 3.0], "second": [2.0, 2.0, 4.0, 4.0]})
    y_train = pd.Series([50.0, 51.0, 52.0, 53.0])
    model = _fit_final_estimator(
        "elastic_net",
        {"alpha": 0.1, "l1_ratio": 0.5},
        X_train,
        y_train,
    )

    assert np.allclose(model.named_steps["scaler"].mean_, X_train.mean().to_numpy())
    assert np.max(model.named_steps["model"].n_iter_) < model.named_steps["model"].max_iter


def test_mape_is_undefined_when_any_actual_denominator_is_zero() -> None:
    metrics = evaluate_predictions(
        np.array([0.0, 2.0]),
        np.array([1.0, 2.5]),
        np.array([0.0, 1.0]),
    )
    assert np.isnan(metrics["mape"])
    with pytest.raises(ValueError, match="equal length"):
        evaluate_predictions(np.array([1.0]), np.array([1.0, 2.0]))


def test_stage1_forecasting_outputs_expected_columns_and_files() -> None:
    predictions, metrics, metadata = run_stage1_forecasting()

    required_prediction_columns = {
        "model",
        "forecast_origin",
        "target_date",
        "horizon",
        "actual",
        "predicted",
        "error",
    }
    assert required_prediction_columns.issubset(predictions.columns)
    required_metric_columns = {
        "horizon",
        "model",
        "mae",
        "rmse",
        "mape",
        "r2",
        "directional_accuracy",
        "bias",
    }
    assert required_metric_columns.issubset(metrics.columns)
    assert metadata
    assert not predictions.empty
    assert not metrics.empty
    for split in metadata["split_metadata"].values():
        assert split["final_train_label_end"] < split["first_test_origin"]
        assert split["test_rows"] > 0
    for horizon, horizon_predictions in predictions.groupby("horizon"):
        expected_month = horizon_predictions["forecast_origin"] + pd.offsets.MonthBegin(horizon)
        assert (horizon_predictions["target_date"].to_numpy() == expected_month.to_numpy()).all()
        targets_by_model = horizon_predictions.groupby("model")["target_date"].apply(
            lambda values: tuple(values.astype(str))
        )
        assert targets_by_model.nunique() == 1
    assert set(predictions["model"]) == {
        "random_walk",
        "arima",
        "elastic_net",
        "random_forest",
        "xgboost",
    }
    assert np.allclose(
        predictions["error"].to_numpy(),
        predictions["predicted"].to_numpy() - predictions["actual"].to_numpy(),
    )
    random_walk = predictions.loc[predictions["model"] == "random_walk"]
    assert np.allclose(random_walk["predicted"], random_walk["origin_value"])

    panel = load_stage1_dataset().set_index("date")["usd_inr_monthly"]
    for row in predictions.itertuples():
        assert row.origin_value == pytest.approx(panel.loc[row.forecast_origin])
        assert row.actual == pytest.approx(panel.loc[row.target_date])

    for horizon in (1, 3, 6):
        arima_artifact = MODELS_ROOT / f"arima_{horizon}m.json"
        assert arima_artifact.exists()
        assert json.loads(arima_artifact.read_text(encoding="utf-8"))["model"] == "ARIMA"
        assert (MODELS_ROOT / f"elastic_net_{horizon}m.pkl").exists()
        assert (MODELS_ROOT / f"random_forest_{horizon}m.pkl").exists()
        assert (MODELS_ROOT / f"xgboost_{horizon}m.pkl").exists()
    assert (PREDICTIONS_ROOT / "stage1_exchange_rate_predictions.csv").exists()
    assert EXCHANGE_DATA.exists()
