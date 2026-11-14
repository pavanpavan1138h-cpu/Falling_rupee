# Stage 4 Data Feasibility Audit

**Audit date:** 2026-11-10  
**Scope:** Read-only inspection of existing processed data, feature outputs, Stage 1/2 archives,
Stage 3 derived panel, and prior audit reports.  
**No data, source code, model artifact, prediction, or prior-stage output was modified.**

## 1. Executive assessment

**Design feasibility: READY WITH LIMITATIONS.** The local data support a retrospective monthly
classification design using published CPI inflation above 6% as the elevated class. The
continuous CPI target and the observed FX, Brent, repo, NEER/REER, WPI, and Stage 3 panel
calendars overlap adequately in January 2014-December 2024. A conservative January 2015 origin
start yields 114-119 labels per horizon and 29 elevated labels per horizon.

The limiting factor is not row-level missingness in the common period but the small number and
clustering of elevated episodes: only three elevated target months (two runs) occur in a common
18-month July 2023-December 2024 test. This cannot support stable model ranking or operational
calibration claims. Historical release dates/vintages are also absent, so the design is
retrospective rather than verified real time.

## 2. Dataset inventory and observed availability

The following are observed file facts. Counts refer to file contents and, where stated, the
2014-2024 common period; they are not claims about historical publication availability.

| Dataset | Observed coverage / rows | Common-period facts | Duplicate/missingness and timing assessment |
|---|---|---|---|
| `data/processed/cpi_monthly_clean.csv` | 165 months, Jan 2013-Sep 2026 | 132 continuous months Jan 2014-Dec 2024; published inflation 132/132 observed | No duplicate dates in sample. Published CPI is missing across 2025 and resumes in a separate Jan-Sep 2026 segment (9 values); do not bridge. Eight of the 2014 months have >6% inflation. |
| `data/processed/features/cpi_features.csv` | 165 monthly rows, Jan 2013-Sep 2026 | CPI history variables align to the CPI calendar | Its generated lag columns are missing at the beginning by construction. Several CPI index-change columns are computed from the index and must not be treated as publisher-reported inflation. |
| `data/processed/usd_inr_monthly_clean.csv` and `features/exchange_rate_features.csv` | 646 monthly rows, Jan 1973-Oct 2026 | 132 complete common-period monthly values | No common-period date gaps or duplicates observed. INR per USD; positive movement denotes rupee depreciation. Historical retrieval vintage/release timing is not authenticated. |
| `data/processed/brent_monthly_clean.csv` and `features/brent_features.csv` | 474 monthly rows, May 1987-Oct 2026 | 132 common-period observations, complete and positive | No common-period date gaps or duplicates observed. Local extraction vintage, aggregation, revisions, and release timing remain unverified. Existing rolling-volatility feature has a scaling concern detailed below. |
| `data/processed/features/brent_inr_proxy_features.csv` | 474 monthly rows, May 1987-Oct 2026 | 132 common-period joined values, complete | Constructed as Brent USD/barrel × USD/INR. It is an approximate product proxy, not actual landed import cost, and mechanically includes FX. |
| `data/processed/repo_rate_clean.csv` and `features/repo_rate_features.csv` | 165 monthly rows, Jan 2013-Sep 2026 | 132 common-period observations, no missing numeric values observed | Month-key convention (month-end setting vs another measure), source series identity, and release timing remain unresolved. The generated first-difference indicator also requires correction before general use. |
| `data/processed/neer_reer_monthly_clean.csv` and `features/neer_reer_features.csv` | 165 monthly rows, Jan 2013-Sep 2026 | 132 complete common-period monthly observations | Local export mapping, vintage, series interpretation, and release timing remain unresolved. Four candidate indices are potentially redundant. |
| `data/processed/wpi_monthly_clean.csv` | Long table; 146,861 rows, 869 series, Apr 2012-Apr 2026 | WPI All Commodities, Fuel & Power, and Manufactured Products each have 132 positive, complete common-period observations | No duplicate `(comm_code, date)` keys and no missing index cells observed. Dates repeat across different commodities by design; source has 505 zeros in six detailed series with unresolved semantics. WPI is an index, not a publisher-reported inflation target, and release/vintage timing is not established. |
| `data/processed/features/wpi_features.csv` | 169 monthly rows, Apr 2012-Apr 2026 | Generated All Commodities, Primary Articles, Fuel & Power, and Manufactured Products series cover the common calendar | Annual WPI change is index-derived. The feature file's nominal date does not establish that its value was published by the origin. |
| `data/processed/features/research_master_feature_panel.csv` | 646 monthly rows, Jan 1973-Oct 2026 | 132 common-period dates | Outer-merged panel preserves sparse feature missingness. The CPI 12-month published-rate lag has leading missing values; it must not be filled or used to connect the 2025 CPI gap. It is not a pre-cleared model matrix. |
| `data/processed/stage3/stage3_analysis_panel.csv` | 132 rows, Jan 2014-Dec 2024 | Features and index-derived outcomes align on the Stage 3 common sample | Includes contemporaneous reference-month changes. Any use for Stage 4 requires an explicit origin lag; do not use fitted values, residuals, or hypothesis outputs as features. |

