# Stage 3 Data Feasibility Audit

**Audit date:** 2026-11-10  
**Scope:** Read-only inspection of existing processed files and prior project audits. No data or
previous-stage outputs were modified.

## 1. Dataset inventory and observed coverage

| Dataset / project file | Observed shape and coverage | Fields / units | Stage 3 feasibility notes |
|---|---|---|---|
| `data/processed/usd_inr_monthly_clean.csv` | 646 monthly rows, Jan 1973–Oct 2026; contiguous, no missing USD/INR values | `date`, `usd_inr_monthly`, `period`; INR per USD | Suitable for log changes in the candidate 2014–2024 common period. Prior source audit identifies monthly Federal Reserve G.5-style average but no attributable retrieval vintage in the file. |
| `data/processed/cpi_monthly_clean.csv` | 165 monthly rows, Jan 2013–Sep 2026; contiguous; index complete | All India / Combined / CPI (General), `index_value`, publisher `inflation_value` | Index: 165 nonmissing and positive. Published inflation: 141 nonmissing, 24 blank. |
| `data/processed/wpi_monthly_clean.csv` | Long table: 146,861 rows, 869 series, 169 months Apr 2012–Apr 2026 | `comm_name`, `comm_code`, `comm_wt`, `date`, `index_value` | No missing numeric index cells. 505 zero values occur in six disaggregated commodity series; meaning is undocumented. |
| WPI `All commodities` | 169 values, Apr 2012–Apr 2026 | WPI headline index | No missing or zero values. 132 monthly values in the 2014–2024 common sample. |
| WPI `II FUEL & POWER` | 169 values, Apr 2012–Apr 2026 | WPI group index | No missing or zero values. Confirm series hierarchy/name before estimation. |
| WPI `III   MANUFACTURED PRODUCTS` | 169 values, Apr 2012–Apr 2026 | WPI group index | No missing or zero values. Confirm series hierarchy/name before estimation. |
| `data/processed/brent_monthly_clean.csv` | 474 contiguous rows, May 1987–Oct 2026; no missing values within file | `brent_usd_per_barrel`, USD/barrel | Complete over common sample; local exact extraction vintage, monthly aggregation rule and revisions remain undocumented. |
| `data/processed/neer_reer_monthly_clean.csv` | 165 contiguous rows, Jan 2013–Sep 2026 | Trade and Export NEER/REER index levels | Complete over common sample; local values not matched to dated source export/vintage. |
| `data/processed/repo_rate_clean.csv` | 165 contiguous rows, Jan 2013–Sep 2026 | `repo_rate`, percentage rate | Complete over common sample, but date key and whether value is month-end setting or another measure remain unresolved. |
| `data/processed/features/research_master_feature_panel.csv` | 646 monthly rows, Jan 1973–Oct 2026; sparse merged features | Existing log/percent changes, CPI and WPI features, controls | Not all fields span the full panel. Use source component files to validate aligned values; do not infer availability from panel row count. |

## 2. CPI continuity, published inflation and index distinction

The CPI source calendar is continuous from January 2013 through September 2026. The published
inflation field has 141 observations and 24 blanks. Its verified contiguous segments are:

| Segment | Count | Treatment in Stage 3 design |
|---|---:|---|
| Jan 2013–Dec 2013 | 12 | Published rate unavailable; index observations are present |
| Jan 2014–Dec 2024 | 132 | Longest uninterrupted published-inflation sample |
| Jan 2025–Dec 2025 | 12 | Published inflation unavailable; do not interpolate or substitute |
| Jan 2026–Sep 2026 | 9 | Separate short segment; do not concatenate across 2025 |

The prior CPI continuity audit documents an aggregate general-index linkage across the 2024-base
transition but warns that this does not establish published-inflation continuity or detailed
component continuity. The local workbook retrieval/vintage is not authenticated. The Stage 3
primary CPI/WPI comparison therefore uses the common Jan 2014–Dec 2024 index-derived annual
log-change definition, avoiding the 2025 transition in the estimation window. A separate CPI
published-inflation sensitivity must remain explicitly publisher-reported and limited to its
continuous sample; no missing values are filled.

The WPI processed file has no published inflation column. Existing `wpi_all_commodities_yoy_inflation`
in the engineered panel is a calculated feature (157 nonmissing values over the whole panel),
not proof of a publisher-reported inflation field. Any Stage 3 outcome calculated from WPI
index levels must be labelled index-derived.

## 3. Common sample

For January 2014–December 2024, the selected files contain 132 consecutive values each for:

