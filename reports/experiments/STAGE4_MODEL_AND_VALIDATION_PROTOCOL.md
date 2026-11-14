# Stage 4 Model and Validation Protocol

**Status:** Approved Stage 4 protocol; implementation authorization was provided by explicit researcher request. This document does not authorize Stage 5.  
**Primary target:** Published All India / Combined CPI General inflation \(>6\%\) at month \(t+h\).

## 1. Estimation unit and leakage-safe design matrix

Each row represents one forecast origin \(t\) and one fixed horizon \(h\). The binary outcome is
\(Y^{(h)}_t=1[y_{t+h}>6]\). Build a separate direct classifier for \(h=1,3,6\). Do not use
future CPI, USD/INR, Brent, WPI, repo, or NEER/REER observations.

The model frame must include at least:

| Field | Requirement |
|---|---|
| `forecast_origin` | Unique monthly origin |
| `target_month` | Exactly `forecast_origin + h` calendar months |
| `horizon_months` | One of 1, 3, 6 |
| `target_inflation` | Source published CPI value for target month |
| `elevated_target` | 1 iff `target_inflation > 6.0`; exactly 6.0 is 0 |
| `feature_observation_end` | Latest reference month contributing to any predictor; must be < origin |
| `feature_set` | Prespecified ablation label |
| source/provenance fields | Source series, transformation, lag, vintage/timing caveat |

Use a contiguous monthly key and verify unique dates before creating row lags. Never use a
row-based lag across a missing calendar month. Reject duplicate dates, target gaps, and
unexplained missing feature values. Keep 2025 and the separate 2026 CPI segment disconnected.

## 2. Prespecified information sets

1. **B0 CPI history:** a small set of published CPI lags, one change, and one trailing summary.
2. **B1 CPI + observed FX:** signed depreciation/appreciation, limited cumulative movement, and
   at most one trailing volatility statistic.
3. **B2 CPI + FX + Brent USD:** B1 plus lagged Brent change and, optionally, a corrected
   volatility summary.
4. **B3 CPI + FX + Brent-INR proxy:** B1 plus a lagged proxy change, evaluated as an alternative
   to B2 rather than a simultaneous duplicate.
5. **B4/B5 conditional:** add source-validated repo/one NEER or REER series/WPI in separate
   ablations only after timing and identity are approved.

Do not include every engineered column. The sample has fewer than 120 eligible labels per
horizon and only 12 elevated labels in the initial training block; redundant lags, four
correlated NEER/REER series, or broad interactions would be overfitting risks. Feature selection
must be prespecified or fit inside the training portion of each fold.

## 3. Outer chronological partitions

Use common **target-month** blocks to hold the final target set fixed across horizons:

| Role | Target-month range | Counts at >6% |
|---|---|---|
| Initial training | Horizon-eligible start through Dec 2020 | h1: 71 (12 positive), h3: 69 (12), h6: 66 (12) |
| Validation | Feb 2021-Dec 2022 (h1); Apr 2021-Dec 2022 (h3); Jul 2021-Dec 2022 (h6) | h1: 23 (12 positive, 11 negative); h3: 21 (12, 9); h6: 18 (10, 8) |
| Validation-to-test gap | Jan-Jun 2023 | 6 per horizon (2 positive, 4 negative) |
| Final test | Jul 2023-Dec 2024 | 18 per horizon (3 positive, 15 negative) |

The target-date blocks, not origin-month labels, define these counts. Validation begins at the
common January 2021 origin; target months before January 2021+h are omitted from validation
scoring so their labels cannot be in the future at the first validation origin. For the common
final-test targets, forecast origins are June 2023-November 2024 (h1), April 2023-September
2024 (h3), and January 2023-June 2024 (h6).

Use the same target months for all configurations and candidate models within each horizon.
The test set is not used to select features, model class, hyperparameters, class weighting,
calibration, thresholds, or reporting narratives.

