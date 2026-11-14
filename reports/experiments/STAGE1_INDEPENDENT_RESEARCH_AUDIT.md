# Stage 1 Independent Research Audit

**Research scope:** Monthly USD/INR exchange-rate level forecasts at 1-, 3-, and 6-month horizons  
**Audit status:** Completed; Stage 2 has not been started  
**Decision:** **VERIFIED WITH LIMITATIONS**

## 1. Executive assessment

Independent inspection identified material defects in the initial Stage 1 evaluation: the random-walk benchmark used a stale training-end observation at later test origins, ARIMA forecasts were not aligned to the requested forecast origins and horizons, and directional accuracy was not calculated relative to each forecast origin. The original implementation also did not purge overlapping target labels at validation boundaries, and its reported Elastic Net advantage was not supported by a correctly aligned comparison.

These defects were corrected. The regenerated outputs now compare five implemented approaches on the same 23 target months for each horizon. ARIMA (0,1,1) has the lowest MAE and RMSE at all three horizons, but its gains over the corrected random walk are small. Elastic Net, Random Forest, and XGBoost do not beat the random walk. The final experiment reproduces byte-for-byte across consecutive runs, and hashes confirm that all 30 raw and processed files remained unchanged.

Stage 1 is suitable as a carefully bounded retrospective benchmark, not as evidence of real-time forecasting readiness or a stable model advantage. The short holdout, sparse high-depreciation cases, and unverified historical release timing must be carried forward. No Stage 2 work is authorized or included here.

## 2. Original defects discovered

### 2.1 Stale random-walk benchmark

The original benchmark searched only the training partition for the last observation at or before each test forecast origin. For origins after the training end, it therefore repeatedly forecast from the same old training-end value instead of the latest USD/INR level available at that origin. This was not the intended random-walk level benchmark and made model comparisons invalid.

**Correction:** the benchmark now receives the observed panel and uses the latest USD/INR observation with date no later than the forecast origin. The saved random-walk prediction equals the recorded `origin_value` for every forecast.

### 2.2 ARIMA horizon and origin misalignment

The original code fitted ARIMA once and forecast a sequence across the test set. Those sequential one-step outputs did not represent the requested 1-, 3-, or 6-month-ahead forecast for each listed origin; moreover, the early forecast sequence was compared with targets from a later test block.

**Correction:** order selection uses the initial training block only. At each held-out origin, the selected ARIMA order is refitted on observations available through that origin, and the prediction is taken from the direct `h`-step forecast for that origin.

### 2.3 Incorrect directional accuracy

The original metric compared changes between adjacent rows of actual and predicted test values. That is not forecast direction accuracy for each origin, particularly for overlapping multi-step forecasts.

**Correction:** for each forecast, direction is calculated by comparing `predicted - origin_value` with `actual - origin_value`. A tie in either sign is treated as a direction mismatch.

### 2.4 Horizon-overlapping labels at validation boundaries

The initial design did not remove training rows whose target month reached a validation or test origin. For a multi-month direct target, this can allow training labels to extend into the next evaluation window.

**Correction:** expanding time-series CV folds purge training rows unless their `target_date` is strictly before the first validation origin. Before the final model fit, only pre-test rows whose target dates precede the first test origin are retained. The final test observations are not used in model selection or fitting.

### 2.5 Unsupported prior model ranking

The earlier report described Elastic Net as the leading model based on the defective evaluation. Recalculation with aligned origins, targets, and the corrected benchmark reverses that conclusion: ARIMA is best by MAE and RMSE at all horizons, narrowly ahead of the random walk. The tree models and Elastic Net perform substantially worse.

### 2.6 Artifact reproducibility

The first audit runs exposed tiny Random Forest prediction differences from parallel fitting and non-identical ARIMA pickle bytes despite identical forecast values.

**Correction:** Random Forest fitting is single-threaded. ARIMA is persisted as a canonical JSON specification/parameter artifact rather than a serialized fitted state. Consecutive final runs produced identical hashes for predictions, metrics, metadata, and all 12 model artifacts.

## 3. Tests added or modified

`tests/test_forecasting.py` now tests:

