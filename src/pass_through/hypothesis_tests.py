"""Formal tests for asymmetric response, CPI/WPI contrasts, and Brent interactions."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
import statsmodels.api as sm

from src.pass_through.estimation import wald_equalities
from src.pass_through.models import ModelDesign


def test_short_run_asymmetry(
    result: Any,
    q: int,
    outcome: str,
) -> dict[str, Any]:
    """Test equality of signed depreciation and appreciation coefficients jointly."""
    lags = range(q + 1)
    test = wald_equalities(
        result,
        [f"depreciation_lag_{lag}" for lag in lags],
        [f"appreciation_lag_{lag}" for lag in lags],
    )
    return {
        "hypothesis": "H1 short-run exchange-rate asymmetry",
        "outcome": outcome,
        "null": "beta_depreciation_j = beta_appreciation_j for all included FX lags",
        "alternative": "At least one signed depreciation/appreciation lag coefficient differs",
        **test,
    }


def test_brent_interactions(
    result: Any,
    outcome: str,
) -> dict[str, Any]:
    """Test the pre-specified FX-by-lagged-Brent interaction block."""
    names = list(result.params.index)
    terms = ["depreciation_x_brent", "appreciation_x_brent"]
    missing = set(terms).difference(names)
    if missing:
        raise ValueError(f"Brent interaction test is missing terms: {sorted(missing)}")
    restriction = np.zeros((len(terms), len(names)), dtype=float)
    for row, term in enumerate(terms):
        restriction[row, names.index(term)] = 1.0
    test = result.wald_test(restriction, scalar=True)
    return {
        "hypothesis": "H4 imported-cost conditioning interaction block",
        "outcome": outcome,
        "null": "Both FX-by-lagged-Brent interaction coefficients are zero",
        "alternative": "At least one interaction coefficient differs from zero",
        "test": "HAC Wald joint test",
        "statistic": float(test.statistic),
        "degrees_of_freedom": len(terms),
        "p_value": float(test.pvalue),
        "restriction": ", ".join(f"{term} = 0" for term in terms),
    }


def test_cpi_wpi_fx_contrast(
    cpi_design: ModelDesign,
    wpi_design: ModelDesign,
    p: int,
    q: int,
) -> dict[str, Any]:
    """Test common-month equality of CPI/WPI FX terms with date-clustered covariance."""
    if not cpi_design.dates.equals(wpi_design.dates):
        raise ValueError("CPI/WPI comparison must use identical monthly observations.")
    if cpi_design.feature_names != wpi_design.feature_names:
        raise ValueError("CPI/WPI comparison must use identical model terms.")

    terms = list(cpi_design.feature_names)
    dates = pd.concat([cpi_design.dates, wpi_design.dates], ignore_index=True)
    wpi_indicator = np.concatenate(
        [np.zeros(len(cpi_design.outcome)), np.ones(len(wpi_design.outcome))]
    )
    base_x = pd.concat([cpi_design.regressors, wpi_design.regressors], ignore_index=True)
    stacked = base_x.copy()
    stacked["wpi_outcome"] = wpi_indicator
    for term in terms:
        if term != "const":
            stacked[f"wpi_x_{term}"] = stacked[term] * wpi_indicator
    outcome = pd.concat([cpi_design.outcome, wpi_design.outcome], ignore_index=True)
    fitted = sm.OLS(outcome, stacked).fit(
        cov_type="cluster",
        cov_kwds={"groups": dates, "use_correction": True},
    )
    fx_terms = [
        term
        for term in terms
        if term.startswith("depreciation_lag_") or term.startswith("appreciation_lag_")
    ]
    restrictions = np.zeros((len(fx_terms), len(fitted.params)), dtype=float)
    param_names = list(fitted.params.index)
    for row, term in enumerate(fx_terms):
        interaction = f"wpi_x_{term}"
        if interaction not in param_names:
            raise ValueError(f"Missing CPI/WPI coefficient contrast term {interaction}.")
        restrictions[row, param_names.index(interaction)] = 1.0
    test = fitted.wald_test(restrictions, scalar=True)
    return {
        "hypothesis": "H3 CPI versus WPI exchange-rate response",
        "null": "All selected CPI and WPI signed FX lag coefficients are equal",
        "alternative": "At least one comparable CPI/WPI signed FX coefficient differs",
        "test": "Date-clustered joint Wald test in stacked outcome model",
        "statistic": float(test.statistic),
        "degrees_of_freedom": len(fx_terms),
        "p_value": float(test.pvalue),
        "restriction": ", ".join(f"wpi_x_{term} = 0" for term in fx_terms),
        "observations_per_outcome": int(len(cpi_design.outcome)),
        "stacked_rows": int(len(outcome)),
        "sample_start": cpi_design.dates.min().date().isoformat(),
        "sample_end": cpi_design.dates.max().date().isoformat(),
        "lag_p": p,
        "lag_q": q,
        "covariance": "clustered by common month to allow contemporaneous CPI/WPI dependence",
    }