## 4. Expanding validation, purging, and model freeze

- Generate expanding-origin validation predictions on the training/validation period, in
  chronological order. The first validation origin is January 2021 at each horizon; its first
  scored target is February 2021 (h1), April 2021 (h3), or July 2021 (h6). Within each fold,
  only training labels whose target month is strictly earlier than the validation origin may
  be used. Purge earlier-origin rows with labels that have not yet been observed by that origin.
- For each validation origin, scalers, imputers, selectors, weights, resampling, and calibrators
  are fitted on that fold's training data only. Do not use random shuffling.
- Hyperparameter/threshold selection is performed only on the scored, horizon-specific
  validation target blocks above (Feb 2021-Dec 2022 for h1, Apr 2021-Dec 2022 for h3, and
  Jul 2021-Dec 2022 for h6). The Jan-Jun 2023 block is not used for choosing a model or
  threshold. During validation replay, previously matured labels may enter later expanding
  validation fits only if their target month is strictly before that later origin.
- Before the first final-test origin at each horizon, refit the selected specification on all
  eligible labels whose target month is strictly before that origin. This can include some
  Jan-Jun 2023 labels for h1/h3 when they have matured by the first test origin; it cannot
  include any label dated on or after that origin. Recalculate scaling and class weights from
  this final pre-test training data.
- Freeze the fitted pipeline and probability threshold for the entire final test; do not
  update using final-test target values.
- Save each origin/target pair and assert calendar-month addition, feature-end boundary,
  uniqueness, no missing target, and identical sample keys across paired models.

The direct \(t+h\) label is one target month, not an outcome over a duration. Nevertheless,
adjacent labels are dependent because CPI year-on-year rates share underlying months and
successive forecast information windows overlap. Purging addresses future target availability;
it does not make the final 18 rows independent. Report episode-level metrics and avoid IID
uncertainty claims. If a confidence interval is included, use a prespecified time-block method
and clearly acknowledge that two test episodes make it unstable.

## 5. Candidate models and fixed search boundaries

### Logistic Regression — primary

- Pipeline: `StandardScaler` + L2-regularized logistic regression for continuous features.
- Candidate `C`: 0.01, 0.1, 1, 10.
- `class_weight`: `None` or `balanced`, computed from the current training fold.
- Fix solver and maximum iterations; record convergence warnings and fail visibly if the model
  does not converge.
- Use coefficient signs and grouped effects only as conditional associations; scaling and
  regularization affect coefficient magnitudes.

### Random Forest — nonlinear benchmark

- No scaling required.
- Candidate trees: 300 or 500; maximum depth: 2, 3, or 5; minimum leaf size: 5 or 10;
  `max_features`: `sqrt` or 0.5; class weights: `None` or `balanced_subsample`.
- Fix seed and parallelism. Shallow trees and larger leaves are intended to control variance.

### XGBoost — exploratory gradient-boosted benchmark

- No scaling required for tree splits.
- Candidate estimators: 100 or 200; depth: 1 or 2; learning rate: 0.03 or 0.1;
  `min_child_weight`: 5 or 10; row/column subsample: 0.8 or 1.0; `reg_lambda`: 1 or 10;
  `gamma`: 0 or 0.5.
- Calculate `scale_pos_weight` from each training fold only; do not use validation/test class
  counts to set it. Fix seed, thread count, and any early-stopping rule. No early stopping on
  the final test.
- Keep this model exploratory because the number of independent positive episodes is small.

Use a narrow grid and validation-only selection. Do not expand the search because a test result
looks disappointing. No deep learning, automated architecture search, or synthetic data is
proposed.

## 6. Class imbalance, probabilities, and operating threshold

The primary class counts are not extreme in aggregate (about one quarter positive) but are
episodic. Begin with unweighted logistic regression as the reference and compare training-fold
class weighting. Do not use resampling by default. If a later, separately approved resampling
experiment is conducted, it must be nested inside each training fold; validation and final test
remain real and untouched.