The inspected engineered CPI, FX, Brent, Brent-INR proxy, repo, NEER/REER, and WPI feature
tables each have zero duplicate dates and no missing calendar months within Jan 2014-Dec 2024.
Expected leading transformation/lag missingness exists outside or at the start of those
windows; it must not be imputed to join the CPI break.

## 3. Target class counts and episode concentration

The target was computed from the observed `inflation_value` in the continuous CPI segment, not
from CPI index levels and not from Stage 2 predictions.

| Target sample | N | >6% | <=6% | Positive share |
|---|---:|---:|---:|---:|
| Jan 2014-Dec 2024, all published values | 132 | 37 | 95 | 28.0% |
| 1-month eligible targets, Feb 2015-Dec 2024 | 119 | 29 | 90 | 24.4% |
| 3-month eligible targets, Apr 2015-Dec 2024 | 117 | 29 | 88 | 24.8% |
| 6-month eligible targets, Jul 2015-Dec 2024 | 114 | 29 | 85 | 25.4% |

The 2014 elevated episode (Jan-Aug 2014, 8 months) is not in the primary eligible target
windows. Within the eligible sample the observed elevated runs include isolated months,
2019-2020, 2021, 2022, and 2023-2024 episodes. This temporal clustering means 29 monthly
positive labels do not equal 29 independent episodes.

The proposed target-month split provides the following leakage-safe blocks. Validation begins
at a common January 2021 forecast origin; therefore its first target month differs by horizon.
The early post-training labels whose forecast origins precede January 2021 are not validation
observations.

| Block | Target dates | 1-month N / classes | 3-month N / classes | 6-month N / classes |
|---|---|---:|---:|---:|
| Initial training | Eligible start-Dec 2020 | 71: 12 positive, 59 negative | 69: 12 positive, 57 negative | 66: 12 positive, 54 negative |
| Validation | Feb 2021-Dec 2022 (h1); Apr 2021-Dec 2022 (h3); Jul 2021-Dec 2022 (h6) | 23: 12 positive, 11 negative | 21: 12 positive, 9 negative | 18: 10 positive, 8 negative |
| Validation-to-test gap | Jan-Jun 2023 | 6: 2 positive, 4 negative | 6: 2 positive, 4 negative | 6: 2 positive, 4 negative |
| Final test | Jul 2023-Dec 2024 | 18: 3 positive, 15 negative | 18: 3 positive, 15 negative | 18: 3 positive, 15 negative |

At >4%, the eligible target samples have 89/119, 87/117, and 84/114 elevated labels; this
alternative would make the positive class dominant and represents above-midpoint inflation.
At >8%, all three eligible samples have zero elevated observations; supervised evaluation at
that threshold is infeasible on the selected sample.

## 4. Horizon alignment feasibility

For origin month \(t\), the label is the published CPI value at \(t+h\), with \(h=1,3,6\).
Under the common July 2023-December 2024 final-test target window, test origins differ by
horizon:

| Horizon | Eligible origins | Eligible targets | Final-test origins | Final-test targets |
|---|---|---|---|---|
| 1 month | Jan 2015-Nov 2024 (119) | Feb 2015-Dec 2024 | Jun 2023-Nov 2024 | Jul 2023-Dec 2024 |
| 3 months | Jan 2015-Sep 2024 (117) | Apr 2015-Dec 2024 | Apr 2023-Sep 2024 | Jul 2023-Dec 2024 |
| 6 months | Jan 2015-Jun 2024 (114) | Jul 2015-Dec 2024 | Jan 2023-Jun 2024 | Jul 2023-Dec 2024 |

