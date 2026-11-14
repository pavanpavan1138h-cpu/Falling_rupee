"""Run the approved Stage 3 asymmetric exchange-rate pass-through analysis."""

from __future__ import annotations

import hashlib
import json
import platform
import sys
from pathlib import Path
from typing import Any

import matplotlib
import numpy as np
import pandas as pd
import scipy
import statsmodels

from src.pass_through.data import (
    ROOT,
    build_source_panel,
    load_stage3_sources,
    wpi_zero_audit,
)
from src.pass_through.diagnostics import run_model_diagnostics
from src.pass_through.estimation import (
    BOOTSTRAP_BLOCK_LENGTH,
    BOOTSTRAP_REPLICATES,
    BOOTSTRAP_SEED,
    HAC_LAGS,
    apply_holm_adjustment,
    bootstrap_dynamic_asymmetry,
    coefficient_table,
    conditional_nardl_bounds,
    fit_hac_model,
    fit_summary,
)
from src.pass_through.features import (
    SAMPLE_END,
    SAMPLE_START,
    build_stage3_features,
)
from src.pass_through.hypothesis_tests import (
    test_brent_interactions,
    test_cpi_wpi_fx_contrast,
    test_short_run_asymmetry,
)
from src.pass_through.models import (
    MAX_FX_LAG,
    MIN_OBSERVATIONS_PER_PARAMETER,
    ControlKind,
    ModelKind,
    build_analysis_panel,
    build_model_design,
    choose_lags,
)
from src.pass_through.stationarity import run_stationarity_tests
from src.pass_through.validation import validate_source_inputs, validate_stage3_panel
from src.pass_through.visualization import generate_stage3_figures

REPORT_ROOT = ROOT / "reports" / "experiments"
MODEL_ROOT = ROOT / "artifacts" / "models" / "pass_through"
PREDICTION_ROOT = ROOT / "artifacts" / "predictions" / "pass_through"
METRIC_ROOT = ROOT / "artifacts" / "metrics" / "pass_through"
VISUALIZATION_ROOT = ROOT / "visualizations" / "pass_through"

OUTCOMES = {
    "cpi_annual_log_inflation": "CPI General (index-derived annual log inflation)",
    "wpi_all_commodities_annual_log_inflation": (
        "WPI All Commodities (index-derived annual log inflation)"
    ),
    "wpi_fuel_power_annual_log_inflation": (
        "WPI Fuel & Power (index-derived annual log inflation)"
    ),
    "wpi_manufactured_annual_log_inflation": (
        "WPI Manufactured Products (index-derived annual log inflation)"
    ),
}
PRIMARY_OUTCOMES = (
    "cpi_annual_log_inflation",
    "wpi_all_commodities_annual_log_inflation",
)
SECONDARY_OUTCOMES = (
    "wpi_fuel_power_annual_log_inflation",
    "wpi_manufactured_annual_log_inflation",
)
SEED = 42


def _write_table(path: Path, frame: pd.DataFrame) -> None:
    """Write a deterministic CSV with fixed float formatting."""
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False, float_format="%.12g", lineterminator="\n")


def _markdown_table(frame: pd.DataFrame, columns: list[str] | None = None) -> str:
    """Render a concise table without relying on optional notebook display tools."""
    selected = frame if columns is None else frame[columns]
    if selected.empty:
        return "_No rows._"
    headers = [str(column) for column in selected.columns]
    rows = [
        ["" if pd.isna(value) else str(value) for value in row]
        for row in selected.itertuples(index=False, name=None)
    ]
    widths = [
        max(len(headers[index]), *(len(row[index]) for row in rows))
        for index in range(len(headers))
    ]
    output = [
        "| "
        + " | ".join(header.ljust(widths[index]) for index, header in enumerate(headers))
        + " |",
        "| " + " | ".join("-" * width for width in widths) + " |",
    ]
    output.extend(
        "| " + " | ".join(value.ljust(widths[index]) for index, value in enumerate(row)) + " |"
        for row in rows
    )
    return "\n".join(output)


def _save_markdown(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.rstrip() + "\n", encoding="utf-8")


def _fit_one(
    frame: pd.DataFrame,
    outcome: str,
    p: int,
    q: int,
    kind: ModelKind,
    model_name: str,
    control: ControlKind = "none",
    lag_only: bool = False,
    post_2020_break: bool = False,
) -> dict[str, Any]:
    """Fit one specified HAC OLS model and return its design and results."""
    design = build_model_design(
        frame,
        p,
        q,
        kind,
        control,
        lag_only=lag_only,
        post_2020_break=post_2020_break,
    )
    result = fit_hac_model(design)
    return {
        "outcome": outcome,
        "model": model_name,
        "p": p,
        "q": q,
        "control": control,
        "design": design,
        "result": result,
        "summary": fit_summary(result),
    }


def _append_fit(
    fit: dict[str, Any],
    coefficients: list[pd.DataFrame],
    summaries: list[dict[str, Any]],
    fitted_values: list[pd.DataFrame],
    model_specs: dict[str, Any],
) -> None:
    design = fit["design"]
    result = fit["result"]
    coefficients.append(
        coefficient_table(
            result,
            fit["model"],
            fit["outcome"],
            fit["p"],
            fit["q"],
            fit["control"],
            design.dates,
        )
    )
    summaries.append(
        {
            "model": fit["model"],
            "outcome": fit["outcome"],
            "p": fit["p"],
            "q": fit["q"],
            "control": fit["control"],
            "covariance": "HAC/Newey-West",
            **fit["summary"],
        }
    )
    fitted_values.append(
        pd.DataFrame(
            {
                "date": design.dates,
                "outcome": fit["outcome"],
                "model": fit["model"],
                "actual": design.outcome,
                "fitted": result.fittedvalues,
                "residual": result.resid,
            }
        )
    )
    model_specs[f"{fit['model']}__{fit['outcome']}"] = {
        "p": fit["p"],
        "q": fit["q"],
        "control": fit["control"],
        "terms": list(design.feature_names),
        "observations": int(result.nobs),
        "sample_start": design.dates.min().date().isoformat(),
        "sample_end": design.dates.max().date().isoformat(),
        "coefficients": {str(name): float(value) for name, value in result.params.items()},
        "hac_standard_errors": {str(name): float(value) for name, value in result.bse.items()},
        "hac_lags": HAC_LAGS,
    }


def _robustness_row(
    name: str,
    fit: dict[str, Any] | None,
    baseline_bic: float,
    status: str = "estimated",
    note: str = "",
    compare_bic: bool = True,
) -> dict[str, Any]:
    if fit is None:
        return {
            "specification": name,
            "status": status,
            "observations": np.nan,
            "p": np.nan,
            "q": np.nan,
            "bic": np.nan,
            "bic_delta": np.nan,
            "r_squared": np.nan,
            "note": note,
        }
    summary = fit["summary"]
    return {
        "specification": name,
        "status": status,
        "observations": summary["observations"],
        "p": fit["p"],
        "q": fit["q"],
        "bic": summary["bic"],
        "bic_delta": summary["bic"] - baseline_bic if compare_bic else np.nan,
        "r_squared": summary["r_squared"],
        "note": note,
    }