- USD/INR monthly rate.
- CPI General index and CPI published inflation.
- WPI All Commodities, Fuel & Power, and Manufactured Products indices.
- Brent crude price.
- Trade NEER and Trade REER.
- Repo rate.

Annual index changes can use the January 2013 index as the prior-year reference for January
2014. USD/INR log change can use December 2013 as its prior-month reference. Thus all 132
calendar outcomes have the necessary observed lag bases in the existing files, before dynamic
regression lags are applied. The model's actual effective N will be lower after its own outcome
and predictor lag construction and must be reported from the final estimation frame.

For a conservative exact CPI/WPI comparison, use the same Jan 2014–Dec 2024 calendar for all
outcomes and controls. WPI continues to April 2026 and the CPI index to September 2026, but
different end dates would confound coefficient comparison and the CPI published rate has a
2025 gap. Any later extended-sample sensitivity is a separate design, not an appended continuous
published-inflation series.

## 4. WPI zeros and hierarchy

The 505 numeric zero observations are in six detailed series: Cauliflower (56), Grapes (70),
Litchi (141), Mango (98), Orange (56), and Peas (Green) (84). Zero semantics are not documented
in the local file or prior data audit. Do not replace these values with missing, interpolate
them, or take their logarithm without authoritative publisher clarification.

The selected headline and two major-group series are positive at all 169 recorded dates and have
zero zeros during the common sample:

- `All commodities`: minimum 104.7, maximum 167.6 over the full available series.
- `II FUEL & POWER`: minimum 75.5, maximum 181.7.
- `III   MANUFACTURED PRODUCTS`: minimum 103.5, maximum 152.4.

These are observed processed-file ranges, not empirical pass-through results. The design can
avoid the zero-valued detailed commodity rows by restricting secondary outcomes to the named
aggregate groups; this does not resolve or reinterpret the six series' zeros.

## 5. Frequency, transformations and quality limits

All relevant series have monthly date keys; the component files have no duplicate months for
the selected series. The candidate levels are positive over the selected estimation window.
The proposed transformation is:

- USD/INR: log first difference, split into positive depreciation and negative appreciation
  components.
- CPI/WPI: log change over 12 months, consistently calculated from the selected index levels.
- Brent, NEER/REER: log changes, as extension/robustness variables.
- Repo: first difference in percentage points only after its monthly observation convention is
  verified.

No interpolation or artificial gap filling is needed for the proposed 2014–2024 common sample.
Prior release/vintage audits show that calendar completeness is not point-in-time availability.
Current files do not establish that all observations or revisions were available in their
nominal month. The research must be reported as retrospective and observation-date based, not as
a real-time backtest.

## 6. Integration feasibility

No I(0)/I(1)/I(2) classification is asserted in this design audit. Unit-root tests, deterministic
terms, and break sensitivity have not been run as part of this design-only task. Before any
NARDL/ARDL bounds procedure, Stage 3 implementation must test the actual estimation series in
levels and first differences, use complementary tests and plots, assess structural-break
sensitivity, and rule out I(2) variables. A standard bounds test is not valid if any included
variable is I(2). If cointegration is not supported, do not use an error-correction
interpretation.

## 7. Feasibility conclusion

**Retrospective CPI/WPI comparison: feasible with limitations.** There are 132 common monthly
index observations before model-specific lag losses; selected aggregate WPI series are positive
and complete. Use clearly labelled index-derived inflation for the primary like-for-like
comparison, plus a separate published-CPI sensitivity. The short sample, unresolved source
vintages, CPI published-inflation gap, WPI zero semantics in detailed commodities, and unresolved
repo/NEER source conventions must be carried into design approval and later reporting.

**Real-time or causal pass-through claim: not established.** Point-in-time releases and an
identification strategy are absent.

## 8. Source files and prior evidence reviewed

- `data/processed/usd_inr_monthly_clean.csv`
- `data/processed/cpi_monthly_clean.csv`
- `data/processed/wpi_monthly_clean.csv`
- `data/processed/brent_monthly_clean.csv`
- `data/processed/neer_reer_monthly_clean.csv`
- `data/processed/repo_rate_clean.csv`
- `data/processed/features/research_master_feature_panel.csv`
- `reports/data_audit/CPI_CONTINUITY_AND_LINKAGE_AUDIT.md`
- `reports/data_audit/RELEASE_TIMING_AND_VINTAGE_AUDIT.md`
- `reports/data_audit/DATA_ISSUES_REGISTER.md`