Use probability scores for PR-AUC, ROC-AUC, and Brier score. Report the default 0.5 operating
threshold and, if an operational threshold is desired, choose it on validation data only under
a predeclared policy rule. A high-recall/F-beta operating point may be shown as sensitivity, but
no economic cost ratio is known. Because class weighting may distort probabilities, report
calibration separately; do not assume weighted scores are calibrated probabilities. Isotonic
calibration is not recommended with this sample; any sigmoid calibration must be fit inside
chronological training folds.

## 7. Metrics, episode handling, and undefined results

For each fixed final-test sample, provide:

- Confusion matrix (explicit order: non-elevated, elevated).
- Precision, recall, F1, specificity, false-positive rate, and false-negative rate.
- Average precision / PR-AUC and ROC-AUC.
- Brier score; reliability table/plot only with counts per bin and a warning that 18 rows cannot
  establish stable calibration.
- Counts of missed elevated months, false-alarm months, detected episodes, missed episodes,
  and false-alarm episodes.
- False alarms per test-year and the nominal lead associated with each correctly predicted
  target.

Define an elevated episode as a contiguous run of months with actual inflation >6%. Count a
detected episode once if at least one origin produces an elevated warning for a month in that
run; count any contiguous alarm run not matched to an actual episode as one false-alarm run.
This rule must be fixed before computing test summaries.

Do not coerce undefined statistics to zero. Emit `NA` and the reason if a denominator/class is
absent. Precision is undefined when there are no predicted positives; recall/FNR are undefined
without actual positives; specificity/FPR are undefined without actual negatives; ROC-AUC
requires both actual classes; PR-AUC requires an actual positive class. F1 is zero when its
denominator is nonzero but there are no true positives, and undefined only when there are
neither actual nor predicted positives. Confusion counts remain reportable. Brier is
numerically defined for one-class samples but cannot substitute for a calibration assessment.

Accuracy is secondary: an always-negative classifier is correct on 74.6%-75.6% of eligible
labels overall, and 83.3% of the proposed test labels. It could therefore look strong while
missing elevated inflation.

## 8. Incremental value and explainability

Use paired changes in validation/test metrics for B0 vs B1, B1 vs B2, and B1 vs B3. Report
identical row counts, target dates, and uncertainty limitations. Test data are for one final
evaluation after specification lock, not iterative feature selection.

Explain model predictions with:

- Regularized logistic coefficient signs and magnitudes on standardized predictors.
- Grouped permutation importance on validation data, repeated across chronological folds.
- Feature-group ablations and their paired PR-AUC/Brier/recall changes.
- Optional model-specific SHAP summaries only after a model is locked, marked exploratory, and
  never interpreted causally.

Importance measures describe the fitted predictive mapping and correlated features can divide
or exchange importance. No coefficient or explanation is evidence that depreciation, oil,
repo, NEER/REER, or WPI caused a target event.

## 9. Reproducibility and quality controls for later implementation

Before any Stage 4 implementation, record exact Python/package versions, fixed random seeds,
feature definitions, threshold, split dates, model grids, and source hashes. Persist run
metadata, predictions with forecast origin/target/horizon, metric tables with denominators,
and model specification. Test:

1. \(t+h\) target alignment for every row and horizon.
2. No feature reference date at or after the origin.
3. No training label reaches a validation/test origin.
4. Chronological split order and common comparison keys.
5. Training-only scaling, class weights, threshold/calibration fits.
6. Correct >6% label rule, especially equality at 6%.
7. Confusion/metric formulas and explicit undefined values.
8. Reproducibility and raw/processed/prior-stage output hashes.

The researcher subsequently authorized Stage 4 implementation while accepting the documented
retrospective timing and sample-size limitations. The implementation uses separately
constructed, calendar-safe features and does not modify the existing shared feature-engineering
module. Stage 5 remains unauthorized.
