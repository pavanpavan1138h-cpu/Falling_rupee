# POME EL Data Quality Audit

This audit is non-destructive. Blank spreadsheet cells outside a meaningful table are not counted as missing observations.

| Dataset | Confirmed checks | Confirmed findings | Status |
|---|---|---|---|
| Brent monthly | 474 rows; monthly dates; date duplicates and nulls checked | 1987-05 to 2026-10; no missing values or duplicate dates | Source definition verified; local vintage pending |
| USD/INR daily | 14,044 rows; complete-row duplicates checked | 552 missing numeric values; non-trading-day versus true-gap interpretation not established | Review needed |
| USD/INR monthly | 646 rows; monthly dates; nulls and duplicate dates checked | 1973-01 to 2026-10; no missing values or duplicate dates | Source definition verified; local vintage pending |
| RBI repo rate | 165 monthly rows; nulls and duplicates checked | 2013-01 to 2026-09; no missing values or duplicate dates | Exact source series and local observation convention pending |
| NEER/REER | Actual header and table rows inspected separately | Four numeric series; 165 continuous monthly observations, 2013-01 to 2026-09; no missing values or duplicate periods in the data table | RBI definitions/base verified; local source/vintage not matched |
| CPI current | `CPI Data` sheet, 21 monthly records | `index` complete; `inflation` blank in 12 records; detail fields `group`, `class`, `sub_class`, `item`, `code` blank throughout | MoSPI design verified; local workbook provenance/vintage pending; blank published inflation entries need context |
| CPI back series | `CPI Data` sheet, 144 monthly records | `index` complete; `inflation` blank in 12 records; same five unused detail fields blank throughout | MoSPI back-series scope verified; local workbook provenance/vintage pending |
| WPI | All sheet cells, header structure, month columns, row labels, and numeric index cells inspected | 169 continuous month columns (2012-04 to 2026-04) × 869 labeled series; no blank or nonnumeric cells in the index block; 505 numeric zero values in six commodity rows; no duplicate codes/names or constant series | OEA source and later-download content match verified; zero semantics, local vintage, and formal 167.6 final status pending |

## WPI confirmed findings and potential anomalies

- The WPI index block contains 146,861 cells (`869 × 169`): all are numeric; none is blank or negative.
- There are 505 numeric zeros, confined to Peas (Green), Cauliflower, Mango, Orange, Grapes, and Litchi. They remain numeric values in the source; the workbook provides no missing-value convention that establishes whether they mean unavailable/not applicable observations or genuine zeros. Treat this as a potential data issue, not as confirmed missingness, and do not replace them.
- No series is constant across the 169 months. Positive values range from 25.9 to 1,077.1. Large movements are not automatically classified as errors or outliers.
- Monthly headers are continuous and common to all row series. Consequently, calendar coverage is identical, although zero-coded entries may affect analytical usability for those six commodity series.
- The April 2026 All commodities value is 167.6, displayed to one decimal place. OEA's official 14 May release reports 167.0 provisional; the later official downloadable workbook and uploaded workbook report 167.6. This is a material between-vintage difference, not rounding. The available evidence does not confirm the later value's formal final status; preserve both source dates and values.

## Other confirmed and unresolved issues

- The NEER/REER CSV's first seven rows are title/audit metadata, row 8 is the actual table header, and the 165 rows after it are monthly observations. The preliminary classification of the entire file as an audit summary was incorrect.
- CPI aggregate index observations are populated in both files. The 12 blank inflation values per file must not be interpreted as missing index observations. Five all-empty hierarchical fields are unused for the aggregate series.
- CPI back/current date ranges are adjacent and form continuous calendar coverage from 2013-01 through 2026-09, with 165 unique months and no overlapping months. Official release/vintage agreement has not been independently established.
- Daily USD/INR missingness remains unresolved; no imputation or calendar filling was performed.
- The local WPI workbook lacks embedded workbook properties, a source statement, notes, footnotes, or a revision/vintage identifier. The official OEA source page and April 2026 press release independently verify the publisher and 2011-12=100 base; the local retrieval/vintage remains unknown.

## Official source and vintage review

Official source publications now verify the definitions of the Federal Reserve daily/monthly USD-INR series, EIA Brent, RBI's 40-currency NEER/REER methodology, MoSPI's 2024-base CPI design, and OEA's 2011-12 WPI methodology and release timing. These source-level facts do not authenticate most local extracts. The RBI repo CSV remains unreconciled to an exact series. WPI is the sole full-sheet content match to a later official source workbook; its local retrieval date is unknown, and the formal final status of April 2026=167.6 remains unverified. See [Official Source Verification](./OFFICIAL_SOURCE_VERIFICATION.md) and [Release Timing and Vintage Audit](./RELEASE_TIMING_AND_VINTAGE_AUDIT.md).
