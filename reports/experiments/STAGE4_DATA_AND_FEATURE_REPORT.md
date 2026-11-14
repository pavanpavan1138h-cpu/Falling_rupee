# Stage 4 Data and Feature Report

## Evidence and scope

The pipeline reads existing processed source files only. It does not modify source datasets,
prior-stage outputs, or the shared feature-engineering module. No synthetic observations are
created. Source release timestamps and historical vintages remain unverified, so this is a
retrospective, reference-month-safe analysis rather than a real-time backtest.

| Source        | File                                     | Use                                                    |
|:--------------|:-----------------------------------------|:-------------------------------------------------------|
| Published CPI | data\processed\cpi_monthly_clean.csv     | All India / Combined / CPI (General) / inflation_value |
| USD/INR       | data/processed/usd_inr_monthly_clean.csv | Monthly INR per USD source levels                      |
| Brent         | data/processed/brent_monthly_clean.csv   | Monthly USD/barrel source levels                       |

The target is the published All India / Combined / CPI (General) `inflation_value`. The CPI
index is not substituted. The selected continuous segment is 2014-01
through 2024-12 (132 months);
the 2025 gap and separate 2026 segment are excluded.

## Outcome and feature samples

For horizon `h`, each row predicts the published inflation rate in `target_month`, which equals
`forecast_origin + h`. A target is elevated exactly when it is strictly greater than 6.0%;
the exact 6.0% boundary is non-elevated. All feature reference months end at
`forecast_origin - 1`.

| Set   |   N |   Elevated |   Non-elevated | Origin start   | Origin end   | Target start   | Target end   |
|:------|----:|-----------:|---------------:|:---------------|:-------------|:---------------|:-------------|
| C0_1m | 119 |         29 |             90 | 2015-01-01     | 2024-11-01   | 2015-02-01     | 2024-12-01   |
| C1_1m | 119 |         29 |             90 | 2015-01-01     | 2024-11-01   | 2015-02-01     | 2024-12-01   |
| C2_1m | 119 |         29 |             90 | 2015-01-01     | 2024-11-01   | 2015-02-01     | 2024-12-01   |
| C3_1m | 119 |         29 |             90 | 2015-01-01     | 2024-11-01   | 2015-02-01     | 2024-12-01   |
| C0_3m | 117 |         29 |             88 | 2015-01-01     | 2024-09-01   | 2015-04-01     | 2024-12-01   |
| C1_3m | 117 |         29 |             88 | 2015-01-01     | 2024-09-01   | 2015-04-01     | 2024-12-01   |
| C2_3m | 117 |         29 |             88 | 2015-01-01     | 2024-09-01   | 2015-04-01     | 2024-12-01   |
| C3_3m | 117 |         29 |             88 | 2015-01-01     | 2024-09-01   | 2015-04-01     | 2024-12-01   |
| C0_6m | 114 |         29 |             85 | 2015-01-01     | 2024-06-01   | 2015-07-01     | 2024-12-01   |
| C1_6m | 114 |         29 |             85 | 2015-01-01     | 2024-06-01   | 2015-07-01     | 2024-12-01   |
| C2_6m | 114 |         29 |             85 | 2015-01-01     | 2024-06-01   | 2015-07-01     | 2024-12-01   |
| C3_6m | 114 |         29 |             85 | 2015-01-01     | 2024-06-01   | 2015-07-01     | 2024-12-01   |

## Prespecified configurations