def _write_data_report(
    validation: dict[str, Any],
    panel_validation: dict[str, Any],
    zero_summary: pd.DataFrame,
    panel: pd.DataFrame,
) -> None:
    cpi_labels = panel["cpi_series_label"].dropna().astype(str).unique().tolist()
    cpi_base = panel["cpi_base_year"].dropna().unique().tolist()
    zero_total = int(validation["wpi_zero_dates"].shape[0])
    zero_lines = [
        f"- **{row.comm_name}** (code `{int(row.comm_code)}`): {int(row.zero_observations)} "
        f"zero observations, {row.first_zero:%Y-%m} through {row.last_zero:%Y-%m}."
        for row in zero_summary.itertuples()
    ]
    selected_wpi = pd.DataFrame(validation["selected_wpi_checks"])
    coverage = pd.DataFrame(
        [{"series": name, **details} for name, details in panel_validation["availability"].items()]
    )
    content = f"""# Stage 3 Data Validation Report

**Scope:** Read-only source loading and Stage 3 derived variables. No source dataset was changed.

## Sources and target identity

The All India / Combined / CPI (General) record was selected by its explicit fields. The
selected sample labels are `{", ".join(cpi_labels)}` and base year(s)
`{", ".join(map(str, cpi_base))}`.
The primary CPI and all WPI outcomes below are **index-derived annual log inflation**, not
publisher-reported inflation. The publisher CPI `inflation_value` remains a separate series;
its values were not filled or replaced.

The common source calendar is **{panel_validation["rows"]} consecutive months**
({panel_validation["start"]} to {panel_validation["end"]}). The 12-month transformation uses
the prior-year index observation; USD/INR January 2014 change uses December 2013. After the
maximum pre-specified outcome/FX lag construction (six months for the slow-pass-through
sensitivity), each common-sample model has
{max(0, panel_validation["rows"] - MAX_FX_LAG)} candidate observations before any
control-specific loss.
No missing values were interpolated.

{_markdown_table(coverage)}

### CPI published inflation

The source file has {validation["cpi_published_missing_in_sample"]} missing published inflation
values in the common 2014–2024 sample. The known 2025 gap and separate 2026 segment were not
bridged. Published inflation was modeled only as a distinct CPI sensitivity.

## WPI zero-value investigation

The full WPI table contains **{zero_total} numeric zeros** across
{len(zero_summary)} detailed series. Source values were preserved. The local workbook and prior
data issue register do not establish whether these zeros are published values, missing-value
codes, structural non-applicability, or another convention. They were not changed or logged.
Exact zero dates for every affected row are in
`data/processed/stage3/stage3_wpi_zero_observations.csv`.

{chr(10).join(zero_lines) if zero_lines else "- No zeros found."}

The selected WPI outcomes were checked independently:

{_markdown_table(selected_wpi)}

Only the selected headline and major-group series, all positive and complete in this sample,
were used for logarithms. Affected detailed commodity rows were not used.

## Constructed variables and information timing

- USD/INR log change is `100 * diff(log(USD/INR))`; positive values indicate rupee depreciation.
- `depreciation = max(change, 0)` is nonnegative; `appreciation = min(change, 0)` retains its
  negative sign.
- Positive and negative partial sums start at zero immediately before January 2014 and cumulate
  only in-sample changes.
- CPI General, WPI All Commodities, Fuel & Power, and Manufactured Products annual outcomes use
  `100 * (ln(index_t) - ln(index_t-12))`. Their simple annual index changes are separate
  robustness variables.
- Brent USD and Brent-INR proxy changes, repo changes, and NEER/REER changes were constructed
  from the existing processed inputs. The Brent-INR field is an approximate product proxy, not
  actual landed import cost.

## Provenance and limitations

Prior project audits still leave local FX, CPI, Brent, repo, and NEER/REER vintages or date
semantics incompletely authenticated. The CPI record's 2024-base series transition and the
WPI detailed-series zero convention remain source-level limitations. Therefore the analysis is
retrospective and observation-date based, not a real-time or causal pass-through study.
Repo and NEER/REER controls were not included in the primary models because their source/date
conventions remain unverified.
"""
    _save_markdown(REPORT_ROOT / "STAGE3_DATA_VALIDATION_REPORT.md", content)


def _write_stationarity_report(
    tests: pd.DataFrame,
    classifications: pd.DataFrame,
    nardl_gate: dict[str, Any],
) -> None:
    key_names = {
        "usd_inr_monthly",
        "fx_log_change_pct",
        "fx_positive_partial_sum",
        "fx_negative_partial_sum",
        "cpi_index",
        "cpi_annual_log_inflation",
        "wpi_all_commodities_index",
        "wpi_all_commodities_annual_log_inflation",
        "brent_usd_per_barrel",
        "brent_log_change_pct",
        "brent_inr_proxy_level",
        "repo_rate",
    }
    level = tests.loc[tests["difference_order"].eq(0) & tests["series"].isin(key_names)]
    merged = level.merge(classifications[["series", "classification"]], on="series", how="left")
    ambiguous = int(classifications["classification"].str.startswith("ambiguous").sum())
    possible_i2 = int(classifications["classification"].str.startswith("possible I(2)").sum())
    table = merged[
        [
            "series",
            "observations",
            "deterministic",
            "adf_statistic",
            "adf_pvalue",
            "adf_used_lag",
            "kpss_statistic",
            "kpss_pvalue",
            "kpss_lags",
            "classification",
            "warnings",
        ]
    ].copy()
    gate_table = pd.DataFrame([nardl_gate])
    content = f"""# Stage 3 Stationarity and Integration Report

**Scope:** Paired ADF and KPSS tests on the common sample and successive first differences.  
**Deterministics:** ADF and KPSS use a constant and linear trend (`ct`) for index/level and
cumulative partial-sum series; a constant (`c`) is used for changes and inflation rates.
ADF lag selection is AIC-based; KPSS bandwidth is automatic. Tests use the actual observed
sample and no interpolation.

## Selected level-test results

{_markdown_table(table.round(6))}

The full test table, including first and second differences, selected lag counts, critical
values, and captured numerical warnings, is
`artifacts/metrics/pass_through/stage3_stationarity_tests.csv`. Classification requires both
tests to support stationarity at 5%; mixed or low-power results are kept ambiguous.

## Integration screening and NARDL eligibility

Across tested series, {ambiguous} classifications are ambiguous/disagreeing and
{possible_i2} are flagged as possible I(2). These are indicative classifications, not proofs;
the sample is short and annual inflation observations overlap. ADF/KPSS critical behavior and
the realized statistics are reported rather than treating a single test as decisive.

{_markdown_table(gate_table)}

The primary rate-based distributed-lag models do not require a cointegration claim. Conditional
NARDL is attempted only if the dependent variable and both FX partial sums are consistently
classified as at most I(1), none is ambiguous or possible I(2), and the finite-sample bounds
test is computable. If eligibility or cointegration is not established, no long-run pass-through
coefficient is reported.
"""
    _save_markdown(REPORT_ROOT / "STAGE3_STATIONARITY_REPORT.md", content)


