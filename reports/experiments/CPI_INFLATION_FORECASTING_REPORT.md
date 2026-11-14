# CPI Inflation Forecasting Report

## Observed results

Primary target: published All India Combined CPI General year-on-year inflation, 2014-01-01 to 2024-12-01.
This is a retrospective, observation-date-based experiment, not a real-time backtest.

### C0 model baselines

|   horizon | configuration   | model          |   n | evaluation_start   | evaluation_end   |    mae |   rmse |      r2 |    bias |    mape |
|----------:|:----------------|:---------------|----:|:-------------------|:-----------------|-------:|-------:|--------:|--------:|--------:|
|         1 | C0              | autoregression |  18 | 2023-07-01         | 2024-12-01       | 0.8854 | 1.2244 | -0.8356 | -0.2077 | 16.3868 |
|         1 | C0              | elastic_net    |  18 | 2023-07-01         | 2024-12-01       | 0.9278 | 1.2296 | -0.8514 | -0.1691 | 17.2725 |
|         1 | C0              | random_forest  |  18 | 2023-07-01         | 2024-12-01       | 1.0378 | 1.3202 | -1.1342 | -0.1028 | 19.6350 |
|         1 | C0              | sarimax        |  18 | 2023-07-01         | 2024-12-01       | 0.8474 | 1.1628 | -0.6555 | -0.1266 | 15.7692 |
|         1 | C0              | xgboost        |  18 | 2023-07-01         | 2024-12-01       | 0.9339 | 1.2339 | -0.8644 | -0.2201 | 17.2989 |
|         3 | C0              | autoregression |  18 | 2023-07-01         | 2024-12-01       | 0.7621 | 1.0173 | -0.2673 | -0.2251 | 14.3202 |
|         3 | C0              | elastic_net    |  18 | 2023-07-01         | 2024-12-01       | 0.6325 | 0.8928 |  0.0240 | -0.2003 | 12.0763 |
|         3 | C0              | random_forest  |  18 | 2023-07-01         | 2024-12-01       | 0.8029 | 1.0976 | -0.4753 | -0.3099 | 15.2272 |
|         3 | C0              | sarimax        |  18 | 2023-07-01         | 2024-12-01       | 0.8567 | 1.0625 | -0.3823 | -0.2290 | 16.1231 |
|         3 | C0              | xgboost        |  18 | 2023-07-01         | 2024-12-01       | 0.8032 | 1.0656 | -0.3903 | -0.3459 | 15.1884 |
|         6 | C0              | autoregression |  18 | 2023-07-01         | 2024-12-01       | 0.9169 | 1.0852 | -0.4420 | -0.1676 | 16.9790 |
|         6 | C0              | elastic_net    |  18 | 2023-07-01         | 2024-12-01       | 0.8853 | 1.0668 | -0.3936 | -0.1838 | 16.5263 |
|         6 | C0              | random_forest  |  18 | 2023-07-01         | 2024-12-01       | 0.9047 | 1.0962 | -0.4714 | -0.4148 | 17.0012 |
|         6 | C0              | sarimax        |  18 | 2023-07-01         | 2024-12-01       | 0.9905 | 1.1964 | -0.7527 |  0.0367 | 18.6826 |
|         6 | C0              | xgboost        |  18 | 2023-07-01         | 2024-12-01       | 0.9851 | 1.1670 | -0.6678 | -0.2557 | 18.9668 |

### Incremental information-set comparison

