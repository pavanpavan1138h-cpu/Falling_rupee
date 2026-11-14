# Source-to-File Reconciliation

## Method and conclusion

The local files were compared to official source definitions and publication scope. For most files, the official sources establish the meaning of a series identifier or the national series design, but no dated source extract was available for a full-value comparison. WPI is the exception: the complete used sheet matches a later official OEA download cell-for-cell. No source data was changed.

## Reconciliation matrix

| Local file | Source-side evidence | Observed file characteristics | Reconciliation status |
|---|---|---|---|
| `03_USD_INR_Exchange_Rate_Daily.csv` | Federal Reserve/FRED DEXINUS; H.10 quote definition | Daily dates and numeric values; local identifier is consistent with DEXINUS. | **Definition verified; file origin/vintage and full value match not verified.** 552 null numeric fields require source-calendar reconciliation. |
| `03_USD_INR_Exchange_Rate_Monthly.csv` | Federal Reserve/FRED EXINUS; monthly mean of available daily figures; current incomplete month may be preliminary | Monthly series through 2026-10; local identifier consistent with EXINUS. | **Definition verified; file origin/vintage and full value match not verified.** |
| `02_Brent_Crude_Oil_Spot_Price_Monthly_USD_per_Barrel.csv` | EIA/FRED `MCOILBRENTEU`, monthly USD/barrel, NSA | Local identifier and coverage align with that series. | **Series meaning broadly verified; monthly aggregation formula, file origin, vintage and complete value match not verified.** |
| `04_India_RBI_Policy_Repo_Rate_Monthly.csv` | RBI Statistics/DBIE are official entry points; no exact series identifier or metadata export tied to this file | 165 monthly rows, `period,value`; values are consistent with month-end policy settings, date labels are month starts. | **Not source-reconciled.** Month-end-setting interpretation remains an inference; obtain dated RBI series export and metadata. |
| `05_India_RBI_NEER_REER_40_Currency_Monthly.csv` | RBI 40-currency method, 2015–16 base, trade/export measures, weighting details | Preamble then a 165-row monthly table with the four expected NEER/REER variables. | **Definitions and labels align; data values, 2026 vintage and file source not reconciled to a dated RBI export.** |
| `06_India_CPI_General_Combined_Monthly_2024_Base.xlsx` | MoSPI 2024-base CPI release, 2024=100, current-series scope | Local workbook declares `Current`, All India, Combined, CPI (General); coverage 2025-01 to 2026-09. | **Scope/labels align; workbook origin, values, download date and vintage not verified.** |
| `07_India_CPI_General_Combined_Back_Series_2024_Base.xlsx` | MoSPI release documents combined general-index back series 2013-01 to 2024-12; general-level linking only | Local workbook declares `Back`, All India, Combined, CPI (General); coverage 2013-01 to 2024-12. | **Scope/labels align; workbook origin, values, download date and vintage not verified.** |
| `08_India_WPI_Monthly_Index_2011_12_Base_Raw.xls` | OEA/DPIIT official 2011–12 download and workbook | `MONTHLY_INDEX`, 870 × 172 cells; 169 monthly columns, 869 named series. | **Verified content match:** all 870 × 172 cell values match the later official `monthly_index_202606.xls` workbook. This does not establish the uploaded workbook's retrieval date or formal vintage. |

## Findings and follow-up

- CPI workbook date spans form a continuous, adjacent 2013-01–2026-09 general-index calendar. This is consistent with MoSPI's published back/current scope, but is not independent provenance proof. The data are general-index levels; do not infer that detailed historic groups can be chained.
- The repo CSV's period labels and values suggest a month-end setting keyed to month-start. This convention must be verified before interpretation.
- NEER/REER file preamble information is not a substitute for source provenance; the actual monthly table is present and must not be classified as audit-only text.
- WPI's uploaded file matches the later official current download. April and March 2026 differ from their earlier provisional press-release values; the exact local vintage and formal final status of 167.6 remain unresolved.
- A dated, attributable source extract and retrieval timestamp should be recorded for each non-WPI file before its values are described as source-verified.

See [Official Source Verification](./OFFICIAL_SOURCE_VERIFICATION.md) and [Release Timing and Vintage Audit](./RELEASE_TIMING_AND_VINTAGE_AUDIT.md).
