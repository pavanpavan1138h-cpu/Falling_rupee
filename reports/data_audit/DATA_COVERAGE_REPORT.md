# POME EL Data Coverage Report

Coverage is calculated from actual observation dates. This report does not merge or transform source datasets.

| Dataset | Start | End | Frequency | Actual observations | Calendar gaps / qualification |
|---|---|---|---|---:|---|
| Brent monthly | 1987-05 | 2026-10 | Monthly | 474 | No gaps or duplicate months detected |
| USD/INR monthly | 1973-01 | 2026-10 | Monthly | 646 | No gaps or duplicate months detected |
| RBI repo rate | 2013-01 | 2026-09 | Monthly | 165 | No gaps or duplicate months detected |
| CPI back series | 2013-01 | 2024-12 | Monthly | 144 | Complete monthly dates |
| CPI current series | 2025-01 | 2026-09 | Monthly | 21 | Complete monthly dates; directly adjacent to back series |
| CPI back + current date coverage | 2013-01 | 2026-09 | Monthly | 165 unique months | No date overlap or missing calendar month; release/vintage compatibility remains to be verified |
| NEER/REER actual table | 2013-01 | 2026-09 | Monthly | 165 | Continuous after excluding seven metadata rows and using the actual header |
| WPI `MONTHLY_INDEX` | 2012-04 | 2026-04 | Monthly | 169 periods per labeled row | Continuous month-coded columns; 869 rows, with 505 numeric zero cells requiring semantic verification |

## Common calendar overlap

- Brent, monthly USD/INR, repo rate, combined CPI date coverage, and the actual NEER/REER table share 2013-01 through 2026-09: **165 calendar months**.
- Adding WPI reduces the common calendar overlap to 2013-01 through 2026-04: **160 calendar months**.
- The overlap is a date-coverage result, not a declaration that all series are analytically compatible. Official definitions are now verified for Federal Reserve FX, EIA Brent, RBI NEER/REER methodology, MoSPI CPI design, and OEA WPI. Local source/vintage provenance remains incomplete, the repo CSV is not mapped to an exact RBI series, and WPI zero semantics remain unknown.
- WPI availability ends five months before the latest month common to the other five monthly sources. CPI inflation has blank values in 12 records in each source workbook even though the CPI index series is populated.

## Stage-specific coverage implications

- Exchange-rate forecasting has monthly file coverage through 2026-10. Official daily/monthly quote and aggregation definitions are verified, but local retrieval/vintages and forecast-origin availability are not.
- CPI forecasting and CPI-dependent stages have a continuous 2013-01 to 2026-09 calendar span. MoSPI's 2024-base scope and general-index linkage are verified; the local workbooks' source/vintages, published inflation blanks, and release-time records still need resolution.
- Pass-through work using repo and NEER/REER is calendar-covered from 2013-01 to 2026-09. RBI's NEER/REER method is documented, but the repo series and local NEER/REER values lack a dated source match.
- WPI/persistence work has monthly columns from 2012-04 to 2026-04. OEA source/content agreement is verified, but the local vintage, formal April 2026 final status, and numeric zero convention remain unresolved.
- No dataset has been merged, aligned, or transformed as part of this audit.

## Source-vintage limitation

See [Official Source Verification](./OFFICIAL_SOURCE_VERIFICATION.md), [Release Timing and Vintage Audit](./RELEASE_TIMING_AND_VINTAGE_AUDIT.md), and [Dataset Suitability Review](./RESEARCH_DATASET_SUITABILITY.md). The common periods above measure only observation-date overlap; they do not establish release-time compatibility or strict real-time usability.