This permits identical **final-test target months** across horizons while preserving exact
origin-to-target mapping. Validation target months differ to preserve chronological maturity
at a common first validation origin. Each model and feature ablation must use the same
origin-target pairs within a horizon. Results across horizons are paired by final-test target
month but not by forecast origin.

## 5. Stage 1 and Stage 2 prediction archive audit

### Stage 1 exchange-rate predictions

**Verified:** `reports/experiments/EXCHANGE_RATE_FORECAST_PREDICTIONS.csv` contains 345 rows:
five models × three horizons × 23 forecasts. The forecast origins cover June 2024-September
2026; it is a final holdout archive, not a sufficiently broad historical feature panel for
training the Stage 4 classifier. Do not treat Stage 1 predictions as realized FX observations.

### Stage 2 FX forecast archive

**Verified:** `reports/experiments/CPI_FX_FORECAST_ARCHIVE.csv` contains 792 rows: 132 origins
from January 2014-December 2024 × three horizons × two methods (fixed ARIMA(0,1,1) and random
walk). Its provenance identifies 383 historical rolling-origin rows per model and 13 reused
Stage 1 rows per model. The Stage 2 independent audit reports origin-only fitting, exact
matching of reused predictions to fixed-specification refits, and no selection using CPI test
outcomes.

This archive is not required for Stage 4's primary model, which uses observed lagged FX
indicators. Forecast FX may be tested only as a separately specified secondary feature because
it adds a nested forecast, model uncertainty, and retrospective (not real-time) provenance.
Never use its future realized FX `actual` values or join it only by target month.

### Stage 2 CPI forecasting outputs

**Verified:** `reports/experiments/CPI_FORECAST_PREDICTIONS.csv` contains 1,134 rows with
forecast origins from January 2023-November 2024; the target months are July 2023-December
2024, with 18 targets per model/configuration/horizon. It is a prior-stage test-results file,
not a predictor dataset. Its predicted/actual values, errors, model ranks, and fitted outputs
must not be supplied to Stage 4 classifiers. The published CPI target source is the eligible
observation for generating Stage 4 labels.

## 6. Leakage and timing findings

1. The existing engineered feature tables are indexed by observation/reference month. Some
   columns at row \(t\) use the row-\(t\) value (e.g., CPI index changes, current Brent changes,
   current FX changes). Directly using those columns for a prediction of \(t+h\) is not safe
   under an end-of-month cutoff without a documented release timestamp. The proposed design
   uses a strict one-reference-month lag and validates feature-end dates at row level.
2. Existing CPI columns include both published inflation and index-derived changes. Only the
   published `inflation_value` defines the target and the proposed CPI-history predictors.
3. Existing rolling windows are trailing by pandas' default behavior, not centered; nevertheless
   their reference month must be lagged to \(t-1\). No complete model matrix should be assumed
   safe merely because feature-engineering comments describe past-only calculations.
4. The `_log_change` helper differences a series after filtering to positive values. An invalid
   or missing month can therefore be skipped; a future eligible feature builder must assert
   monthly continuity and preserve a missing return at gaps.
5. The existing Brent rolling volatility applies an additional factor of 100 to returns already
   expressed as percentage log changes. Its units are 100 times the standard deviation in
   percentage points; absent documentation, treat it as a scale ambiguity and recompute or
   explicitly document/test its units before use.
6. The existing repo change indicator may classify its first missing difference as a change
   because missing values compare unequal to zero. It is not eligible until missingness is
   preserved and the series convention is authenticated.
7. Release timestamps/vintages are absent for key sources. A reference-date lag reduces
   contemporaneous leakage but cannot prove point-in-time availability.

## 7. Feasibility conclusions

- **1-month:** feasible as the primary, constrained retrospective classification pilot; only 3
  elevated test months limit the strength of test claims.
- **3-month:** feasible only as an exploratory secondary horizon; same small number of test
  events and overlapping serial information.
- **6-month:** eligible labels exist, but test evidence remains only 3 positive months and
  models must be trained from earlier origins. Keep exploratory; do not use as a standalone
  operational model ranking.
- **Threshold 8%:** not feasible for supervised fitting/evaluation after the CPI-history
  eligibility start.
- **Real-time warning claim:** not verified until release-date/vintage data are available.

## 8. Integrity and scope

This audit read existing files and prior reports only. It did not download external data, create
data, change raw or processed datasets, modify Stage 1-3 outputs, train a classifier, or start
Stage 5. See the accompanying design, feature matrix, and validation protocol for proposed
implementation controls. Stage 4 implementation remains subject to researcher approval.
