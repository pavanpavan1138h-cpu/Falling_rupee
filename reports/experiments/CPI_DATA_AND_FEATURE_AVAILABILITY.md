# CPI Data and Feature Availability

## Verified CPI source facts

- Processed source: `data/processed/cpi_monthly_clean.csv`.
- Selected series: All India / Combined / CPI (General).
- Target: published `inflation_value` only; no substitution from `index_value`.
- Source calendar: 2013-01-01 to
  2026-09-01, 165 monthly rows.
- Published values: 141; missing published values:
  24.
- Continuous published segments:
  `[{"start": "2014-01-01", "end": "2024-12-01", "observations": 132}, {"start": "2026-01-01", "end": "2026-09-01", "observations": 9}]`.
- Chosen segment: 2014-01-01 to
  2024-12-01,
  132 months.
- The 2025 calendar-year gap in published inflation separates the 2024-base back series from the
  2026 current published-rate segment. The latter contains only nine contiguous months, insufficient
  for a separate, comparable train/validation/test experiment. Neither the CPI index nor a
  calculated inflation series is used to bridge the gap.

## Stage 1 FX forecast coverage

The inspected Stage 1 prediction archive contains only its chronological holdout period and does
not cover the Stage 2 historical training and evaluation origins. Stage 1 metadata verifies ARIMA
order (0,1,1) at all three horizons. Stage 2 therefore reuses matching Stage 1 out-of-sample ARIMA
and random-walk predictions where available and constructs the remaining FX archive using fixed
ARIMA(0,1,1) fits through each forecast origin plus a separate random-walk benchmark.

Archive counts: `{"stage1_arima_order_verified": [0, 1, 1], "stage1_predictions_reused_arima": 13, "stage1_predictions_reused_random_walk": 13, "generated_historical_arima_rows": 383, "forecast_origin_count": 132, "horizons": [1, 3, 6], "generated_as_retrospective_not_real_time": true}`. All archive rows include origin, target
month, horizon, model, predicted FX level, origin level, and provenance. Historical rolling-origin
forecasts are not genuine real-time forecasts.

## Common feature coverage by configuration and horizon

| configuration_horizon   |   origins | origin_start   | origin_end   | target_start   | target_end   |   predictor_count |
|:------------------------|----------:|:---------------|:-------------|:---------------|:-------------|------------------:|
| C0_1m                   |       119 | 2015-01-01     | 2024-11-01   | 2015-02-01     | 2024-12-01   |                 5 |
| C1_1m                   |       119 | 2015-01-01     | 2024-11-01   | 2015-02-01     | 2024-12-01   |                15 |
| C2_1m                   |       119 | 2015-01-01     | 2024-11-01   | 2015-02-01     | 2024-12-01   |                 7 |
| C3_1m                   |       119 | 2015-01-01     | 2024-11-01   | 2015-02-01     | 2024-12-01   |                15 |
| C0_3m                   |       117 | 2015-01-01     | 2024-09-01   | 2015-04-01     | 2024-12-01   |                 5 |
| C1_3m                   |       117 | 2015-01-01     | 2024-09-01   | 2015-04-01     | 2024-12-01   |                15 |
| C2_3m                   |       117 | 2015-01-01     | 2024-09-01   | 2015-04-01     | 2024-12-01   |                 7 |
| C3_3m                   |       117 | 2015-01-01     | 2024-09-01   | 2015-04-01     | 2024-12-01   |                15 |
| C0_6m                   |       114 | 2015-01-01     | 2024-06-01   | 2015-07-01     | 2024-12-01   |                 5 |
| C1_6m                   |       114 | 2015-01-01     | 2024-06-01   | 2015-07-01     | 2024-12-01   |                15 |
| C2_6m                   |       114 | 2015-01-01     | 2024-06-01   | 2015-07-01     | 2024-12-01   |                 7 |
| C3_6m                   |       114 | 2015-01-01     | 2024-06-01   | 2015-07-01     | 2024-12-01   |                15 |

All configurations were restricted to common origins within a horizon. Feature counts are CPI
history 5 (C0), CPI+Brent 15 (C1), CPI+predicted FX 7 (C2), and CPI+Brent-INR proxy 15 (C3).

## Availability assumptions

No exact historical CPI, Brent, FX, or macro release timestamps/vintages are available. For the
retrospective observation-date experiment, CPI target lags and commodity/proxy features are lagged
at least one month; C2 is an origin-generated future FX forecast. This prevents target-month
realized values from entering predictors but does not prove that the corresponding source
observations were published by the nominal origin timestamp.