- Calendar-month target alignment and predictor lag availability.
- Rejection of incomplete monthly calendars.
- Invariance of origin-time predictors when target-month inputs are changed.
- Purging training labels that overlap validation origins.
- Chronological train/validation/test ordering.
- The random walk using the latest observation available at the requested origin.
- Direction, MAE, RMSE, bias, and invalid/zero-denominator MAPE behavior.
- Training-only StandardScaler fitting and Elastic Net convergence.
- Exact target-month alignment, common target dates across models, prediction errors, and prediction-to-source values.
- Output columns and presence/content of persisted model artifacts.

The complete suite contains **29 passing tests**.

## 4. Final forecasting methodology

- **Target:** monthly USD/INR level, INR per USD; a rise represents rupee depreciation.
- **Horizon construction:** target month is calendar origin month plus `h`; monthly continuity and unique month dates are validated before row lags are used.
- **Origin-time predictors:** USD/INR levels and changes at lag 0 and lags 1, 2, 3, 6, and 12; Brent, Brent-INR proxy, repo rate, and trade-weighted NEER/REER levels or changes at lags 1, 2, 3, 6, and 12.
- **Machine-learning direct targets:** Elastic Net, Random Forest, and XGBoost estimate the horizon-specific target level from origin-time features. Each model is fit once on the pre-test training sample; test predictors are evaluated at successive origins.
- **ARIMA:** candidates `(0,0,0)`, `(1,0,0)`, `(2,0,0)`, `(1,1,0)`, `(0,1,1)`, `(1,1,1)`, and `(2,1,0)` are compared by training-only AIC. The chosen order is refit at every test origin for a direct `h`-step forecast.
- **Random walk:** forecasts the latest observed exchange-rate level available at each origin.
- **Outer chronological partition:** approximately 70% initial training, 15% validation, 15% final test on each horizon-specific eligible sample. Hyperparameter tuning uses three expanding time-series folds within initial training, with overlapping target labels purged. The validation partition is included in the final pre-test fit only when its target label ends before the first test origin.
- **Feature scaling:** StandardScaler is inside the Elastic Net scikit-learn Pipeline and is fitted separately within each CV fit and again on the final pre-test fit. No scaling is applied to the tree estimators.
- **Search spaces:** Elastic Net `alpha=[0.01, 0.1, 1.0]`, `l1_ratio=[0.1, 0.5, 0.9]`; Random Forest `n_estimators=[200,400]`, `max_depth=[None,5,8]`, `min_samples_leaf=[1,2]`; XGBoost `n_estimators=[200,400]`, `max_depth=[2,3,5]`, `learning_rate=[0.03,0.06]`, `subsample=[0.8,1.0]`. Seed is 42.
- **Metrics:** MAE, RMSE, out-of-sample R-squared, origin-relative directional accuracy, mean forecast error (`predicted - actual`), and MAPE. INR per USD is positive throughout these samples, so MAPE denominators are nonzero; MAPE is secondary because scale-dependent level errors and baseline comparisons are more informative.

The source panel contains 646 monthly rows from January 1973 through October 2026. Complete candidate feature coverage restricts horizon-eligible origins to February 2014 onward. Eligible sample sizes are 152, 150, and 147 for 1-, 3-, and 6-month targets. Each horizon has 23 final test forecasts, and all models at a given horizon use the same target months, December 2024 through October 2026.

| Horizon | Eligible rows | Initial train | Validation | Final pre-test train | Test origins | Common test targets |
|---:|---:|---:|---:|---:|---|---|
| 1 month | 152 | 106 | 23 | 128 | Nov 2024–Sep 2026 | Dec 2024–Oct 2026 |
| 3 months | 150 | 105 | 22 | 124 | Sep 2024–Jul 2026 | Dec 2024–Oct 2026 |
| 6 months | 147 | 102 | 22 | 118 | Jun 2024–Apr 2026 | Dec 2024–Oct 2026 |

The final training label end precedes the first test origin for every horizon: October 2024 < November 2024 for 1M, August 2024 < September 2024 for 3M, and May 2024 < June 2024 for 6M.

## 5. Forecast-origin and target-horizon alignment

