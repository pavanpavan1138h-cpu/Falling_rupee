# Stage 4 Independent Research Audit

**Audit date:** 2026-11-10  
**Final classification: VERIFIED WITH LIMITATIONS.**  
**Stage 5:** Not started; no Stage 5 work is authorized by this audit.

## 1. Executive assessment

An independent reconstruction confirms the published CPI target, all forecast-origin/target
dates, the model feature values, chronological purging, validation-only model selection, and
the saved pointwise test metrics. No future realized CPI, USD/INR, or Brent observation is
present in the audited predictor matrix. The 2025 CPI gap is not bridged. All 48
configuration/model/horizon test groups reconcile to the stored metric values within the
precision of the CSV files, and no stored alert class differs from the saved probability and
threshold.

The reported `false_alarm_episodes` is a coarse run-level measure: it counts a contiguous
alert run as false only when the run overlaps no actual elevated target month. This follows
the approved protocol's rule to count an alarm run not matched to an episode. It is not the
same as counting contiguous pointwise false-positive stretches. Thus h=6 can have zero
unmatched alert runs and 15 false-positive months. This is an interpretation/reporting
limitation, not a discrepancy in the saved calculation or a reason to reject the
pointwise classification metrics. The audit recommends stating this definition wherever the
episode count is presented and keeping it alongside false-positive-month counts.

The saved data, code, predictions, metrics, and models were not modified. Stage 5 remains
unauthorized and was not started.

## 2. Scope and protection

Inspected the Stage 4 design, feature/target matrix, feasibility audit, validation protocol,
data/feature report, model results, evaluation/robustness report, and final report; the Stage 2
independent audit; the Stage 3 final report; issue and decision logs; all Python modules under
`src/risk_classification/`; Stage 4 tests; `pyproject.toml`; `config/settings.py`; generated
target/feature data, prediction archive, metric tables, model specifications, run metadata,
and diagnostic images.

Fresh pre-audit SHA-256 hashes were captured for 276 existing project files. All remained
unchanged through the audit before the two permitted governance-log updates. The historical
220-file pre-implementation manifest also matches all 220 current files. The pipeline's
292-file protected-file map matches all current files. No raw/processed source data, Stage 1,
Stage 2, Stage 3, or Stage 4 implementation/results were changed.

The Stage 4 pipeline's 32-entry two-run manifests are identical to each other. Their 28
generated data/model/prediction/metric/visualization entries still match current files.
Two report entries (`STAGE4_EVALUATION_AND_ROBUSTNESS_REPORT.md` and
`STAGE4_FINAL_RESEARCH_REPORT.md`) were edited after those pipeline runs to record their
results, so their current hashes naturally differ from the historical run manifests. This
does not affect the repeatability comparison of the 28 experiment artifacts.

## 3. Target construction audit

The target was independently rebuilt from `cpi_monthly_clean.csv`, selecting
All India / Combined / CPI (General) and the published `inflation_value`. There are no
duplicate valid target months. The longest continuous segment is January 2014–December 2024,
with 132 nonmissing observations; a separate January–September 2026 segment has nine
observations. The 2025 gap is not interpolated or concatenated.

| Sample | N | Elevated \(>6\%\) | Non-elevated \(\le6\%\) | Result |
|---|---:|---:|---:|---|
| Continuous published segment, Jan 2014–Dec 2024 | 132 | 37 | 95 | Matches source |
| h=1 eligible targets, Feb 2015–Dec 2024 | 119 | 29 | 90 | Reconstructed |
| h=3 eligible targets, Apr 2015–Dec 2024 | 117 | 29 | 88 | Reconstructed |
| h=6 eligible targets, Jul 2015–Dec 2024 | 114 | 29 | 85 | Reconstructed |
| Final test, Jul 2023–Dec 2024, each horizon | 18 | 3 | 15 | Reconstructed |

The boundary is coded strictly as `target_inflation > 6.0`; exactly 6.0, if present, would be
negative. No value is exactly 6.0 in the continuous 132-month segment. Each target date equals
forecast origin plus its horizon, and no target label is imputed. The target files for all
three horizons exactly match the independent source reconstruction.

## 4. Feature leakage audit

