"""Unit tests for formal Stage 3 restrictions and reproducible block resampling."""

from __future__ import annotations

import numpy as np
import pandas as pd
import statsmodels.api as sm

from src.pass_through.estimation import bootstrap_dynamic_asymmetry, fit_hac_model
from src.pass_through.hypothesis_tests import (
    test_cpi_wpi_fx_contrast as check_cpi_wpi_fx_contrast,
)
from src.pass_through.hypothesis_tests import (
    test_short_run_asymmetry as check_short_run_asymmetry,
)
from src.pass_through.models import ModelDesign


def _design(offset: float = 0.0) -> ModelDesign:
    rng = np.random.default_rng(42)
    n = 72
    dep = rng.gamma(1.0, 0.4, n)
    app = -rng.gamma(1.0, 0.4, n)
    outcome_lag = rng.normal(size=n)
    y = 0.3 + 0.2 * outcome_lag + 0.4 * dep + 0.25 * app + rng.normal(0, 0.2, n) + offset
    x = pd.DataFrame(
        {
            "const": np.ones(n),
            "outcome_lag_1": outcome_lag,
            "depreciation_lag_0": dep,
            "appreciation_lag_0": app,
        }
    )
    return ModelDesign(
        outcome=pd.Series(y),
        regressors=x,
        dates=pd.Series(pd.date_range("2018-01-01", periods=n, freq="MS")),
        feature_names=tuple(x.columns),
    )


def test_h1_joint_signed_scale_restriction_returns_expected_schema() -> None:
    design = _design()
    result = sm.OLS(design.outcome, design.regressors).fit(cov_type="HAC", cov_kwds={"maxlags": 3})

    test = check_short_run_asymmetry(result, q=0, outcome="cpi")

    assert test["degrees_of_freedom"] == 1
    assert 0.0 <= test["p_value"] <= 1.0
    assert "beta_depreciation_j" in test["restriction"]


def test_paired_cpi_wpi_test_requires_common_dates_and_terms() -> None:
    cpi = _design()
    wpi = _design(offset=0.1)

    test = check_cpi_wpi_fx_contrast(cpi, wpi, p=1, q=0)

    assert test["observations_per_outcome"] == 72
    assert test["stacked_rows"] == 144
    assert test["degrees_of_freedom"] == 2
    assert 0.0 <= test["p_value"] <= 1.0


def test_moving_block_dynamic_bootstrap_is_reproducible() -> None:
    design = _design()
    result = fit_hac_model(design, maxlags=3)

    first, first_joint = bootstrap_dynamic_asymmetry(
        design, result, p=1, q=0, replicates=29, block_length=6, seed=7
    )
    second, second_joint = bootstrap_dynamic_asymmetry(
        design, result, p=1, q=0, replicates=29, block_length=6, seed=7
    )

    pd.testing.assert_frame_equal(first, second)
    assert first_joint == second_joint
    assert first["horizon_months"].tolist() == [1, 3, 6]