The corrected target mapping uses monthly periods rather than assuming an unvalidated shift: `target_date = origin_month + horizon`, and `target_level` is looked up at that calendar month. For example, February 2021 at a 3-month horizon maps to May 2021. Tests verify target values, FX lag 0/1 meaning, macro feature lags beginning at 1, and all saved prediction dates against the source panel.

For every horizon, saved predictions include `forecast_origin`, `target_date`, `origin_value`, `actual`, `predicted`, and `error`. Models share identical test target dates within each horizon. Random-walk predictions equal `origin_value`. ARIMA predicts the requested horizon from each origin rather than a test-block sequence.

## 6. Leakage prevention assessment

**Verified within the conventional monthly panel design:** target construction is calendar-aligned; exchange-rate predictors are observed at or before the forecast-origin month; macro predictors are lagged at least one month; target-month perturbation tests leave origin predictors unchanged; CV and final fitting purge labels that reach or cross validation/test origins; test outcomes are not used to select hyperparameters or ARIMA order.

**Not verified as real-time availability:** the panel date is a monthly reference date, not an archived information timestamp. Historical release dates, revisions, and vintage availability for Brent and macroeconomic series are not incorporated. Lagging these variables one month is a conservative feature alignment convention, not proof that each value was published by the relevant forecast timestamp. Results therefore describe a conventional retrospective experiment, not a genuine real-time backtest.

## 7. Corrected random-walk benchmark

For each origin `t`, all horizons use the random-walk level forecast equal to the latest USD/INR level available at or before `t`. The benchmark is now evaluated on the same 23 origin/target pairs as every other model at each horizon. The previous benchmark, which stayed fixed at the training-end value, is invalid and must not be used.

## 8. Elastic Net convergence findings

The earlier run emitted convergence warnings at the former iteration/tolerance settings; those warnings were not suppressed. The scaler is fitted within each CV pipeline fold. The search was changed to stronger regularization candidates (`alpha` minimum 0.01), `max_iter=200000`, and `tol=1e-5`. The corrected repeated experiment reported **zero tuning convergence warnings** at each horizon; the final fits raised no convergence warning. A focused test also verifies the scaler uses training-only means and the Elastic Net fit converges.

The old Elastic Net ranking is not retained. In corrected test results, Elastic Net is worse than both ARIMA and the random walk at all horizons, so convergence is not a basis for an improvement claim.

## 9. Final model comparison

All rows below use 23 identical held-out target months per horizon. Errors and bias are in INR per USD; directional accuracy is a proportion. Bias is `predicted - actual`, so negative values indicate average underprediction.

| Horizon | Model | MAE | RMSE | OOS R² | Directional accuracy | Mean error / bias |
|---:|---|---:|---:|---:|---:|---:|
| 1M | Random Walk | 0.743717 | 0.925569 | 0.943354 | 0.000000 | -0.486265 |
| 1M | ARIMA | **0.712119** | **0.915490** | **0.944581** | **0.608696** | **-0.378049** |
| 1M | Elastic Net | 1.390170 | 1.653136 | 0.819296 | 0.347826 | -1.309394 |
| 1M | Random Forest | 7.182071 | 8.391189 | -3.655837 | 0.260870 | -7.182071 |
| 1M | XGBoost | 7.419657 | 8.467301 | -3.740681 | 0.260870 | -7.419657 |
| 3M | Random Walk | 1.804609 | 2.081934 | 0.713394 | 0.000000 | -1.493252 |
| 3M | ARIMA | **1.788003** | **2.029120** | **0.727751** | **0.565217** | **-1.378777** |
| 3M | Elastic Net | 5.180218 | 5.779439 | -1.208626 | 0.217391 | -5.180218 |
| 3M | Random Forest | 8.082969 | 9.283175 | -4.698279 | 0.217391 | -8.082969 |
| 3M | XGBoost | 8.193188 | 9.298666 | -4.717313 | 0.217391 | -8.193188 |
| 6M | Random Walk | 3.041226 | 3.479835 | 0.199303 | 0.000000 | -3.033070 |
| 6M | ARIMA | **2.973032** | **3.404570** | **0.233565** | **0.695652** | **-2.937809** |
| 6M | Elastic Net | 6.589316 | 7.378666 | -2.600032 | 0.043478 | -6.589316 |
| 6M | Random Forest | 8.466641 | 9.772982 | -5.315459 | 0.043478 | -8.466641 |
| 6M | XGBoost | 8.260899 | 9.576390 | -5.063932 | 0.043478 | -8.260899 |