|   horizon | model           | configuration   |   common_n | evaluation_start   | evaluation_end   | comparison_status    |   c0_mae |   configuration_mae |   delta_mae_vs_C0 |   c0_rmse |   configuration_rmse |   delta_rmse_vs_C0 | improvement    |
|----------:|:----------------|:----------------|-----------:|:-------------------|:-----------------|:---------------------|---------:|--------------------:|------------------:|----------:|---------------------:|-------------------:|:---------------|
|         1 | autoregression  | C1              |         18 | 2023-07-01         | 2024-12-01       | paired_common_sample |   0.8854 |              0.9180 |            0.0326 |    1.2244 |               1.2460 |             0.0216 | worse_or_equal |
|         1 | autoregression  | C2              |         18 | 2023-07-01         | 2024-12-01       | paired_common_sample |   0.8854 |              0.9914 |            0.1060 |    1.2244 |               1.2566 |             0.0322 | worse_or_equal |
|         1 | autoregression  | C3              |         18 | 2023-07-01         | 2024-12-01       | paired_common_sample |   0.8854 |              0.9795 |            0.0941 |    1.2244 |               1.2617 |             0.0373 | worse_or_equal |
|         1 | cpi_persistence | C1              |          0 | nan                | nan              | unavailable          | nan      |            nan      |          nan      |  nan      |             nan      |           nan      | unavailable    |
|         1 | cpi_persistence | C2              |          0 | nan                | nan              | unavailable          | nan      |            nan      |          nan      |  nan      |             nan      |           nan      | unavailable    |
|         1 | cpi_persistence | C3              |          0 | nan                | nan              | unavailable          | nan      |            nan      |          nan      |  nan      |             nan      |           nan      | unavailable    |
|         1 | elastic_net     | C1              |         18 | 2023-07-01         | 2024-12-01       | paired_common_sample |   0.9278 |              0.7634 |           -0.1644 |    1.2296 |               1.0535 |            -0.1762 | improved       |
|         1 | elastic_net     | C2              |         18 | 2023-07-01         | 2024-12-01       | paired_common_sample |   0.9278 |              0.9886 |            0.0607 |    1.2296 |               1.2448 |             0.0152 | worse_or_equal |
|         1 | elastic_net     | C3              |         18 | 2023-07-01         | 2024-12-01       | paired_common_sample |   0.9278 |              0.7982 |           -0.1296 |    1.2296 |               1.0514 |            -0.1782 | improved       |
|         1 | random_forest   | C1              |         18 | 2023-07-01         | 2024-12-01       | paired_common_sample |   1.0378 |              1.1645 |            0.1267 |    1.3202 |               1.4341 |             0.1139 | worse_or_equal |
|         1 | random_forest   | C2              |         18 | 2023-07-01         | 2024-12-01       | paired_common_sample |   1.0378 |              1.1266 |            0.0888 |    1.3202 |               1.3747 |             0.0545 | worse_or_equal |
|         1 | random_forest   | C3              |         18 | 2023-07-01         | 2024-12-01       | paired_common_sample |   1.0378 |              1.2004 |            0.1627 |    1.3202 |               1.4463 |             0.1261 | worse_or_equal |
|         1 | sarimax         | C1              |         18 | 2023-07-01         | 2024-12-01       | paired_common_sample |   0.8474 |              0.9675 |            0.1201 |    1.1628 |               1.3488 |             0.1861 | worse_or_equal |
|         1 | sarimax         | C2              |         18 | 2023-07-01         | 2024-12-01       | paired_common_sample |   0.8474 |              0.8880 |            0.0406 |    1.1628 |               1.1632 |             0.0004 | worse_or_equal |
|         1 | sarimax         | C3              |         18 | 2023-07-01         | 2024-12-01       | paired_common_sample |   0.8474 |              0.9778 |            0.1304 |    1.1628 |               1.3584 |             0.1956 | worse_or_equal |
|         1 | xgboost         | C1              |         18 | 2023-07-01         | 2024-12-01       | paired_common_sample |   0.9339 |              0.9627 |            0.0289 |    1.2339 |               1.2142 |            -0.0198 | mixed          |
|         1 | xgboost         | C2              |         18 | 2023-07-01         | 2024-12-01       | paired_common_sample |   0.9339 |              1.1224 |            0.1885 |    1.2339 |               1.4034 |             0.1695 | worse_or_equal |
|         1 | xgboost         | C3              |         18 | 2023-07-01         | 2024-12-01       | paired_common_sample |   0.9339 |              0.9566 |            0.0227 |    1.2339 |               1.1569 |            -0.0770 | mixed          |
|         3 | autoregression  | C1              |         18 | 2023-07-01         | 2024-12-01       | paired_common_sample |   0.7621 |              0.8589 |            0.0968 |    1.0173 |               1.0106 |            -0.0067 | mixed          |
|         3 | autoregression  | C2              |         18 | 2023-07-01         | 2024-12-01       | paired_common_sample |   0.7621 |              0.9672 |            0.2052 |    1.0173 |               1.0858 |             0.0685 | worse_or_equal |
|         3 | autoregression  | C3              |         18 | 2023-07-01         | 2024-12-01       | paired_common_sample |   0.7621 |              0.9218 |            0.1597 |    1.0173 |               1.0205 |             0.0032 | worse_or_equal |
|         3 | cpi_persistence | C1              |          0 | nan                | nan              | unavailable          | nan      |            nan      |          nan      |  nan      |             nan      |           nan      | unavailable    |
|         3 | cpi_persistence | C2              |          0 | nan                | nan              | unavailable          | nan      |            nan      |          nan      |  nan      |             nan      |           nan      | unavailable    |
|         3 | cpi_persistence | C3              |          0 | nan                | nan              | unavailable          | nan      |            nan      |          nan      |  nan      |             nan      |           nan      | unavailable    |
|         3 | elastic_net     | C1              |         18 | 2023-07-01         | 2024-12-01       | paired_common_sample |   0.6325 |              0.7548 |            0.1223 |    0.8928 |               0.9367 |             0.0440 | worse_or_equal |
|         3 | elastic_net     | C2              |         18 | 2023-07-01         | 2024-12-01       | paired_common_sample |   0.6325 |              0.6199 |           -0.0127 |    0.8928 |               0.8965 |             0.0037 | mixed          |
|         3 | elastic_net     | C3              |         18 | 2023-07-01         | 2024-12-01       | paired_common_sample |   0.6325 |              0.7919 |            0.1593 |    0.8928 |               0.8950 |             0.0022 | worse_or_equal |
|         3 | random_forest   | C1              |         18 | 2023-07-01         | 2024-12-01       | paired_common_sample |   0.8029 |              0.9503 |            0.1475 |    1.0976 |               1.1228 |             0.0252 | worse_or_equal |
|         3 | random_forest   | C2              |         18 | 2023-07-01         | 2024-12-01       | paired_common_sample |   0.8029 |              0.9708 |            0.1679 |    1.0976 |               1.1019 |             0.0043 | worse_or_equal |
|         3 | random_forest   | C3              |         18 | 2023-07-01         | 2024-12-01       | paired_common_sample |   0.8029 |              0.9067 |            0.1038 |    1.0976 |               1.0903 |            -0.0073 | mixed          |
|         3 | sarimax         | C1              |         18 | 2023-07-01         | 2024-12-01       | paired_common_sample |   0.8567 |              0.8749 |            0.0182 |    1.0625 |               0.9948 |            -0.0677 | mixed          |
|         3 | sarimax         | C2              |         18 | 2023-07-01         | 2024-12-01       | paired_common_sample |   0.8567 |              0.8984 |            0.0417 |    1.0625 |               1.0568 |            -0.0057 | mixed          |
|         3 | sarimax         | C3              |         18 | 2023-07-01         | 2024-12-01       | paired_common_sample |   0.8567 |              0.8630 |            0.0063 |    1.0625 |               0.9810 |            -0.0815 | mixed          |
|         3 | xgboost         | C1              |         18 | 2023-07-01         | 2024-12-01       | paired_common_sample |   0.8032 |              0.8301 |            0.0269 |    1.0656 |               0.9799 |            -0.0856 | mixed          |
|         3 | xgboost         | C2              |         18 | 2023-07-01         | 2024-12-01       | paired_common_sample |   0.8032 |              0.8632 |            0.0600 |    1.0656 |               1.0376 |            -0.0280 | mixed          |
|         3 | xgboost         | C3              |         18 | 2023-07-01         | 2024-12-01       | paired_common_sample |   0.8032 |              0.8352 |            0.0319 |    1.0656 |               1.0093 |            -0.0562 | mixed          |
|         6 | autoregression  | C1              |         18 | 2023-07-01         | 2024-12-01       | paired_common_sample |   0.9169 |              0.8791 |           -0.0378 |    1.0852 |               1.0042 |            -0.0810 | improved       |
|         6 | autoregression  | C2              |         18 | 2023-07-01         | 2024-12-01       | paired_common_sample |   0.9169 |              1.6779 |            0.7610 |    1.0852 |               1.9675 |             0.8823 | worse_or_equal |
|         6 | autoregression  | C3              |         18 | 2023-07-01         | 2024-12-01       | paired_common_sample |   0.9169 |              1.0972 |            0.1803 |    1.0852 |               1.2291 |             0.1439 | worse_or_equal |
|         6 | cpi_persistence | C1              |          0 | nan                | nan              | unavailable          | nan      |            nan      |          nan      |  nan      |             nan      |           nan      | unavailable    |
|         6 | cpi_persistence | C2              |          0 | nan                | nan              | unavailable          | nan      |            nan      |          nan      |  nan      |             nan      |           nan      | unavailable    |
|         6 | cpi_persistence | C3              |          0 | nan                | nan              | unavailable          | nan      |            nan      |          nan      |  nan      |             nan      |           nan      | unavailable    |
|         6 | elastic_net     | C1              |         18 | 2023-07-01         | 2024-12-01       | paired_common_sample |   0.8853 |              0.6666 |           -0.2187 |    1.0668 |               0.9704 |            -0.0964 | improved       |
|         6 | elastic_net     | C2              |         18 | 2023-07-01         | 2024-12-01       | paired_common_sample |   0.8853 |              0.6666 |           -0.2187 |    1.0668 |               0.9704 |            -0.0964 | improved       |
|         6 | elastic_net     | C3              |         18 | 2023-07-01         | 2024-12-01       | paired_common_sample |   0.8853 |              0.6666 |           -0.2187 |    1.0668 |               0.9704 |            -0.0964 | improved       |
|         6 | random_forest   | C1              |         18 | 2023-07-01         | 2024-12-01       | paired_common_sample |   0.9047 |              0.7939 |           -0.1107 |    1.0962 |               0.9734 |            -0.1227 | improved       |
|         6 | random_forest   | C2              |         18 | 2023-07-01         | 2024-12-01       | paired_common_sample |   0.9047 |              0.9612 |            0.0565 |    1.0962 |               1.1073 |             0.0112 | worse_or_equal |
|         6 | random_forest   | C3              |         18 | 2023-07-01         | 2024-12-01       | paired_common_sample |   0.9047 |              0.7863 |           -0.1184 |    1.0962 |               0.9575 |            -0.1387 | improved       |
|         6 | sarimax         | C1              |         18 | 2023-07-01         | 2024-12-01       | paired_common_sample |   0.9905 |              1.2215 |            0.2309 |    1.1964 |               1.5032 |             0.3068 | worse_or_equal |
|         6 | sarimax         | C2              |         18 | 2023-07-01         | 2024-12-01       | paired_common_sample |   0.9905 |              1.0159 |            0.0254 |    1.1964 |               1.2151 |             0.0187 | worse_or_equal |
|         6 | sarimax         | C3              |         18 | 2023-07-01         | 2024-12-01       | paired_common_sample |   0.9905 |              1.2855 |            0.2949 |    1.1964 |               1.5468 |             0.3505 | worse_or_equal |
|         6 | xgboost         | C1              |         18 | 2023-07-01         | 2024-12-01       | paired_common_sample |   0.9851 |              0.8572 |           -0.1279 |    1.1670 |               1.0217 |            -0.1454 | improved       |
|         6 | xgboost         | C2              |         18 | 2023-07-01         | 2024-12-01       | paired_common_sample |   0.9851 |              1.1263 |            0.1412 |    1.1670 |               1.3183 |             0.1513 | worse_or_equal |
|         6 | xgboost         | C3              |         18 | 2023-07-01         | 2024-12-01       | paired_common_sample |   0.9851 |              0.9009 |           -0.0842 |    1.1670 |               1.1079 |            -0.0591 | improved       |

