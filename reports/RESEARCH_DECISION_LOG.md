# POME EL Research Decision Log

This document is a template for recording significant research decisions made during the POME EL workflow. It is designed to capture rationale, evidence, and trade-offs without inventing completed research decisions.

## Research decision record template

| Field | Details |
| --- | --- |
| Decision ID | [Enter unique decision identifier] |
| Date | [YYYY-MM-DD] |
| Research stage | [Stage 1 / Stage 2 / Stage 3 / Stage 4 / Stage 5 / Cross-stage] |
| Decision description | [Describe the decision made and the context requiring it.] |
| Research question affected | [State the research question, hypothesis, or analysis objective affected.] |
| Alternatives considered | [List the options reviewed, compared, or rejected.] |
| Selection rationale | [Explain why this option was selected.] |
| Supporting evidence | [Provide relevant literature, technical notes, diagnostics, prior results, or reference materials.] |
| Statistical or methodological justification | [Describe the analytical basis, assumptions, or methodological rationale for the choice.] |
| Limitations | [Document known boundaries, risks, or caveats of the decision.] |
| Impact on subsequent stages | [Describe the downstream implications for later analyses, models, or reporting.] |
| Approval status | [Pending / Reviewed / Approved / Rejected / Deferred] |

## Blank example template

### Example: blank research decision template

| Field | Details |
| --- | --- |
| Decision ID | [RDEC-000] |
| Date | [YYYY-MM-DD] |
| Research stage | [Research stage or cross-stage] |
| Decision description | [Decision summary.] |
| Research question affected | [Research question or problem addressed.] |
| Alternatives considered | [Alternative A, Alternative B, Alternative C.] |
| Selection rationale | [Why the selected approach was preferred.] |
| Supporting evidence | [Evidence used to support the decision.] |
| Statistical or methodological justification | [Methodological basis and assumptions.] |
| Limitations | [Known constraints and risks.] |
| Impact on subsequent stages | [What changes this decision creates for later stages.] |
| Approval status | [Status] |

## Notes

- Keep the log aligned with the project’s research methodology and reproducibility standards.
- Do not record fabricated decisions or completed work not yet performed.
- Update the approval status when review, sign-off, or revision occurs.

## Open source and methodology decisions

The following are **questions awaiting an explicit research decision**, not completed decisions or approvals. The entries preserve uncertainty identified during the read-only source audit.

### RDEC-SOURCE-001: Exchange-rate source vintage and daily null interpretation

| Field | Details |
| --- | --- |
| Decision ID | RDEC-SOURCE-001 |
| Date | 2026-11-09 |
| Research stage | Stage 1 / Cross-stage |
| Decision description | Determine the attributable local source/vintage for both USD/INR files and the treatment policy, if any, for 552 daily numeric nulls. |
| Research question affected | Which USD/INR observations and publication vintages are eligible at each forecast origin? |
| Alternatives considered | Preserve source values and nulls pending provenance; use a documented archived source extract; adopt another documented availability policy after evidence review. No option is selected. |
| Selection rationale | Not applicable; source matching and calendar semantics have not been completed. |
| Supporting evidence | Federal Reserve H.10 `DEXINUS` defines daily noon buying rates; G.5 `EXINUS` defines monthly averages of available daily rates. Local file retrieval dates and full-value matches are absent. |
| Statistical or methodological justification | A point-in-time rule and a missing-day convention are prerequisites for leakage-safe evaluation; neither can be inferred solely from date coverage. |
| Limitations | Missing daily values may include non-publication/non-trading days; their cause is not yet resolved. |
| Impact on subsequent stages | Affects Stage 1 targets and any cross-stage exchange-rate input. |
| Approval status | Pending |

### RDEC-SOURCE-002: RBI repo observation convention

