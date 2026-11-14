# Stage 4 Research Design: Early Warning Classification

**Status:** Design proposal; Stage 4 implementation was subsequently authorized by explicit researcher request. This document does not authorize Stage 5.  
**Research direction:** “When Does Rupee Depreciation Become Inflationary? An Explainable AI-Driven Early-Warning Framework for Imported Inflation Risk in India.”  
**Evidence cutoff:** Existing local files and prior-stage reports inspected on 2026-11-10.

## 1. Purpose and research question

Stage 4 will investigate whether economic indicators known by a forecast origin help identify
whether published Indian CPI inflation will be elevated in a specified future month:

> Can exchange-rate movements and imported-cost indicators provide early warning signals of
> elevated CPI inflation in India?

The stage evaluates predictive information, not causal effects. The prior Stage 2 and Stage 3
classifications are **VERIFIED WITH LIMITATIONS**. Their retrospective nature, limited samples,
unverified historical releases/vintages, and lack of causal identification carry forward. Stage
1 FX predictions, Stage 2 forecasts, and Stage 3 fitted results are not observations to be
relabelled as independent evidence.

**Verified:** The local CPI file has a continuous 132-month published-inflation segment from
January 2014 through December 2024. The 2025 gap and the separate nine-month 2026 segment must
remain separate.

**Proposed:** Restrict Stage 4's primary supervised sample to origins from January 2015 onward.
This supplies a full year of published CPI history for the prespecified CPI-history features
without filling the earlier missing lags.

## 2. Outcome, forecast origin, and horizons

Let \(y_m\) be the published All India / Combined / CPI (General) year-on-year inflation rate
for reference month \(m\), in percentage points. Let \(t\) denote a monthly forecast-origin
month, with the operational information cutoff at the end of that month. For horizon
\(h\in\{1,3,6\}\):

\[
Y^{(h)}_t = \mathbb{1}\{y_{t+h} > 6.0\}.
\]

- **Elevated:** \(y_{t+h}>6.0\%\).
- **Non-elevated:** \(y_{t+h}\le 6.0\%\), including an observation exactly equal to 6.0%.
- **1-month horizon:** classify inflation in month \(t+1\), not inflation in month \(t\).
- **3-month horizon:** classify inflation in month \(t+3\), not the maximum over months \(t+1\)
  through \(t+3\).
- **6-month horizon:** classify inflation in month \(t+6\), not whether an episode occurs at
  any time during the next six months.

Features use dates no later than \(t-1\) as a conservative reference-month cutoff. This avoids
using same-reference-month observations whose release may occur after the origin. Because local
historical release timestamps and vintages are unavailable, this is an **observation-date-safe
retrospective convention**, not proof that each value was actually published by the origin.
Stage 4 must not be described as a genuine real-time backtest.

The primary 6% threshold is retained. It has a policy rationale as the upper edge of India's
4% CPI target with a +/-2 percentage-point tolerance band; crossing it is substantively
interpretable. It is not selected by optimizing model performance.

### Threshold sensitivity

The 4% midpoint may be shown as a prespecified descriptive sensitivity, but it changes the
meaning from elevated/breach risk to above-target inflation and produces a majority-positive
class. An 8% severe-inflation threshold is only a descriptive sensitivity: it yields no
positive labels in any January 2015-or-later eligible horizon sample, so it cannot support
supervised model evaluation. Neither sensitivity replaces the primary label.

## 3. Target feasibility and sample window

**Verified counts from `cpi_monthly_clean.csv`:**

| Sample definition | Observations | Elevated >6% | Non-elevated <=6% | Elevated share |
|---|---:|---:|---:|---:|
| Continuous published-CPI segment, Jan 2014-Dec 2024 | 132 | 37 | 95 | 28.0% |
| 1-month eligible target sample, Feb 2015-Dec 2024 | 119 | 29 | 90 | 24.4% |
| 3-month eligible target sample, Apr 2015-Dec 2024 | 117 | 29 | 88 | 24.8% |
| 6-month eligible target sample, Jul 2015-Dec 2024 | 114 | 29 | 85 | 25.4% |

The first eight elevated months of the 2014 segment cannot be represented in the conservative
January 2015-onward origin sample because adequate prior published-inflation history is not
available. The 6% events are temporally clustered rather than independent monthly examples.

### Proposed chronological evaluation calendar

The initial training targets end in December 2020. To ensure each first validation prediction
origin is January 2021, validation target months start at \(t+h\): February 2021 for h=1,
April 2021 for h=3, and July 2021 for h=6. This prevents training on labels that would not
have matured at the validation origin. Model comparisons use identical origins and targets
within each horizon. A common final-test target window is retained across horizons.

