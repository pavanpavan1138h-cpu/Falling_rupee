"""Unit tests for Stage 3 econometric diagnostic outputs."""

from __future__ import annotations

import numpy as np
import pandas as pd
import statsmodels.api as sm

from src.pass_through.diagnostics import run_model_diagnostics
from src.pass_through.models import ModelDesign


def test_diagnostics_return_residual_influence_and_stability_records() -> None:
    rng = np.random.default_rng(19)
    n = 80
    dates = pd.date_range("2015-01-01", periods=n, freq="MS")
    dep = rng.gamma(1.0, 0.3, n)
    app = -rng.gamma(1.0, 0.3, n)
    lag_y = rng.normal(size=n)
    y = 0.2 + 0.3 * lag_y + 0.2 * dep + 0.1 * app + rng.normal(0, 0.5, n)
    regressors = pd.DataFrame(
        {
            "const": 1.0,
            "outcome_lag_1": lag_y,
            "depreciation_lag_0": dep,
            "appreciation_lag_0": app,
        }
    )
    design = ModelDesign(
        outcome=pd.Series(y),
        regressors=regressors,
        dates=pd.Series(dates),
        feature_names=tuple(regressors.columns),
    )
    result = sm.OLS(y, regressors).fit(cov_type="HAC", cov_kwds={"maxlags": 3})

    report, influence, stability = run_model_diagnostics(
        design, result, "test_outcome", "asymmetric", p=1, q=0
    )

    assert "breusch_godfrey_lm_pvalue" in report
    assert "ramsey_reset_pvalue" in report
    assert "cusum_pvalue" in report
    assert not influence.empty
    assert {"date", "depreciation_lag_0", "appreciation_lag_0"}.issubset(stability.columns)