**Best model by both MAE and RMSE:** ARIMA at 1M, 3M, and 6M. Relative to the corrected random walk, the RMSE reductions are approximately 1.2%, 2.5%, and 2.2% respectively. These are small gains on a 23-observation holdout; no statistical significance is claimed.

Out-of-sample R-squared uses the test-sample mean as its reference, not the random-walk benchmark. It can be negative and is not a substitute for paired benchmark comparison. The positive values for the level models do not establish economic causality or generalizable predictive superiority.

## 10. Robustness and high-depreciation performance

### Chronological subwindows

For a descriptive stability check, each horizon's 23 test targets was split in chronological order into an 11-observation early half and a 12-observation late half. ARIMA and the random walk had similar RMSEs in both halves, with their ordering changing by horizon/window. Elastic Net did not lead in either half:

| Horizon | Early half: ARIMA / Random Walk / Elastic Net RMSE | Late half: ARIMA / Random Walk / Elastic Net RMSE |
|---:|---:|---:|
| 1M | 0.699 / 0.799 / 1.043 | 1.076 / 1.028 / 2.059 |
| 3M | 1.818 / 1.837 / 3.264 | 2.205 / 2.284 / 7.366 |
| 6M | 1.985 / 1.964 / 3.619 | 4.313 / 4.436 / 9.610 |

These short, post-hoc subwindows are descriptive, not independent validation sets.

### High-depreciation targets

For each horizon, a descriptive threshold was set to the 95th percentile of positive training-period target-minus-origin level changes (INR per USD). Test targets meeting or exceeding the threshold were:

| Horizon | Training 95th percentile threshold | Test target months meeting threshold |
|---:|---:|---|
| 1M | 1.679250 | Mar 2026, May 2026 (n=2) |
| 3M | 3.329200 | May 2026 (n=1) |
| 6M | 5.153695 | May 2026 (n=1) |

| Horizon | Model | High-depreciation n | MAE | RMSE | Bias |
|---:|---|---:|---:|---:|---:|
| 1M | Random Walk | 2 | 2.062700 | 2.062723 | -2.062700 |
| 1M | ARIMA | 2 | 2.098905 | 2.099843 | -2.098905 |
| 1M | Elastic Net | 2 | 3.513145 | 3.523503 | -3.513145 |
| 1M | Random Forest | 2 | 11.791197 | 11.904034 | -11.791197 |
| 1M | XGBoost | 2 | 11.706291 | 11.762627 | -11.706291 |
| 3M | Random Walk | 1 | 4.787700 | 4.787700 | -4.787700 |
| 3M | ARIMA | 1 | 4.876951 | 4.876951 | -4.876951 |
| 3M | Elastic Net | 1 | 9.895238 | 9.895238 | -9.895238 |
| 3M | Random Forest | 1 | 14.383256 | 14.383256 | -14.383256 |
| 3M | XGBoost | 1 | 14.824775 | 14.824775 | -14.824775 |
| 6M | Random Walk | 1 | 6.689100 | 6.689100 | -6.689100 |
| 6M | ARIMA | 1 | 6.552777 | 6.552777 | -6.552777 |
| 6M | Elastic Net | 1 | 11.807278 | 11.807278 | -11.807278 |
| 6M | Random Forest | 1 | 15.067043 | 15.067043 | -15.067043 |
| 6M | XGBoost | 1 | 14.898612 | 14.898612 | -14.898612 |

The episode counts are far too small for a stable claim about extreme depreciation performance. All models materially underpredict these selected target moves.

### Statistical comparison and uncertainty

No Diebold-Mariano test was conducted. There are only 23 paired test errors per horizon; 3- and 6-month forecasts from adjacent monthly origins have overlapping target intervals and serially dependent errors. A defensible test would require an overlap-aware long-run variance estimate and would remain very low-powered at this sample size. Multiple horizons/models further complicate interpretation. The small sample does not justify reporting an inferential test as decisive evidence. No prediction intervals or uncertainty estimates are available.