A negative delta MAE/RMSE means the added information improved the corresponding
metric on identical target months. Results are not causal and no significance is asserted.

### Lowest-RMSE model/configuration per horizon

|   horizon | configuration   | model         |   n | evaluation_start   | evaluation_end   |    mae |   rmse |      r2 |    bias |    mape |
|----------:|:----------------|:--------------|----:|:-------------------|:-----------------|-------:|-------:|--------:|--------:|--------:|
|         1 | C3              | elastic_net   |  18 | 2023-07-01         | 2024-12-01       | 0.7982 | 1.0514 | -0.3537 | -0.0474 | 15.2512 |
|         3 | C0              | elastic_net   |  18 | 2023-07-01         | 2024-12-01       | 0.6325 | 0.8928 |  0.0240 | -0.2003 | 12.0763 |
|         6 | C3              | random_forest |  18 | 2023-07-01         | 2024-12-01       | 0.7863 | 0.9575 | -0.1226 |  0.3731 | 16.2983 |

## Diagnostics and robustness

- Test-window split comparisons: 126 descriptive rows.
- High-inflation error rows: 63; thresholds are based on initial training data.
- Brent spike error rows: 63; target-month Brent is used only to label ex-post diagnostics, not as a predictor.
- Residual diagnostic rows: 63. Ljung-Box results are exploratory because multi-step errors overlap.
- Lag sensitivity compares C0 autoregression using lags 1,2,3,6,12 with a reduced lag-1/lag-12 specification.
- CPI back-series/current boundary sensitivity: the 2014–2024 continuous published-rate segment is used. The disjoint 2026 segment has nine points and cannot support an independent experiment.

