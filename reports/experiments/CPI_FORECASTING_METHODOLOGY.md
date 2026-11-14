# CPI Inflation Forecasting Methodology

## Research question and target

Does incorporating exchange-rate and imported-cost information improve forecasts of Indian CPI
inflation compared with CPI-history-only models? The target is the **published All India, Combined,
CPI General year-on-year inflation rate** (`inflation_value`), in percentage points. The CPI index
is not substituted or used as a calculated target.

The target used is the longest contiguous published-rate segment,
2014-01-01 through
2024-12-01
(132 observations). A forecast from origin
month t and horizon h targets CPI inflation at month t+h.

## Information sets

- **C0:** CPI published inflation lags 1, 2, 3, 6, and 12 months.
- **C1:** C0 plus lagged Brent monthly USD-per-barrel level and monthly percentage change
  (lags 1, 2, 3, 6, 12).
- **C2:** C0 plus the ARIMA(0,1,1) USD/INR forecast for t+h and its predicted percentage change
  relative to the origin FX level. Actual future FX observations are never substituted. The FX
  archive retains a separate random-walk forecast benchmark.
- **C3:** C0 plus lagged Brent-INR proxy level and percentage change (lags 1, 2, 3, 6, 12).
  This is an approximate imported-cost proxy, not actual landed crude cost or an official
  import-price index.

These are separate nested comparisons; C1, C2, and C3 are not combined.

## Models

Each configuration/horizon uses an autoregressive distributed-lag OLS model, SARIMAX, Elastic Net,
Random Forest, and XGBoost. The CPI persistence baseline forecasts the last published inflation
value available before each origin and is reported under C0. SARIMAX uses order
(1, 0, 0) and seasonal order
(0, 0, 0, 12); CPI seasonal
history is also represented explicitly by its 12-month lag. SARIMAX is refit at each origin and
forecasts recursively through the horizon using only exogenous features dated no later than that
origin. It is not supplied with future realized Brent, FX, or CPI predictors.

Elastic Net scaling is inside the model pipeline. Random Forest and XGBoost use seed
42, single-thread execution, and constrained parameter grids recorded in the
machine-readable metadata.

## Validation and metric protocol

Origin samples are chronologically partitioned approximately 70% training, 15% validation, and 15%
final test. Hyperparameters are tuned only in three expanding folds within the initial training
block; folds purge target labels not available before their validation origin. Models are refit at
each test origin using only outcomes whose target month precedes that origin. Configurations use
common origins and target months within each horizon.

Metrics are MAE, RMSE, test-mean-referenced out-of-sample R-squared, bias
(`prediction - actual`), and MAPE only when every actual is at least 1 percentage point in absolute
value. Negative R-squared is permitted. Forecast errors overlap for 3- and 6-month horizons;
comparisons are descriptive and no Diebold-Mariano test is reported.

## Assumptions and limitations

The data have observation months but no complete historical release timestamp or vintage archive.
The experiment is retrospective and observation-date based, not a genuine real-time backtest. The
published CPI rate is missing throughout calendar 2025; the 2026 segment has only nine observations.
The analysis therefore uses the uninterrupted 2014–2024 published-rate segment and does not bridge
or silently calculate missing inflation values. See `CPI_DATA_AND_FEATURE_AVAILABILITY.md` and
`STAGE1_INDEPENDENT_RESEARCH_AUDIT.md` for source and prior-stage context.