All 14 features actually supplied to the four configurations were independently recalculated
from the source CPI and market levels. Their maximum absolute difference from the saved
feature matrix was zero at the stored precision. Every row has `feature_observation_end` equal
to origin minus one month. The construction uses exact calendar-period lookups and rejects
missing/nonpositive FX or Brent levels; it does not fill or skip across a gap. CPI uses the
verified contiguous published segment. The rolling CPI and FX statistics are backward-looking;
no centered window is present.

The detailed 23-row, feature-by-feature audit—including excluded repo, NEER/REER, WPI, and
prior-stage forecast candidates—is in
[STAGE4_FEATURE_LEAKAGE_AUDIT.csv](./STAGE4_FEATURE_LEAKAGE_AUDIT.csv).

Findings:

- CPI lags, change, mean, and volatility use only published CPI observations dated through
  \(t-1\); the CPI index is not substituted.
- USD/INR features use observed source levels only through \(t-1\). No future realized FX
  value, Stage 1 forecast, or Stage 2 prediction is used.
- Brent and the Brent-INR product proxy use only source levels through \(t-1\). The proxy is
  explicitly an approximate mechanical product, not actual landed import cost.
- Brent and proxy six-month volatility are calculated in the loading panel but are not part
  of any fitted model feature list. Repo, NEER/REER, and WPI are not loaded into the Stage 4
  feature builder.
- There are no separate positive depreciation and negative appreciation components. The
  signed FX return and signed cumulative net return encode direction, but do not separately
  estimate direction-specific effects; this is narrower than the feature/target matrix's
  proposed `max(r,0)` / `min(r,0)` design. It is not future leakage, but it limits
  interpretation of asymmetric exchange-rate signals.
- Reference-month timing is not proof of actual availability: release dates and historical
  data vintages remain unverified. The experiment is retrospective, not a genuine real-time
  backtest.

## 5. Chronological validation audit

The origin/target/split manifest was independently inspected. Validation predictions are
expanding-origin. At each validation origin, training labels are restricted to target months
strictly earlier than that origin. The final model for each configuration/horizon is refit
once at its first test origin and then frozen for the 18-target test, as required by the
approved protocol.

| Horizon | Initial training (N / positive) | Validation (N / positive) | Unscored gap (N / positive) | Final test (N / positive) | First test origin |
|---:|---:|---:|---:|---:|---|
| 1 | 71 / 12 | 23 / 12 | 6 / 2 | 18 / 3 | Jun 2023 |
| 3 | 69 / 12 | 21 / 12 | 6 / 2 | 18 / 3 | Apr 2023 |
| 6 | 66 / 12 | 18 / 10 | 6 / 2 | 18 / 3 | Jan 2023 |

The manifest also identifies unscored validation warm-up rows: one for h=1, three for h=3,
and six for h=6. They are not validation score rows; their labels can enter later fits only
after they mature. The Jan–Jun 2023 target block is not used for model selection. At the
first test origins, training contains 100/26, 96/26, and 90/24 total/elevated rows for h=1,
h=3, and h=6 respectively. Every final-test target month is strictly later than its frozen
training-label cutoff. Representative boundary pairs:

| Horizon | First test origin → target | Last test origin → target | Frozen training cutoff (exclusive) |
|---:|---|---|---|
| 1 | Jun 2023 → Jul 2023 | Nov 2024 → Dec 2024 | Jun 2023 |
| 3 | Apr 2023 → Jul 2023 | Sep 2024 → Dec 2024 | Apr 2023 |
| 6 | Jan 2023 → Jul 2023 | Jun 2024 → Dec 2024 | Jan 2023 |

No random shuffling, imputation, or feature selection is used. StandardScaler is inside the
Logistic Regression pipeline and is fitted on each training fold only. Random Forest and
XGBoost do not use scaling. Logistic class weighting and XGBoost's negative/positive weight
are derived from each training fold. Thresholds are chosen from validation predictions only.
The Stage 4 test outcomes do not enter candidate selection, global model selection, or
threshold choice. The frozen-model design is consistent with the approved protocol.

## 6. Model and configuration audit

The code passed the feature lists directly to all fitted estimators; feature-importance rows
and the generated feature matrix confirm the same membership:

| Configuration | Actual membership |
|---|---|
| C0 | CPI lags, CPI one-month change, CPI three-month mean, CPI six-month volatility |
| C1 | C0 plus lagged USD/INR one-month return, three-month cumulative return, six-month volatility |
| C2 | C1 plus lagged Brent USD one-month and three-month cumulative returns |
| C3 | C1 plus lagged Brent-INR proxy one-month and three-month cumulative returns; no Brent USD return |