| Target block | Target months | 1-month labels | 3-month labels | 6-month labels | >6% labels |
|---|---|---:|---:|---:|---|
| Initial training | Eligible start through Dec 2020 | 71 | 69 | 66 | 12 each |
| Validation | Feb 2021-Dec 2022 (h1); Apr 2021-Dec 2022 (h3); Jul 2021-Dec 2022 (h6) | 23 (12) | 21 (12) | 18 (10) | Elevated labels in parentheses |
| Validation-to-test gap | Jan-Jun 2023 | 6 | 6 | 6 | 2 each; not used for tuning |
| Untouched final test | Jul 2023-Dec 2024 | 18 | 18 | 18 | 3 each |

Target months before each validation start are omitted from validation scoring so no training
label reaches beyond the first validation origin. The final-test targets are common across
horizons; their forecast origins are target month minus \(h\) months. Thus final-test origins
are June 2023-November 2024 for 1-month, April 2023-September 2024 for 3-month, and January
2023-June 2024 for 6-month forecasts. The first 6-month test origin is January 2023;
validation targets through December 2022 precede it. In final fitting, include a labeled row
only if its target month is strictly before that horizon's first final-test origin. Do not fit
on any final-test labels.

The test contains only three elevated months, in two elevated runs (July-August 2023 and
October 2024). This is too little for a robust model ranking, precise calibration assessment,
or broad generalization claim. Report per-month and per-episode outcomes as exploratory.

## 4. Feature information sets

All predictors must be constructed from documented source variables, keyed to an uninterrupted
monthly calendar, and available by the specified cutoff. Calculations may use a feature value
dated \(t-1\), but never a realized value dated \(t+h\) or later.

### Core ablation sequence

1. **CPI-only baseline:** parsimonious lagged published CPI features.
2. **CPI + FX:** add signed USD/INR movements and cumulative/volatility measures.
3. **CPI + FX + Brent USD:** add lagged international Brent measures.
4. **CPI + FX + Brent-INR proxy:** use as a separate alternative to Brent USD, not alongside
   both in the primary ablation, because the proxy mechanically includes USD/INR.
5. **Conditional extensions:** repo, one validated NEER/REER series, and lagged WPI only after
   source meaning, vintage, and availability are sufficiently verified.

Use the same eligible origin/target rows across models within each horizon. Report incremental
predictive value through paired comparisons against the CPI-only baseline; do not infer
economic irrelevance when an indicator fails to improve a small test sample.

The existing engineered files contain contemporaneous features. Rebuild or lag them explicitly
at the origin in any future implementation; do not pass the master feature panel to a classifier
without an audited feature-time mapping.

## 5. Candidate classifiers

### Primary interpretable baseline: regularized logistic regression

Use a penalized logistic regression with a small, prespecified feature set. It estimates
probabilities, is a transparent baseline, and supports coefficient direction and uncertainty
discussion. Standardize continuous predictors inside a scikit-learn pipeline, fitting each
scaler only on the current training fold. One-hot or indicator features should not be scaled
unless a documented pipeline convention requires it.

Proposed narrow search: L2 penalty; `C` in `{0.01, 0.1, 1, 10}`; class weighting `None` or
`balanced`; solver and convergence settings fixed in advance. Use a sufficiently high iteration
limit and surface convergence warnings. Do not add a large interaction or polynomial expansion.

### Nonlinear benchmark: Random Forest

Use only as a constrained nonlinear comparator. Trees need no feature scaling. Proposed
boundaries: 300 or 500 trees; maximum depth 2, 3, or 5; minimum leaf size 5 or 10; `max_features`
`sqrt` or 0.5; class weighting `None` or `balanced_subsample`. Fix the seed and parallelism.
Shallow trees and larger leaves limit variance in the small sample.

### Exploratory gradient-boosted benchmark: XGBoost

Use only if the installed package and exact environment are recorded. Keep the model shallow
and strongly regularized; proposed boundaries: `n_estimators` 100 or 200; `max_depth` 1 or 2;
`learning_rate` 0.03 or 0.1; `min_child_weight` 5 or 10; `subsample` and `colsample_bytree`
0.8 or 1.0; `reg_lambda` 1 or 10; `gamma` 0 or 0.5. Compute any positive-class weight from
the current training fold only. Use no test-based early stopping.

The small event count does not justify deep learning or broad automated searches. Logistic
regression is the primary model; tree models are secondary benchmarks and must not be portrayed
as reliable merely because they can fit nonlinear patterns.

## 6. Validation and leakage controls

- Preserve strict time order; never use random train/test shuffling.
- Use the proposed training, validation, embargo, and test target-month blocks above.
- Within training/validation, generate expanding-window, rolling-origin predictions.
- At each fold's first validation origin \(v\), train only on rows whose target month is
  strictly earlier than \(v\). Purge any earlier-origin row whose label has not yet been
  observed by \(v\); this removes the horizon-crossing tail. Apply the same rule to every
  horizon and every configuration.
- Fit imputation, scaling, feature selection, calibration, class weights, and any resampling
  separately inside each training fold. Prefer no imputation: reject or explicitly account for
  missing predictors rather than silently filling.
- Select hyperparameters and any probability threshold on validation data only. Freeze the
  selected pipeline before evaluating the final test.
