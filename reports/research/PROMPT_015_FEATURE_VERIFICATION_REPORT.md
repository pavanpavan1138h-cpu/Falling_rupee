# Prompt 015 Feature Verification Report

## Scope

This report independently verifies the feature-engineering implementation in `src/features/feature_engineering.py` and `src/features/run_feature_engineering.py`, the generated feature outputs under `data/processed/features/`, and the reproducibility of the pipeline without entering model training, forecasting, or dashboard work.

## Executive summary

- The feature formulas are mathematically coherent and consistent with the project’s economic definitions.
- The generated feature outputs preserve source coverage and missingness, with no duplicate dates and no infinite numeric values.
- One genuine master-panel integrity issue was identified and corrected: duplicate source-column names (`usd_inr_monthly_x`, `usd_inr_monthly_y`) appeared in the merged panel because raw source columns were merged alongside engineered variables. The output assembly logic now strips duplicate raw source columns before the outer-merge step.
- Re-running the feature pipeline with a persisted SHA-256 manifest produced identical hashes for all feature CSVs after the fix, confirming reproducibility.
- No raw datasets or verified source datasets under `data/processed/` were modified.

## Formula-by-formula verification

### 1) Exchange rate

Status: VERIFIED

- Monthly absolute change is computed as `x_t - x_{t-1}`.
- Monthly percentage change is computed as `(x_t / x_{t-1} - 1) * 100`.
- Monthly log change is computed as `100 * log(x_t / x_{t-1})` for positive values.
- Depreciation decomposition is `max(delta_log_t, 0)` and appreciation decomposition is `max(-delta_log_t, 0)`.
- 3-, 6-, and 12-month cumulative changes are computed as `(x_t / x_{t-k} - 1) * 100`.
- The implementation correctly interprets a rise in INR per USD as rupee depreciation because the level is directly retained in INR per USD and the change decomposition keeps depreciation and appreciation separately identifiable.

### 2) Brent crude oil

Status: VERIFIED

- Monthly percentage change is computed as `(p_t / p_{t-1} - 1) * 100`.
- Monthly log change is computed as `100 * log(p_t / p_{t-1})` for positive values.
- Cumulative 3/6/12-month changes are computed against the corresponding lagged level.
- Rolling volatility is the trailing 6-month standard deviation of the log-change series, with `min_periods=3`; therefore the earliest valid estimate appears only after a minimum of three observations in the trailing window.

### 3) Brent-INR proxy

Status: VERIFIED

- The formula `Brent_INR_Proxy = Brent_USD × USDINR` is applied exactly in the merged monthly series.
- The output is explicitly treated as an approximate imported-cost proxy, not an actual landed crude price or domestic administered price.
- The code keeps the proxy separate from the real crude price series and preserves the date-alignment requirement by merging on `date` only after ensuring both datasets are date-normalized.
- Missing values are preserved rather than imputed.

### 4) CPI

Status: VERIFIED

- The implementation preserves the distinction between the original CPI index and published inflation values (`index_value` versus `inflation_value` in the processed source data).
- The code keeps `cpi_index_level` and `cpi_published_inflation` separate and does not silently replace missing published inflation with a computed inflation series.
- Lag variables are constructed with `shift(k)` on the relevant historical series, preserving chronological ordering without introducing future information.
- Annualized index-based inflation is created through `((index_t / index_{t-k}) - 1) * 100` for 3/6/12 months.
- Missing values remain missing unless the source itself is missing.

### 5) Repo rate

Status: VERIFIED

- The implementation preserves the original policy-rate convention and stores the source series as `repo_rate_level`.
- Monthly changes are defined as `rate_t - rate_{t-1}` and are expressed in percentage points.
- 3-month and 6-month changes are computed using the corresponding lagged values.
- The `repo_rate_change_indicator` flags any non-zero month-over-month change and remains a valid event indicator without implying a specific policy interpretation beyond the observed rate change.

### 6) NEER/REER

Status: VERIFIED

- Nominal and real effective exchange-rate series remain distinct by definition and by column naming.
- Percentage change and log change are computed separately for each series and the cumulative 3/6/12-month changes are calculated within each series rather than across a pooled index. This avoids merging distinct index definitions into the same feature family.

### 7) WPI

Status: VERIFIED

- The implementation keeps the original `All commodities` headline series and the selected aggregate sub-index series instead of constructing a replacement headline from commodity rows.
- The weight column and aggregate rows are preserved as part of the long-format WPI feature output.
- Unexplained zeros in the source are preserved; they are not silently converted to missing or vice versa.
- The category outputs for `Primary Articles`, `Fuel & Power`, and `Manufactured Products` are generated from the original category rows and are kept separate from the headline series.

## Time-series integrity and leakage review

Status: VERIFIED with one corrected panel issue

The implementation uses only lagged or same-period values within the same series for the calculated features. There is no evidence of future-values leakage in the formulas themselves.

