# Stage 4 Evaluation and Robustness Report

## Chronological evaluation

|   horizon_months | partition            |   n |   elevated |   non_elevated | target_start   | target_end   | training_label_cutoff                               |
|-----------------:|:---------------------|----:|-----------:|---------------:|:---------------|:-------------|:----------------------------------------------------|
|                1 | initial_training     |  71 |         12 |             59 | 2015-02-01     | 2020-12-01   | target month <= 2020-12                             |
|                1 | expanding_validation |  23 |         12 |             11 | 2021-02-01     | 2022-12-01   | target month strictly before each validation origin |
|                1 | validation_test_gap  |   6 |          2 |              4 | 2023-01-01     | 2023-06-01   | not scored for model selection or final testing     |
|                1 | untouched_final_test |  18 |          3 |             15 | 2023-07-01     | 2024-12-01   | target month strictly before 2023-06                |
|                3 | initial_training     |  69 |         12 |             57 | 2015-04-01     | 2020-12-01   | target month <= 2020-12                             |
|                3 | expanding_validation |  21 |         12 |              9 | 2021-04-01     | 2022-12-01   | target month strictly before each validation origin |
|                3 | validation_test_gap  |   6 |          2 |              4 | 2023-01-01     | 2023-06-01   | not scored for model selection or final testing     |
|                3 | untouched_final_test |  18 |          3 |             15 | 2023-07-01     | 2024-12-01   | target month strictly before 2023-04                |
|                6 | initial_training     |  66 |         12 |             54 | 2015-07-01     | 2020-12-01   | target month <= 2020-12                             |
|                6 | expanding_validation |  18 |         10 |              8 | 2021-07-01     | 2022-12-01   | target month strictly before each validation origin |
|                6 | validation_test_gap  |   6 |          2 |              4 | 2023-01-01     | 2023-06-01   | not scored for model selection or final testing     |
|                6 | untouched_final_test |  18 |          3 |             15 | 2023-07-01     | 2024-12-01   | target month strictly before 2023-01                |

Each validation prediction is generated at its origin from an expanding training sample whose
labels have target months strictly earlier than that origin. Final models are refit once at the
first test origin with the same maturity rule, then frozen over the test. The January-June 2023
target block is not scored for tuning or final testing. Consecutive 3- and 6-month direct
forecast targets overlap in information and are dependent; the final sample has only 18
observations and three elevated months in two episodes.

## Incremental predictive value

Positive `delta_pr_auc_vs_c0` indicates higher average precision than C0, while positive
`delta_brier_vs_c0` indicates worse Brier score. Each difference is paired by identical target
month for the same classifier.

