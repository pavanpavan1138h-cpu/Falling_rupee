"""Residual, collinearity, and parameter-stability diagnostics."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.stats.diagnostic import (
    acorr_breusch_godfrey,
    acorr_ljungbox,
    breaks_cusumolsresid,
    het_breuschpagan,
    linear_reset,
)
from statsmodels.stats.outliers_influence import OLSInfluence, variance_inflation_factor
from statsmodels.stats.stattools import jarque_bera

from src.pass_through.models import ModelDesign


def run_model_diagnostics(
    design: ModelDesign,
    result: Any,
    outcome: str,
    model: str,
    p: int,
    q: int,
) -> tuple[dict[str, Any], pd.DataFrame, pd.DataFrame]:
    """Run standard residual checks and return influence/stability series."""
    ordinary = sm.OLS(design.outcome, design.regressors).fit()
    residuals = np.asarray(ordinary.resid, dtype=float)
    nlags = min(max(3, p, q + 1), max(1, len(residuals) // 5))
    bg_result = acorr_breusch_godfrey(ordinary, nlags=nlags, result_object=True)
    lb = acorr_ljungbox(
        residuals, lags=[min(6, len(residuals) - 1), min(12, len(residuals) - 1)], return_df=True
    )
    bp_lm, bp_lm_p, bp_f, bp_f_p = het_breuschpagan(residuals, design.regressors)
    reset = linear_reset(ordinary, power=2, use_f=True)
    jb_stat, jb_pvalue, skew, kurtosis = jarque_bera(residuals)
    cusum_stat, cusum_pvalue, cusum_critical = breaks_cusumolsresid(
        residuals, ddof=design.regressors.shape[1]
    )
    influence = OLSInfluence(ordinary).summary_frame()
    influence = influence.assign(date=design.dates.to_numpy())
    influence["outcome"] = outcome
    influence["model"] = model
    top_influence = influence.reindex(
        influence["cooks_d"].abs().sort_values(ascending=False).head(10).index
    )

    predictors = design.regressors.drop(columns=["const"], errors="ignore")
    vif_rows = [
        {
            "term": column,
            "variance_inflation_factor": float(
                variance_inflation_factor(
                    design.regressors.to_numpy(dtype=float),
                    design.regressors.columns.get_loc(column),
                )
            ),
        }
        for column in predictors.columns
    ]
    vif = pd.DataFrame(vif_rows)
    if predictors.shape[1]:
        vif["outcome"] = outcome
        vif["model"] = model

    stability_rows: list[dict[str, Any]] = []
    tracked = [
        term
        for term in (
            "depreciation_lag_0",
            "appreciation_lag_0",
            "fx_lag_0",
        )
        if term in design.regressors
    ]
    minimum = max(25, design.regressors.shape[1] * 2)
    for end in range(minimum, len(design.outcome) + 1):
        recursive = sm.OLS(
            design.outcome.iloc[:end],
            design.regressors.iloc[:end],
        ).fit()
        row: dict[str, Any] = {
            "date": design.dates.iloc[end - 1],
            "observations": end,
            "outcome": outcome,
            "model": model,
        }
        row.update({term: float(recursive.params[term]) for term in tracked})
        stability_rows.append(row)

    diagnostics = {
        "outcome": outcome,
        "model": model,
        "observations": int(len(residuals)),
        "parameters": int(design.regressors.shape[1]),
        "breusch_godfrey_lags": nlags,
        "breusch_godfrey_lm_statistic": float(bg_result.lm),
        "breusch_godfrey_lm_pvalue": float(bg_result.lmpval),
        "breusch_godfrey_f_statistic": float(bg_result.fval),
        "breusch_godfrey_f_pvalue": float(bg_result.fpval),
        "ljung_box_6_statistic": float(lb.iloc[0]["lb_stat"]),
        "ljung_box_6_pvalue": float(lb.iloc[0]["lb_pvalue"]),
        "ljung_box_12_statistic": float(lb.iloc[-1]["lb_stat"]),
        "ljung_box_12_pvalue": float(lb.iloc[-1]["lb_pvalue"]),
        "breusch_pagan_lm_statistic": float(bp_lm),
        "breusch_pagan_lm_pvalue": float(bp_lm_p),
        "breusch_pagan_f_statistic": float(bp_f),
        "breusch_pagan_f_pvalue": float(bp_f_p),
        "ramsey_reset_f_statistic": float(reset.fvalue),
        "ramsey_reset_pvalue": float(reset.pvalue),
        "jarque_bera_statistic": float(jb_stat),
        "jarque_bera_pvalue": float(jb_pvalue),
        "residual_skewness": float(skew),
        "residual_kurtosis": float(kurtosis),
        "cusum_statistic": float(cusum_stat),
        "cusum_pvalue": float(cusum_pvalue),
        "cusum_critical_values": str(cusum_critical),
        "condition_number": float(np.linalg.cond(design.regressors.to_numpy(dtype=float))),
        "hac_covariance": "Newey-West, Bartlett kernel, maxlags=12",
        "interpretation_note": (
            "Diagnostics are specification checks, not validity certificates; HAC does not repair "
            "omitted dynamics, endogeneity, or source-vintage uncertainty."
        ),
    }
    return diagnostics, top_influence.reset_index(names="row"), pd.DataFrame(stability_rows)