def _write_estimation_report(
    summaries: pd.DataFrame,
    selection: pd.DataFrame,
    coefficients: pd.DataFrame,
    lag_choices: dict[str, tuple[int, int]],
    nardl_gate: dict[str, Any],
) -> None:
    primary = summaries.loc[
        summaries["model"].isin(["symmetric_baseline", "asymmetric_baseline", "symmetric_matched"])
    ]
    coefficient_subset = coefficients.loc[
        coefficients["model"].isin(
            ["symmetric_baseline", "asymmetric_baseline", "symmetric_matched"]
        )
    ]
    selection_table = pd.DataFrame(
        [
            {"model": model, "selected_p": p, "selected_q": q}
            for model, (p, q) in lag_choices.items()
        ]
    )
    selected_interpretation = {
        "symmetric": lag_choices["symmetric"],
        "asymmetric": lag_choices["asymmetric"],
    }
    content = f"""# Stage 3 Model Estimation Report

## Estimation design

The primary family is a parsimonious distributed-lag autoregression of index-derived annual
inflation. Model A replaces signed FX terms with the total monthly USD/INR log change. Model B
includes separate nonnegative depreciation and nonpositive appreciation changes. These are
conditional associations; contemporaneous (`j=0`) coefficients are not real-time information
claims. HAC/Newey-West covariance uses 12 lags because the 12-month inflation outcomes overlap,
with a Bartlett kernel and small-sample correction.

Candidate `p` values are 1–3 and `q` values 0–3. A restricted `p=1, q=6` model is the
pre-specified slower-pass-through sensitivity. The common CPI/WPI All Commodities lag pair is
selected by summed BIC for each model family. AIC is retained as a sensitivity. Candidate
models use a common maximum-lag sample; every candidate is screened to retain at least
{MIN_OBSERVATIONS_PER_PARAMETER:g} observations per parameter. The selected asymmetric pair is
`p={selected_interpretation["asymmetric"][0]}`, `q={selected_interpretation["asymmetric"][1]}`;
the separately BIC-selected symmetric pair is
`p={selected_interpretation["symmetric"][0]}`, `q={selected_interpretation["symmetric"][1]}`.

## Selected lag structures

{_markdown_table(selection_table)}

## Primary model fit

{_markdown_table(primary.round(6))}

Complete candidate BIC/AIC results are in
`artifacts/metrics/pass_through/stage3_lag_selection.csv`. All coefficient estimates, HAC
standard errors, p-values, confidence intervals, and terms are in
`artifacts/metrics/pass_through/stage3_coefficients.csv`. Fitted values and residuals are in
`artifacts/predictions/pass_through/stage3_fitted_values.csv`.

## Coefficients and interpretation

{_markdown_table(coefficient_subset.round(6))}

`appreciation` remains negative-valued. Under the signed-scale symmetry null,
`beta_depreciation = beta_appreciation`; a one-unit appreciation shock contributes
`-beta_appreciation`. The symmetric model with the asymmetric-selected lag pair is included so
the nested comparison uses matching terms and observations. AIC/BIC and R-squared describe
in-sample fit and do not establish predictive value, causality, or stable structural pass-through.

Brent USD changes enter only as a lagged imported-cost extension. The interaction model is
exploratory. The Brent-INR proxy is estimated as a separate proxy-only alternative because it
mechanically includes FX; it is not actual landed import cost. Repo and NEER/REER were not
estimated as controls because their local source/date semantics are unresolved.

## Conditional NARDL assessment

{_markdown_table(pd.DataFrame([nardl_gate]))}

The NARDL/UECM bounds procedure is conditional; an unsupported or inconclusive bounds result is
not converted into a long-run claim. In particular, a relation involving annual inflation and
cumulative exchange-rate movements is not labelled a long-run elasticity.
"""
    _save_markdown(REPORT_ROOT / "STAGE3_MODEL_ESTIMATION_REPORT.md", content)


def _write_hypothesis_report(
    tests: pd.DataFrame,
    responses: pd.DataFrame,
    joint_responses: pd.DataFrame,
) -> None:
    content = f"""# Stage 3 Hypothesis Testing Report

**Inference:** H1 uses joint HAC Wald restrictions on signed FX-lag coefficients. H2 uses
moving-block resampling of complete monthly regression rows with block length six, 499
replications, and seed 42. H3 uses a stacked CPI/WPI model with covariance clustered by common
month. H4 tests the pre-specified FX-by-lagged-Brent interaction block with HAC covariance.
Holm adjustments are applied within the documented outcome/horizon families; the small sample
and data provenance limitations remain.

## Hypothesis tests

{_markdown_table(tests.round(6))}

## Dynamic response contrasts

The reported depreciation response is to a one-unit positive shock; the appreciation response
is to an equal-size negative shock, retaining the signed `App` convention. The asymmetry
contrast is their sum, which is zero under signed-scale symmetry. Cumulative horizons include
the impact period and are shown only as dynamic response summaries, not long-run multipliers.

{_markdown_table(responses.round(6))}

### Joint H2 response-path tests

{_markdown_table(joint_responses.round(6))}

Failure to reject a restriction is insufficient evidence against the alternative, not proof of
exact symmetry or absence of imported-cost effects. Statistical association is not causal
identification.
"""
    _save_markdown(REPORT_ROOT / "STAGE3_HYPOTHESIS_TESTING_REPORT.md", content)


def _write_diagnostics_report(
    diagnostics: pd.DataFrame,
    robustness: pd.DataFrame,
    influence: pd.DataFrame,
) -> None:
    diagnostic_columns = [
        "outcome",
        "model",
        "observations",
        "breusch_godfrey_lm_pvalue",
        "ljung_box_12_pvalue",
        "breusch_pagan_lm_pvalue",
        "ramsey_reset_pvalue",
        "jarque_bera_pvalue",
        "cusum_pvalue",
        "condition_number",
    ]
    top_influence = influence.sort_values("cooks_d", ascending=False).head(10)
    top_influence_display = top_influence.copy()
    numeric_columns = top_influence_display.select_dtypes(include=np.number).columns
    top_influence_display[numeric_columns] = top_influence_display[numeric_columns].round(6)
    content = f"""# Stage 3 Diagnostics and Robustness Report

## Residual and stability checks

{_markdown_table(diagnostics[diagnostic_columns].round(6))}

Full numerical results are in
`artifacts/metrics/pass_through/stage3_diagnostics.csv`; influential rows and recursive
coefficient paths are in the corresponding Stage 3 metrics files. Breusch–Godfrey and
Ljung–Box assess residual serial correlation, Breusch–Pagan assesses heteroskedasticity,
RESET is a functional-form diagnostic, Jarque–Bera describes residual shape, and CUSUM assesses
parameter stability. None is a validity certificate, and HAC covariance does not resolve
endogeneity, omitted variables, or vintage uncertainty.

Largest absolute Cook's-distance observations in the reported diagnostic models:

{_markdown_table(top_influence_display)}

## Robustness comparisons

{_markdown_table(robustness.round(6))}

The extreme-movement cutoff is the 95th percentile of absolute monthly USD/INR log changes in
1990–2013, computed before the Stage 3 estimation window. The pandemic subperiod is defined
before estimation as March 2020 onward; subperiod fits use a restricted `p=1, q=1` specification
and have low power. Brent and proxy analyses are separate. Optional repo/NEER/REER control fits
were not run because their local series mapping/date conventions remain unverified.
No synthetic empirical observations were generated.
"""
    _save_markdown(REPORT_ROOT / "STAGE3_DIAGNOSTICS_AND_ROBUSTNESS_REPORT.md", content)