These are comparable same-origin/same-target ablations and agree with the approved four-set
design. No configuration silently contains another configuration's imported-cost features.

The actual candidate grid is narrower than the protocol's proposed search boundaries:
Logistic Regression uses C={0.1, 1, 10}; Random Forest uses 300 trees, depth 2/3, minimum leaf
5; XGBoost uses 100 trees, depth 1/2, learning rate 0.03, minimum child weight 5, 0.8 row and
column subsampling, and L2 value 10. The reduced grid is bounded and does not use test
outcomes; it is a documented protocol deviation, not leakage.

The majority/prevalence baseline predicts the positive-class prevalence of the matured
training labels and applies the fixed 0.5 alert threshold. Since the training prevalence is
below 0.5, it predicts no alerts. Its constant probabilities and resulting metrics are
reproducible from the training counts.

An independent in-memory rerun of the 144 candidate configurations on expanding validation
origins reproduced the chosen candidate within each configuration/model/horizon and the
validation-only overall winners:

| Horizon | Selected validation model | Parameters | Validation AP | Threshold |
|---:|---|---|---:|---:|
| 1 | C0 Logistic Regression | C=10, balanced, lbfgs | 0.672 | 0.589 |
| 3 | C3 Logistic Regression | C=0.1, balanced, lbfgs | 0.746 | 0.108 |
| 6 | C3 XGBoost | depth=1, 100 trees, learning rate=0.03, min_child_weight=5, subsample/colsample=0.8, reg_lambda=10 | 0.830 | 0.211 |

These selections were made from validation results. The following held-out metrics are
reported separately and were not used to change the selected models.

## 7. Independent metric reconciliation

Predictions were grouped by horizon/configuration/model and sorted by target month. Confusion
counts and pointwise metrics were recalculated from saved actual labels, probabilities, and
thresholds. Stored alert classes were also checked against `probability >= threshold`.
All 48 groups and all stored metric columns reconcile. There are zero alert-class
mismatches. Largest absolute rounding difference across stored metrics is approximately
\(3.34\times10^{-12}\); it occurs in false alarms per year. The 1,248-row
[STAGE4_AUDIT_METRIC_RECONCILIATION.csv](./STAGE4_AUDIT_METRIC_RECONCILIATION.csv)
contains each saved value, independent value, difference, and reconciliation status.
Balanced accuracy and contiguous false-positive-mask runs are included as audit-only
metrics because they were not saved in the original metric table.

| Horizon | Selected model | TP / FP / TN / FN | Precision | Recall | F1 | AP | ROC-AUC | Brier | Specificity | Balanced accuracy |
|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | C0 Logistic Regression | 0 / 4 / 11 / 3 | 0.000 | 0.000 | 0.000 | 0.140 | 0.222 | 0.305 | 0.733 | 0.367 |
| 3 | C3 Logistic Regression | 2 / 14 / 1 / 1 | 0.125 | 0.667 | 0.211 | 0.253 | 0.533 | 0.169 | 0.067 | 0.367 |
| 6 | C3 XGBoost | 3 / 15 / 0 / 0 | 0.167 | 1.000 | 0.286 | 0.400 | 0.667 | 0.210 | 0.000 | 0.500 |

The selected h=1 model has lower AP and worse Brier score than the prevalence baseline
(AP 0.167, Brier 0.148). At h=3 and h=6 the selected models have higher AP than prevalence
(0.253 and 0.400 versus 0.167), but worse Brier scores (0.169 and 0.210 versus approximately
0.150) and very poor selectivity. These small-sample comparisons do not establish imported
cost indicators' general predictive value or any causal economic effect.

Undefined test precision for no-alert prevalence baselines is encoded as `NA` in the CSV
metric file, not zero. The Markdown model-results table renders these entries as `nan` despite
stating that they are `NA`; this is a presentation inconsistency, not a numeric substitution.
The final test has both classes, so AP and ROC-AUC are defined for these groups. Calibration
plots use only 18 points and three positives per horizon and are descriptive only; no
calibration reliability claim is supported.

## 8. Episode and false-alarm audit

The independently reconstructed test episodes are July–August 2023 and October 2024 for each
horizon. The reported count of positive months and the pointwise confusion matrices are
correct. Event detection, however, is not the same as positive-month detection:

