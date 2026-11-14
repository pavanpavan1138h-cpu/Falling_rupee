# POME EL Issue Log

This document is a template for recording project and research issues encountered during the POME EL workflow. It is intentionally structured for traceability, investigation, and verification without inventing real project issues.

## Supported issue categories

- Software and technical errors
- Data quality and availability
- Methodological limitations
- Model performance
- Synthetic data quality
- Visualization and dashboard issues

## Issue record template

| Field | Details |
| --- | --- |
| Issue ID | [Enter unique issue identifier] |
| Date identified | [YYYY-MM-DD] |
| Research stage | [Stage 1 / Stage 2 / Stage 3 / Stage 4 / Stage 5 / Cross-stage] |
| Issue category | [Select one supported category] |
| Problem description | [Describe the issue clearly and precisely.] |
| Expected behaviour | [What should happen under the intended workflow or research design?] |
| Actual behaviour | [What happened instead, including observed symptoms or outputs.] |
| Root cause | [Likely causal explanation or suspected failure mode.] |
| Supporting evidence | [Logs, output excerpts, screenshots, notes, references, code locations, or diagnostic findings.] |
| Investigation performed | [Describe the analysis, code review, checks, reproductions, or validation steps performed.] |
| Solutions attempted | [Detail any mitigation steps, workarounds, or tests applied.] |
| Final resolution | [State the final outcome, whether resolved, deferred, or escalated.] |
| Research impact | [Describe the impact on methodology, outputs, interpretation, or downstream research decisions.] |
| Current status | [Open / In progress / Resolved / Deferred / Blocked] |
| Verification details | [List the validation performed, evidence reviewed, and the confirmation status.] |

## Blank example template

### Example: blank issue template

| Field | Details |
| --- | --- |
| Issue ID | [ISSUE-000] |
| Date identified | [YYYY-MM-DD] |
| Research stage | [Research stage or cross-stage] |
| Issue category | [Category] |
| Problem description | [Brief description of the problem.] |
| Expected behaviour | [Expected result.] |
| Actual behaviour | [Observed result.] |
| Root cause | [Hypothesized root cause.] |
| Supporting evidence | [Evidence, logs, code references, screenshots, or notes.] |
| Investigation performed | [Investigation steps taken.] |
| Solutions attempted | [Mitigation or experiment attempts.] |
| Final resolution | [Final outcome.] |
| Research impact | [Impact on analysis, risk, or findings.] |
| Current status | [Status] |
| Verification details | [Verification performed and result.] |

## Notes

- Use this log to record evidence-based issues and resolution trails.
- Do not add fabricated issues or speculative findings.
- Update the status as investigations or resolutions progress.

## Stage 3 design issues identified

These are evidence-based constraints identified during the Stage 3 read-only feasibility audit.
No data were changed, and no Stage 3 model was estimated.

### STAGE3-DATA-001: CPI published-inflation discontinuity

| Field | Details |
| --- | --- |
| Issue ID | STAGE3-DATA-001 |
| Date identified | 2026-11-10 |
| Research stage | Stage 3 |
| Issue category | Data quality and availability |
| Problem description | The processed CPI published inflation field has no observations for calendar 2025, separating the 2014–2024 segment from the nine published observations in 2026. |
| Expected behaviour | CPI published inflation observations remain publisher-sourced and are not filled or joined over a gap. |
| Actual behaviour | The file contains 132 consecutive published observations in Jan 2014–Dec 2024, 12 missing months in 2025, and a separate Jan–Sep 2026 segment of nine observations. |
| Root cause | The project’s prior CPI continuity audit attributes the boundary to separate 2024-base back/current series coverage and does not establish a published-inflation bridging rule. |
| Supporting evidence | `data/processed/cpi_monthly_clean.csv`; `reports/data_audit/CPI_CONTINUITY_AND_LINKAGE_AUDIT.md`; `reports/experiments/CPI_DATA_AND_FEATURE_AVAILABILITY.md`. |
| Investigation performed | Read-only inspection of dates, published-inflation completeness, and the prior CPI linkage audit. |
| Solutions attempted | None. The design excludes gap filling and treats index-derived inflation as a separately named measure. |
| Final resolution | Unresolved publisher/vintage issue; proposed common-sample design uses index-derived annual inflation for CPI/WPI comparison and a separately labelled published-CPI sensitivity. |
| Research impact | Limits published-CPI analysis to a continuous segment and prevents a falsely continuous official inflation series. |
| Current status | Open |
| Verification details | Confirmed 132 values from Jan 2014–Dec 2024, 12 blanks in 2025, and nine values Jan–Sep 2026; no data modified. |