| Field | Details |
| --- | --- |
| Decision ID | RDEC-SOURCE-002 |
| Date | 2026-11-09 |
| Research stage | Cross-stage |
| Decision description | Verify whether the local monthly value is the policy repo rate in force at month-end and establish the source series/date-key convention. |
| Research question affected | What policy stance was observable for each monthly research period? |
| Alternatives considered | Month-end policy setting; monthly average or another published series. No option is selected. |
| Selection rationale | Not applicable; the month-end interpretation is an inference from the local step pattern, not a file specification. |
| Supporting evidence | RBI Statistics/DBIE are official entry points; the local CSV has only `period,value` and no exact series identifier or source metadata. |
| Statistical or methodological justification | Policy-rate level and a monthly average are different quantities and imply different timing. |
| Limitations | Exact RBI/DBIE series mapping and source vintage have not been established. |
| Impact on subsequent stages | Affects covariate timing in Stages 1, 3, and 4 and may affect persistence analysis. |
| Approval status | Pending |

### RDEC-SOURCE-003: CPI workbook provenance and continuity

| Field | Details |
| --- | --- |
| Decision ID | RDEC-SOURCE-003 |
| Date | 2026-11-09 |
| Research stage | Stages 2–5 / Cross-stage |
| Decision description | Decide whether and how to use the local CPI current/back workbooks after authenticating their sources and preserving the 2024-base general-index linkage limits. |
| Research question affected | Which CPI general-index values and published inflation rates represent a consistent available series? |
| Alternatives considered | Defer use until dated official extracts are matched; use only the directly source-verified portion; another evidence-supported choice. No option is selected. |
| Selection rationale | Not applicable; file-level provenance and vintages are not verified. |
| Supporting evidence | MoSPI documents 2024=100, HCES 2023–24 weights, 2013–2024 general-index back data, and direct linkage only at the general-index level. |
| Statistical or methodological justification | Index-linking does not establish detailed-component continuity or real-time release availability. Published inflation fields must not be silently replaced. |
| Limitations | Local workbook origin, values, download timestamps, and vintage are not authenticated; 12 published inflation entries in each workbook are blank. |
| Impact on subsequent stages | Affects Stage 2 target definition and CPI inputs to Stages 3–5. |
| Approval status | Pending |

### RDEC-SOURCE-004: NEER/REER source export and vintage

| Field | Details |
| --- | --- |
| Decision ID | RDEC-SOURCE-004 |
| Date | 2026-11-09 |
| Research stage | Stages 1 and 3 / Cross-stage |
| Decision description | Authenticate the local four-series table against a dated RBI export and establish which RBI method/base applies to the complete local history. |
| Research question affected | Should nominal and real effective exchange rates be used as measures or predictors, and with what interpretation? |
| Alternatives considered | Defer until a dated source match; use after validation; omit if a match cannot be established. No option is selected. |
| Selection rationale | Not applicable; local numeric values are not matched to a dated RBI export. |
| Supporting evidence | RBI's official 2021 Bulletin documents the 40-currency, 2015–16=100 trade/export-weighted methodology; local observations extend to 2026-09. |
| Statistical or methodological justification | RBI definitions and index direction are required to interpret appreciation/depreciation consistently; historical revisions and weights may matter. |
| Limitations | Exact local source, extraction date, recent observations, and later revision policy remain unknown. |
| Impact on subsequent stages | Affects interpretation and external-competitiveness measures in Stages 1 and 3. |
| Approval status | Pending |

### RDEC-SOURCE-005: WPI zero semantics and April 2026 vintage

| Field | Details |
| --- | --- |
| Decision ID | RDEC-SOURCE-005 |
| Date | 2026-11-09 |
| Research stage | Stage 5 / Cross-stage |
| Decision description | Obtain the publisher's numeric-zero convention and decide which WPI publication vintage is appropriate for any future analysis, including whether April 2026=167.6 is formally final. |
| Research question affected | Which WPI observations can be interpreted as valid category values at a given publication date? |
| Alternatives considered | Retain numeric zeros as published pending clarification; apply a documented OEA convention if obtained; preserve historical release snapshots for point-in-time use. No option is selected. |
| Selection rationale | Not applicable; zero semantics and formal final status remain unverified. |
| Supporting evidence | 505 zeros occur in six series. OEA's 14 May release reports April 2026=167.0 provisional; later official downloadable workbook and matching local file report 167.6. |
| Statistical or methodological justification | Numeric zeros cannot be reclassified as missing without source documentation; different publication values must be distinguished by vintage. |
| Limitations | Local retrieval date is unknown; no revised-April release or per-observation final-status marker was found. |
| Impact on subsequent stages | Affects Stage 5 WPI coverage and any CPI/WPI comparison or real-time exercise. |
| Approval status | Pending |

