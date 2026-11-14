# Release Timing and Vintage Audit

## Purpose and status

Forecast-origin suitability depends on when an observation was published and which revision was available at that time. The eight local source files have no consistent retrieval timestamps or source-vintage manifests. The publication facts below come from official documentation; file-specific vintage availability is distinguished from those facts. Accessed 2026-11-09.

| Dataset | Official publication timing / revision evidence | Local file vintage status |
|---|---|---|
| USD/INR daily, Federal Reserve H.10 | Daily observations are published through weekly H.10 releases; the H.10 site provides release and historical pages. The local values are not tagged with a release date. | DEXINUS identifier is consistent with the official series, but complete values were not compared with archived H.10/FRED vintages. Retrieval date and as-of vintage **PENDING VERIFICATION**. |
| USD/INR monthly, Federal Reserve G.5 | Monthly average of available daily rates. The current month can be preliminary if not all daily data are available. G.5 provides release-date and country-data access. | EXINUS identifier is consistent with the official series; the file does not record which monthly release or download vintage was saved. |
| Brent monthly, EIA | EIA publishes the monthly series; the reviewed EIA/FRED metadata does not establish a fixed publication-day rule, exact local extraction date, or the monthly calculation formula. | File identifier is consistent with the official series; no dated source snapshot or revision history is attached. |
| RBI repo | RBI publishes policy-rate/statistical information through official RBI sources and DBIE. The local monthly file contains no release date, series ID, observation-time rule, or source vintage. | Month-end-setting interpretation is a high-confidence inference from step changes, not a verified specification. Exact series and historical vintages **PENDING VERIFICATION**. |
| NEER/REER | RBI methodology is documented in its January 2021 Bulletin article; a current-statistics table is published in the RBI Bulletin. The inspected material does not establish a fixed monthly release day or a complete later revision policy. | Local 40-currency table has 165 months through 2026-09, but its extraction date and vintage are unknown; observations were not matched to a dated RBI export. |
| CPI current/back | MoSPI's January 2026 CPI release was published 12 February 2026 and described January as provisional. It indicates that the February CPI release was due 12 March or next working day. The release establishes monthly timing around the 12th for that example; no general revision-window policy was verified. | Local files have no download/retrieval timestamps or vintage identifiers. The official release's back-series scope aligns with the local date partition but does not authenticate the workbooks. |
| WPI 2011–12 series | OEA's April 2026 release, dated 14 May, says WPI is normally released on the 14th (or next working day), around two weeks after the reference month. It says figures are provisional and finalized after 10 weeks, then frozen. | The uploaded workbook matches the later official `monthly_index_202606.xls` values cell-for-cell. Its local retrieval date is unknown. The later workbook's date/content supports a later vintage, but it does not mark each observation final. |

## April 2026 WPI: contemporaneous and later values

- The OEA 14 May 2026 release reports All Commodities April 2026 = **167.0 provisional** and March = **160.8 provisional**.
- The official downloadable 2011–12 workbook `monthly_index_202606.xls`, last modified 15 July 2026, reports April = **167.6** and March = **161.2**. The uploaded workbook matches the official workbook across all 870 × 172 cells, including those values.
- This is a material between-vintage difference, not one-decimal rounding. The official release's 10-week provisional period makes later revision plausible. However, the available evidence does not include a specific final/revised April press release or an observation-level final-status marker. Therefore 167.6 should be called the later official downloadable-series value; its formal finalized status is **PENDING VERIFICATION**.
- Preserve both values and their source dates in any future point-in-time work. The currently uploaded file's own download date is unknown, so it cannot be assigned a precise vintage solely from its contents.

Sources: [OEA April 2026 release](https://eaindustry.nic.in/archive_data/wpi_press_release_201112/summary_apr_2026.doc), [OEA download page](https://eaindustry.nic.in/download_data_1112.asp), [official workbook](https://eaindustry.nic.in/indx_download_1112/monthly_index_202606.xls).

## Real-time/backtest readiness

No uploaded file has a sufficiently documented source extraction date, point-in-time archive, or observation-level revision history for all of its values. Current historical series can include revisions that were unavailable at a forecast origin. Consequently:

1. Calendar coverage is not evidence of contemporaneous availability.
2. A strict real-time forecast/backtest claim is **not supported** by the current local files.
3. Any future as-of design must define release timestamps, publication calendars, revision handling, and vintage source for each series before preprocessing or model development.