| Horizon | Elevated months detected | Actual episodes detected | False-positive months | Saved unmatched alert runs | Contiguous false-positive-mask runs |
|---:|---:|---:|---:|---:|---:|
| 1 | 0 / 3 | 0 / 2 | 4 | 3 | 3 |
| 3 | 2 / 3 | 1 / 2 | 14 | 1 | 2 |
| 6 | 3 / 3 | 2 / 2 | 15 | 0 | 2 |

The saved implementation defines a false-alarm episode as a contiguous predicted-alert run
having **no** actual elevated target month anywhere in that run. This matches the approved
protocol's unmatched-alarm-run definition. It does not split a mixed run into true-event and
false-positive portions, and it has no one-to-one event matching or horizon-specific
tolerance. Consequently, the h=6 always-alert run intersects the true episodes and is counted
as zero unmatched alert runs, despite 15 false-positive months. The independent contiguous
false-positive-mask run count answers a different question; its difference from the saved
unmatched-run count is expected, not a computation discrepancy. Both quantities should be
named and interpreted distinctly.

Detecting all three elevated months at h=6 does not imply a useful warning system: it alerts
in every test month, has 15 false-positive months, zero specificity, and precision 0.167.
The h=3 model detects two months from only one of the two actual episodes. No causal warning
lead is established; \(h\) is only the nominal direct-target horizon.

## 9. Statistical interpretation and unresolved issues

- Each horizon's held-out set has only 18 observations, three positive months, and two
  elevated episodes. Monthly targets and adjacent horizons are dependent.
- AP, ROC-AUC, model ranking, threshold performance, and calibration are unstable with this
  event count. Validation thresholds themselves were selected on a small episodic sample.
- The test metrics are descriptive and retrospective. Historical release dates and vintages
  are absent; reference-month lagging does not establish a point-in-time real-time information
  set.
- The proxy is not landed import cost. Feature importance and incremental prediction scores
  are not causal evidence.
- The directional FX effect is not separately parameterized into depreciation and
  appreciation components.
- The event-level false-alarm episode metric is a coarse unmatched-alert-run count; report it
  with pointwise false-positive months. No code correction was required or made in this audit.
- Markdown renders undefined precision as `nan` where the CSV correctly records `NA`.
- No statistical significance or independent-event uncertainty claim is made.

## 10. Reproducibility and integrity

The stored Stage 4 run-one and run-two hash manifests each contain 32 entries and are
identical. Their 28 data/model/prediction/metric/visualization artifacts match current hashes,
including predictions, metrics, processed Stage 4 files, model specifications, serialized
models, and all ten valid PNG visualizations. The two report files noted in the protection
section have expected post-run documentation edits and are not experiment-result artifacts.
The 220-file pre-implementation manifest and 292-file pipeline protected map both have zero
current mismatches.

Run metadata records seed 42, Python 3.13.0, NumPy 2.5.4, pandas 3.1.1,
scikit-learn 1.9.1, XGBoost 3.4.1, joblib 1.6.0, and Matplotlib 3.11.2. The metadata records
zero Logistic Regression convergence warnings; fitting treats such warnings as errors.
Binary fitted-model artifacts reproduced byte-for-byte across the two runs, which is
environment-specific evidence and not proof of portability.

## 11. Required clarifications and final decision

1. Retain the approved unmatched-alert-run definition, but state it next to reported
   `false_alarm_episodes` values and report pointwise false-positive months alongside it.
   If a different event-matching rule is desired, predefine it for direct 1-, 3-, and
   6-month forecasts and obtain separate approval before recalculating any Stage 4 outputs.
2. Keep separate depreciation/appreciation components out of the claims unless approved and
   evaluated; the current signed-return model does not separately estimate directional
   contributions.
3. Use `NA` rather than `nan` in human-readable metric tables for undefined values. The saved
   CSV correctly uses `NA`; this is a documentation presentation improvement.

**Final classification: VERIFIED WITH LIMITATIONS.** Target construction, feature-time
boundaries, chronological purging, validation-only selection, model feature separation,
saved pointwise metrics, and the protocol-defined unmatched-alert-run calculation pass
independent checks. Statistical and vintage limitations materially restrict interpretation:
only 18 test months and three elevated observations in two episodes per horizon, no
historical release/vintage verification, and highly uncertain calibration and episode
performance. The coarse unmatched-run measure must not be used without the corresponding
false-positive-month counts. Stage 5 has not been started.
