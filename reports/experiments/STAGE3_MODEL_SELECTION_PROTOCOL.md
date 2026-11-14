# Stage 3 Model Selection and Inference Protocol

**Status:** Proposed protocol; not executed. No Stage 3 models, tests, or results were produced.

## 1. Pre-estimation freeze

Before examining coefficient p-values or fitted responses, record researcher approval of:

1. Primary common sample: January 2014–December 2024.
2. Primary dependent variable: CPI/WPI index-derived annual log inflation, explicitly distinct
   from publisher-reported inflation.
3. Primary exchange-rate change: monthly USD/INR log change, with positive depreciation and
   negative appreciation.
4. Primary outcome(s): CPI General and WPI All Commodities; Fuel & Power and Manufactured
   Products are secondary.
5. Primary asymmetric distributed-lag equation, control stages, maximum lags, deterministic
   terms, covariance estimator, asymmetry tests, and multiplicity policy.
6. Whether source mapping checks for CPI/WPI hierarchy and Brent extraction are acceptable for a
   retrospective exercise.

Maintain a dated specification record. Do not use the test outcomes to revise the primary
hypotheses, lag limits, transformations, or sample endpoints.

## 2. Sample and variable checks

- Validate one unique observation per month for every selected source series and report the
  exact common dates, effective observations, missingness, zeros, and exclusions.
- Do not interpolate CPI published inflation over 2025 or bridge the 2026 segment to 2024.
- Do not silently substitute index-derived CPI inflation for the published CPI field.
- Confirm WPI `comm_name`/`comm_code` mappings. Preserve all numeric zero values. If a candidate
  series contains zero, do not take its logarithm or recode it without publisher evidence.
- Calculate \(\Delta e_t=100[\ln(E_t)-\ln(E_{t-1})]\); check positive FX levels and month
  spacing. Define positive and negative components using the stated sign convention.
- Align annual index-derived inflation at month \(t\) using \(P_{t-12}\); do not use future
  values. Record any lag-related edge loss.
- Keep the outcome data on their common Jan 2014–Dec 2024 calendar for the headline CPI/WPI
  contrast.

## 3. Integration and model eligibility gate

For the primary rate-based asymmetric distributed-lag model, inspect plots and test whether the
outcome and change regressors are compatible with a stationary dynamic regression. Use
complementary ADF/PP and KPSS tests with explicitly reported deterministic components, lag
selection, sample, and structural-break caveats. Use break-aware tests as sensitivity, not as
automatic evidence of a particular economic break.

Do not treat any single unit-root-test result as conclusive. If the primary variables appear
nonstationary in levels, do not run a levels regression without an appropriate cointegration
argument.

NARDL is eligible only if:

1. Every variable included in the bounds equation is at most I(1); explicitly screen for I(2).
2. Lag order and deterministic terms are declared before bounds inference.
3. A long-run relationship is tested and supported using a defensible bounds procedure and
   finite-sample inference.
4. Diagnostics and stability are adequate for an error-correction interpretation.

An I(2) variable invalidates standard ARDL bounds testing. If no cointegration is supported,
report no long-run NARDL coefficient or error-correction claim; retain the stationary
inflation-rate/change specification.

## 4. Primary lag and control selection

Primary model family: asymmetric distributed-lag autoregression of index-derived annual
inflation. Use a deliberately small candidate grid:

- Outcome autoregressive lags \(p\): 1–3, with maximum 6 only if information criteria and
  residual diagnostics justify the added parameters.
- Positive/negative FX lag horizon \(q\): include same-month and lags through a maximum of 3,
  with maximum 6 as the pre-specified slower-pass-through sensitivity.
- Use BIC as the primary information criterion and AIC as a sensitivity check. Apply the same
  candidate rule to CPI and WPI; report if a common lag specification is not selected.
- Require sufficient residual degrees of freedom and report parameter count/effective N for
  every candidate. If the selected model is too parameter intensive for the sample, reduce the
  grid by the pre-registered rule rather than choosing a model by significance.
- Compare symmetric and asymmetric equations on the same observations and dynamic terms.
- Baseline contains no large control vector. Add lagged Brent USD change as the first separate
  imported-cost extension after provenance review.
- Estimate Brent-INR proxy in place of Brent USD in an alternative, not together with the
  exchange-rate decomposition and Brent USD. Repo and one NEER/REER measure are separate
  optional robustness models after source/date convention confirmation.

No machine-learning tuning, random cross-validation, or Stage 1/2 retraining is part of Stage 3.

## 5. Hypothesis tests and uncertainty

| Test | Restriction / inference | Reporting requirement |
|---|---|---|
| Short-run asymmetry | Joint Wald \(H_0:\beta^+_j=\beta^-_j\) across selected distributed lags | HAC covariance; coefficient vector, test statistic, df, p-value, joint confidence/response intervals |
| Dynamic timing and persistence | Contrasts of depreciation and equal-sized appreciation response paths through months 1, 3, 6 | Dynamic multipliers; delta-method and moving-block-bootstrap intervals; do not select horizons after viewing significance |
| CPI versus WPI | Equality of positive/negative FX response vectors in same-sample stacked or paired system | Outcome-by-FX interactions; time-clustered/HAC or paired block bootstrap |
| Imported-cost conditioning | Joint zero restriction on pre-specified FX × Brent interactions | Keep interaction count small; report uncertainty and model family |
| NARDL short-run | Wald tests on positive/negative differenced partial-sum coefficients | Only after model eligibility gate |
| NARDL long-run | \(H_0:\theta^+=\theta^-\) for signed partial sums | Only after I(2) exclusion and evidence of cointegration |