|   horizon_months | model               | baseline_configuration   | extended_configuration   |   common_n | common_target_start   | common_target_end   |   c0_pr_auc_average_precision |   extended_pr_auc_average_precision |   delta_pr_auc_vs_c0 |   c0_brier_score |   extended_brier_score |   delta_brier_vs_c0 |   c0_precision |   extended_precision |   c0_recall |   extended_recall |   c0_f1 |   extended_f1 | comparison_scope                                                  |
|-----------------:|:--------------------|:-------------------------|:-------------------------|-----------:|:----------------------|:--------------------|------------------------------:|------------------------------------:|---------------------:|-----------------:|-----------------------:|--------------------:|---------------:|---------------------:|------------:|------------------:|--------:|--------------:|:------------------------------------------------------------------|
|                1 | logistic_regression | C0                       | C1                       |         18 | 2023-07-01            | 2024-12-01          |                         0.140 |                               0.177 |                0.037 |            0.305 |                  0.174 |              -0.131 |          0.000 |                0.000 |       0.000 |             0.000 |   0.000 |         0.000 | paired identical target months; separate validation-selected fits |
|                1 | logistic_regression | C0                       | C2                       |         18 | 2023-07-01            | 2024-12-01          |                         0.140 |                               0.160 |                0.019 |            0.305 |                  0.194 |              -0.110 |          0.000 |                0.000 |       0.000 |             0.000 |   0.000 |         0.000 | paired identical target months; separate validation-selected fits |
|                1 | logistic_regression | C0                       | C3                       |         18 | 2023-07-01            | 2024-12-01          |                         0.140 |                               0.160 |                0.019 |            0.305 |                  0.194 |              -0.110 |          0.000 |                0.000 |       0.000 |             0.000 |   0.000 |         0.000 | paired identical target months; separate validation-selected fits |
|                1 | random_forest       | C0                       | C1                       |         18 | 2023-07-01            | 2024-12-01          |                         0.154 |                               0.140 |               -0.014 |            0.238 |                  0.226 |              -0.012 |          0.083 |                0.100 |       0.333 |             0.333 |   0.133 |         0.154 | paired identical target months; separate validation-selected fits |
|                1 | random_forest       | C0                       | C2                       |         18 | 2023-07-01            | 2024-12-01          |                         0.154 |                               0.143 |               -0.011 |            0.238 |                  0.214 |              -0.024 |          0.083 |                0.000 |       0.333 |             0.000 |   0.133 |         0.000 | paired identical target months; separate validation-selected fits |
|                1 | random_forest       | C0                       | C3                       |         18 | 2023-07-01            | 2024-12-01          |                         0.154 |                               0.143 |               -0.011 |            0.238 |                  0.215 |              -0.023 |          0.083 |                0.000 |       0.333 |             0.000 |   0.133 |         0.000 | paired identical target months; separate validation-selected fits |
|                1 | xgboost             | C0                       | C1                       |         18 | 2023-07-01            | 2024-12-01          |                         0.159 |                               0.170 |                0.011 |            0.256 |                  0.248 |              -0.008 |          0.091 |                0.167 |       0.333 |             0.667 |   0.143 |         0.267 | paired identical target months; separate validation-selected fits |
|                1 | xgboost             | C0                       | C2                       |         18 | 2023-07-01            | 2024-12-01          |                         0.159 |                               0.149 |               -0.010 |            0.256 |                  0.248 |              -0.008 |          0.091 |                0.000 |       0.333 |             0.000 |   0.143 |         0.000 | paired identical target months; separate validation-selected fits |
|                1 | xgboost             | C0                       | C3                       |         18 | 2023-07-01            | 2024-12-01          |                         0.159 |                               0.156 |               -0.003 |            0.256 |                  0.239 |              -0.018 |          0.091 |                0.000 |       0.333 |             0.000 |   0.143 |         0.000 | paired identical target months; separate validation-selected fits |
|                1 | prevalence_baseline | C0                       | C1                       |         18 | 2023-07-01            | 2024-12-01          |                         0.167 |                               0.167 |                0.000 |            0.148 |                  0.148 |               0.000 |        nan     |              nan     |       0.000 |             0.000 |   0.000 |         0.000 | paired identical target months; separate validation-selected fits |
|                1 | prevalence_baseline | C0                       | C2                       |         18 | 2023-07-01            | 2024-12-01          |                         0.167 |                               0.167 |                0.000 |            0.148 |                  0.148 |               0.000 |        nan     |              nan     |       0.000 |             0.000 |   0.000 |         0.000 | paired identical target months; separate validation-selected fits |
|                1 | prevalence_baseline | C0                       | C3                       |         18 | 2023-07-01            | 2024-12-01          |                         0.167 |                               0.167 |                0.000 |            0.148 |                  0.148 |               0.000 |        nan     |              nan     |       0.000 |             0.000 |   0.000 |         0.000 | paired identical target months; separate validation-selected fits |
|                3 | logistic_regression | C0                       | C1                       |         18 | 2023-07-01            | 2024-12-01          |                         0.131 |                               0.300 |                0.169 |            0.201 |                  0.166 |              -0.035 |          0.167 |                0.125 |       1.000 |             0.667 |   0.286 |         0.211 | paired identical target months; separate validation-selected fits |
|                3 | logistic_regression | C0                       | C2                       |         18 | 2023-07-01            | 2024-12-01          |                         0.131 |                               0.253 |                0.122 |            0.201 |                  0.169 |              -0.033 |          0.167 |                0.125 |       1.000 |             0.667 |   0.286 |         0.211 | paired identical target months; separate validation-selected fits |
|                3 | logistic_regression | C0                       | C3                       |         18 | 2023-07-01            | 2024-12-01          |                         0.131 |                               0.253 |                0.122 |            0.201 |                  0.169 |              -0.032 |          0.167 |                0.125 |       1.000 |             0.667 |   0.286 |         0.211 | paired identical target months; separate validation-selected fits |
|                3 | random_forest       | C0                       | C1                       |         18 | 2023-07-01            | 2024-12-01          |                         0.224 |                               0.261 |                0.037 |            0.203 |                  0.166 |              -0.037 |          0.167 |                0.167 |       1.000 |             1.000 |   0.286 |         0.286 | paired identical target months; separate validation-selected fits |
|                3 | random_forest       | C0                       | C2                       |         18 | 2023-07-01            | 2024-12-01          |                         0.224 |                               0.283 |                0.059 |            0.203 |                  0.172 |              -0.031 |          0.167 |                0.167 |       1.000 |             1.000 |   0.286 |         0.286 | paired identical target months; separate validation-selected fits |
|                3 | random_forest       | C0                       | C3                       |         18 | 2023-07-01            | 2024-12-01          |                         0.224 |                               0.283 |                0.059 |            0.203 |                  0.171 |              -0.032 |          0.167 |                0.167 |       1.000 |             1.000 |   0.286 |         0.286 | paired identical target months; separate validation-selected fits |
|                3 | xgboost             | C0                       | C1                       |         18 | 2023-07-01            | 2024-12-01          |                         0.285 |                               0.533 |                0.249 |            0.201 |                  0.182 |              -0.020 |          0.167 |                0.167 |       1.000 |             1.000 |   0.286 |         0.286 | paired identical target months; separate validation-selected fits |
|                3 | xgboost             | C0                       | C2                       |         18 | 2023-07-01            | 2024-12-01          |                         0.285 |                               0.279 |               -0.006 |            0.201 |                  0.169 |              -0.033 |          0.167 |                0.167 |       1.000 |             1.000 |   0.286 |         0.286 | paired identical target months; separate validation-selected fits |
|                3 | xgboost             | C0                       | C3                       |         18 | 2023-07-01            | 2024-12-01          |                         0.285 |                               0.275 |               -0.009 |            0.201 |                  0.173 |              -0.028 |          0.167 |                0.167 |       1.000 |             1.000 |   0.286 |         0.286 | paired identical target months; separate validation-selected fits |
|                3 | prevalence_baseline | C0                       | C1                       |         18 | 2023-07-01            | 2024-12-01          |                         0.167 |                               0.167 |                0.000 |            0.150 |                  0.150 |               0.000 |        nan     |              nan     |       0.000 |             0.000 |   0.000 |         0.000 | paired identical target months; separate validation-selected fits |
|                3 | prevalence_baseline | C0                       | C2                       |         18 | 2023-07-01            | 2024-12-01          |                         0.167 |                               0.167 |                0.000 |            0.150 |                  0.150 |               0.000 |        nan     |              nan     |       0.000 |             0.000 |   0.000 |         0.000 | paired identical target months; separate validation-selected fits |
|                3 | prevalence_baseline | C0                       | C3                       |         18 | 2023-07-01            | 2024-12-01          |                         0.167 |                               0.167 |                0.000 |            0.150 |                  0.150 |               0.000 |        nan     |              nan     |       0.000 |             0.000 |   0.000 |         0.000 | paired identical target months; separate validation-selected fits |
|                6 | logistic_regression | C0                       | C1                       |         18 | 2023-07-01            | 2024-12-01          |                         0.242 |                               0.255 |                0.013 |            0.231 |                  0.187 |              -0.044 |          0.167 |                0.167 |       1.000 |             1.000 |   0.286 |         0.286 | paired identical target months; separate validation-selected fits |
|                6 | logistic_regression | C0                       | C2                       |         18 | 2023-07-01            | 2024-12-01          |                         0.242 |                               0.283 |                0.041 |            0.231 |                  0.168 |              -0.063 |          0.167 |                0.167 |       1.000 |             1.000 |   0.286 |         0.286 | paired identical target months; separate validation-selected fits |
|                6 | logistic_regression | C0                       | C3                       |         18 | 2023-07-01            | 2024-12-01          |                         0.242 |                               0.283 |                0.041 |            0.231 |                  0.168 |              -0.063 |          0.167 |                0.167 |       1.000 |             1.000 |   0.286 |         0.286 | paired identical target months; separate validation-selected fits |
|                6 | random_forest       | C0                       | C1                       |         18 | 2023-07-01            | 2024-12-01          |                         0.333 |                               0.359 |                0.025 |            0.211 |                  0.198 |              -0.012 |          0.167 |                0.167 |       1.000 |             1.000 |   0.286 |         0.286 | paired identical target months; separate validation-selected fits |
|                6 | random_forest       | C0                       | C2                       |         18 | 2023-07-01            | 2024-12-01          |                         0.333 |                               0.389 |                0.056 |            0.211 |                  0.206 |              -0.005 |          0.167 |                0.167 |       1.000 |             1.000 |   0.286 |         0.286 | paired identical target months; separate validation-selected fits |
|                6 | random_forest       | C0                       | C3                       |         18 | 2023-07-01            | 2024-12-01          |                         0.333 |                               0.556 |                0.222 |            0.211 |                  0.208 |              -0.003 |          0.167 |                0.167 |       1.000 |             1.000 |   0.286 |         0.286 | paired identical target months; separate validation-selected fits |
|                6 | xgboost             | C0                       | C1                       |         18 | 2023-07-01            | 2024-12-01          |                         0.725 |                               0.410 |               -0.315 |            0.224 |                  0.193 |              -0.031 |          0.167 |                0.167 |       1.000 |             1.000 |   0.286 |         0.286 | paired identical target months; separate validation-selected fits |
|                6 | xgboost             | C0                       | C2                       |         18 | 2023-07-01            | 2024-12-01          |                         0.725 |                               0.333 |               -0.392 |            0.224 |                  0.213 |              -0.011 |          0.167 |                0.167 |       1.000 |             1.000 |   0.286 |         0.286 | paired identical target months; separate validation-selected fits |
|                6 | xgboost             | C0                       | C3                       |         18 | 2023-07-01            | 2024-12-01          |                         0.725 |                               0.400 |               -0.325 |            0.224 |                  0.210 |              -0.014 |          0.167 |                0.167 |       1.000 |             1.000 |   0.286 |         0.286 | paired identical target months; separate validation-selected fits |
|                6 | prevalence_baseline | C0                       | C1                       |         18 | 2023-07-01            | 2024-12-01          |                         0.167 |                               0.167 |                0.000 |            0.149 |                  0.149 |               0.000 |        nan     |              nan     |       0.000 |             0.000 |   0.000 |         0.000 | paired identical target months; separate validation-selected fits |
|                6 | prevalence_baseline | C0                       | C2                       |         18 | 2023-07-01            | 2024-12-01          |                         0.167 |                               0.167 |                0.000 |            0.149 |                  0.149 |               0.000 |        nan     |              nan     |       0.000 |             0.000 |   0.000 |         0.000 | paired identical target months; separate validation-selected fits |
|                6 | prevalence_baseline | C0                       | C3                       |         18 | 2023-07-01            | 2024-12-01          |                         0.167 |                               0.167 |                0.000 |            0.149 |                  0.149 |               0.000 |        nan     |              nan     |       0.000 |             0.000 |   0.000 |         0.000 | paired identical target months; separate validation-selected fits |

