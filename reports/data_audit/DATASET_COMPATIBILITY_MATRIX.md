# Dataset Compatibility Matrix

This matrix compares observed calendar coverage only. It does not imply that series may be merged or used together without definitions, publication timing, and vintage checks.

| Dataset | Actual monthly date coverage | Count | Calendar continuity | Principal compatibility questions |
|---|---|---:|---|---|
| USD/INR monthly | 1973-01 to 2026-10 | 646 | Continuous | Federal Reserve G.5/FRED definition: monthly mean of available daily rates, current incomplete month may be preliminary; local vintage/full match pending |
| Brent monthly | 1987-05 to 2026-10 | 474 | Continuous | EIA/FRED verifies monthly, USD/barrel, NSA; local vintage and exact monthly calculation convention pending |
| RBI repo rate | 2013-01 to 2026-09 | 165 | Continuous | Month-end policy setting is an inference; exact RBI series ID, units, timing convention and vintage pending |
| CPI back + current | 2013-01 to 2026-09 | 165 | Continuous; two files are adjacent and non-overlapping | MoSPI verifies 2024-base scope and general-index back series; local file provenance/vintage pending; published inflation is blank in 12 records in each file |
| NEER/REER actual table | 2013-01 to 2026-09 | 165 | Continuous | RBI verifies 40-currency method and 2015–16=100; four measures present; local values/vintage not matched |
| WPI `MONTHLY_INDEX` | 2012-04 to 2026-04 | 169 | Continuous month columns | OEA/DPIIT source and exact later-download content match verified; local vintage, formal April final status, and zero semantics pending |

## Pairwise and common calendar coverage

- USD/INR monthly, Brent, RBI repo, combined CPI, and the NEER/REER observation table have a shared span of **2013-01 through 2026-09 (165 months)**.
- Including WPI, the shared calendar span is **2013-01 through 2026-04 (160 months)**.
- WPI ends in April 2026, while the other five monthly sources extend through September 2026 or later.
- Daily USD/INR is not included in the monthly common-overlap calculation.

## Compatibility qualifications

1. Calendar alignment is not publication-time alignment. Official schedules are documented for H.10/G.5, CPI (monthly around the 12th in the example reviewed), and WPI (normally the 14th or next working day); file-level as-of vintages remain absent. EIA, repo, and NEER/REER timing for these local snapshots remains insufficiently documented.
2. CPI has complete index fields but blank published inflation values in 12 rows of each workbook. The index and inflation fields must not be treated as interchangeable.
3. WPI's six affected commodity series contain numeric zeros whose meaning is undocumented. This does not create calendar gaps, but it affects confidence in those values' analytical interpretation.
4. CPI and WPI use different bases (CPI workbook fields: 2024; WPI official series: 2011-12=100). Index levels across those bases are not directly comparable without a justified methodology.
5. Definitions are source-verified for FX, Brent, CPI, NEER/REER, and WPI, but the local files' point-in-time provenance is not. Repo is not source-reconciled. WPI's local retrieval vintage is unrecorded. No merge or transformation is authorized by this audit.

6. WPI April 2026 has a material source-vintage difference: the official May 14 release reports 167.0 provisional; the later official 2011-12 workbook and uploaded workbook report 167.6. The later value's formal final status is not independently confirmed; respect release history at each forecast origin.
