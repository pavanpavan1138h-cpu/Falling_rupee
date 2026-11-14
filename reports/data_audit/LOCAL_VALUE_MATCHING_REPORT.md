# Local Value Matching Report

This report records whether the uploaded local observations match the corresponding official series or only match the series definition. It is a read-only comparison against official source files retrieved outside `data/raw/`. No source data were overwritten, merged, or edited.

## Summary classification

| Dataset | Official source | Classification | Evidence summary |
|---|---|---|---|
| Brent monthly | FRED/EIA `MCOILBRENTEU` | EXACT MATCH | Local file matches the official monthly series exactly on all 474 dates. |
| USD/INR daily | FRED/Federal Reserve `DEXINUS` | EXACT MATCH (on comparable dates) | Local file matches the official daily source on dates where the official series is published. Missing local values correspond to the same official missing dates. |
| USD/INR monthly | FRED/Federal Reserve `EXINUS` | EXACT MATCH | Local file matches the official monthly average series exactly on all 646 dates. |
| RBI repo rate | RBI Statistics / DBIE | UNVERIFIED | The exact original series could not be authenticated; the file is not yet tied to a dated RBI source export. |
| NEER/REER | RBI Bulletin / DBIE | SOURCE DEFINITION MATCH ONLY | Official RBI methodology and the four target series are identified, but the local values were not matched to a dated RBI export. |
| CPI current | MoSPI 2024-base CPI release | SOURCE DEFINITION MATCH ONLY | Workbook design and coverage match the official published scope, but the workbook's source provenance and exact value-by-value authenticity remain unverified. |
| CPI back series | MoSPI 2024-base CPI back series | SOURCE DEFINITION MATCH ONLY | Workbook design and coverage match the official 2013-2024 back-series scope, but the exact workbook provenance remains unverified. |
| WPI | OEA official workbook and provisional press release | MATCH WITH DOCUMENTED DIFFERENCES | The uploaded workbook exactly matches the later official OEA workbook; a different provisional press release value is documented for April 2026. |

## Exact match evidence

### Brent monthly

- Official source: <https://fred.stlouisfed.org/series/MCOILBRENTEU>
- Source file used for comparison: `reports/audit_downloads/MCOILBRENTEU_fred.csv` (downloaded read-only)
- Result: 474/474 dates match exactly; 0 mismatches.
- Interpretation: the local file is an exact copy of the official FRED monthly series for the shared period.

### USD/INR monthly

- Official source: <https://fred.stlouisfed.org/series/EXINUS>
- Source file used for comparison: `reports/audit_downloads/EXINUS_fred.csv`
- Result: 646/646 dates match exactly; 0 mismatches.
- Interpretation: the local monthly USD/INR file matches the official G.5 monthly average exactly.

### USD/INR daily

- Official source: <https://fred.stlouisfed.org/series/DEXINUS>
- Source file used for comparison: `reports/audit_downloads/DEXINUS_fred.csv`
- Result: the local daily file and the official daily series share the same dates and values where both are populated. The 552 local nulls correspond to official missing dates; no value mismatches were detected on comparable dates.
- Interpretation: the file is a valid daily series representation of the official H.10 quote, with the expected non-trading-day gaps.

## Match with documented differences

### WPI

- Official provisional release: <https://eaindustry.nic.in/archive_data/wpi_press_release_201112/summary_apr_2026.doc>
- Official current workbook: <https://eaindustry.nic.in/indx_download_1112/monthly_index_202606.xls>
- Result: the uploaded workbook matches the later official workbook cell-for-cell. The provisional release reports April 2026 All Commodities = 167.0, while the later official workbook and the uploaded workbook report 167.6.
- Interpretation: this is a documented vintage difference, not a value-level error. The local workbook is an exact copy of the later official workbook but not of the contemporaneous provisional release.

## Source definition match only / unresolved cases

### RBI repo rate

- Official access route: <https://www.rbi.org.in/Scripts/Statistics.aspx> and <https://data.rbi.org.in>
- Current status: impossible to authenticate the local file to a dated RBI export within this audit. The observed values appear consistent with month-end policy repo settings, but that is an inference and not an exact official series match.
- Recommendation: keep the file as an auxiliary series only until a dated RBI/DBIE extract is obtained and matched.

### NEER/REER

- Official sources: <https://www.rbi.org.in/Scripts/BS_ViewBulletin.aspx?Id=20020> and RBI Bulletin Table 36
- Current status: the local file clearly contains the four expected RBI series and 165 continuous monthly observations, but the local file was not matched to a dated RBI export. The methodology and the 40-currency, 2015-16=100 base are verified, but the local file provenance and vintage remain unresolved.
- Recommendation: retain as a source-defined series pending authenticated extraction.

### CPI current and back series

- Official sources: MoSPI launch release and FAQ links in `OFFICIAL_SOURCE_VERIFICATION.md`
- Current status: the workbook design and coverage match the official scope, but no dated source download was authenticated. This is therefore source-definition verification only.
- Recommendation: retain only as a general-index continuity reference unless official downloadable workbooks are matched against the local files.

## Final conclusion

The local files are exact matches to the official sources for Brent, monthly USD/INR, and daily USD/INR on comparable dates. WPI matches the later official OEA workbook, but not the provisional April 2026 release value. The RBI repo, NEER/REER, and CPI files are source-defined and structurally consistent with official publications, but they are not yet exact-file matches to dated official exports.
