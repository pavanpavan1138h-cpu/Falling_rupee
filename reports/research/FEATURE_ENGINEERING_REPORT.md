# POME EL Feature Engineering Report

Date: 2026-11-09

## Scope
This report documents the feature-engineering step performed on the verified processed datasets. The work is limited to the creation of transparent, leakage-safe derived variables for research use. No model evaluation, synthetic data generation, forecasting model fitting, or causal estimation was performed.

## Source-to-feature mapping

| Feature family | Source dataset | Source columns | Engineered outputs | Unit / interpretation |
| --- | --- | --- | --- | --- |
| Exchange rate | `data/processed/usd_inr_monthly_clean.csv` | `date`, `usd_inr_monthly` | `usd_inr_level`, `usd_inr_mom_change`, `usd_inr_mom_pct_change`, `usd_inr_log_change`, `usd_inr_depreciation_log_change`, `usd_inr_appreciation_log_change`, `usd_inr_3m_cumulative_change_pct`, `usd_inr_6m_cumulative_change_pct`, `usd_inr_12m_cumulative_change_pct` | INR per USD; depreciation is an increase in INR per USD |
| Brent crude | `data/processed/brent_monthly_clean.csv` | `date`, `brent_usd_per_barrel` | `brent_usd_per_barrel_level`, `brent_mom_pct_change`, `brent_log_change`, `brent_3m_cumulative_change_pct`, `brent_6m_cumulative_change_pct`, `brent_12m_cumulative_change_pct`, `brent_6m_rolling_volatility` | USD per barrel |
| Brent-INR proxy | `data/processed/brent_monthly_clean.csv` + `data/processed/usd_inr_monthly_clean.csv` | `date`, `brent_usd_per_barrel`, `usd_inr_monthly` | `brent_inr_proxy_level`, `brent_inr_proxy_mom_pct_change`, `brent_inr_proxy_log_change`, `brent_inr_proxy_3m_cumulative_change_pct`, `brent_inr_proxy_6m_cumulative_change_pct`, `brent_inr_proxy_12m_cumulative_change_pct` | Approximate INR per barrel |
| CPI | `data/processed/cpi_monthly_clean.csv` | `date`, `index_value`, `inflation_value` | `cpi_index_level`, `cpi_published_inflation`, `cpi_mom_change_index`, `cpi_mom_pct_change_index`, `cpi_3m_index_inflation`, `cpi_6m_index_inflation`, `cpi_12m_index_inflation`, `cpi_1m_..._12m_index_lag`, `cpi_1m_..._12m_inflation_lag` | Index points; published inflation percent annualized/period rate where supplied |
| Repo rate | `data/processed/repo_rate_clean.csv` | `date`, `repo_rate` | `repo_rate_level`, `repo_rate_change_pp`, `repo_rate_3m_change_pp`, `repo_rate_6m_change_pp`, `repo_rate_change_indicator` | Percentage points |
| NEER/REER | `data/processed/neer_reer_monthly_clean.csv` | `date`, `Trade_NEER`, `Trade_REER`, `Export_NEER`, `Export_REER` | Level, monthly percent change, log change, 3m/6m/12m cumulative change for each index | Index points |
| WPI | `data/processed/wpi_monthly_clean.csv` | `date`, `comm_name`, `comm_code`, `comm_wt`, `index_value` | `wpi_all_commodities_index`, `wpi_all_commodities_mom_change`, `wpi_all_commodities_mom_pct_change`, `wpi_all_commodities_yoy_inflation`, category-specific index and change features for `Primary Articles`, `Fuel & Power`, and `Manufactured Products` | Index points |

## Feature definitions and formulas

### 1. Exchange-rate level and changes

- `usd_inr_level`: source monthly exchange rate, retained in original INR per USD units.
- `usd_inr_mom_change`: `x_t - x_{t-1}`
- `usd_inr_mom_pct_change`: `(x_t / x_{t-1} - 1) * 100`
- `usd_inr_log_change`: `100 * log(x_t / x_{t-1})`
- `usd_inr_depreciation_log_change`: `max(delta_log_t, 0)`
- `usd_inr_appreciation_log_change`: `max(-delta_log_t, 0)`
- `usd_inr_3m/6m/12m_cumulative_change_pct`: `(x_t / x_{t-k} - 1) * 100`

Interpretation: an increase in INR per USD denotes rupee depreciation. A decrease denotes appreciation.

### 2. Brent crude-oil features

