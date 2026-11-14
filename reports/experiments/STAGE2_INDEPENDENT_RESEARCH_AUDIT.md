# Stage 2 Independent Research Audit

**Scope:** CPI inflation forecasting information sets C0–C3  
**Audit date:** 2026-11-10  
**Stage 3:** Not started

## 1. Executive assessment

The Stage 2 target, horizon mapping, feature separation, expanding-origin fitting, and
configuration comparisons were traced through source code and checked against the generated
prediction and metadata files. The CPI target is the published All India / Combined / CPI
(General) inflation rate, not the CPI index. The analysis uses the uninterrupted 132-month
segment January 2014–December 2024; it does not join the separate nine-month 2026 segment over
the 2025 gap.

The C0–C3 feature lists match their stated definitions. Historical FX inputs use an ARIMA(0,1,1)
forecast produced from FX observations no later than its forecast origin. Thirteen available
Stage 1 forecasts were reused; each matches an independent fixed-specification refit exactly.
Stage 1 selected the ARIMA order by AIC on its initial training partition, not by final-test
forecast performance or CPI outcomes. This does not introduce test-outcome selection
contamination into C2.

Independent paired recalculation confirms 18 common forecast-origin/target pairs per horizon.
Incremental predictive value is mixed and model dependent; it is not evidence of an economic
causal effect. The experiment is retrospective rather than a real-time backtest, has only 18
test targets per horizon, and cannot support robust extreme-episode or statistical-significance
claims.

**Final classification: VERIFIED WITH LIMITATIONS.** No material implementation defect requiring
a Stage 2 code correction was identified. The following limits must remain explicit: absent
historical release timestamps/vintages, short and overlapping test errors, lack of prediction
intervals, and no causal interpretation.

## 2. CPI target validity

The loader selects `state == All India`, `sector == Combined`, and `division == CPI (General)`,
then reads the published `inflation_value`. It never uses `index_value` as a replacement or
calculates substitute inflation.

Verified target segments:

| Published segment | Observations | Audit result |
|---|---:|---|
| 2014-01 through 2024-12 | 132 consecutive months | Used |
| 2026-01 through 2026-09 | 9 consecutive months | Kept separate; not modeled |

The 2025 gap is not interpolated or concatenated across. Duplicate monthly target dates are
rejected, and the feature-frame builder checks the selected target calendar is contiguous.
For each horizon `h ∈ {1, 3, 6}`, origin month `t` maps to target month `t+h`; the observed
prediction archive has the expected target date and actual value for every saved forecast.

## 3. C0/C1/C2/C3 feature integrity

Inspection of the frame builder, actual fitted-model feature lists in run metadata, and the
prediction-generation path confirms:

| Set | Features actually supplied to fitted models |
|---|---|
| C0 | CPI inflation lags 1, 2, 3, 6, 12 |
| C1 | C0 plus lagged Brent USD level and monthly percentage change, each at lags 1, 2, 3, 6, 12 |
| C2 | C0 plus forecast USD/INR level at `t+h` and its forecast percentage change from the origin level |
| C3 | C0 plus lagged Brent-INR proxy level and percentage change, each at lags 1, 2, 3, 6, 12 |

The fitted-model metadata contains 5, 15, 7, and 15 predictors for C0, C1, C2, and C3,
respectively, for every horizon. No realized Brent, FX, or proxy column is silently carried into
another information set. The Brent-INR measure is correctly characterized as an approximate
proxy, not landed import cost or an official import-price series.

## 4. FX forecast provenance and nested selection

The FX archive contains forecast origin, target date, horizon, forecast, origin FX level, model,
and provenance for both ARIMA and random-walk rows. Archive metadata records 396 fixed-specification
ARIMA origin/horizon forecasts in total: 383 generated historically and 13 reused from Stage 1;
13 Stage 1 random-walk rows are also reused.

For historical rows, source code fits ARIMA(0,1,1) only on USD/INR observations dated no later
than the origin and uses the direct `h`-step forecast. The random-walk benchmark uses the origin
level. For reused rows, the origin/target/horizon key must match. Independent refits at all 13
reused ARIMA origin/horizon pairs gave exactly the same predicted value (difference 0 at recorded
precision), and every recorded origin FX level matched the source panel.

