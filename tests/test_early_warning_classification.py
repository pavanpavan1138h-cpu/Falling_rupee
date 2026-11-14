"""Tests for the Stage 4 early-warning data and evaluation contracts."""

from __future__ import annotations

import pandas as pd

from src.risk_classification.evaluation import (
    choose_f1_threshold,
    classification_metrics,
)
from src.risk_classification.features import (
    FEATURE_COLUMNS,
    HORIZONS,
    build_classification_frames,
    load_stage4_sources,
)
from src.risk_classification.models import Candidate, fit_candidate
from src.risk_classification.run_experiments import (
    _feature_eligibility_table,
    _origin_split_manifest,
)


def test_published_target_and_horizon_samples_are_valid() -> None:
    target, market, metadata = load_stage4_sources()
    frames, _ = build_classification_frames(target, market)

    assert metadata["cpi_index_used_as_target"] is False
    assert metadata["cpi_observations"] == 132
    assert metadata["cpi_segment_start"] == "2014-01"
    assert metadata["cpi_segment_end"] == "2024-12"
    expected_counts = {1: (119, 29), 3: (117, 29), 6: (114, 29)}
    for horizon, (count, positive) in expected_counts.items():
        frame = frames[("C0", horizon)]
        assert len(frame) == count
        assert int(frame["elevated_target"].sum()) == positive
        assert frame["target_month"].is_monotonic_increasing
        assert (frame["target_month"] > frame["forecast_origin"]).all()
        assert (
            frame["target_month"].dt.to_period("M")
            == frame["forecast_origin"].dt.to_period("M") + horizon
        ).all()
        assert (frame["feature_observation_end"] < frame["forecast_origin"]).all()
        assert (
            frame["elevated_target"]
            == (frame["target_inflation"] > 6.0).astype(int)
        ).all()


def test_configuration_features_are_separated_and_share_rows() -> None:
    target, market, _ = load_stage4_sources()
    frames, _ = build_classification_frames(target, market)

    assert set(FEATURE_COLUMNS["C0"]).isdisjoint(
        {"fx_log_return_1m", "brent_log_return_1m", "brent_inr_proxy_log_return_1m"}
    )
    assert "fx_log_return_1m" in FEATURE_COLUMNS["C1"]
    assert "brent_log_return_1m" in FEATURE_COLUMNS["C2"]
    assert "brent_inr_proxy_log_return_1m" in FEATURE_COLUMNS["C3"]
    assert "brent_log_return_1m" not in FEATURE_COLUMNS["C3"]
    for horizon in HORIZONS:
        reference = frames[("C0", horizon)][["forecast_origin", "target_month"]]
        for configuration in FEATURE_COLUMNS:
            compared = frames[(configuration, horizon)][
                ["forecast_origin", "target_month"]
            ]
            pd.testing.assert_frame_equal(reference, compared)


def test_validation_threshold_uses_probability_and_actual_arrays() -> None:
    actual = [0, 0, 1, 1]
    probabilities = [0.1, 0.2, 0.7, 0.8]

    assert choose_f1_threshold(actual, probabilities) == 0.7


def test_undefined_metrics_are_preserved_for_one_class_outcomes() -> None:
    metrics = classification_metrics(
        actual=[0, 0, 0],
        probabilities=[0.1, 0.2, 0.3],
        threshold=0.5,
        horizon=1,
        target_months=pd.Series(pd.date_range("2024-01-01", periods=3, freq="MS")),
    )

    assert metrics["roc_auc"] != metrics["roc_auc"]
    assert metrics["pr_auc_average_precision"] != metrics["pr_auc_average_precision"]
    assert metrics["brier_score"] >= 0
    assert "no actual positive labels" in metrics["undefined_metric_notes"]


def test_episode_counts_distinguish_missed_and_false_alarm_runs() -> None:
    metrics = classification_metrics(
        actual=[0, 0, 1, 1, 0, 0],
        probabilities=[0.9, 0.9, 0.1, 0.1, 0.1, 0.9],
        threshold=0.5,
        horizon=1,
        target_months=pd.Series(pd.date_range("2024-01-01", periods=6, freq="MS")),
    )

    assert metrics["actual_elevated_episodes"] == 1
    assert metrics["detected_elevated_episodes"] == 0
    assert metrics["missed_elevated_episodes"] == 1
    assert metrics["false_alarm_episodes"] == 2


def test_feature_eligibility_documents_membership_and_origin_timing() -> None:
    eligibility = _feature_eligibility_table().set_index("feature")

    assert "cpi_lag_1" in eligibility.index
    assert "C0" in eligibility.loc["cpi_lag_1", "configurations"]
    assert "C1" in eligibility.loc["fx_log_return_1m", "configurations"]
    assert "C2" in eligibility.loc["brent_log_return_1m", "configurations"]
    assert "C3" in eligibility.loc[
        "brent_inr_proxy_log_return_1m", "configurations"
    ]
    assert "not actual landed import cost" in eligibility.loc[
        "brent_inr_proxy_log_return_1m", "proxy_limitation"
    ]
    assert eligibility["required_lag"].str.contains("t-1").all()


def test_origin_manifest_purges_unavailable_validation_and_test_labels() -> None:
    target, market, _ = load_stage4_sources()
    frames, _ = build_classification_frames(target, market)
    frame = frames[("C0", 3)]
    manifest = _origin_split_manifest(frame, 3)

    validation = manifest.loc[manifest["partition"].eq("expanding_validation")]
    assert (validation["training_label_cutoff_exclusive"] == validation["forecast_origin"]).all()
    assert (validation["mature_training_n"] > 0).all()

    test = manifest.loc[manifest["partition"].eq("untouched_final_test")]
    first_test_origin = test["forecast_origin"].min()
    assert (test["training_label_cutoff_exclusive"] == first_test_origin).all()
    assert (test["target_month"] > first_test_origin).all()
    assert (test["mature_training_n"] == test["mature_training_n"].iloc[0]).all()


def test_logistic_scaler_is_fitted_only_on_training_rows() -> None:
    target, market, _ = load_stage4_sources()
    frames, _ = build_classification_frames(target, market)
    frame = frames[("C0", 1)]
    features = FEATURE_COLUMNS["C0"]
    training = frame.iloc[:80]
    withheld = frame.iloc[80:]
    assert training["elevated_target"].nunique() == 2

    estimator = fit_candidate(
        Candidate(
            "logistic_regression",
            {
                "C": 1.0,
                "class_weight": "balanced",
                "solver": "lbfgs",
                "max_iter": 5000,
            },
        ),
        features,
        training,
        training["elevated_target"].astype(int),
        seed=42,
    )

    pd.testing.assert_series_equal(
        pd.Series(estimator.named_steps["scale"].mean_, index=features),
        training[features].mean(),
        check_names=False,
    )
    assert not estimator.named_steps["scale"].mean_.tolist() == withheld[features].mean().tolist()