| Configuration   | Predictor groups                                                                                                                                                                                                             |   Feature count |
|:----------------|:-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------------:|
| C0              | cpi_lag_1, cpi_lag_3, cpi_lag_6, cpi_lag_12, cpi_change_1m, cpi_mean_3m, cpi_volatility_6m                                                                                                                                   |               7 |
| C1              | cpi_lag_1, cpi_lag_3, cpi_lag_6, cpi_lag_12, cpi_change_1m, cpi_mean_3m, cpi_volatility_6m, fx_log_return_1m, fx_cumulative_return_3m, fx_volatility_6m                                                                      |              10 |
| C2              | cpi_lag_1, cpi_lag_3, cpi_lag_6, cpi_lag_12, cpi_change_1m, cpi_mean_3m, cpi_volatility_6m, fx_log_return_1m, fx_cumulative_return_3m, fx_volatility_6m, brent_log_return_1m, brent_cumulative_return_3m                     |              12 |
| C3              | cpi_lag_1, cpi_lag_3, cpi_lag_6, cpi_lag_12, cpi_change_1m, cpi_mean_3m, cpi_volatility_6m, fx_log_return_1m, fx_cumulative_return_3m, fx_volatility_6m, brent_inr_proxy_log_return_1m, brent_inr_proxy_cumulative_return_3m |              12 |

## Feature construction, rationale, and timing

| Feature                                        | Construction                                                       | Rationale                                      | Availability/leakage control                                              |
|:-----------------------------------------------|:-------------------------------------------------------------------|:-----------------------------------------------|:--------------------------------------------------------------------------|
| CPI published-inflation lags                   | y[t-1], y[t-3], y[t-6], y[t-12]                                    | Inflation persistence and recent price level   | Published CPI history only through t-1                                    |
| CPI change, trailing mean, trailing volatility | y[t-1]-y[t-2]; mean of y[t-1:t-3]; sample SD of y[t-1:t-6]         | Recent acceleration, level, and instability    | Trailing windows end at t-1; no centered windows                          |
| USD/INR one-month log return                   | 100 * (ln(FX[t-1]) - ln(FX[t-2]))                                  | Positive values indicate INR depreciation      | Source reference months precede origin; no future FX                      |
| USD/INR three-month cumulative return          | Sum of three consecutive monthly FX log returns through t-1        | Accumulated depreciation/appreciation          | No gap bridging; all three months precede origin                          |
| USD/INR six-month volatility                   | Sample SD of six consecutive monthly FX log returns through t-1    | Recent exchange-rate instability               | Trailing window ends at t-1                                               |
| Brent USD log returns                          | 100 * log change in USD/barrel level; one-month and 3-month sum    | Lagged international oil-cost signal           | Only source levels dated no later than t-1                                |
| Brent-INR proxy log returns                    | Brent USD/barrel * USD/INR, then one-month and 3-month log changes | Approximate rupee cost proxy for an oil barrel | Lagged through t-1; not actual landed import cost; mechanically embeds FX |

C0 is CPI history only. C1 adds lagged USD/INR information. C2 adds lagged Brent USD movements
to C1. C3 adds the lagged Brent-INR product proxy to C1 as an alternative imported-cost signal.
The proxy mechanically combines Brent USD/barrel and USD/INR; it is not actual landed import
cost and excludes freight, insurance, taxes, contracts, quality, and other costs. The feature
matrix recomputes calendar-safe returns and trailing summaries from unchanged source levels;
it does not use the pre-engineered, unit-ambiguous Brent volatility field.

The primary features are CPI lags at 1, 3, 6, and 12 months, a one-month change, a trailing
three-month mean and six-month standard deviation; USD/INR one-month log return, trailing
three-month cumulative log return and six-month return volatility; and, in C2/C3, one-month and
three-month Brent or Brent-INR proxy log returns. All trailing windows end at `t-1`. The FX sign
is explicit: a positive log return means INR depreciation. No repo, NEER/REER, WPI, realized
future FX, prior-stage predictions, or target-month predictors enter the primary model.

## Timing and data integrity checks

- Every target month equals the origin plus the stated horizon; each predictor ends before origin.
- CPI source months are unique and the selected published series is consecutive.
- Market source levels are aligned by calendar month and missing months are rejected, not filled.
- All four configurations share identical origins and target months within each horizon.
- Data source and prior-stage integrity hashes are recorded in
  `artifacts/metrics/early_warning/stage4_run_metadata.json`.