- `brent_usd_per_barrel_level`: original monthly Brent price.
- `brent_mom_pct_change`: monthly percentage change in Brent price.
- `brent_log_change`: monthly log change in price, in percent points.
- `brent_3m/6m/12m_cumulative_change_pct`: cumulative change over the selected horizon.
- `brent_6m_rolling_volatility`: six-month rolling standard deviation of Brent log changes. Minimum observation count is 3, to avoid unstable estimates with insufficient history.

### 3. Brent-INR proxy features

- `brent_inr_proxy_level = Brent_USD_t * USDINR_t`
- This is an approximate domestic-currency cost proxy, not an actual landed price or domestic administered price.
- It excludes freight, insurance, refining, taxes, and domestic pricing adjustments.
- It is suitable for imported-cost exposure analysis but not as a domestic price or transaction-price estimate.

### 4. CPI features

- `cpi_index_level`: original CPI index value.
- `cpi_published_inflation`: retained source-published inflation when available; no substitution with derived values.
- `cpi_mom_change_index`: `index_t - index_{t-1}`
- `cpi_mom_pct_change_index`: `(index_t / index_{t-1} - 1) * 100`
- `cpi_3m/6m/12m_index_inflation`: `(index_t / index_{t-k} - 1) * 100`
- `cpi_1m/2m/3m/6m/12m_index_lag`: lagged index values.
- `cpi_1m/2m/3m/6m/12m_inflation_lag`: lagged published inflation values.

The implementation preserves missing published inflation values and does not silently replace them with computed inflation values.

### 5. Repo-rate features

- `repo_rate_level`: original policy rate in percentage points.
- `repo_rate_change_pp`: `repo_rate_t - repo_rate_{t-1}`
- `repo_rate_3m_change_pp`: `repo_rate_t - repo_rate_{t-3}`
- `repo_rate_6m_change_pp`: `repo_rate_t - repo_rate_{t-6}`
- `repo_rate_change_indicator`: binary flag for a non-zero month-to-month change.

### 6. NEER/REER features

For each of `Trade_NEER`, `Trade_REER`, `Export_NEER`, and `Export_REER`:

- level: retained source index values
- monthly percent change: `(x_t / x_{t-1} - 1) * 100`
- log change: `100 * log(x_t / x_{t-1})`
- 3m/6m/12m cumulative change: `(x_t / x_{t-k} - 1) * 100`

These remain distinct by definition and are not merged into a single effective-exchange-rate series.

### 7. WPI features

- `wpi_all_commodities_index`: original `All commodities` headline index retained from the long-form WPI workbook.
- `wpi_all_commodities_mom_change`: month-over-month change
- `wpi_all_commodities_mom_pct_change`: month-over-month percentage change
- `wpi_all_commodities_yoy_inflation`: 12-month cumulative change in the all-commodities index
- Category features for `Primary Articles`, `Fuel & Power`, and `Manufactured Products` are also constructed with the same pattern.

The implementation does not reconstruct a headline WPI from commodity rows; it keeps the original aggregate row set intact and preserves the weight column and zero values where they exist in the source data.

## Leakage-safe design

All features were created with a strict time-ordering convention:

- Only values from the same series at the same time or earlier are used.
- Percentage and log changes depend on lagged values within the same series.
- Cumulative changes use the corresponding lagged observation, never future values.
- Rolling volatility uses the trailing window only.
- No synthetic observations were introduced.
- Missing values remain missing; they were not imputed.

## Data coverage and missingness preserved

The generated feature files preserve the coverage and missingness of the underlying source data. In particular:

- Daily USD/INR observations remain daily and are not mixed with monthly data.
- Monthly exchange-rate features maintain the monthly frequency of the verified monthly series.
- CPI and WPI features retain their gaps when the underlying source values are missing.
- The feature panel remains an outer-join panel keyed by date, so the analyst can inspect where each source is available without forcing full coverage.

## Output files generated

Under `data/processed/features/` the project now contains:

- `exchange_rate_features.csv`
- `brent_features.csv`
- `brent_inr_proxy_features.csv`
- `cpi_features.csv`
- `repo_rate_features.csv`
- `neer_reer_features.csv`
- `wpi_features.csv`
- `research_master_feature_panel.csv`

## Limitations and research interpretation

- The Brent-INR proxy is not a landed import cost and should be treated as a domestic-currency cost proxy, not a full cost-of-imports measure.
- CPI published inflation is retained as a separate source variable, not replaced by derived inflation from the index.
- WPI category series are retained exactly as source-defined and not assumed to be replacement headline inflation measures.
- The master panel is intended for transparent alignment and research use; it is not a finalized model dataset.