These are descriptive prediction comparisons, not evidence that a feature has or lacks a causal
economic effect. Brent-INR is an approximate product proxy, not landed import cost.

## Error, episode, and threshold diagnostics

The saved test metrics report precision, recall, F1, average precision (PR-AUC), ROC-AUC, Brier
score, calibration-relevant probabilities, confusion counts, false-positive/negative rates,
false alarms per year, and episode sensitivity. Direct forecast warning lead is the nominal
horizon `h`; it is not interpreted as causal lead time. Missed elevated outcomes are missed
warnings, while false positives are attention-consuming alarms. No policy cost ratio is assumed.

|   horizon_months |   threshold_percent_strictly_greater |   eligible_n |   elevated |   non_elevated |
|-----------------:|-------------------------------------:|-------------:|-----------:|---------------:|
|            1.000 |                                4.000 |      119.000 |     89.000 |         30.000 |
|            1.000 |                                6.000 |      119.000 |     29.000 |         90.000 |
|            1.000 |                                8.000 |      119.000 |      0.000 |        119.000 |
|            3.000 |                                4.000 |      117.000 |     87.000 |         30.000 |
|            3.000 |                                6.000 |      117.000 |     29.000 |         88.000 |
|            3.000 |                                8.000 |      117.000 |      0.000 |        117.000 |
|            6.000 |                                4.000 |      114.000 |     84.000 |         30.000 |
|            6.000 |                                6.000 |      114.000 |     29.000 |         85.000 |
|            6.000 |                                8.000 |      114.000 |      0.000 |        114.000 |