### RDEC-STAGE3-001: Proposed common-sample asymmetric pass-through design

| Field | Details |
| --- | --- |
| Decision ID | RDEC-STAGE3-001 |
| Date | 2026-11-10 |
| Research stage | Stage 3 |
| Decision description | Proposed—not yet approved—use of a parsimonious asymmetric distributed-lag model on consistently index-derived annual CPI/WPI inflation over the common January 2014–December 2024 sample; retain a symmetric nested benchmark and make NARDL conditional on integration/cointegration evidence. |
| Research question affected | Whether rupee depreciation and appreciation have different magnitude, timing, and persistence for CPI and WPI, and whether imported-cost conditions are associated with those differences. |
| Alternatives considered | Use published CPI inflation and a calculated WPI rate as if equivalent; extend through the CPI 2025 published-rate gap; make NARDL the default; use only a symmetric model; use index-derived annual rates for a common CPI/WPI period with a separate published-CPI sensitivity. |
| Selection rationale | The processed WPI file contains index levels but no published inflation field. CPI published inflation is missing in 2025 and is segmented. Using the same index-derived annual log-change definition on the shared 2014–2024 dates creates a more comparable outcome without fabricating publisher data. A direct asymmetric distributed-lag model tests the primary asymmetry question without assuming cointegration; NARDL remains conditional. |
| Supporting evidence | Read-only coverage audit of `data/processed/cpi_monthly_clean.csv`, `wpi_monthly_clean.csv`, `usd_inr_monthly_clean.csv`, `brent_monthly_clean.csv`, `repo_rate_clean.csv`, and `neer_reer_monthly_clean.csv`; 132 common monthly observations are available Jan 2014–Dec 2024. Prior CPI continuity and release-vintage audits document the 2025 published-rate gap and incomplete point-in-time provenance. |
| Statistical or methodological justification | Same-sample outcome definitions improve CPI/WPI coefficient comparability. The asymmetric DL tests signed-component restrictions directly. Standard ARDL bounds inference is prohibited if any included series is I(2); a long-run error-correction interpretation requires evidence of cointegration. |
| Limitations | This is a retrospective, non-causal proposal. CPI/WPI source vintages are incomplete; WPI detailed-series zero semantics remain undocumented; Brent provenance, repo date convention, and local NEER/REER export mapping require care. Annual index-derived inflation is not publisher-reported inflation. Effective sample size declines after dynamic lags. |
| Impact on subsequent stages | If approved, Stage 3 implementation may follow this protocol only. No Stage 3 estimation, Stage 4 work, data modification, or synthetic data is authorized by this log entry. |
| Approval status | Approved with limitations; implementation explicitly authorized by researcher on 2026-11-10 |

### RDEC-STAGE4-001: Early-warning classification design and implementation approval