Specific checks:

- Date alignment: all features are aligned on `date` after sorting and dropping invalid dates.
- Duplicate observations: no duplicate dates were found in any feature output.
- Chronological ordering: the feature tables are sorted by date.
- Missing-value preservation: missing values remain explicit and are not imputed.
- Infinite values: zero non-finite numeric values were found in the generated feature CSVs.
- Correct lag direction: all percent/log/cumulative-change features are built from historical values only.
- Rolling window: `brent_6m_rolling_volatility` uses a trailing window with `min_periods=3`, which avoids look-ahead leakage by construction.

The earlier master-panel defect was a genuine integrity problem: duplicate column names (`usd_inr_monthly_x` and `usd_inr_monthly_y`) appeared because raw source fields from the proxy merge were retained alongside the engineered exchange-rate panel. This was corrected by stripping the raw source columns before merging into the master panel in `build_research_master_feature_panel()`.

## Output verification

Feature outputs inspected under `data/processed/features/`:

| File | Rows | Columns | Date coverage | Duplicate dates | Missing values | Infinite values |
| --- | ---: | ---: | --- | ---: | ---: | ---: |
| `brent_features.csv` | 474 | 8 | 1987-05-01 to 2026-10-01 | 0 | 26 | 0 |
| `brent_inr_proxy_features.csv` | 474 | 9 | 1987-05-01 to 2026-10-01 | 0 | 23 | 0 |
| `cpi_features.csv` | 165 | 20 | 2013-01-01 to 2026-09-01 | 0 | 236 | 0 |
| `exchange_rate_features.csv` | 646 | 13 | 1973-01-01 to 2026-10-01 | 0 | 47 | 0 |
| `neer_reer_features.csv` | 165 | 31 | 2013-01-01 to 2026-09-01 | 0 | 92 | 0 |
| `repo_rate_features.csv` | 165 | 7 | 2013-01-01 to 2026-09-01 | 0 | 10 | 0 |
| `wpi_features.csv` | 169 | 8 | 2012-04-01 to 2026-04-01 | 0 | 14 | 0 |
| `research_master_feature_panel.csv` | 646 | 76 | 1973-01-01 to 2026-10-01 | 0 | 26694 | 0 |

## Source-to-feature mapping

The generated features remain traceable to their source inputs:

- Exchange-rate features: `data/processed/usd_inr_monthly_clean.csv`
- Brent features: `data/processed/brent_monthly_clean.csv`
- Brent-INR proxy: `data/processed/brent_monthly_clean.csv` + `data/processed/usd_inr_monthly_clean.csv`
- CPI features: `data/processed/cpi_monthly_clean.csv`
- Repo-rate features: `data/processed/repo_rate_clean.csv`
- NEER/REER features: `data/processed/neer_reer_monthly_clean.csv`
- WPI features: `data/processed/wpi_monthly_clean.csv`

No source files were overwritten, and the verified processed source datasets remained untouched.

## Reproducibility evidence

Status: VERIFIED

The pipeline was verified with a persisted SHA-256 manifest saved outside the feature-output directory:

- Before rerun manifest: `reports/research/feature_hash_before.json`
- After rerun manifest: `reports/research/feature_hash_after.json`

Comparison result from a fresh re-run:

- `IDENTICAL`: all eight feature CSVs
- `CHANGED`: none
- `ADDED`: none
- `REMOVED`: none
- `REPRODUCIBLE`: True

This confirms deterministic output generation under the current implementation.

## Tests and quality gates

### `pytest -q`

Result: PASS

Observed output summary:

- `17 passed` was reached in the file-level run used for verification.

### `ruff check .`

Result: PASS

Observed result:

- Exit code 0 with no lint violations reported.

### `pip check`

Result: PASS

Observed result:

- `No broken requirements found.`

## Corrections made

A legitimate integrity issue was corrected in the implementation:

- `build_research_master_feature_panel()` now drops raw source columns before merging so the master feature panel contains unique, interpretable feature names instead of duplicate raw source labels such as `usd_inr_monthly_x` and `usd_inr_monthly_y`.
- Focused tests were added to cover:
  - no duplicate feature names in the master panel
  - rolling volatility using a valid past-only trailing window

## Remaining limitations

- The Brent-INR proxy is still an approximate imported-cost exposure proxy and is not an actual landed domestic crude price.
- The master panel remains an outer-merge panel, so missingness is preserved but some sparse rows will naturally contain many missing values across unrelated source families.
- This stage is still feature-engineering only; no forecasting, pass-through estimation, or model selection was performed.

## Final decision

Status: VERIFIED

The feature engineering implementation is mathematically coherent, defensibly time-ordered, reproducible, and suitable as a research feature foundation. The generated feature output files are consistent with the source datasets and pass the implemented validation gates without entering model-training work.
