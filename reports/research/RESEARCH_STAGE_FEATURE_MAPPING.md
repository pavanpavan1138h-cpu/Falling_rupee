# POME EL Research Stage Feature Mapping

## Stage 1: USD/INR forecasting

- Candidate target: monthly USD/INR level or month-ahead change
- Candidate predictors:
  - `usd_inr_level`
  - `usd_inr_mom_change`
  - `usd_inr_mom_pct_change`
  - `usd_inr_depreciation_log_change`
  - `usd_inr_appreciation_log_change`
  - `usd_inr_3m_cumulative_change_pct`
  - `usd_inr_6m_cumulative_change_pct`
  - `usd_inr_12m_cumulative_change_pct`
- Forecast-safe status: valid when computed using only historical values through the forecast origin.
- Exclusions: daily USD/INR series must not be treated as a monthly forecast target or predictor without explicit aggregation rules.
- Known limitation: the monthly source series is a market exchange rate, not a causal policy instrument.

## Stage 2: CPI inflation forecasting

- Candidate target: CPI inflation or future CPI index movement
- Candidate predictors:
  - `cpi_index_level`
  - `cpi_published_inflation`
  - `cpi_3m_index_inflation`
  - `cpi_6m_index_inflation`
  - `cpi_12m_index_inflation`
  - `cpi_1m_..._12m_index_lag`
  - `cpi_1m_..._12m_inflation_lag`
  - `brent_usd_per_barrel_level`
  - `brent_inr_proxy_level`
  - `repo_rate_level`
  - `repo_rate_change_pp`
  - `usd_inr_level`
- Forecast-safe status: valid only when the forecast origin is aligned to the information actually available at that time.
- Exclusions: no synthetic inflation values substituted for published CPI inflation; no future values used as predictors.
- Known limitation: published inflation values may be sparse or incomplete in the raw source layout and should not be silently approximated.

## Stage 3: Asymmetric exchange-rate pass-through

- Candidate target: CPI inflation or import-price pressure
- Candidate predictors:
  - `usd_inr_depreciation_log_change`
  - `usd_inr_appreciation_log_change`
  - `brent_inr_proxy_level`
  - `brent_inr_proxy_mom_pct_change`
  - `Trade_NEER` and `Trade_REER` percent change features
  - `Export_NEER` and `Export_REER` percent change features
- Forecast-safe status: valid if each variable is constructed from historical observations only and the timing of macroeconomic releases is respected.
- Exclusions: avoid mixing monthly and daily exchange-rate series; do not use future depreciation or appreciation values to define historical pass-through.
- Known limitation: pass-through is not causal by construction and requires explicit interpretive framing.

## Stage 4: High-inflation early warning

- Candidate target: high-inflation episode indicator or inflation acceleration outcome
- Candidate predictors:
  - `cpi_3m_index_inflation`
  - `cpi_6m_index_inflation`
  - `cpi_12m_index_inflation`
  - `wpi_all_commodities_yoy_inflation`
  - `brent_inr_proxy_3m_cumulative_change_pct`
  - `brent_inr_proxy_6m_cumulative_change_pct`
  - `repo_rate_change_pp`
  - `usd_inr_depreciation_log_change`
- Forecast-safe status: valid only with a clearly specified forecast origin and vintage-aware chronology.
- Exclusions: no future WPI/CPI outcomes or revisions should be used to flag prior periods as high-inflation events.
- Known limitation: this is an early-warning design, not a causal model of inflation.

## Stage 5: Inflation persistence and WPI analysis

- Candidate target: WPI or CPI persistence over multiple horizons
- Candidate predictors:
  - `wpi_all_commodities_index`
  - `wpi_all_commodities_mom_change`
  - `wpi_all_commodities_mom_pct_change`
  - `wpi_all_commodities_yoy_inflation`
  - `wpi_primary_articles_mom_change`
  - `wpi_fuel_and_power_mom_change`
  - `wpi_manufactured_products_mom_change`
  - `cpi_published_inflation`
  - `cpi_3m_index_inflation`
  - `cpi_6m_index_inflation`
- Forecast-safe status: valid if the persistence measures are built from lagged actual values only.
- Exclusions: do not replace WPI headline values with commodity-level recombinations or category averages unless explicitly justified by a documented source design.
- Known limitation: WPI is a producer-price index and not identical to CPI inflation, so interpretation must remain careful.

## Shared governance rule

All stage mappings assume a forecast-origin design in which features are generated only from information available at or before the time origin. The feature set is research-ready but not model-ready until a stage-specific evaluation protocol is defined and validated.