## 11. Reproducibility results

The complete pipeline was run consecutively in the same environment with seed 42. The final two runs reproduced byte-for-byte across all **17** generated prediction, metric, metadata, and model artifact files:

- Prediction CSVs: identical; SHA-256 `2f3892580d0011bec11d45ac1fb97b0ca43c92ef4f36ee9037ca8f9ff9265452`.
- Metric CSVs: identical; SHA-256 `2b86b2210139161a9928e042d97f483e01cb4e7fbcc76b1a654e933d7e40ca94`.
- Model metadata/specifications: identical; metadata SHA-256 `c5ad74e09fafe8914a02db3b90a30d1b208cbb5545f5b7ceda89abff8a14067f`.
- All 12 saved model artifacts (three canonical ARIMA JSON specifications and nine Elastic Net, Random Forest, and XGBoost fitted-model pickles): identical across runs.
- Environment recorded in metadata: Python 3.13.0, NumPy 2.5.4, pandas 3.1.1, scikit-learn 1.9.1, statsmodels 0.15.0, XGBoost 3.4.1.
- Pipeline command from project root: `.\.venv\Scripts\python.exe src\forecasting\exchange_rate\run_experiments.py`.

Thus both prediction/metric reproducibility and binary artifact reproducibility were verified for this environment. No nondeterministic artifacts remained in these repeated runs.

## 12. Raw and processed data integrity

SHA-256 manifests were calculated before and after the final pipeline run for every file under `data/raw/` and `data/processed/`. All **30** files were unchanged; no file was added or missing. This includes the previously verified processed source data and engineered feature outputs. The experiment writes predictions, metrics, metadata, and model artifacts only to their designated report/artifact locations.

## 13. Final quality gates

Executed from the project root using the project virtual environment:

| Command | Result | Exit code |
|---|---|---:|
| `.\.venv\Scripts\python.exe -m pytest -q` | 29 passed | 0 |
| `.\.venv\Scripts\python.exe -m ruff check .` | All checks passed | 0 |
| `.\.venv\Scripts\python.exe -m pip check` | No broken requirements found | 0 |
| `.\.venv\Scripts\python.exe src\forecasting\exchange_rate\run_experiments.py` | 345 predictions; 15 model-horizon metric rows generated | 0 |

## 14. Remaining limitations and carry-forward conditions

1. **Not a real-time backtest:** historical release timestamps, data vintages, and revisions are unavailable or not modeled. A later real-time evaluation must establish which values were actually known at each origin.
2. **Short final holdout:** 23 observations per horizon produce uncertain rankings and weak inference; the small ARIMA gain over the random walk should not be treated as robust evidence of superiority.
3. **Sparse extremes:** only 1–2 test observations meet the training-derived high-depreciation thresholds.
4. **Overlapping forecast errors:** multi-step monthly-origin errors are dependent. Forecast-comparison tests are deferred until a sufficiently informative design/sample exists.
5. **No uncertainty intervals:** point forecasts only; prediction intervals and calibration have not been evaluated.
6. **Single fixed outer split:** chronological half-sample checks are descriptive. A broader rolling-origin evaluation would better assess stability without using test data for model selection.
7. **Feature interpretation:** lagged Brent, repo, NEER/REER, and exchange-rate features are predictive inputs only; no causal conclusions are supported.
8. **Scope boundary:** this audit does not authorize CPI forecasting, pass-through estimation, classification, persistence analysis, synthetic-data experiments, SHAP, or dashboard work.

## 15. Final research-readiness decision

**VERIFIED WITH LIMITATIONS**

The corrected Stage 1 code, origin/target mapping, benchmark, split discipline, metrics, tests, reproducible outputs, and protected-data integrity checks are verified for the stated conventional monthly backtest. The earlier Elastic Net superiority claim is withdrawn; corrected results identify ARIMA as narrowly best by MAE/RMSE at all horizons, with Random Walk close behind and the machine-learning models materially worse.

This classification does **not** certify real-time information availability, strong generalization, statistical significance, prediction uncertainty, or causal interpretation. Those limitations must be carried forward before any subsequent research stage is considered. **Stage 2 has not been started.**