The >4% and >8% values are label-count sensitivities only and did not replace or retune the
primary >6% label. An 8% elevated class is too sparse for supervised evaluation in the eligible
period. Brier score is retained for one-class samples, but would not alone establish calibration.
Metrics requiring an absent class or denominator are `NA`, with counts and reasons recorded.

## Reproducibility and protected integrity

Seed: 42. Python: 3.13.0 (NumPy 2.5.4, pandas 3.1.1, scikit-learn 1.9.1,
XGBoost 3.4.1, joblib 1.6.0, Matplotlib 3.11.2). No Logistic Regression convergence
warnings occurred; these warnings are promoted to errors during fitting. Two complete
pipeline runs exited 0. All 28 generated data/model/prediction/metric/visualization artifacts
matched byte-for-byte; aggregate manifest hash:
`bf20da9f8619b252b734f790c96f1b534668e531e5a6fc5c6ff38edca9df5163`.
This confirms prediction and metric reproducibility as well as serialized model/specification
reproducibility for these runs. The 220-file pre-implementation manifest and the pipeline's
292-file protected-file guard both remained unchanged.

Final validation exited 0 for `python -m pytest -q` (64 passed), `ruff check .`, and
`python -m pip check`. These repeatability and gate results do not overcome the small,
episode-clustered final test sample.

