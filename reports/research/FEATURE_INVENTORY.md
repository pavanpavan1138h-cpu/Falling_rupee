# POME EL Feature Inventory

This document captures proposed candidate features for the POME EL research workflow. It is intentionally structured as a design inventory and does not represent verified production features.

## Research stage map

- Stage 1: USD/INR exchange-rate forecasting
- Stage 2: Indian CPI inflation forecasting
- Stage 3: Asymmetric exchange-rate pass-through analysis
- Stage 4: High-inflation early-warning classification
- Stage 5: Inflation persistence and WPI analysis

## Proposed feature list

| Feature name or proposed definition | Economic meaning | Research stage | Required source variables | Formula or representation | Frequency | Potential lag | Availability requirements | Leakage risks | Research justification | Implementation status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Exchange-rate level | Current USD/INR exchange rate level | Stage 1, 2, 3 | Exchange-rate series | Level, same date or period | Monthly | 0 | Source series must be available and date-aligned | Low if contemporaneous only | Core macro baseline | Proposed |
| Exchange-rate change | Monthly or period-over-period change in exchange rate | Stage 1, 2, 3 | Exchange-rate series | Delta_t = x_t - x_{t-1} | Monthly | 1 | Consistent date index required | Low if computed on past data only | Captures depreciation dynamics | Proposed |
| Depreciation component | Positive exchange-rate change indicating depreciation | Stage 3, 4 | Exchange-rate series | max(delta_t, 0) | Monthly | 1 | Requires robust time index | Low if computed using known history only | Asymmetric pass-through hypothesis | Proposed |
| Appreciation component | Negative exchange-rate change indicating appreciation | Stage 3, 4 | Exchange-rate series | min(delta_t, 0) | Monthly | 1 | Requires robust time index | Low if computed using known history only | Distinguishes appreciation effects | Proposed |
| Lagged exchange-rate variables | Historical exchange-rate levels or changes | Stage 1, 2, 3 | Exchange-rate series | x_{t-k}, delta_{t-k} | Monthly | 1 to 12+ | Consistent frequency and vintage mapping | Moderate if future data leaks through | Captures delayed pass-through and persistence | Proposed |
| Brent crude oil price | Global oil price benchmark | Stage 2, 4 | International crude oil series | Level or transformed measure | Monthly | 0 | Source must be verified and date-aligned | Moderate if future values are used | Important for imported inflation on energy inputs | Proposed |
| Brent crude converted into INR | Oil cost in domestic currency | Stage 2, 3, 4 | Brent price + exchange rate | Brent_t * exchange_rate_t | Monthly | 0 | Requires source and conversion consistency | Moderate if future exchange-rate values are used | Currency conversion reflects imported inflation pass-through | Proposed |
| CPI inflation history | Past CPI inflation observations | Stage 2, 4, 5 | CPI inflation series | Inflation_t or cumulative inflation | Monthly | 0 to 12+ | Verified inflation measure required | Low if using known historical values only | Baseline inflation persistence and forecasting | Proposed |
| Inflation change | Difference in CPI inflation over recent periods | Stage 2, 4, 5 | CPI inflation series | inflation_t - inflation_{t-1} | Monthly | 1 | Consistent frequency required | Low if computed only on history | Captures inflation acceleration | Proposed |
| Rolling inflation statistics | Rolling averages or std. dev. of inflation | Stage 2, 4, 5 | CPI inflation series | mean/inflation window | Monthly | 1 to 12 | Requires consistent window lengths | Low if using only past data | Captures persistence and volatility | Proposed |
| RBI repo rate | Policy rate benchmark | Stage 2, 3, 4 | RBI policy-rate data | Level or change in repo rate | Monthly or event-driven | 0 | Verified series required | Moderate if policy rates are not known at origin | Monetary conditions and inflation expectations | Proposed |
| NEER indicator | Nominal effective exchange rate | Stage 1, 3 | NEER/REER dataset | Index or percent change | Monthly | 0 to 12 | Data availability and re-basing must be checked | Moderate if data is not aligned | External competitiveness and trade effects | Proposed |
| REER indicator | Real effective exchange rate | Stage 3, 4 | NEER/REER dataset | Index or percent change | Monthly | 0 to 12 | Requires consistent source index | Moderate if index base changes | Real competitiveness and inflation risk | Proposed |
| WPI headline | Headline wholesale price inflation | Stage 5 | WPI series | WPI level or inflation rate | Monthly | 0 | Must be verified and seasonally interpreted carefully | Low if using only historical date-aligned values | Link between producer prices and CPI | Proposed |
| WPI Fuel & Power | Fuel and power sub-index inflation | Stage 5 | WPI component data | Sub-index level or inflation rate | Monthly | 0 | Data availability and classification must be confirmed | Moderate if component definition changes | Fuel pass-through route to CPI | Proposed |
| Macro control variables | Additional macroeconomic controls | Stage 2, 4 | Relevant macro series | Series level or change | Monthly or quarterly | 0 to 12 | Requires source validation | Moderate if controls are mis-timed | Reduce omitted-variable bias | Proposed |