## Convergence and statistical inference

Elastic Net convergence warning counts are stored by configuration and horizon in run metadata.
No Diebold-Mariano test was conducted; the finite test samples and overlapping 3/6-month errors
do not support a reliable inferential comparison. Prediction intervals were not generated.

## Reproducibility and preservation

- Python 3.13.0; pandas 3.1.1; scikit-learn 1.9.1; statsmodels 0.15.0; XGBoost 3.4.1.
- Fixed seed: 42.
- Protected raw/processed data hash check: unchanged (30 files).
- No raw or verified processed data were written by Stage 2.

## Limitations and interpretation

The CPI published inflation rate is discontinuous at the available 2025 base-series boundary;
the uninterrupted older segment is used without calculating substitute inflation. The test
sample is short, source vintage and publication timestamps are not archived, and the 2026
published series is too short for separate evaluation. Imported-cost variables are predictive
inputs only; no causal conclusions follow. No CPI index target substitution, synthetic research
data, Stage 3/4/5 analysis, SHAP, or dashboard work is included.

## Files

- Forecast predictions: `CPI_FORECAST_PREDICTIONS.csv`
- Model metrics: `CPI_MODEL_COMPARISON.csv`
- Paired C0 comparison: `CPI_CONFIGURATION_INCREMENTAL_COMPARISON.csv`
- Method: `CPI_FORECASTING_METHODOLOGY.md`
- Data availability: `CPI_DATA_AND_FEATURE_AVAILABILITY.md`

**Stage 2 readiness:** results are available for researcher review; do not begin Stage 3 until approved.