The pipeline also writes horizon-specific target files, a row-level origin/split manifest,
and a feature-eligibility table under `data/processed/stage4/` and
`artifacts/metrics/early_warning/`. Diagnostic figures include class distribution, observed
episodes, PR/ROC curves, confusion matrices, calibration, selected-model feature importance,
configuration comparisons, and final-test warning timelines under
`visualizations/early_warning/`.

## Feature-importance evidence

Importance is model-specific descriptive association, not causal contribution. Logistic
coefficients are in standardized input units; tree importances are impurity/split importances.
They must not be interpreted as structural economic effects.

| configuration   | model               |   horizon_months | feature                 |   importance | importance_method                 |
|:----------------|:--------------------|-----------------:|:------------------------|-------------:|:----------------------------------|
| C0              | logistic_regression |                1 | cpi_change_1m           |       -0.187 | standardized_logistic_coefficient |
| C0              | logistic_regression |                1 | cpi_lag_1               |        1.422 | standardized_logistic_coefficient |
| C0              | logistic_regression |                1 | cpi_lag_12              |       -1.107 | standardized_logistic_coefficient |
| C0              | logistic_regression |                1 | cpi_lag_3               |       -0.586 | standardized_logistic_coefficient |
| C0              | logistic_regression |                1 | cpi_lag_6               |        0.957 | standardized_logistic_coefficient |
| C0              | logistic_regression |                1 | cpi_mean_3m             |        0.826 | standardized_logistic_coefficient |
| C0              | logistic_regression |                1 | cpi_volatility_6m       |        0.556 | standardized_logistic_coefficient |
| C0              | random_forest       |                1 | cpi_change_1m           |        0.078 | tree_feature_importance           |
| C0              | random_forest       |                1 | cpi_lag_1               |        0.350 | tree_feature_importance           |
| C0              | random_forest       |                1 | cpi_lag_12              |        0.077 | tree_feature_importance           |
| C0              | random_forest       |                1 | cpi_lag_3               |        0.126 | tree_feature_importance           |
| C0              | random_forest       |                1 | cpi_lag_6               |        0.096 | tree_feature_importance           |
| C0              | random_forest       |                1 | cpi_mean_3m             |        0.224 | tree_feature_importance           |
| C0              | random_forest       |                1 | cpi_volatility_6m       |        0.048 | tree_feature_importance           |
| C0              | xgboost             |                1 | cpi_change_1m           |        0.107 | tree_feature_importance           |
| C0              | xgboost             |                1 | cpi_lag_1               |        0.362 | tree_feature_importance           |
| C0              | xgboost             |                1 | cpi_lag_12              |        0.060 | tree_feature_importance           |
| C0              | xgboost             |                1 | cpi_lag_3               |        0.107 | tree_feature_importance           |
| C0              | xgboost             |                1 | cpi_lag_6               |        0.114 | tree_feature_importance           |
| C0              | xgboost             |                1 | cpi_mean_3m             |        0.215 | tree_feature_importance           |
| C0              | xgboost             |                1 | cpi_volatility_6m       |        0.035 | tree_feature_importance           |
| C1              | logistic_regression |                1 | cpi_change_1m           |       -0.032 | standardized_logistic_coefficient |
| C1              | logistic_regression |                1 | cpi_lag_1               |        0.998 | standardized_logistic_coefficient |
| C1              | logistic_regression |                1 | cpi_lag_12              |       -0.772 | standardized_logistic_coefficient |
| C1              | logistic_regression |                1 | cpi_lag_3               |       -0.104 | standardized_logistic_coefficient |
| C1              | logistic_regression |                1 | cpi_lag_6               |        0.832 | standardized_logistic_coefficient |
| C1              | logistic_regression |                1 | cpi_mean_3m             |        0.671 | standardized_logistic_coefficient |
| C1              | logistic_regression |                1 | cpi_volatility_6m       |        0.620 | standardized_logistic_coefficient |
| C1              | logistic_regression |                1 | fx_cumulative_return_3m |        0.198 | standardized_logistic_coefficient |
| C1              | logistic_regression |                1 | fx_log_return_1m        |        0.025 | standardized_logistic_coefficient |