Stage 1's saved ARIMA specification files identify selection as “AIC on the initial training
partition only”; the Stage 1 implementation confirms that AIC search uses the initial training
block, then refits the selected order through each forecast origin. The selected order was
(0,1,1) for all horizons. It was not selected using final-test forecast performance or Stage 2
CPI test outcomes. One reused Stage 1 ARIMA forecast per horizon falls on a Stage 2 final-test
origin; those forecasts are still generated without future FX and are exactly equivalent to the
fixed-specification historical refit. Therefore reuse does not contaminate Stage 2 test selection.

The FX forecasts are conventional historical rolling-origin forecasts, not genuine real-time
forecasts: release dates and historical data vintages are unavailable. The separate random-walk
series is retained for FX benchmarking but is not used as a C2 predictor.

## 5. Forecast-origin and horizon alignment

The saved CPI predictions have 1,134 rows. Every emitted model/configuration/horizon group has
18 test forecasts; for every forecast, `target_date` is exactly `forecast_origin + horizon`
calendar months, and `error == predicted - actual`. C2's ARIMA forecast is joined on all three
keys: forecast origin, target date, and horizon. Its percentage change is computed relative to
the origin FX level.

CPI and Brent/proxy predictors are backward row lags over the contiguous monthly target calendar.
There are no centered rolling features. At origin `t`, CPI, Brent, and Brent-INR predictors use
observations through `t-1`; C2 uses a forecast produced at `t`. SARIMAX's recursive exogenous
path uses the feature rows for historical origins through the current origin; it does not receive
future realized exogenous values. Its forecast path includes the intervening target months so its
last forecast corresponds to `t+h`.

No archived release timestamps establish that nominal-month source observations were actually
published by each origin. Thus the feature calendar prevents target-month/future observation
leakage but does not establish a true real-time information set.

## 6. Chronological validation and leakage

The eligible origins are ordered and partitioned into approximately 70% initial training, 15%
validation, and 15% final test. The test target months are July 2023–December 2024, 18 per
horizon. C0–C3 use the same common origins and target months within each horizon.

Elastic Net, Random Forest, and XGBoost hyperparameters are selected by three expanding
`TimeSeriesSplit` folds inside the initial training block. Training rows are purged unless their
target month is strictly before the first validation origin. Hyperparameter selection does not
use the validation or final test outcomes. The validation outcomes enter later test-origin refits
only after their target dates precede that origin. At every test origin, supervised training rows
must have both an earlier origin and a target date earlier than the current origin.

Scaling is inside the Elastic Net pipeline, so each fold fits its own scaler on its training rows.
SARIMAX also fits its exogenous scaler on the available training rows only. No random splitting is
used. Code and generated metadata support the stated leakage controls.

## 7. Models and metric implementation