| Field | Details |
| --- | --- |
| Decision ID | RDEC-STAGE4-001 |
| Date | 2026-11-10 |
| Research stage | Stage 4 |
| Decision description | Approve the constrained Stage 4 implementation of the design to classify published All India / Combined / CPI (General) inflation greater than 6% at an exact future target month \(t+h\), using lagged CPI-history, exchange-rate, and imported-cost indicators. |
| Research question affected | Can indicators available by a forecast origin provide early warning of elevated CPI inflation one, three, or six months ahead? |
| Alternatives considered | Predict current-month instead of future CPI; classify whether any event occurs within the next h months; substitute CPI index-derived inflation for published inflation; bridge the 2025 gap; change the 6% primary threshold; use all existing engineered columns without timing review; add synthetic observations. |
| Selection rationale | The future single-month target preserves a clear origin/target distinction. The >6% threshold is the policy tolerance-band upper edge and is retained as requested. The observed 2014-2024 published CPI segment provides a limited but usable retrospective sample; conservative lagged features reduce reference-month leakage. Existing feature and vintage limitations are explicitly gated rather than assumed away. |
| Supporting evidence | Read-only profile of `data/processed/cpi_monthly_clean.csv`, all relevant `data/processed/features/` files, Stage 1/2 prediction archives, `data/processed/stage3/stage3_analysis_panel.csv`, Stage 2 and Stage 3 independent audits, and source inspection of `src/features/feature_engineering.py`. Eligible sample counts are 119/117/114 with 29 elevated labels for each horizon; the proposed common 18-target test has 3 elevated months in 2 episodes. |
| Statistical or methodological justification | Use chronological expanding validation, target-availability purging, training-only preprocessing, common comparisons, a locked final test, and class-sensitive metrics. Regularized logistic regression is the primary interpretable baseline; constrained Random Forest/XGBoost are secondary benchmarks. Synthetic augmentation is not justified by this episode count. |
| Limitations | Historical release timestamps/vintages are absent; the final test has only three elevated outcomes in two episodes; performance and calibration estimates are unstable; 3-/6-month results are exploratory; Brent-INR is only an approximate proxy; repo and NEER/REER provenance/date semantics are unresolved. Stage 4 avoids the questionable pre-engineered Brent-volatility and repo-change fields without changing upstream code. This design makes no causal claims. |
| Impact on subsequent stages | Stage 4 implementation and retrospective evaluation were completed under the explicit implementation request and are classified VERIFIED WITH LIMITATIONS. The documented timing, vintage, sample-size, model-performance, and proxy limitations remain binding. Stage 5 is not authorized. |
| Approval status | Stage 4 implementation approved and completed with limitations; Stage 5 not authorized |

### RDEC-STAGE4-AUDIT-001: Independent Stage 4 audit disposition

| Field | Details |
| --- | --- |
| Decision ID | RDEC-STAGE4-AUDIT-001 |
| Date | 2026-11-10 |
| Research stage | Stage 4 / Cross-stage |
| Decision description | Record the independent audit disposition for the completed Stage 4 early-warning experiment without changing its code, predictions, metrics, or model artifacts. |
| Research question affected | Do exchange-rate and imported-cost indicators provide verified early warnings of elevated published CPI inflation at one, three, or six months ahead? |
| Alternatives considered | Treat the saved false-alarm-run statistic as a computational defect; accept it under the approved unmatched-alert-run definition while requiring pointwise false-positive counts alongside it; replace it with a different event-matching rule. |
| Selection rationale | Independent reconstruction verified the target, leakage boundaries, chronological purging, validation-only selection, model feature membership, and all pointwise test metrics. The saved episode rule matches the approved protocol's count of contiguous alert runs not matched to an actual episode. It is coarse: the six-month model has 15 false-positive months but zero unmatched alert runs because its single alert run overlaps actual elevated months. |
| Supporting evidence | `reports/experiments/STAGE4_INDEPENDENT_RESEARCH_AUDIT.md`; `reports/experiments/STAGE4_AUDIT_METRIC_RECONCILIATION.csv`; `reports/experiments/STAGE4_FEATURE_LEAKAGE_AUDIT.csv`; saved Stage 4 prediction and metric archives. |
| Statistical or methodological justification | A run-level unmatched-alarm count and a pointwise false-positive-month count answer different questions. The approved protocol's event-run definition is implemented; report it explicitly and pair it with the pointwise confusion counts to avoid interpreting a long mixed alert run as a low alert burden. |
| Limitations | This disposition concerns the complete reported Stage 4 evaluation, not the independently verified pointwise scores. Only three elevated test months in two episodes limit all performance conclusions. Signed FX returns are not separately decomposed into depreciation and appreciation contributions. |
| Impact on subsequent stages | The Stage 4 experiment is classified VERIFIED WITH LIMITATIONS. Historical release/vintage, small test sample, and coarse event-run interpretation remain limitations. No Stage 5 work is authorized or started. Existing Stage 4 results remain unchanged by the audit. |
| Approval status | Independent audit completed as VERIFIED WITH LIMITATIONS; researcher approval is still required before Stage 5 or any changes to Stage 4 results. |
