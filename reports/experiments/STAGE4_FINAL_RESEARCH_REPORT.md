# Stage 4 Final Research Report

## Executive assessment

**Classification: VERIFIED WITH LIMITATIONS.** The Stage 4 implementation and retrospective
evaluation completed using the verified published-CPI segment, origin-safe lagged predictors,
chronological validation, and an untouched common final-test target window. This does not
establish real-time deployability, causal effects, or reliable operational warning performance.

## Selected models and observed results

Models/configurations were selected using validation average precision and Brier-score tie
breaks, not test outcomes. Their held-out metrics are linked below.

|   horizon_months | configuration   | model               | candidate_id                                                                                                                    |   validation_pr_auc_average_precision |   selected_threshold |
|-----------------:|:----------------|:--------------------|:--------------------------------------------------------------------------------------------------------------------------------|--------------------------------------:|---------------------:|
|                1 | C0              | logistic_regression | C-10.0_class_weight-balanced_max_iter-5000_solver-lbfgs                                                                         |                                 0.672 |                0.589 |
|                3 | C3              | logistic_regression | C-0.1_class_weight-balanced_max_iter-5000_solver-lbfgs                                                                          |                                 0.746 |                0.108 |
|                6 | C3              | xgboost             | colsample_bytree-0.8_gamma-0.0_learning_rate-0.03_max_depth-1_min_child_weight-5_n_estimators-100_reg_lambda-10.0_subsample-0.8 |                                 0.830 |                0.211 |

The full final-test comparison is in
[STAGE4_MODEL_RESULTS_REPORT.md](./STAGE4_MODEL_RESULTS_REPORT.md).
The test contains only 18 observations and three elevated months (two episodes) per horizon.
The >6% classification boundary is strict; 6.0% is non-elevated.

Stage 2 and Stage 3 remain **VERIFIED WITH LIMITATIONS**; their retrospective and
non-causal constraints remain in force. Stage 4 does not use prior-stage fitted predictions
as predictors.

## Evidence and integrity

- Input target: published All India / Combined / CPI (General) `inflation_value`;
  CPI index substitution: no.
- Target period: January 2014-December 2024, 132 consecutive months; no 2025 gap bridging.
- All predictor reference dates precede their forecast origins; future realized
  FX/Brent/CPI values are not predictors.
- C0/C1/C2/C3 are same-origin/same-target ablations and are described in
  [STAGE4_DATA_AND_FEATURE_REPORT.md](./STAGE4_DATA_AND_FEATURE_REPORT.md).
- Prior-stage outputs and raw/existing processed data are protected by before/after hashes.
- Horizon-specific target datasets, an origin/split manifest, and feature eligibility details
  are generated for auditability.
- Final-test diagnostics are saved for class counts, episodes, PR/ROC, confusion matrices,
  calibration, feature importance, configuration comparisons, and risk timelines.
- No synthetic data, deep learning, dashboard, or Stage 5 work was performed.

## Final execution and reproducibility

The complete Stage 4 pipeline exited 0 on two consecutive runs. All 28 generated
data/model/prediction/metric/visualization artifacts had matching SHA-256 hashes across
the runs; their aggregate manifest hash is
`bf20da9f8619b252b734f790c96f1b534668e531e5a6fc5c6ff38edca9df5163`.
This includes the prediction archive, metric tables, serialized models, specifications,
and diagnostic images. Python 3.13.0 was used with NumPy 2.5.4, pandas 3.1.1,
scikit-learn 1.9.1, XGBoost 3.4.1, joblib 1.6.0, Matplotlib 3.11.2, and seed 42.
No Logistic Regression convergence warnings occurred; fitting treats such warnings as errors.

Final quality gates all exited 0: `python -m pytest -q` (64 passed),
`ruff check .`, `python -m pip check`, and both complete pipeline runs.
The 220-file pre-implementation protected manifest remained unchanged. The pipeline's
292-file protected-file guard also reported no changes on either run.

Held-out performance is weak and highly uncertain: the selected 1-month model had average
precision 0.140, Brier score 0.305, detected 0/3 elevated months, and raised 4 false alerts;
the 3-month model had average precision 0.253, Brier score 0.169, detected 2/3, and raised
14 false alerts; the 6-month model had average precision 0.400, Brier score 0.210, detected
3/3, and raised 15 false alerts. Each horizon has only 18 test observations and two elevated
episodes. The results are descriptive retrospective evidence, not a basis for deployment.

## Limitations carried forward

1. The final test has only three elevated target months in two episodes; discrimination,
   calibration, model rankings, and episode sensitivity are highly uncertain.
2. CPI year-on-year observations and 3-/6-month horizon outcomes overlap; monthly rows
   are dependent.
3. Historical release dates and data vintages are unavailable. Reference-month lagging is not proof
   of actual real-time availability.
4. The Brent-INR variable is a mechanical, approximate product proxy and not landed import cost.
5. Repo, NEER/REER, and WPI are excluded from primary models because provenance/timing was not
   sufficiently resolved.
6. Predictive feature importance and incremental scores are not causal evidence.
7. Threshold selection and validation metrics are themselves uncertain on a small episodic sample.

See [STAGE4_EVALUATION_AND_ROBUSTNESS_REPORT.md](./STAGE4_EVALUATION_AND_ROBUSTNESS_REPORT.md)
for paired comparisons, errors, episode findings, and reproducibility details. Stage 5 has not
been started; stop for researcher review.
