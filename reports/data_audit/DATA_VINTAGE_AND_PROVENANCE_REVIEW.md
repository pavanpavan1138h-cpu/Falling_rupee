# Data Vintage and Provenance Review

This review records only provenance details observable in the files. An indicator name or filename is not treated as independent verification of the publisher, release vintage, or revision policy.

| Dataset | Information present in source file | Pending verification |
|---|---|---|
| USD/INR daily | Local identifier is consistent with DEXINUS. Official Federal Reserve/FRED metadata verifies INR per USD, daily noon buying rate in New York, not seasonally adjusted. | Local retrieval date, complete value match, archived vintage, and classification of 552 numeric nulls |
| USD/INR monthly | Local identifier is consistent with EXINUS. Official Federal Reserve/G.5 metadata verifies INR per USD and monthly average of available daily rates; current incomplete month may be preliminary. | Local retrieval date, complete value match, and archived vintage |
| Brent monthly | Local identifier is consistent with MCOILBRENTEU. EIA/FRED verifies monthly dollars/barrel, not seasonally adjusted. | Local retrieval date, exact monthly calculation convention, complete value match, and vintage |
| RBI repo rate | Local `period,value` format; month-end setting is inferred from rate changes. RBI provides Statistics/DBIE access. | Exact series identifier, rate definition/unit, source export, date-key rule, retrieval date, and vintage |
| NEER/REER | Local table has four expected measures. RBI official methodology verifies 40-currency series, 2015–16 base, trade/export weighting and definitions. | Full data match to dated RBI export, retrieval date, current vintage and later revision policy |
| CPI current and back series | Local workbooks declare 2024 base and current/back labels. MoSPI official release verifies design and combined general-index back-series scope. | Local file authenticity, extraction date, value match, revision/vintage alignment and any release timestamps |
| WPI | OEA/DPIIT official 2011–12 download and current workbook verified; local sheet matches all workbook cell values. Official April 2026 release dated 2026-05-14 reports 167.0 provisional; later official download reports 167.6. The release says publication is normally on the 14th (or next working day), around two weeks after the reference month, and provisional values are finalized after 10 weeks then frozen. | Local retrieval date and precise vintage remain unknown. The later workbook's 167.6 is not formally identified as final by the evidence reviewed. Numeric zero convention is pending. |

## WPI April 2026 discrepancy

The uploaded WPI workbook reports All commodities = **167.6** in `MONTHLY_INDEX!FP2` (`INDX042026`; one-decimal display). OEA/DPIIT's **May 14, 2026** official April press release reports **167.0 (provisional)**. The later official 2011–12 series workbook (`monthly_index_202606.xls`) reports 167.6, and the uploaded workbook's full sheet matches that download cell-for-cell. This supports a provisional-to-later-download vintage difference; it is not rounding. The release says provisional values are finalized after 10 weeks, but no specific revised-April release or per-observation status marker was found to verify that 167.6 is formally final. The local workbook's own retrieval/vintage date is not recorded.

Official references: https://eaindustry.nic.in/archive_data/wpi_press_release_201112/summary_apr_2026.doc ; https://eaindustry.nic.in/download_data_1112.asp ; https://eaindustry.nic.in/indx_download_1112/monthly_index_202606.xls

## Workbook metadata check

xlrd inspection exposed no WPI workbook document properties. The worksheet contains no source statement, notes, or footnote region. The official OEA publication independently verifies the publisher, base year, and weight units; the workbook's own retrieval date and vintage remain `PENDING VERIFICATION`.

## Other official source evidence

The official definitions and remaining file-level gaps for the other seven datasets are documented in [Official Source Verification](./OFFICIAL_SOURCE_VERIFICATION.md), [Data Definition and Methodology Review](./DATA_DEFINITION_AND_METHODOLOGY.md), and [Source-to-File Reconciliation](./SOURCE_TO_FILE_RECONCILIATION.md). In brief, source definitions are now verified for the Fed exchange-rate series, EIA Brent, MoSPI CPI design, and RBI NEER/REER methodology, but local extraction/vintage records are missing. The repo series remains unreconciled to a specific RBI series.