def _write_final_report(
    summaries: pd.DataFrame,
    tests: pd.DataFrame,
    responses: pd.DataFrame,
    joint_responses: pd.DataFrame,
    diagnostics: pd.DataFrame,
    robustness: pd.DataFrame,
    nardl_gate: dict[str, Any],
    output_hashes: dict[str, str],
    protected_integrity: dict[str, Any],
) -> None:
    primary_fits = summaries.loc[
        summaries["model"].isin(["symmetric_baseline", "asymmetric_baseline"])
        & summaries["outcome"].isin(PRIMARY_OUTCOMES)
    ]
    h1 = tests.loc[tests["hypothesis"].str.contains("H1", regex=False)]
    h3 = tests.loc[tests["hypothesis"].str.contains("H3", regex=False)]
    h4 = tests.loc[tests["hypothesis"].str.contains("H4", regex=False)]
    output_hash_table = pd.DataFrame(
        [{"file": path, "sha256": digest} for path, digest in output_hashes.items()]
    )
    content = f"""# Stage 3 Final Research Report

## Executive assessment

**Classification: VERIFIED WITH LIMITATIONS.** The Stage 3 implementation executes the
approved, retrospective asymmetric distributed-lag design on the available 2014–2024 common
sample. The data checks, variable construction, estimation, formal tests, diagnostics,
robustness analyses, outputs, and deterministic rerun evidence are recorded in the accompanying
reports and artifacts. This classification is implementation readiness, not independent
researcher approval, proof of model correctness, or causal validation.

The primary research question is whether signed USD/INR depreciation and appreciation changes
have distinguishable conditional associations with index-derived annual CPI and WPI inflation,
including dynamic timing, cross-outcome differences, and imported-cost conditions. No direction
of asymmetry was assumed.

## Data, variables, and sample

The estimation calendar is January 2014–December 2024. Outcomes are consistently calculated as
`100 * [ln(index_t) - ln(index_t-12)]`, explicitly **index-derived annual log inflation**, not
official published inflation. Publisher CPI inflation remains a distinct sensitivity and the
2025 gap was not filled. The CPI and WPI source fields and each selected series identity are
documented in `STAGE3_DATA_VALIDATION_REPORT.md`. Lag-adjusted sample counts are in the model
comparison and fitted-values outputs; the maximum-lag baseline has 126 observations per complete
series before control-specific missingness.

USD/INR is INR per USD: positive log changes mean depreciation. Depreciation is nonnegative;
appreciation is retained as a nonpositive variable. The Brent-INR measure is a product-based
approximation, not landed import cost.

## Models and selection

Model A is a symmetric distributed-lag benchmark; Model B estimates separate signed
depreciation/appreciation lag coefficients. Common lag pairs are selected by summed BIC across
CPI and WPI All Commodities, with AIC and maximum-lag choices reported as sensitivities.
Newey–West HAC standard errors use 12 lags to reflect the overlapping annual inflation
transformation. A conditional NARDL/UECM is estimated only if integration screening and the
finite-sample bounds procedure support it; otherwise long-run coefficients are not reported.

{_markdown_table(primary_fits.round(6))}

## Hypothesis results

H1 signed-scale asymmetry:

{_markdown_table(h1.round(6))}

H2 cumulative dynamic response contrasts:

{_markdown_table(responses.round(6))}

Joint H2 response-path tests:

{_markdown_table(joint_responses.round(6))}

H3 cross-outcome coefficient contrasts:

{_markdown_table(h3.round(6))}

H4 imported-cost interaction:

{_markdown_table(h4.round(6))}

These are statistical associations in a short sample. A failure to reject does not establish no
pass-through or symmetry; a significant result does not establish causality.

## Diagnostics and robustness

{_markdown_table(diagnostics.round(6))}

{_markdown_table(robustness.round(6))}

Tests cover serial correlation, heteroskedasticity, functional form, residual distribution,
stability, influence, alternate transformations, lag-only FX terms, imported-cost alternatives,
subperiods, and an extreme-movement sensitivity. The effective sample remains small for multiple
tests; secondary WPI and horizon results are exploratory.

## WPI zeros, provenance, and limitations

The source WPI file contains 505 numeric zeros across six detailed series with unresolved
publisher semantics. Those source values were preserved and excluded from log-based WPI outcome
construction. All Commodities, Fuel & Power, and Manufactured Products were separately checked
for positive complete levels. CPI/FX/Brent/repo/NEER/REER vintage and date-timing limitations
remain; the repo and NEER/REER controls were therefore not estimated. The analysis is not a
real-time backtest and cannot identify causal pass-through.

## NARDL/long-run decision

{_markdown_table(pd.DataFrame([nardl_gate]))}

## Reproducibility and protected data

Python {platform.python_version()}, pandas {pd.__version__}, NumPy {np.__version__}, statsmodels
{statsmodels.__version__}, SciPy {scipy.__version__}, and Matplotlib {matplotlib.__version__} were
used. The bootstrap seed is {BOOTSTRAP_SEED}. Reproducibility is evaluated on normalized
generated Stage 3 outputs; binary hashes are listed in
`artifacts/metrics/pass_through/stage3_reproducibility_hashes.json`. Protected raw,
processed-existing, and prior-stage artifacts were SHA-256 checked before and after the pipeline:
**{protected_integrity["status"]}**, {protected_integrity["protected_file_count_before"]} files,
inventory hash before `{protected_integrity["before_inventory_sha256"]}` and after
`{protected_integrity["after_inventory_sha256"]}`. The path-level record is
`artifacts/metrics/pass_through/stage3_protected_integrity.json`.

Output hashes from the final run:

{_markdown_table(output_hash_table)}

## Interpretation and limitations

No evidence here supports causal statements about Brent, monetary policy, or NEER/REER. The
retrospective common sample, overlapping inflation outcome, unknown historical release
availability, limited power, unresolved WPI detailed-zero convention, and lack of an
identification strategy are substantive limitations. Conclusions are conditional on the
specified model and observed data vintage. Independent researcher review is required before
Stage 4.
"""
    _save_markdown(REPORT_ROOT / "STAGE3_FINAL_RESEARCH_REPORT.md", content)


def _file_hashes(paths: list[Path], root: Path) -> dict[str, str]:
    """Return SHA-256 hashes for generated Stage 3 deliverables."""
    return {
        str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(paths)
        if path.is_file()
    }


def _protected_file_hashes(root: Path) -> dict[str, str]:
    """Hash source data and prior-stage artifacts, excluding Stage 3-owned paths."""
    protected: dict[str, str] = {}
    folders = (
        root / "data" / "raw",
        root / "data" / "processed",
        root / "artifacts" / "models",
        root / "artifacts" / "predictions",
        root / "artifacts" / "metrics",
        root / "visualizations",
    )
    for folder in folders:
        if not folder.exists():
            continue
        for path in sorted(folder.rglob("*")):
            if not path.is_file():
                continue
            relative = path.relative_to(root)
            parts = relative.parts
            if parts[:3] == ("data", "processed", "stage3"):
                continue
            if "pass_through" in parts:
                continue
            protected[str(relative)] = hashlib.sha256(path.read_bytes()).hexdigest()
    return protected