## Proposed nested CPI configurations

The following nested CPI forecasting configurations are proposed research designs and remain conditional on verified data availability and consistent forecast-origin information.

### C0: CPI inflation history
- Feature set: CPI inflation history only.
- Purpose: establish a baseline persistence model.
- Status: Proposed.

### C1: CPI inflation history plus Brent crude
- Feature set: CPI inflation history + Brent crude price series.
- Purpose: test whether global energy costs add predictive value.
- Status: Proposed.

### C2: CPI inflation history plus Brent crude and exchange-rate information
- Feature set: CPI inflation history + Brent crude + exchange-rate levels and changes.
- Purpose: examine whether exchange-rate exposures improve inflation forecasts.
- Status: Proposed.

### C3: CPI inflation history plus Brent-INR information
- Feature set: CPI inflation history + Brent crude converted into INR and related currency-adjusted measures.
- Purpose: evaluate domestic-currency imported inflation exposure.
- Status: Proposed.

## Implementation status legend

- Proposed: candidate feature not yet verified against data availability or research contract.
- Verified ready: source data and contract checks passed.
- In development: implementation is being prepared but not yet validated.
- Deprecated: candidate feature no longer in active research scope.

## Verified implemented feature set

The following feature families were implemented from the verified processed outputs after the audit and preprocessing stages were confirmed. They are included here to distinguish verified implementation from earlier proposal-stage concepts.

| Feature family | File | Status | Notes |
| --- | --- | --- | --- |
| Exchange-rate monthly features | `data/processed/features/exchange_rate_features.csv` | Verified ready | Includes monthly level, change, percent change, log change, depreciation/appreciation decomposition, and 3/6/12-month cumulative changes |
| Brent crude features | `data/processed/features/brent_features.csv` | Verified ready | Includes monthly price level, percent change, log change, cumulative changes, and a 6-month rolling volatility measure |
| Brent-INR proxy | `data/processed/features/brent_inr_proxy_features.csv` | Verified ready | Uses `brent_usd_per_barrel * usd_inr_monthly` and retains domestic-currency proxy interpretation |
| CPI features | `data/processed/features/cpi_features.csv` | Verified ready | Keeps `cpi_index_level` and `cpi_published_inflation` distinct and preserves missing published inflation values |
| Repo-rate features | `data/processed/features/repo_rate_features.csv` | Verified ready | Keeps policy-rate convention and records level, absolute changes, and change indicators |
| NEER/REER features | `data/processed/features/neer_reer_features.csv` | Verified ready | Maintains separate nominal and real exchange-rate index definitions |
| WPI features | `data/processed/features/wpi_features.csv` | Verified ready | Keeps the original `All commodities` headline and relevant category series without reconstructing a synthetic headline |
| Research master panel | `data/processed/features/research_master_feature_panel.csv` | Verified ready | Outer-join panel preserving date-wise source coverage and missingness |

## Governance notes

- Distinguish proposed features from verified available variables.
- Keep all feature logic and formula definitions explicit.
- Document leakage risks before implementation.
- Do not implement features until the data contract and time-series validation protocol are satisfied.