### STAGE3-DATA-002: WPI detailed-series zero semantics

| Field | Details |
| --- | --- |
| Issue ID | STAGE3-DATA-002 |
| Date identified | 2026-11-10 |
| Research stage | Stage 3 |
| Issue category | Data quality and availability |
| Problem description | The WPI long table contains 505 numeric zero values across six detailed commodity series, and the source convention for those zeros remains undocumented. |
| Expected behaviour | A value is not recoded as missing or changed without publisher documentation; log transforms are used only for positive values. |
| Actual behaviour | Cauliflower, Grapes, Litchi, Mango, Orange, and Peas (Green) contain the zeros. All Commodities, II FUEL & POWER, and III MANUFACTURED PRODUCTS are positive and complete in the observed common sample. |
| Root cause | The processed source includes numeric zeros but does not document their meaning. |
| Supporting evidence | `data/processed/wpi_monthly_clean.csv`; `reports/data_audit/DATA_ISSUES_REGISTER.md` (DATA-003). |
| Investigation performed | Read-only grouping by WPI series, date coverage, missing values, zeros, and common-sample positivity. |
| Solutions attempted | None. The blueprint restricts proposed WPI outcomes to verified positive aggregates and preserves detailed zeros unchanged. |
| Final resolution | Zero semantics remain unresolved; detailed affected series are not proposed as outcomes until clarified. |
| Research impact | Limits disaggregated WPI analysis and prohibits ungrounded zero replacement or log transformation. |
| Current status | Open |
| Verification details | 505 zeros in six series; selected aggregate and major-group WPI series each have 132 positive common-sample values. No file modified. |

### STAGE3-METHOD-001: Incomplete vintages and contemporaneous timing

| Field | Details |
| --- | --- |
| Issue ID | STAGE3-METHOD-001 |
| Date identified | 2026-11-10 |
| Research stage | Stage 3 / Cross-stage |
| Issue category | Methodological limitations |
| Problem description | Local source files do not consistently establish extraction vintage or historical release availability for CPI, USD/INR, Brent, repo, and NEER/REER; WPI observations can be revised. |
| Expected behaviour | Any real-time or causal interpretation has documented point-in-time inputs and a defensible identification strategy. |
| Actual behaviour | Monthly calendars are complete over the proposed common sample, but the prior release/vintage audit does not establish real-time availability; repo date convention and NEER/REER export mapping remain open. |
| Root cause | Source retrieval dates, observation vintages, and consistent release metadata are absent from local files. |
| Supporting evidence | `reports/data_audit/RELEASE_TIMING_AND_VINTAGE_AUDIT.md`; `reports/data_audit/DATA_ISSUES_REGISTER.md` (DATA-002, DATA-004, DATA-006, DATA-009, DATA-010). |
| Investigation performed | Reviewed prior provenance/vintage audits and inspected date coverage in all candidate processed series. |
| Solutions attempted | None. The proposed design is explicitly retrospective and associational; uncertain controls are gated on source verification. |
| Final resolution | Not resolved. A real-time design and causal claims remain out of scope until separate evidence and identification decisions are approved. |
| Research impact | Prevents labeling this Stage 3 design as a genuine real-time backtest or causal pass-through estimate. |
| Current status | Open |
| Verification details | Confirmed as a documented cross-stage limitation; no new source data downloaded and no source file changed. |

## Stage 4 early-warning design issues

The following are evidence-based feasibility and feature-eligibility issues identified by
read-only inspection. No code or data was changed to address them.

### STAGE4-FEATURE-001: Existing engineered predictors require correction or exclusion