Use Newey–West/HAC errors with a lag length tied to the selected dynamic horizon and a
moving-block bootstrap as a sensitivity. Choose and document a block-length rule before
inference. For multiple secondary WPI outcomes or interaction families, report raw and adjusted
p-values (for example Holm) and emphasize effect sizes and confidence intervals.

Do not interpret p-values as proof of pass-through. A non-significant test is inconclusive, not
evidence that effects are exactly zero or symmetric.

## 6. Diagnostic test matrix

| Diagnostic | Purpose | Protocol / action if concern appears |
|---|---|---|
| Residual serial correlation | Check dynamic misspecification | Breusch–Godfrey/LM and residual ACF/Ljung–Box; extend or revise lags only under the frozen rule |
| Heteroskedasticity | Assess nonconstant variance | Breusch–Pagan/White; retain HAC inference and disclose |
| Functional form | Detect omitted nonlinearities | RESET plus residual/fitted plots; treat as diagnostic, not automatic license for extensive search |
| Residual distribution | Identify extreme-tail/non-normal residual patterns | Q-Q/histogram and an appropriate test; use robust/bootstrap uncertainty, not normality as a binary validity gate |
| Stability | Detect coefficient instability | Recursive estimates, CUSUM/CUSUMSQ or equivalent; report sample and power limitations |
| Structural breaks | Assess sensitivity to regime changes | Pre-specified break dates plus a restrained unknown-break sensitivity; account for search/multiplicity |
| Collinearity | Check separated FX terms and controls | Correlation/condition indices/VIF; replace Brent with Brent-INR, never mechanically stack them |
| Influence/outliers | Assess concentration in extreme depreciation episodes | Studentized residual/leverage and leave-episode-out sensitivity using a stated threshold |
| WPI group validity | Protect against zero/log problems | Confirm selected series mapping; check positive index values and all 132 common months before log change |
| CPI/WPI sample comparability | Prevent calendar composition from driving difference | Same dates and model terms; report date-by-date common N and paired contrasts |

No diagnostic outcome is assumed in this blueprint.

## 7. Robustness matrix

| Sensitivity | Essential / optional | Comparison rule |
|---|---|---|
| Published CPI inflation vs index-derived CPI | Essential | Separate outcomes and labels; published series only Jan 2014–Dec 2024 for continuous segment |
| Simple YoY percent change vs annual log change for CPI/WPI | Essential | Same index levels, dates, lags, model, and inference |
| Simple FX percentage change vs log change | Essential | Same sample, sign split, and lag-selection protocol |
| Lag maximum 3 vs 6; BIC vs AIC | Essential | Freeze candidate grids; report effective N and parameter counts |
| Same-month FX term vs lag-only terms | Essential | Explicitly distinguish contemporaneous association from delayed response |
| Headline WPI vs Fuel & Power / Manufactured Products | Essential secondary | Same dates; mark secondary inference and adjust multiplicity |
| No imported-cost control vs Brent USD changes | Essential extension | Verify source definition; compare paired common sample |
| Brent USD vs Brent-INR proxy | Essential alternative | Separate specifications; no simultaneous inclusion |
| Repo and one NEER/REER control | Optional | Only after exact source/date convention and vintage review |
| Estimation subperiod / structural-break sensitivity | Essential | Pre-specify dates or test; do not search for a window yielding significance |
| Extreme depreciation episode inclusion/exclusion | Essential | Threshold and dates stated in advance; preserve all data, fit only a clearly defined subset |
| NARDL partial sums and bounds model | Conditional | Run only if I(2) excluded, cointegration tested and supported |
| Longer CPI index-linked period after 2024 | Optional | Separate index-derived sensitivity; never assert published inflation continuity |

## 8. Expected outputs (planned, not generated)

Expected tables:

1. Variable definitions, units, sample dates, missingness, and transformation provenance.
2. Descriptive statistics and pairwise correlations for the approved sample.
3. Integration-test results with deterministic terms and break sensitivities.
4. Lag-selection scores, parameter counts, and effective observations.
5. Symmetric/asymmetric primary results with HAC and bootstrap uncertainty.
6. Short-run asymmetry tests and cumulative dynamic response contrasts.
7. CPI/WPI and WPI-group response contrasts.
8. Brent and alternative Brent-INR extensions, kept as separate models.
9. Residual, stability, influence, and robustness summaries.

Expected figures:

- FX depreciation and appreciation series and partial sums.
- Index-derived CPI/WPI inflation with FX movements.
- Positive/negative lag coefficient paths.
- Cumulative response paths with confidence bands.
- CPI/WPI coefficient contrasts.
- Stability, residual, and influence diagnostics.

Create these only from actual approved Stage 3 estimates. No fabricated or illustrative result
plots are authorized.

## 9. Interpretation framework and stop rules

1. Establish data and source conventions before interpreting coefficients.
2. Report the symmetric benchmark and the asymmetric restriction test together.
3. Describe sign, magnitude, timing, persistence, uncertainty, sample, and controls.
4. Interpret CPI/WPI differences in light of their basket, upstream/downstream composition, and
   common-sample design.
5. Describe Brent interactions as conditional association, not causation.
6. If unit-root/cointegration conditions fail, stop the NARDL branch and report the valid
   change/rate model only.
7. If source mapping, WPI group hierarchy, or treatment of selected zeros cannot be established,
   omit the affected optional series and record the reason; do not alter source data.
8. If diagnostics reveal severe misspecification or instability, classify the evidence as
   inconclusive and revise only after researcher review.

The design is **READY WITH LIMITATIONS** for a retrospective associational study after researcher
approval. It is not ready for a real-time early-warning claim or causal effect claim.
