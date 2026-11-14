# Stage 1 USD/INR Forecasting Results

> **Audit update:** This report replaces the initial Stage 1 comparison, whose forecast-origin alignment and benchmark defects were corrected during independent review. The complete methodology, defect history, leakage assessment, robustness checks, reproducibility evidence, and limitations are documented in [STAGE1_INDEPENDENT_RESEARCH_AUDIT.md](./STAGE1_INDEPENDENT_RESEARCH_AUDIT.md). Do not use the initial Elastic Net ranking.

The corrected experiment forecasts the monthly USD/INR level (INR per USD) at 1-, 3-, and 6-month horizons using the Random Walk, ARIMA, Elastic Net, Random Forest, and XGBoost. Each horizon has 23 common final test targets (December 2024–October 2026).

| Horizon | Model | MAE | RMSE | OOS R² | Directional accuracy | Bias |
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

ARIMA is the lowest-error model by MAE and RMSE at all horizons, but its reductions against the corrected random walk are small (about 1.2%–2.5% in RMSE) on a 23-observation holdout. The machine-learning models do not beat the random-walk benchmark. These are predictive comparisons, not causal findings, and no statistical significance is claimed.

## Outputs

- Corrected predictions: [EXCHANGE_RATE_FORECAST_PREDICTIONS.csv](./EXCHANGE_RATE_FORECAST_PREDICTIONS.csv)
- Corrected model metrics: [EXCHANGE_RATE_MODEL_COMPARISON.csv](./EXCHANGE_RATE_MODEL_COMPARISON.csv)
- Audit and research-readiness decision: [STAGE1_INDEPENDENT_RESEARCH_AUDIT.md](./STAGE1_INDEPENDENT_RESEARCH_AUDIT.md)

**Decision:** VERIFIED WITH LIMITATIONS. This is a conventional retrospective monthly experiment, not a genuine real-time backtest. The small test sample, sparse high-depreciation cases, and unverified publication timing must be considered before later research.