| Field | Details |
| --- | --- |
| Issue ID | STAGE4-FEATURE-001 |
| Date identified | 2026-11-10 |
| Research stage | Stage 4 |
| Issue category | Software and technical errors |
| Problem description | Existing feature-engineering outputs include predictor semantics that are not suitable for unreviewed classifier use: Brent rolling volatility applies an extra factor of 100 to already percentage-scaled log returns, leaving units undocumented; the generic log-change helper removes nonpositive/missing values before differencing and can bridge a gap; and the first missing repo-rate difference can be marked as a change by `.ne(0)`. |
| Expected behaviour | Volatility has documented units and is calculated consistently from consecutive monthly returns; missing months remain missing rather than being skipped; an unavailable repo change remains missing and is not classified as a policy change. |
| Actual behaviour | `src/features/feature_engineering.py` applies the additional volatility multiplier, differences the positive-only subsequence, and converts `.ne(0)` to an integer without first preserving missing values. |
| Root cause | Feature functions do not fully preserve return units and missing-month semantics at series boundaries or gaps. |
| Supporting evidence | Read-only source inspection of `src/features/feature_engineering.py`; generated `brent_features.csv` and `repo_rate_features.csv` schemas; common 2014-2024 Brent/FX/repo values themselves are complete, so the gap-crossing behavior is a prospective risk rather than an observed common-sample gap. |
| Investigation performed | Traced formulas from source series through engineered columns and checked common-period feature missingness and prior Stage 3/Stage 4 feasibility reports. |
| Solutions attempted | Stage 4 uses a separate calendar-safe feature builder over unchanged source levels and excludes the questionable pre-engineered volatility and repo-change columns. The shared feature code was not edited. |
| Final resolution | Contained for the Stage 4 primary model: lagged returns and rolling summaries are computed from aligned source levels; missing months are rejected rather than bridged. The upstream generic feature issue remains unresolved for other consumers. |
| Research impact | The suspect generated fields do not enter Stage 4 predictors; the upstream feature-engineering issue remains relevant to any future consumer of those fields. |
| Current status | Contained for Stage 4; upstream feature issue remains open |
| Verification details | Stage 4 feature builder validates unique monthly keys, rejects missing months, computes consecutive-month log changes, and asserts all feature dates precede the origin. Pipeline and protected-file checks are recorded in the Stage 4 reports. |

### STAGE4-AUDIT-001: False-alarm episode metric needs explicit interpretation

| Field | Details |
| --- | --- |
| Issue ID | STAGE4-AUDIT-001 |
| Date identified | 2026-11-10 |
| Research stage | Stage 4 |
| Issue category | Methodological limitations |
| Problem description | The saved `false_alarm_episodes` is a coarse unmatched-alert-run metric; it can show zero when a long alert run overlaps an actual elevated target even though many individual months in the run are false positives. |
| Expected behaviour | State the approved unmatched-alert-run definition beside the measure and report pointwise false-positive months separately. If a different event-matching rule is wanted, prespecify it before evaluation. |
| Actual behaviour | The selected six-month model alerts in all 18 test months and has 15 false-positive months, but reports zero unmatched alert runs because its single alert run overlaps actual elevated months. The selected three-month model has 14 false-positive months and one unmatched alert run, while there are two contiguous runs in its pointwise false-positive mask. |
| Root cause | The metric defines an unmatched alert run as a contiguous predicted-alert run with no actual positive month anywhere in that run. It does not split mixed runs into true-event and false-positive portions. This matches the approved protocol's unmatched-run rule but answers a narrower question than false-positive-month counts. |
| Supporting evidence | `reports/experiments/STAGE4_INDEPENDENT_RESEARCH_AUDIT.md`; `reports/experiments/STAGE4_AUDIT_METRIC_RECONCILIATION.csv`; `artifacts/predictions/early_warning/stage4_early_warning_predictions.csv`; `artifacts/metrics/early_warning/stage4_test_metrics.csv`. |
| Investigation performed | Independently reconstructed actual elevated runs, alert runs, pointwise false-positive masks, and all 48 final-test metric groups from the saved labels, probabilities, thresholds, and dates. |
| Solutions attempted | None. The existing Stage 4 code and results were not changed. |
| Final resolution | The code follows the approved unmatched-alert-run definition. Add that definition wherever the count is reported and interpret it alongside false-positive-month counts. A different event-matching definition requires a separate decision and approval before any recomputation. |
| Research impact | No discrepancy was found in the calculation. The measure must not be interpreted alone as the total burden of false alarms; pointwise false-positive months remain the direct alert-burden count. |
| Current status | Open for reporting clarification |
| Verification details | Independent reproduction matches the saved code-defined value exactly for all groups. The h=6 value is zero unmatched runs alongside 15 false-positive months; this is consistent with the approved run-level rule. |

### STAGE4-AUDIT-002: Direction-specific FX components are not modeled separately