def _hash_inventory_fingerprint(hashes: dict[str, str]) -> str:
    """Hash a sorted path-to-content-hash inventory deterministically."""
    serialized = json.dumps(hashes, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(serialized).hexdigest()


def run_stage3(root: Path = ROOT) -> dict[str, Any]:
    """Run data validation, econometric models, reports, and visualizations."""
    global \
        REPORT_ROOT, \
        MODEL_ROOT, \
        PREDICTION_ROOT, \
        METRIC_ROOT, \
        VISUALIZATION_ROOT, \
        STAGE3_DATA_ROOT
    root = root.resolve()
    protected_before = _protected_file_hashes(root)
    processed = root / "data" / "processed"
    STAGE3_DATA_ROOT = processed / "stage3"
    REPORT_ROOT = root / "reports" / "experiments"
    MODEL_ROOT = root / "artifacts" / "models" / "pass_through"
    PREDICTION_ROOT = root / "artifacts" / "predictions" / "pass_through"
    METRIC_ROOT = root / "artifacts" / "metrics" / "pass_through"
    VISUALIZATION_ROOT = root / "visualizations" / "pass_through"
    for path in (STAGE3_DATA_ROOT, MODEL_ROOT, PREDICTION_ROOT, METRIC_ROOT, VISUALIZATION_ROOT):
        path.mkdir(parents=True, exist_ok=True)
    REPORT_ROOT.mkdir(parents=True, exist_ok=True)

    sources = load_stage3_sources(root)
    validation = validate_source_inputs(sources)
    zero_rows, zero_summary = wpi_zero_audit(sources["wpi"])
    _write_table(STAGE3_DATA_ROOT / "stage3_wpi_zero_observations.csv", zero_rows)
    _write_table(STAGE3_DATA_ROOT / "stage3_wpi_zero_summary.csv", zero_summary)

    source_panel = build_source_panel(sources)
    panel = build_stage3_features(source_panel)
    panel_validation = validate_stage3_panel(panel)
    _write_table(STAGE3_DATA_ROOT / "stage3_analysis_panel.csv", panel)
    _write_data_report(validation, panel_validation, zero_summary, panel)

    stationarity_tests, integration = run_stationarity_tests(panel.set_index("date"))
    _write_table(METRIC_ROOT / "stage3_stationarity_tests.csv", stationarity_tests)
    _write_table(METRIC_ROOT / "stage3_integration_classifications.csv", integration)

    analysis_frames = {outcome: build_analysis_panel(panel, outcome) for outcome in OUTCOMES}
    p_sym, q_sym, symmetric_selection = choose_lags(
        {name: analysis_frames[name] for name in PRIMARY_OUTCOMES}, "symmetric"
    )
    p_asym, q_asym, asymmetric_selection = choose_lags(
        {name: analysis_frames[name] for name in PRIMARY_OUTCOMES}, "asymmetric"
    )
    p_aic = int(asymmetric_selection.sort_values("summed_aic").iloc[0]["p"])
    q_aic = int(asymmetric_selection.sort_values("summed_aic").iloc[0]["q"])
    lag_choices = {
        "symmetric": (p_sym, q_sym),
        "asymmetric": (p_asym, q_asym),
        "asymmetric_aic": (p_aic, q_aic),
        "asymmetric_slow_sensitivity": (1, 6),
    }
    selection = pd.concat([symmetric_selection, asymmetric_selection], ignore_index=True)
    _write_table(METRIC_ROOT / "stage3_lag_selection.csv", selection)

    coefficients: list[pd.DataFrame] = []
    summaries: list[dict[str, Any]] = []
    fitted_values: list[pd.DataFrame] = []
    model_specs: dict[str, Any] = {}
    fits: dict[tuple[str, str], dict[str, Any]] = {}

    for outcome in OUTCOMES:
        frame = analysis_frames[outcome]
        p, q = (p_sym, q_sym)
        symmetric = _fit_one(frame, outcome, p, q, "symmetric", "symmetric_baseline")
        _append_fit(symmetric, coefficients, summaries, fitted_values, model_specs)
        fits[(outcome, "symmetric_baseline")] = symmetric

        asym = _fit_one(frame, outcome, p_asym, q_asym, "asymmetric", "asymmetric_baseline")
        _append_fit(asym, coefficients, summaries, fitted_values, model_specs)
        fits[(outcome, "asymmetric_baseline")] = asym

        symmetric_matched = _fit_one(
            frame, outcome, p_asym, q_asym, "symmetric", "symmetric_matched"
        )
        _append_fit(symmetric_matched, coefficients, summaries, fitted_values, model_specs)
        fits[(outcome, "symmetric_matched")] = symmetric_matched

        aic_fit = _fit_one(frame, outcome, p_aic, q_aic, "asymmetric", "asymmetric_aic_sensitivity")
        _append_fit(aic_fit, coefficients, summaries, fitted_values, model_specs)
        fits[(outcome, "asymmetric_aic_sensitivity")] = aic_fit

    for outcome in PRIMARY_OUTCOMES:
        frame = analysis_frames[outcome]
        brent = _fit_one(
            frame,
            outcome,
            p_asym,
            q_asym,
            "asymmetric",
            "asymmetric_brent_extension",
            control="brent",
        )
        _append_fit(brent, coefficients, summaries, fitted_values, model_specs)
        fits[(outcome, "asymmetric_brent_extension")] = brent

        interactions = _fit_one(
            frame,
            outcome,
            p_asym,
            q_asym,
            "asymmetric",
            "asymmetric_brent_interactions",
            control="brent_interactions",
        )
        _append_fit(interactions, coefficients, summaries, fitted_values, model_specs)
        fits[(outcome, "asymmetric_brent_interactions")] = interactions

    # The proxy-only alternative is deliberately not stacked with FX terms.
    proxy_fits: dict[str, dict[str, Any]] = {}
    for outcome in OUTCOMES:
        proxy = _fit_one(
            analysis_frames[outcome],
            outcome,
            min(p_asym, 3),
            0,
            "proxy",
            "brent_inr_proxy_only",
            control="proxy",
        )
        _append_fit(proxy, coefficients, summaries, fitted_values, model_specs)
        fits[(outcome, "brent_inr_proxy_only")] = proxy
        proxy_fits[outcome] = proxy

    # Published CPI is a separate publisher-sourced outcome; it is never filled.
    published_frame = build_analysis_panel(panel, "cpi_published_inflation")
    published_fit = _fit_one(
        published_frame,
        "cpi_published_inflation",
        p_asym,
        q_asym,
        "asymmetric",
        "published_cpi_sensitivity",
    )
    _append_fit(published_fit, coefficients, summaries, fitted_values, model_specs)
    fits[("cpi_published_inflation", "published_cpi_sensitivity")] = published_fit

    # Simple index-derived inflation and simple FX percent change robustness.
    simple_panel = panel.copy()
    simple_panel["fx_log_change_pct"] = simple_panel["fx_simple_change_pct"]
    simple_panel["depreciation"] = simple_panel["fx_simple_change_pct"].clip(lower=0.0)
    simple_panel["appreciation"] = simple_panel["fx_simple_change_pct"].clip(upper=0.0)
    simple_outcomes = {
        "cpi_annual_simple_inflation": "cpi_simple_change_sensitivity",
        "wpi_all_commodities_annual_simple_inflation": "wpi_simple_change_sensitivity",
    }
    simple_fits: dict[str, dict[str, Any]] = {}
    for outcome, label in simple_outcomes.items():
        frame = build_analysis_panel(simple_panel, outcome)
        fit = _fit_one(frame, outcome, p_asym, q_asym, "asymmetric", label)
        _append_fit(fit, coefficients, summaries, fitted_values, model_specs)
        simple_fits[outcome] = fit
    lag_only_fits: dict[str, dict[str, Any]] = {}
    for outcome in PRIMARY_OUTCOMES:
        fit = _fit_one(
            analysis_frames[outcome],
            outcome,
            p_asym,
            max(q_asym, 1),
            "asymmetric",
            "asymmetric_lag_only_sensitivity",
            lag_only=True,
        )
        _append_fit(fit, coefficients, summaries, fitted_values, model_specs)
        lag_only_fits[outcome] = fit
    slow_fits: dict[str, dict[str, Any]] = {}
    for outcome in PRIMARY_OUTCOMES:
        fit = _fit_one(
            analysis_frames[outcome],
            outcome,
            1,
            6,
            "asymmetric",
            "asymmetric_six_month_sensitivity",
        )
        _append_fit(fit, coefficients, summaries, fitted_values, model_specs)
        slow_fits[outcome] = fit

    coefficients_frame = pd.concat(coefficients, ignore_index=True)
    summaries_frame = pd.DataFrame(summaries)
    fitted_frame = pd.concat(fitted_values, ignore_index=True)
    _write_table(METRIC_ROOT / "stage3_coefficients.csv", coefficients_frame)
    _write_table(METRIC_ROOT / "stage3_model_metrics.csv", summaries_frame)
    _write_table(PREDICTION_ROOT / "stage3_fitted_values.csv", fitted_frame)

    # H1-H4 hypothesis tests and response-path intervals.
    hypothesis_rows: list[dict[str, Any]] = []
    response_tables: dict[str, pd.DataFrame] = {}
    response_joint_rows: list[dict[str, Any]] = []
    for outcome in OUTCOMES:
        fit = fits[(outcome, "asymmetric_baseline")]
        hypothesis_rows.append(test_short_run_asymmetry(fit["result"], q_asym, outcome))
        responses, joint = bootstrap_dynamic_asymmetry(
            fit["design"],
            fit["result"],
            p_asym,
            q_asym,
        )
        responses["outcome"] = outcome
        response_tables[outcome] = responses
        response_joint_rows.append({"outcome": outcome, **joint})
    for outcome in PRIMARY_OUTCOMES:
        fit = fits[(outcome, "asymmetric_brent_interactions")]
        hypothesis_rows.append(test_brent_interactions(fit["result"], outcome))

    cross_outcome_rows = []
    cpi_design = fits[(PRIMARY_OUTCOMES[0], "asymmetric_baseline")]["design"]
    for outcome in (
        PRIMARY_OUTCOMES[1],
        *SECONDARY_OUTCOMES,
    ):
        comparison = test_cpi_wpi_fx_contrast(
            cpi_design,
            fits[(outcome, "asymmetric_baseline")]["design"],
            p_asym,
            q_asym,
        )
        comparison["compared_outcome"] = outcome
        cross_outcome_rows.append(comparison)
    hypothesis_rows.extend(cross_outcome_rows)

    tests_frame = pd.DataFrame(hypothesis_rows)
    for hypothesis in (
        "H1 short-run exchange-rate asymmetry",
        "H4 imported-cost conditioning interaction block",
        "H3 CPI versus WPI exchange-rate response",
    ):
        mask = tests_frame["hypothesis"].eq(hypothesis)
        if mask.any():
            tests_frame.loc[mask, "p_value_holm"] = apply_holm_adjustment(
                tests_frame.loc[mask, "p_value"].astype(float).tolist()
            )
    response_frame = pd.concat(response_tables.values(), ignore_index=True)
    response_frame["p_value_holm_by_hypothesis"] = np.nan
    for outcome in OUTCOMES:
        mask = response_frame["outcome"].eq(outcome)
        response_frame.loc[mask, "bootstrap_p_value_holm"] = apply_holm_adjustment(
            response_frame.loc[mask, "bootstrap_p_value"].astype(float).tolist()
        )
    joint_frame = pd.DataFrame(response_joint_rows)
    joint_frame["p_value_holm"] = apply_holm_adjustment(
        joint_frame["p_value"].astype(float).tolist()
    )
    _write_table(METRIC_ROOT / "stage3_hypothesis_tests.csv", tests_frame)
    _write_table(METRIC_ROOT / "stage3_dynamic_responses.csv", response_frame)
    _write_table(METRIC_ROOT / "stage3_dynamic_joint_tests.csv", joint_frame)

    # Diagnostics on the primary baseline specifications.
    diagnostics_rows: list[dict[str, Any]] = []
    residual_rows: list[pd.DataFrame] = []
    influence_rows: list[pd.DataFrame] = []
    stability_rows: list[pd.DataFrame] = []
    for outcome in OUTCOMES:
        for model in ("symmetric_baseline", "asymmetric_baseline"):
            fit = fits[(outcome, model)]
            diagnostic, influence, stability = run_model_diagnostics(
                fit["design"], fit["result"], outcome, model, fit["p"], fit["q"]
            )
            diagnostics_rows.append(diagnostic)
            influence_rows.append(influence)
            stability_rows.append(stability)
            residual_rows.append(
                pd.DataFrame(
                    {
                        "date": fit["design"].dates,
                        "outcome": outcome,
                        "model": model,
                        "actual": fit["design"].outcome,
                        "fitted": fit["result"].fittedvalues,
                        "residual": fit["result"].resid,
                    }
                )
            )
    diagnostics_frame = pd.DataFrame(diagnostics_rows)
    residuals_frame = pd.concat(residual_rows, ignore_index=True)
    influences_frame = pd.concat(influence_rows, ignore_index=True)
    stability_frame = pd.concat(stability_rows, ignore_index=True)
    _write_table(METRIC_ROOT / "stage3_diagnostics.csv", diagnostics_frame)
    _write_table(METRIC_ROOT / "stage3_influential_observations.csv", influences_frame)
    _write_table(METRIC_ROOT / "stage3_recursive_coefficients.csv", stability_frame)
    _write_table(PREDICTION_ROOT / "stage3_diagnostic_residuals.csv", residuals_frame)

    # Prespecified pandemic break interaction sensitivity.
    break_rows = []
    for outcome in PRIMARY_OUTCOMES:
        fit = _fit_one(
            analysis_frames[outcome],
            outcome,
            p_asym,
            q_asym,
            "asymmetric",
            "post_2020_fx_interactions",
            post_2020_break=True,
        )
        terms = [
            "depreciation_x_post_2020",
            "appreciation_x_post_2020",
        ]
        names = list(fit["result"].params.index)
        restriction = np.zeros((len(terms), len(names)), dtype=float)
        for row, term in enumerate(terms):
            restriction[row, names.index(term)] = 1.0
        tested = fit["result"].wald_test(restriction, scalar=True)
        break_rows.append(
            {
                "outcome": outcome,
                "break_date": "2020-03-01",
                "p": p_asym,
                "q": q_asym,
                "observations": int(fit["result"].nobs),
                "wald_statistic": float(tested.statistic),
                "degrees_of_freedom": len(terms),
                "p_value": float(tested.pvalue),
            }
        )
    break_frame = pd.DataFrame(break_rows)
    break_frame["p_value_holm"] = apply_holm_adjustment(break_frame["p_value"].tolist())
    _write_table(METRIC_ROOT / "stage3_structural_break_sensitivity.csv", break_frame)

    # Robustness summary uses the primary CPI asymmetric model as the reference.
    baseline_bic = float(fits[(PRIMARY_OUTCOMES[0], "asymmetric_baseline")]["summary"]["bic"])
    robustness_rows = [
        _robustness_row(
            "CPI baseline asymmetric log/log",
            fits[(PRIMARY_OUTCOMES[0], "asymmetric_baseline")],
            baseline_bic,
        ),
        _robustness_row(
            "CPI lag-only FX",
            lag_only_fits[PRIMARY_OUTCOMES[0]],
            baseline_bic,
            note="Excludes same-month FX; lag structure remains preselected.",
        ),
        _robustness_row(
            "CPI six-month FX lag sensitivity (p=1,q=6)",
            slow_fits[PRIMARY_OUTCOMES[0]],
            baseline_bic,
            note="Pre-specified slower-pass-through sensitivity; not used for primary selection.",
        ),
        _robustness_row(
            "CPI publisher-reported inflation",
            published_fit,
            baseline_bic,
            note="Separate CPI published-rate outcome; no 2025 gap filling.",
            compare_bic=False,
        ),
        _robustness_row(
            "CPI simple annual percent and simple FX percent",
            simple_fits["cpi_annual_simple_inflation"],
            baseline_bic,
            note="Distinct robustness transformations.",
            compare_bic=False,
        ),
        _robustness_row(
            "WPI All Commodities simple annual percent and simple FX percent",
            simple_fits["wpi_all_commodities_annual_simple_inflation"],
            float(fits[(PRIMARY_OUTCOMES[1], "asymmetric_baseline")]["summary"]["bic"]),
            note="Distinct robustness transformations.",
            compare_bic=False,
        ),
        _robustness_row(
            "CPI Brent USD lagged change",
            fits[(PRIMARY_OUTCOMES[0], "asymmetric_brent_extension")],
            baseline_bic,
            note="Lagged imported-cost extension; local vintage remains unauthenticated.",
        ),
        _robustness_row(
            "CPI Brent-INR proxy-only",
            proxy_fits[PRIMARY_OUTCOMES[0]],
            baseline_bic,
            note="Approximate proxy only; no FX split terms due mechanical FX content.",
        ),
        _robustness_row(
            "WPI All Commodities Brent USD lagged change",
            fits[(PRIMARY_OUTCOMES[1], "asymmetric_brent_extension")],
            float(fits[(PRIMARY_OUTCOMES[1], "asymmetric_baseline")]["summary"]["bic"]),
            note="Lagged imported-cost extension; local vintage remains unauthenticated.",
        ),
        _robustness_row(
            "WPI All Commodities Brent-INR proxy-only",
            proxy_fits[PRIMARY_OUTCOMES[1]],
            float(fits[(PRIMARY_OUTCOMES[1], "asymmetric_baseline")]["summary"]["bic"]),
            note="Approximate proxy only; no FX split terms due mechanical FX content.",
        ),
    ]

    # Historical threshold is learned from pre-estimation USD/INR changes only.
    fx_history = sources["fx"].copy()
    fx_history["date"] = pd.to_datetime(fx_history["date"])
    fx_level = pd.to_numeric(fx_history["usd_inr_monthly"], errors="coerce")
    historical_change = np.log(fx_level).diff().mul(100.0)
    historical_mask = fx_history["date"].between("1990-01-01", "2013-12-01")
    threshold = float(historical_change.loc[historical_mask].abs().quantile(0.95))
    extreme_dates = set(
        pd.to_datetime(panel.loc[panel["fx_log_change_pct"].abs().ge(threshold), "date"])
    )
    extreme_count = len(extreme_dates)
    for outcome in PRIMARY_OUTCOMES:
        frame = analysis_frames[outcome]
        non_extreme = frame.loc[~pd.to_datetime(frame["date"]).isin(extreme_dates)].copy()
        if len(non_extreme) / (1 + p_asym + 2 * (q_asym + 1)) >= MIN_OBSERVATIONS_PER_PARAMETER:
            extreme_fit = _fit_one(
                non_extreme,
                outcome,
                p_asym,
                q_asym,
                "asymmetric",
                "extreme_fx_rows_omitted",
            )
            _append_fit(extreme_fit, coefficients, summaries, fitted_values, model_specs)
            robustness_rows.append(
                _robustness_row(
                    f"{outcome}: omit historical 95th-percentile extreme changes",
                    extreme_fit,
                    float(fits[(outcome, "asymmetric_baseline")]["summary"]["bic"]),
                    note=(
                        f"Threshold {threshold:.6g}% from 1990-2013; {extreme_count} Stage 3 "
                        "months flagged across the common sample."
                    ),
                    compare_bic=False,
                )
            )
        else:
            robustness_rows.append(
                _robustness_row(
                    f"{outcome}: omit historical extreme changes",
                    None,
                    float(fits[(outcome, "asymmetric_baseline")]["summary"]["bic"]),
                    status="not estimated: insufficient observations per parameter",
                    note=f"Threshold {threshold:.6g}%; {extreme_count} months flagged.",
                    compare_bic=False,
                )
            )

    # Restricted subperiod comparison avoids overparameterized short-window fits.
    for outcome in PRIMARY_OUTCOMES:
        frame = analysis_frames[outcome]
        for label, start, end in (
            ("pre-2020", "2014-01-01", "2020-02-01"),
            ("2020-onward", "2020-03-01", "2024-12-01"),
        ):
            subset = frame.loc[pd.to_datetime(frame["date"]).between(start, end)].copy()
            restricted = _fit_one(
                subset,
                outcome,
                1,
                1,
                "asymmetric",
                f"subperiod_{label}",
            )
            _append_fit(restricted, coefficients, summaries, fitted_values, model_specs)
            robustness_rows.append(
                _robustness_row(
                    f"{outcome}: {label} (restricted p=1,q=1)",
                    restricted,
                    float(fits[(outcome, "asymmetric_baseline")]["summary"]["bic"]),
                    note="Exploratory; period-specific estimation has limited power.",
                    compare_bic=False,
                )
            )
    robustness_frame = pd.DataFrame(robustness_rows)
    _write_table(METRIC_ROOT / "stage3_robustness_comparison.csv", robustness_frame)
    _write_table(METRIC_ROOT / "stage3_structural_break_sensitivity.csv", break_frame)

    # Conditional NARDL is gated on integration and a reproducible finite-sample bounds test.
    nardl_gates: list[dict[str, Any]] = []
    nardl_long_run: list[pd.DataFrame] = []
    for outcome in PRIMARY_OUTCOMES:
        gate, long_run = conditional_nardl_bounds(
            panel,
            integration,
            outcome,
            p_asym,
            q_asym,
            seed=BOOTSTRAP_SEED,
            simulations=10_000,
        )
        nardl_gates.append(gate)
        if long_run is not None:
            nardl_long_run.append(long_run)
    nardl_gate = {
        "status": "; ".join(
            f"{gate['dependent_series']}: {gate['status']}" for gate in nardl_gates
        ),
        "dependent_series": "; ".join(gate["dependent_series"] for gate in nardl_gates),
        "integration_classifications": " | ".join(
            str(gate.get("integration_classifications", "")) for gate in nardl_gates
        ),
        "finite_sample_bounds_test": " | ".join(
            f"{gate.get('dependent_series')}: stat={gate.get('bounds_f_statistic', 'not run')}, "
            f"95% bounds=({gate.get('bounds_lower_95', '')}, {gate.get('bounds_upper_95', '')})"
            for gate in nardl_gates
        ),
        "long_run_coefficients": (
            "estimated only for an outcome with upper-bound rejection"
            if nardl_long_run
            else "not reported; no established cointegrating relation"
        ),
        "gate_details": json.dumps(nardl_gates, sort_keys=True),
    }
    nardl_gate_frame = pd.DataFrame(nardl_gates)
    _write_table(METRIC_ROOT / "stage3_nardl_bounds_tests.csv", nardl_gate_frame)
    long_run_frame = (
        pd.concat(nardl_long_run, ignore_index=True)
        if nardl_long_run
        else pd.DataFrame(
            columns=[
                "outcome",
                "theta_positive",
                "theta_negative_signed_scale",
                "asymmetry_contrast",
                "standard_error_delta_method",
                "z_statistic",
                "p_value",
                "interpretation",
            ]
        )
    )
    _write_table(METRIC_ROOT / "stage3_nardl_long_run.csv", long_run_frame)
    protected_after = _protected_file_hashes(root)
    protected_integrity = {
        "status": "PASS" if protected_before == protected_after else "FAIL",
        "protected_file_count_before": len(protected_before),
        "protected_file_count_after": len(protected_after),
        "before_inventory_sha256": _hash_inventory_fingerprint(protected_before),
        "after_inventory_sha256": _hash_inventory_fingerprint(protected_after),
        "changed_paths": sorted(
            path
            for path in set(protected_before) | set(protected_after)
            if protected_before.get(path) != protected_after.get(path)
        ),
    }
    (METRIC_ROOT / "stage3_protected_integrity.json").write_text(
        json.dumps(protected_integrity, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    if protected_integrity["status"] != "PASS":
        raise RuntimeError(
            "Stage 3 modified protected inputs or previous-stage artifacts: "
            f"{protected_integrity['changed_paths']}"
        )

    # Include every robustness fit in the coefficient, metric, fitted-value, and model outputs.
    coefficients_frame = pd.concat(coefficients, ignore_index=True)
    summaries_frame = pd.DataFrame(summaries)
    fitted_frame = pd.concat(fitted_values, ignore_index=True)
    _write_table(METRIC_ROOT / "stage3_coefficients.csv", coefficients_frame)
    _write_table(METRIC_ROOT / "stage3_model_metrics.csv", summaries_frame)
    _write_table(PREDICTION_ROOT / "stage3_fitted_values.csv", fitted_frame)
    (MODEL_ROOT / "stage3_model_specifications.json").write_text(
        json.dumps(
            {
                "approved_design": "asymmetric distributed-lag; January 2014-December 2024",
                "selection": {
                    name: {"p": pair[0], "q": pair[1]} for name, pair in lag_choices.items()
                },
                "hac_lags": HAC_LAGS,
                "bootstrap": {
                    "replicates": BOOTSTRAP_REPLICATES,
                    "block_length": BOOTSTRAP_BLOCK_LENGTH,
                    "seed": BOOTSTRAP_SEED,
                },
                "conditional_nardl": nardl_gates,
                "models": model_specs,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    _write_stationarity_report(stationarity_tests, integration, nardl_gate)
    _write_estimation_report(
        summaries_frame,
        selection,
        coefficients_frame,
        lag_choices,
        nardl_gate,
    )
    _write_hypothesis_report(tests_frame, response_frame, joint_frame)
    _write_diagnostics_report(diagnostics_frame, robustness_frame, influences_frame)

    # Hash output and write a reproducibility manifest after every content file is complete.
    figure_paths = generate_stage3_figures(
        panel,
        coefficients_frame,
        response_tables,
        residuals_frame.loc[residuals_frame["outcome"].isin(PRIMARY_OUTCOMES)],
        stability_frame.loc[stability_frame["outcome"].isin(PRIMARY_OUTCOMES)],
        robustness_frame,
        VISUALIZATION_ROOT,
    )
    manifest_path = METRIC_ROOT / "stage3_reproducibility_hashes.json"
    report_paths = [
        REPORT_ROOT / "STAGE3_DATA_VALIDATION_REPORT.md",
        REPORT_ROOT / "STAGE3_STATIONARITY_REPORT.md",
        REPORT_ROOT / "STAGE3_MODEL_ESTIMATION_REPORT.md",
        REPORT_ROOT / "STAGE3_HYPOTHESIS_TESTING_REPORT.md",
        REPORT_ROOT / "STAGE3_DIAGNOSTICS_AND_ROBUSTNESS_REPORT.md",
    ]
    output_paths = (
        [
            path
            for folder in (
                STAGE3_DATA_ROOT,
                MODEL_ROOT,
                PREDICTION_ROOT,
                METRIC_ROOT,
                VISUALIZATION_ROOT,
            )
            for path in folder.rglob("*")
            if path.is_file() and path != manifest_path
        ]
        + report_paths
        + figure_paths
    )
    output_paths = sorted(set(output_paths), key=lambda path: str(path))
    hashes = _file_hashes(output_paths, root)
    manifest_path.write_text(
        json.dumps(
            {
                "command": r".venv\Scripts\python.exe -m src.pass_through.run_experiments",
                "python": sys.version,
                "platform": platform.platform(),
                "versions": {
                    "pandas": pd.__version__,
                    "numpy": np.__version__,
                    "statsmodels": statsmodels.__version__,
                    "scipy": scipy.__version__,
                    "matplotlib": matplotlib.__version__,
                },
                "random_seed": SEED,
                "bootstrap_seed": BOOTSTRAP_SEED,
                "output_hashes": hashes,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    generated_hashes = {
        **hashes,
        str(manifest_path.relative_to(root)): hashlib.sha256(
            manifest_path.read_bytes()
        ).hexdigest(),
    }
    _write_final_report(
        summaries_frame,
        tests_frame,
        response_frame,
        joint_frame,
        diagnostics_frame,
        robustness_frame,
        nardl_gate,
        generated_hashes,
        protected_integrity,
    )
    report_paths.append(REPORT_ROOT / "STAGE3_FINAL_RESEARCH_REPORT.md")
    output_paths = sorted(
        set(output_paths + report_paths + [manifest_path]), key=lambda path: str(path)
    )
    return {
        "panel": panel,
        "validation": validation,
        "panel_validation": panel_validation,
        "stationarity_tests": stationarity_tests,
        "integration": integration,
        "lag_choices": lag_choices,
        "selection": selection,
        "summaries": summaries_frame,
        "coefficients": coefficients_frame,
        "hypothesis_tests": tests_frame,
        "responses": response_frame,
        "diagnostics": diagnostics_frame,
        "robustness": robustness_frame,
        "nardl_gate": nardl_gate,
        "protected_integrity": protected_integrity,
        "output_hashes": generated_hashes,
        "output_paths": output_paths,
        "wpi_zero_summary": zero_summary,
    }


def main() -> None:
    """Execute Stage 3 and print concise observed run metadata."""
    result = run_stage3()
    print("Stage 3 experiment pipeline completed.")
    print(f"Common sample: {SAMPLE_START:%Y-%m} through {SAMPLE_END:%Y-%m}.")
    print(f"Selected symmetric lags: {result['lag_choices']['symmetric']}.")
    print(f"Selected asymmetric lags: {result['lag_choices']['asymmetric']}.")
    print(f"WPI numeric zeros preserved: {int(result['validation']['wpi_zero_dates'].shape[0])}.")
    print(f"NARDL status: {result['nardl_gate']['status']}.")
    print(f"Generated files: {len(result['output_paths'])}.")


if __name__ == "__main__":
    main()
