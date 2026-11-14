"""HAC estimation, fit summaries, and moving-block uncertainty calculations."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy.stats import chi2, norm
from statsmodels.regression.linear_model import RegressionResultsWrapper
from statsmodels.tsa.ardl import ARDL, UECM

from src.pass_through.models import ModelDesign

HAC_LAGS = 12
BOOTSTRAP_REPLICATES = 499
BOOTSTRAP_BLOCK_LENGTH = 6
BOOTSTRAP_SEED = 42


def fit_hac_model(design: ModelDesign, maxlags: int = HAC_LAGS) -> RegressionResultsWrapper:
    """Fit OLS with Newey-West HAC covariance for overlapping annual inflation."""
    return sm.OLS(design.outcome, design.regressors).fit(
        cov_type="HAC",
        cov_kwds={"maxlags": maxlags, "use_correction": True},
    )


def coefficient_table(
    result: RegressionResultsWrapper,
    model: str,
    outcome: str,
    p: int,
    q: int,
    control: str,
    sample_dates: pd.Series,
) -> pd.DataFrame:
    """Serialize HAC coefficient estimates and confidence intervals."""
    intervals = result.conf_int(alpha=0.05)
    return pd.DataFrame(
        {
            "model": model,
            "outcome": outcome,
            "term": result.params.index,
            "coefficient": result.params.to_numpy(dtype=float),
            "hac_standard_error": result.bse.to_numpy(dtype=float),
            "p_value": result.pvalues.to_numpy(dtype=float),
            "ci_95_lower": intervals.iloc[:, 0].to_numpy(dtype=float),
            "ci_95_upper": intervals.iloc[:, 1].to_numpy(dtype=float),
            "p": p,
            "q": q,
            "control": control,
            "observations": int(result.nobs),
            "sample_start": pd.to_datetime(sample_dates).min().date().isoformat(),
            "sample_end": pd.to_datetime(sample_dates).max().date().isoformat(),
        }
    )


def fit_summary(result: RegressionResultsWrapper) -> dict[str, float | int]:
    """Return descriptive fit and information-criterion statistics."""
    return {
        "observations": int(result.nobs),
        "parameters": int(len(result.params)),
        "r_squared": float(result.rsquared),
        "adjusted_r_squared": float(result.rsquared_adj),
        "aic": float(result.aic),
        "bic": float(result.bic),
        "residual_degrees_freedom": int(result.df_resid),
        "residual_std_error": float(np.sqrt(result.mse_resid)),
    }


def wald_equalities(
    result: RegressionResultsWrapper,
    left_terms: list[str],
    right_terms: list[str],
) -> dict[str, float | int | str]:
    """Test joint equality of corresponding signed depreciation/appreciation terms."""
    if len(left_terms) != len(right_terms) or not left_terms:
        raise ValueError("Wald equality terms must be nonempty and have equal lengths.")
    names = list(result.params.index)
    restrictions = np.zeros((len(left_terms), len(names)), dtype=float)
    for row, (left, right) in enumerate(zip(left_terms, right_terms, strict=True)):
        if left not in names or right not in names:
            raise ValueError(f"Missing Wald restriction term: {left} or {right}")
        restrictions[row, names.index(left)] = 1.0
        restrictions[row, names.index(right)] = -1.0
    tested = result.wald_test(restrictions, scalar=True)
    return {
        "test": "HAC Wald equality test",
        "statistic": float(tested.statistic),
        "degrees_of_freedom": int(len(left_terms)),
        "p_value": float(tested.pvalue),
        "restriction": "beta_depreciation_j = beta_appreciation_j for all selected FX lags",
    }


def moving_block_indices(
    n: int,
    block_length: int = BOOTSTRAP_BLOCK_LENGTH,
    rng: np.random.Generator | None = None,
) -> np.ndarray:
    """Draw circular-free contiguous row blocks until n indices are sampled."""
    if n < block_length or block_length < 1:
        raise ValueError("Moving-block bootstrap requires n >= block_length >= 1.")
    generator = rng if rng is not None else np.random.default_rng(BOOTSTRAP_SEED)
    starts = generator.integers(0, n - block_length + 1, size=int(np.ceil(n / block_length)))
    sampled = np.concatenate([np.arange(start, start + block_length) for start in starts])
    return sampled[:n]


def _dynamic_cumulative_response(
    coefficients: pd.Series,
    p: int,
    q: int,
    sign: str,
    horizons: tuple[int, ...],
) -> dict[int, float]:
    """Compute cumulative response to equal-sized depreciation/appreciation shocks."""
    maximum = max(horizons)
    response = np.zeros(maximum + 1, dtype=float)
    for step in range(maximum + 1):
        direct = 0.0
        for lag in range(q + 1):
            source_step = step - lag
            if source_step == 0:
                term = f"{'depreciation' if sign == 'depreciation' else 'appreciation'}_lag_{lag}"
                if term in coefficients.index:
                    shock = 1.0 if sign == "depreciation" else -1.0
                    direct += float(coefficients[term]) * shock
        autoregressive = sum(
            float(coefficients[f"outcome_lag_{lag}"]) * response[step - lag]
            for lag in range(1, min(p, step) + 1)
        )
        response[step] = direct + autoregressive
    cumulative = np.cumsum(response)
    return {horizon: float(cumulative[horizon]) for horizon in horizons}


def bootstrap_dynamic_asymmetry(
    design: ModelDesign,
    result: RegressionResultsWrapper,
    p: int,
    q: int,
    replicates: int = BOOTSTRAP_REPLICATES,
    block_length: int = BOOTSTRAP_BLOCK_LENGTH,
    seed: int = BOOTSTRAP_SEED,
) -> tuple[pd.DataFrame, dict[str, float | int | str]]:
    """Estimate paired moving-block CIs and a joint Wald test for response asymmetry."""
    horizons = (1, 3, 6)
    dep_observed = _dynamic_cumulative_response(result.params, p, q, "depreciation", horizons)
    app_observed = _dynamic_cumulative_response(result.params, p, q, "appreciation", horizons)
    observed = np.array([dep_observed[h] + app_observed[h] for h in horizons], dtype=float)

    rng = np.random.default_rng(seed)
    draws: list[np.ndarray] = []
    n = len(design.outcome)
    for _ in range(replicates):
        indices = moving_block_indices(n, block_length, rng)
        bootstrap_result = sm.OLS(
            design.outcome.iloc[indices].reset_index(drop=True),
            design.regressors.iloc[indices].reset_index(drop=True),
        ).fit()
        dep = _dynamic_cumulative_response(bootstrap_result.params, p, q, "depreciation", horizons)
        app = _dynamic_cumulative_response(bootstrap_result.params, p, q, "appreciation", horizons)
        draws.append(np.array([dep[h] + app[h] for h in horizons], dtype=float))
    draw_array = np.asarray(draws)
    centered = draw_array - draw_array.mean(axis=0)
    covariance = np.cov(draw_array, rowvar=False, ddof=1)
    rank = int(np.linalg.matrix_rank(covariance))
    joint_statistic = float(observed @ np.linalg.pinv(covariance) @ observed)
    joint_pvalue = float(chi2.sf(joint_statistic, rank))

    rows: list[dict[str, float | int]] = []
    for index, horizon in enumerate(horizons):
        lower, upper = np.quantile(draw_array[:, index], [0.025, 0.975])
        tail_probability = min(
            1.0,
            2.0
            * min(
                (np.count_nonzero(centered[:, index] <= observed[index]) + 1) / (replicates + 1),
                (np.count_nonzero(centered[:, index] >= observed[index]) + 1) / (replicates + 1),
            ),
        )
        rows.append(
            {
                "horizon_months": horizon,
                "depreciation_cumulative_response": dep_observed[horizon],
                "appreciation_cumulative_response": app_observed[horizon],
                "asymmetry_contrast": observed[index],
                "bootstrap_ci_95_lower": float(lower),
                "bootstrap_ci_95_upper": float(upper),
                "bootstrap_p_value": float(tail_probability),
                "replicates": replicates,
                "block_length": block_length,
            }
        )
    joint = {
        "test": "moving-block bootstrap Wald test of cumulative response contrasts",
        "statistic": joint_statistic,
        "degrees_of_freedom": rank,
        "p_value": joint_pvalue,
        "replicates": replicates,
        "block_length": block_length,
        "seed": seed,
        "restriction": (
            "depreciation response + equal-sized appreciation response = 0 at months 1, 3, 6"
        ),
    }
    return pd.DataFrame(rows), joint


def apply_holm_adjustment(p_values: list[float]) -> list[float]:
    """Return Holm-adjusted p-values in their original order."""
    from statsmodels.stats.multitest import multipletests

    if not p_values:
        return []
    return multipletests(p_values, method="holm")[1].tolist()


def conditional_nardl_bounds(
    panel: pd.DataFrame,
    integration: pd.DataFrame,
    outcome: str,
    p: int,
    q: int,
    seed: int = BOOTSTRAP_SEED,
    simulations: int = 10_000,
) -> tuple[dict[str, Any], pd.DataFrame | None]:
    """Run a finite-sample ARDL bounds screen only for unambiguously I(0)/I(1) inputs.

    Long-run coefficients are calculated and tested only when the simulated 95%
    upper critical bound is exceeded. The outcome is still an inflation rate, so
    such a relation is not interpreted as a price-level elasticity.
    """
    required_series = (outcome, "fx_positive_partial_sum", "fx_negative_partial_sum")
    classifications = integration.set_index("series")["classification"].to_dict()
    relevant = {name: classifications.get(name, "unclassified") for name in required_series}
    allowed = {"I(0)-consistent", "I(1)-consistent"}
    if not set(relevant.values()).issubset(allowed):
        return (
            {
                "status": (
                    "not estimated: at least one bounds variable is ambiguous or possibly I(2)"
                ),
                "dependent_series": outcome,
                "integration_classifications": "; ".join(
                    f"{name}={value}" for name, value in relevant.items()
                ),
                "finite_sample_bounds_test": "not run",
                "long_run_coefficients": "not reported",
            },
            None,
        )

    data = panel[["date", *required_series]].copy()
    data = data.replace([np.inf, -np.inf], np.nan).dropna()
    if len(data) < 60:
        return (
            {
                "status": (
                    "not estimated: insufficient usable observations for conditional bounds test"
                ),
                "dependent_series": outcome,
                "observations": int(len(data)),
                "integration_classifications": "; ".join(
                    f"{name}={value}" for name, value in relevant.items()
                ),
                "finite_sample_bounds_test": "not run",
                "long_run_coefficients": "not reported",
            },
            None,
        )
    effective_q = max(q, 1)
    regressors = data[["fx_positive_partial_sum", "fx_negative_partial_sum"]].copy()
    model = ARDL(
        data[outcome].astype(float),
        lags=p,
        exog=regressors.astype(float),
        order=effective_q,
        trend="c",
        causal=False,
        missing="raise",
    )
    uecm = UECM.from_ardl(model)
    fitted = uecm.fit()
    bounds = fitted.bounds_test(
        case=3,
        asymptotic=False,
        nsim=simulations,
        rng=seed,
    )
    critical = bounds.critical_values
    lower_95 = float(critical.loc[95.0, "lower"])
    upper_95 = float(critical.loc[95.0, "upper"])
    if bounds.statistic > upper_95:
        decision = "upper bound exceeded: evidence consistent with cointegration"
    elif bounds.statistic <= lower_95:
        decision = "below lower bound: no cointegration evidence"
    else:
        decision = "between bounds: inconclusive"
    output: dict[str, Any] = {
        "status": decision,
        "dependent_series": outcome,
        "observations": int(len(data)),
        "sample_start": pd.to_datetime(data["date"]).min().date().isoformat(),
        "sample_end": pd.to_datetime(data["date"]).max().date().isoformat(),
        "integration_classifications": "; ".join(
            f"{name}={value}" for name, value in relevant.items()
        ),
        "model": "ARDL converted to UECM; unrestricted intercept, no trend (PSS case 3)",
        "p": int(p),
        "q": int(effective_q),
        "bounds_f_statistic": float(bounds.statistic),
        "bounds_lower_95": lower_95,
        "bounds_upper_95": upper_95,
        "bounds_pvalue_lower": float(bounds.pvalue["lower"]),
        "bounds_pvalue_upper": float(bounds.pvalue["upper"]),
        "finite_sample_simulations": int(simulations),
        "simulation_seed": int(seed),
        "long_run_coefficients": "not reported unless the upper bound is exceeded",
    }

    long_run_rows: list[dict[str, Any]] = []
    if bounds.statistic > upper_95:
        names = list(fitted.params.index)
        outcome_level = next(
            (name for name in names if name.startswith(f"{outcome}.L1")),
            None,
        )
        positive_level = next(
            (name for name in names if name.startswith("fx_positive_partial_sum.L1")),
            None,
        )
        negative_level = next(
            (name for name in names if name.startswith("fx_negative_partial_sum.L1")),
            None,
        )
        if not outcome_level or not positive_level or not negative_level:
            raise RuntimeError("UECM fit did not expose the expected lagged-level terms.")
        coefficient = fitted.params
        covariance = np.asarray(fitted.cov_params(), dtype=float)
        name_positions = {name: index for index, name in enumerate(names)}
        phi = float(coefficient[outcome_level])
        beta_positive = float(coefficient[positive_level])
        beta_negative = float(coefficient[negative_level])
        if np.isclose(phi, 0.0):
            raise RuntimeError(
                "UECM lagged outcome coefficient is zero; long-run ratio is undefined."
            )
        theta_positive = -beta_positive / phi
        theta_negative = -beta_negative / phi
        contrast = theta_positive - theta_negative
        gradient = np.zeros(len(names), dtype=float)
        gradient[name_positions[outcome_level]] = (beta_positive - beta_negative) / (phi**2)
        gradient[name_positions[positive_level]] = -1.0 / phi
        gradient[name_positions[negative_level]] = 1.0 / phi
        variance = float(gradient @ covariance @ gradient)
        standard_error = float(np.sqrt(max(variance, 0.0)))
        z_statistic = contrast / standard_error if standard_error > 0 else np.nan
        long_run_rows.append(
            {
                "outcome": outcome,
                "theta_positive": theta_positive,
                "theta_negative_signed_scale": theta_negative,
                "asymmetry_contrast": contrast,
                "standard_error_delta_method": standard_error,
                "z_statistic": z_statistic,
                "p_value": (
                    float(2.0 * norm.sf(abs(z_statistic))) if np.isfinite(z_statistic) else np.nan
                ),
                "interpretation": (
                    "Long-run relation of annual inflation to signed partial sums; "
                    "not a price-level elasticity."
                ),
            }
        )
        output["long_run_coefficients"] = (
            "estimated after upper-bound rejection; see stage3_nardl_long_run.csv"
        )
    return output, pd.DataFrame(long_run_rows) if long_run_rows else None