| Field | Details |
| --- | --- |
| Issue ID | STAGE4-AUDIT-002 |
| Date identified | 2026-11-10 |
| Research stage | Stage 4 |
| Issue category | Methodological limitations |
| Problem description | The approved feature matrix proposes separate positive depreciation and negative appreciation components, but the implemented classifier uses signed net FX returns and signed cumulative net returns only. |
| Expected behaviour | If direction-specific associations are intended, encode depreciation and appreciation contributions separately with a prespecified sign convention, or explicitly limit claims to signed net exchange-rate movement. |
| Actual behaviour | `FEATURE_COLUMNS` includes `fx_log_return_1m` and `fx_cumulative_return_3m`; separate `max(r, 0)` and `min(r, 0)` feature columns are absent. |
| Root cause | The implementation represents FX movement with signed returns rather than the separate directional components proposed in the feature matrix. |
| Supporting evidence | `reports/experiments/STAGE4_FEATURE_AND_TARGET_MATRIX.md`; `src/risk_classification/features.py`; `reports/experiments/STAGE4_FEATURE_LEAKAGE_AUDIT.csv`. |
| Investigation performed | Compared the approved feature matrix with every actual feature list and independently reconstructed the saved feature values from the processed USD/INR source. |
| Solutions attempted | None. Signed returns correctly encode direction; this audit does not change the model or add features. |
| Final resolution | Unresolved design deviation. Decide whether separate direction-specific effects are required before any later use; no feature modification is authorized by this audit. |
| Research impact | A linear logistic model's signed-return term does not separately estimate depreciation and appreciation magnitudes; tree models may split signed values but do not replace a prespecified directional decomposition. No causal or asymmetric effect claim is supported. |
| Current status | Open |
| Verification details | Independent source-to-feature reconstruction matched all implemented feature values exactly; the separate directional terms were not present in the feature matrix or model lists. |

### STAGE4-FEAS-001: Sparse and clustered elevated-inflation episodes

| Field | Details |
| --- | --- |
| Issue ID | STAGE4-FEAS-001 |
| Date identified | 2026-11-10 |
| Research stage | Stage 4 |
| Issue category | Methodological limitations |
| Problem description | The >6% target yields only 29 eligible elevated months per horizon from Jan 2015 onward; a common 18-month final test window contains 3 elevated months in 2 episodes. |
| Expected behaviour | Model discrimination, calibration, and episode detection should be evaluated on enough independent elevated episodes to support the scope of the resulting claim. |
| Actual behaviour | The test has 18 monthly targets per horizon, 3 elevated and 15 non-elevated, with adjacent CPI year-on-year labels and only two elevated runs. Validation-selected test models were weak: at 1 month the selected classifier detected 0/3 elevated months (4 false-positive months); at 3 months it detected 2/3 (14 false-positive months); at 6 months it detected 3/3 (15 false-positive months). |
| Root cause | The continuous published-CPI segment is limited to 2014-2024 and elevated outcomes are clustered in time. |
| Supporting evidence | Read-only counts from `data/processed/cpi_monthly_clean.csv`: 37/132 elevated in the full continuous segment; 29/119, 29/117, and 29/114 in eligible 1-, 3-, and 6-month target samples; 3/18 in Jul 2023-Dec 2024. |
| Investigation performed | Recomputed target counts under the strict >6% rule, evaluated horizon-specific eligible target windows, and counted the proposed chronological test episodes. |
| Solutions attempted | None. The proposed design limits claims, makes 1-month primary, and keeps 3-/6-month results exploratory. |
| Final resolution | Limitation confirmed after execution. Keep 1 month primary and 3-/6-month results exploratory; obtain a longer point-in-time CPI history and additional independent elevated episodes before claiming operational warning performance. |
| Research impact | Weak out-of-sample results, numerous false alarms, and only two test episodes preclude reliable model-ranking, calibration, or operational-warning claims. Predictive performance does not establish a causal economic effect. |
| Current status | Open |
| Verification details | Counts were recalculated from observed published `inflation_value`. Two complete Stage 4 runs exited 0 and reproduced all 28 generated data/model/prediction/metric/visualization artifact hashes (aggregate manifest SHA-256 `bf20da9f8619b252b734f790c96f1b534668e531e5a6fc5c6ff38edca9df5163`). `pytest -q` (64 passed), Ruff, and `pip check` exited 0. All 220 pre-implementation protected files and the pipeline's 292-file protected-file guard remained unchanged. |