Implemented models are autoregressive distributed-lag OLS (linear regression on the
configuration's lagged predictors), SARIMAX, Elastic Net, Random Forest, and XGBoost; C0 also
includes CPI persistence. Persistence uses the last CPI target value known before the forecast
origin. SARIMAX uses order `(1,0,0)` and seasonal order `(0,0,0,12)`, refits at each test origin,
and forecasts recursively with the origin-safe feature path.

The recorded search grids are:

- Elastic Net: `alpha ∈ {0.01, 0.1, 1.0}`, `l1_ratio ∈ {0.1, 0.5, 0.9}`.
- Random Forest: 100/200 trees, depth 2/4, leaf size 2/4.
- XGBoost: 100/200 trees, depth 2/3, learning rate 0.03/0.06, subsample 0.8/1.0.
- Random seed 42; tree models and grid search run single-threaded.

Selected training-only hyperparameters in the saved metadata:

| Set / horizon | Elastic Net α / l1 | Random Forest trees / depth / leaf | XGBoost trees / depth / learning rate / subsample |
|---|---|---|---|
| C0 / 1m | 0.1 / 0.9 | 200 / 2 / 2 | 100 / 2 / 0.03 / 0.8 |
| C0 / 3m | 1.0 / 0.1 | 100 / 4 / 4 | 100 / 2 / 0.03 / 0.8 |
| C0 / 6m | 0.1 / 0.1 | 200 / 2 / 4 | 100 / 2 / 0.03 / 0.8 |
| C1 / 1m | 1.0 / 0.1 | 200 / 4 / 4 | 100 / 2 / 0.03 / 0.8 |
| C1 / 3m | 0.1 / 0.9 | 100 / 4 / 4 | 100 / 2 / 0.03 / 1.0 |
| C1 / 6m | 1.0 / 0.9 | 100 / 4 / 4 | 100 / 3 / 0.03 / 1.0 |
| C2 / 1m | 0.1 / 0.9 | 200 / 4 / 2 | 100 / 3 / 0.06 / 0.8 |
| C2 / 3m | 1.0 / 0.5 | 100 / 2 / 4 | 100 / 2 / 0.03 / 0.8 |
| C2 / 6m | 1.0 / 0.9 | 100 / 2 / 2 | 100 / 3 / 0.03 / 1.0 |
| C3 / 1m | 1.0 / 0.1 | 200 / 4 / 4 | 100 / 2 / 0.03 / 1.0 |
| C3 / 3m | 0.1 / 0.9 | 200 / 4 / 4 | 100 / 3 / 0.03 / 0.8 |
| C3 / 6m | 1.0 / 0.9 | 100 / 2 / 4 | 100 / 3 / 0.03 / 1.0 |

The complete JSON specifications are in
[`stage2_model_configurations.json`](../../artifacts/models/inflation/stage2_model_configurations.json).

The metric code and saved prediction errors agree on MAE, RMSE, bias (`prediction - actual`),
and MAPE (mean absolute percentage error, emitted only when every absolute actual is at least
1 percentage point). MAPE is secondary because percentage errors can be unstable for inflation
near zero.

The reported `r2` is scikit-learn's held-out `r2_score`, whose denominator uses the held-out
actual mean. It is correctly calculated as a test-set coefficient of determination, but should
not be interpreted as a training-mean benchmark-relative forecasting R-squared. Its value is
sample-dependent and does not establish improvement over C0.

Elastic Net CV convergence-warning counts are zero for all 12 configuration/horizon runs.
SARIMAX converged at all 18 of 18 test origins in each configuration/horizon. Residual Ljung–Box
outputs are exploratory; overlapping multi-step errors violate the simple independence
interpretation. No Diebold–Mariano test or prediction intervals were produced. With 18 paired
observations and overlapping 3-/6-month errors, deferring significance claims is appropriate.

## 8. Independent incremental predictive-value recalculation

The following deltas were recomputed directly from the saved forecast archive, paired by both
forecast origin and target date. All 15 model/horizon rows have 18 common pairs. Negative deltas
indicate lower error than the same model under C0; positive deltas indicate higher error. Values
are percentage points of CPI inflation.

| Horizon | Model | N | C1 ΔMAE | C1 ΔRMSE | C2 ΔMAE | C2 ΔRMSE | C3 ΔMAE | C3 ΔRMSE |
|---:|---|---:|---:|---:|---:|---:|---:|---:|
| 1 | Autoregression | 18 | +0.0326 | +0.0216 | +0.1060 | +0.0322 | +0.0941 | +0.0373 |
| 1 | Elastic Net | 18 | -0.1644 | -0.1762 | +0.0607 | +0.0152 | -0.1296 | -0.1782 |
| 1 | Random Forest | 18 | +0.1267 | +0.1139 | +0.0888 | +0.0545 | +0.1627 | +0.1261 |
| 1 | SARIMAX | 18 | +0.1201 | +0.1861 | +0.0406 | +0.0004 | +0.1304 | +0.1956 |
| 1 | XGBoost | 18 | +0.0289 | -0.0198 | +0.1885 | +0.1695 | +0.0227 | -0.0770 |
| 3 | Autoregression | 18 | +0.0968 | -0.0067 | +0.2052 | +0.0685 | +0.1597 | +0.0032 |
| 3 | Elastic Net | 18 | +0.1223 | +0.0440 | -0.0127 | +0.0037 | +0.1593 | +0.0022 |
| 3 | Random Forest | 18 | +0.1475 | +0.0252 | +0.1679 | +0.0043 | +0.1038 | -0.0073 |
| 3 | SARIMAX | 18 | +0.0182 | -0.0677 | +0.0417 | -0.0057 | +0.0063 | -0.0815 |
| 3 | XGBoost | 18 | +0.0269 | -0.0856 | +0.0600 | -0.0280 | +0.0319 | -0.0562 |
| 6 | Autoregression | 18 | -0.0378 | -0.0810 | +0.7610 | +0.8823 | +0.1803 | +0.1439 |
| 6 | Elastic Net | 18 | -0.2187 | -0.0964 | -0.2187 | -0.0964 | -0.2187 | -0.0964 |
| 6 | Random Forest | 18 | -0.1107 | -0.1227 | +0.0565 | +0.0112 | -0.1184 | -0.1387 |
| 6 | SARIMAX | 18 | +0.2309 | +0.3068 | +0.0254 | +0.0187 | +0.2949 | +0.3505 |
| 6 | XGBoost | 18 | -0.1279 | -0.1454 | +0.1412 | +0.1513 | -0.0842 | -0.0591 |

The independent deltas match the generated incremental-comparison file to numerical precision.
No imported-cost configuration improves both MAE and RMSE consistently across models and
horizons. For C0 persistence, C1–C3 comparisons are unavailable by construction because that
baseline is emitted only under C0. None of these predictive comparisons implies that imported
costs have no economic effect; predictive performance is not a causal test.

The minimum-RMSE model/configuration in the saved comparison output is:

| Horizon | Configuration / model | N | MAE | RMSE | Test-set R² | Bias |
|---:|---|---:|---:|---:|---:|---:|
| 1 month | C3 / Elastic Net | 18 | 0.7982 | 1.0514 | -0.3537 | -0.0474 |
| 3 months | C0 / Elastic Net | 18 | 0.6325 | 0.8928 | 0.0240 | -0.2003 |
| 6 months | C3 / Random Forest | 18 | 0.7863 | 0.9575 | -0.1226 | 0.3731 |

## 9. Robustness and episode findings

Episode thresholds use the purged initial training outcomes: high inflation is the training
90th percentile (6.552, 6.613, and 6.668 percentage points for 1-, 3-, and 6-month horizons);
Brent spikes use the training 95th percentile of Brent monthly percentage changes (18.656,
17.346, and 17.755). Episode outcomes do not set these thresholds.

Each horizon has only two high-inflation test forecasts, in one contiguous run. Every model's
mean error on those selected observations is negative. The Brent-spike diagnostic has zero
qualifying test observations at every horizon; the CSV reports zero forecasts and zero runs,
with undefined error metrics. These diagnostics are too small to support robust episode
rankings. Early/late test-window summaries are descriptive splits of the same short test period,
not independent validation.

## 10. Reproducibility and data integrity

Command successfully run twice from the project root:

`.\.venv\Scripts\python.exe -m src.forecasting.inflation.run_experiments`

Environment recorded in Stage 2 metadata: Python 3.13.0, NumPy 2.5.4, pandas 3.1.1,
scikit-learn 1.9.1, statsmodels 0.15.0, XGBoost 3.4.1; seed 42.

Both experiment processes exited 0 (164.3 seconds and 103.6 seconds). The generated output
manifest covered 85 files. Prediction CSVs, metric CSVs, reports, visualizations, run metadata,
FX archive, and model-configuration JSON were byte-identical. Exactly 12 files differed: the
fitted SARIMAX pickle for each of four configurations and three horizons. The other 73 files
were identical. Thus forecast/metric/specification reproducibility is verified, but binary
reproducibility of fitted SARIMAX artifacts is not. The cause of the pickle-byte variation was
not isolated; numerical equivalence of the serialized fitted SARIMAX state across runs is not
claimed.

Final-run SHA-256 values (each listed output was identical in both runs):

| Output | SHA-256 |
|---|---|
| CPI predictions | `8148a5bd18afa1f3c56da1ad87f53dd55fc368b48c1912c79abb4b0bcd61192e` |
| CPI model comparison | `bc73a263ebff906b2565e7e855fecd4f7c14ca0beba8d1084d4b49a5d4f15b94` |
| Incremental comparison | `99de48455be5e48f6d62648046bdbfa7543710483a1b993c1a86f7339b497490` |
| FX forecast archive | `42d8214e795a70b147761fe697004a0f158612324e553f65202c1da8b113a0e5` |
| Run metadata | `18d78fb9dc38485c4117541a1196fb3fc950a6d319b669eadc15a9e35c553d05` |
| Model configuration JSON | `4e8150f21c57276eb80f1dfc0f654348e896639a6d0937713ecc296f68f61796` |

The Stage 2 output-hash comparison returned exit 2 because it correctly detected those 12
non-identical SARIMAX pickle files; both underlying experiment runs succeeded. Raw and processed
data hashes were unchanged for all 30 files after each run, and the Stage 1 FX prediction archive
hash was unchanged.

The direct script-path invocation was also attempted once but exited 1 before pipeline execution
with `ModuleNotFoundError: No module named 'src'`; the module invocation above is the successful
project-root command. This is an invocation/import-path issue, not a forecasting result.

The pipeline itself hashes all files under `data/raw/` and `data/processed/` before and after
each run. This independent audit also compares their file hashes across both runs. The Stage 1
FX prediction archive is input-only and must remain unchanged.

## 11. Defects corrected

No Stage 2 implementation defect requiring a code correction was substantiated. In particular,
the potential C2 Stage 1 reuse concern was investigated rather than assumed: Stage 1 ARIMA order
selection is training-only, reused forecasts reproduce exactly from origin-only histories, and
the CPI test outcomes do not participate in that selection. No generated predictions, metrics,
model configurations, or datasets were manually edited during the audit.

Metric terminology is qualified above: the existing `r2` is test-set `r2_score`, not a
training-mean-relative forecasting R-squared. Forecast comparisons are therefore based on paired
MAE/RMSE deltas, not on treating that R² as an incremental benchmark.

## 12. Final quality gates

Executed from the project root using the project virtual environment:

| Command | Result | Exit code |
|---|---|---:|
| `.\.venv\Scripts\python.exe -m pytest -q` | Completed successfully (`[100%]`) | 0 |
| `.\.venv\Scripts\ruff.exe check .` | All checks passed | 0 |
| `.\.venv\Scripts\python.exe -m pip check` | No broken requirements found | 0 |
| `.\.venv\Scripts\python.exe -m src.forecasting.inflation.run_experiments` | Two completed runs; output-hash comparison found 12 non-identical SARIMAX pickle artifacts | 0 each |

The direct script-path invocation exited 1 during import before running the experiment. The
separate hash-comparison harness exited 2 because fitted SARIMAX pickle bytes differed; this is
reported rather than counted as a pipeline failure.

## 13. Remaining limitations

1. Historical release dates, publication delays, and source vintages/revisions are unavailable;
   this is not a genuine real-time backtest.
2. The final test has only 18 outcomes per horizon; 3-/6-month monthly-origin errors overlap.
   Rankings and episode conclusions are uncertain.
3. There are only two high-inflation targets per horizon and no Brent-spike targets in the test.
4. No prediction intervals or calibrated uncertainty estimates are available.
5. No Diebold–Mariano or other significance test was conducted; the sample and dependent errors
   do not support a reliable inference here.
6. Held-out R² uses the held-out sample mean and is descriptive; it is not a training-mean
   benchmark comparison.
7. Fitted SARIMAX pickle artifacts are not byte-reproducible across consecutive runs; forecasts,
   metrics, reports, metadata, model configuration JSON, and other artifacts are reproducible.
   The numerical equivalence of those differing serialized fit states was not established.
8. Imported-cost variables are predictors only. No causal effect or pass-through estimate is
   identified.
9. The 2026 segment is too short and remains excluded; published inflation is not fabricated to
   bridge the 2025 gap.

## 14. Final research-readiness classification

**VERIFIED WITH LIMITATIONS**

The audited implementation and outputs satisfy the stated retrospective Stage 2 forecasting
design: published target validity, origin/horizon alignment, feature-set integrity, FX
forecast-origin provenance, chronological splits, training-only tuning/scaling, common-sample
comparisons, and reproducibility are verified. This finding does not establish real-time
availability, stable model superiority, statistical significance, prediction uncertainty, or
causality. Carry the limitations above into any later approved research. **Stage 3 has not been
started; stop for researcher review.**