- For the final frozen model at each horizon, train only on labels with target months strictly
  before the first final-test origin. Do not incorporate final-test outcomes into later test
  refits.
- Compare models/configurations on identical final-test target months and origins within each
  horizon. For cross-horizon summaries, show the target dates and differing origin dates
  explicitly.
- The target is a single future month, not an “any elevated month within \(h\) months” label.
  Nonetheless, neighboring CPI year-on-year labels share index months and are serially
  dependent, and adjacent direct-horizon forecasts have overlapping information windows.
  Treat monthly metrics as descriptive; use episode-level counts and, if uncertainty is
  attempted, a time-block procedure rather than IID standard errors.

## 7. Imbalance and augmentation

At the primary threshold, the complete eligible samples contain 29 elevated labels per horizon
versus 85-90 non-elevated labels. Under the proposed split, the initial training block has 12
elevated labels, validation has 10-12 depending on horizon, and the final test has only 3.
This is moderate overall
imbalance but a severe shortage of independent elevated episodes in the test.

Start with unweighted and training-fold class-weighted logistic regression; compare threshold
choices using validation only. Class weighting changes probability calibration, so assess
calibration separately. Any resampling, if explicitly approved later, must occur inside each
training fold only; do not resample validation or test.

Synthetic time-series augmentation is **not justified**. It cannot create independent
inflation episodes and risks inventing economic trajectories. No synthetic observations are
authorized. SMOTE is not a default for temporally ordered, episode-clustered data. If a
separately approved synthetic-method experiment is ever considered, compare it with a
real-data-only model on exactly the same untouched real test observations and keep all
synthetic records out of validation and test.

## 8. Evaluation plan

Report, by horizon, feature configuration, and model, on the same untouched test rows:

- Confusion matrix with fixed positive/negative labels.
- Precision, recall/sensitivity, F1, specificity, false-positive rate (FP/(FP+TN)), and
  false-negative rate (FN/(FN+TP)).
- PR-AUC (state whether average precision is used) and ROC-AUC.
- Brier score and a calibration summary/plot, with the small-sample limitation explicit.
- Counts of true elevated months missed, false alarms, and detected elevated episodes.
- False alarms per year and episode-level sensitivity, deduplicating consecutive positive
  warnings under a prespecified episode rule.
- Warning lead: for this direct-target formulation, an alert correctly predicting \(t+h\)
  has \(h\) calendar months of nominal lead. Report that definition; do not equate it with
  causal warning time or claim extra lead from duplicated consecutive alerts.

Accuracy alone is unsuitable because a majority-class rule is already correct for roughly
74.6%-75.6% of the eligible labels. A missed elevated month/episode is a failure to warn
about inflation risk; a false alarm consumes attention and may reduce trust. No monetary or
policy cost ratio is established, so do not claim one error type has a quantified optimal cost.

Undefined metrics must be `NA` with the numerator/denominator and reason stated, never silently
set to zero. Precision is undefined if there are no predicted positives; recall and false-
negative rate are undefined if there are no actual positives; specificity and false-positive
rate are undefined if there are no actual negatives; ROC-AUC requires both actual classes;
PR-AUC requires an actual positive class. F1 is zero when its denominator is nonzero but
there are no true positives, and undefined only when there are neither actual nor predicted
positives. Brier score remains mathematically defined for one-class outcomes but is not
evidence of calibration. Always retain the confusion counts.

## 9. Economic interpretation and explainability

Incremental predictive value will be assessed through paired, same-origin ablations:

- CPI history versus CPI + FX tests whether observed depreciation/appreciation features add
  warning information beyond inflation persistence.
- Add Brent USD separately to assess whether international oil movements add information.
- Compare the approximate Brent-INR product proxy as an alternative imported-cost signal.
  It is not landed import cost and contains an exchange-rate component by construction.
- Add validated repo, NEER/REER, and WPI indicators only in conditional extensions, with common
  samples and all timing caveats preserved.

Use standardized logistic coefficients for interpretable conditional associations, grouped
feature ablations, and permutation importance calculated on validation data. Any model-specific
explanation (including SHAP) is descriptive of the fitted prediction function, not an economic
causal effect. Report direction/stability across validation folds and avoid claiming that a
feature causes inflation or that an importance score is a structural contribution.

## 10. Decision and implementation gate

**Design feasibility: READY WITH LIMITATIONS.** A retrospective, highly constrained Stage 4
pilot can be specified for all three horizons, but the 18-target final test has only three
elevated months and two episodes. The 1-month horizon is the primary analysis. The 3- and
6-month horizons are exploratory only; the 6-month result should not support a standalone
model-ranking or operational-readiness claim. If a reviewer requires stable test-set
discrimination/calibration estimates, acquire a longer, point-in-time CPI history before
implementation.

Implementation remains blocked pending researcher approval of this design, resolution or
explicit acceptance of the data-timing limitations, and a decision on the existing feature
construction issues recorded in the issue log. This design does not authorize Stage 4 model
training or Stage 5.
