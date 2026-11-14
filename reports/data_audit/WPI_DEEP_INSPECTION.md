# WPI Deep Inspection

## Inspection scope and method

The original `.xls` workbook was read in place using the existing `.venv`, pandas with the `xlrd` engine, and xlrd workbook/cell inspection. No source file was changed, converted, or rewritten.

| Property | Verified result |
|---|---|
| Workbook | `data/raw/08_India_WPI_Monthly_Index_2011_12_Base_Raw.xls` |
| Workbook sheets | One: `MONTHLY_INDEX` |
| Physical sheet dimensions | 870 rows × 172 columns |
| Header | Row 1: `COMM_NAME`, `COMM_CODE`, `COMM_WT`, then month-coded `INDXMMYYYY` fields |
| Data rows | Rows 2–870: 869 named rows |
| Observation columns | Columns D–FP: 169 continuous months, April 2012–April 2026 |
| Blank/non-table areas | No blank rows or columns were found in the used sheet region; no merged cells |
| Workbook properties and notes | xlrd exposed no workbook properties; no separate source note, footnote, or explanatory text area was present in the sheet |
| Monthly index cells | 869 × 169 = 146,861; all are numeric, with no blank or nonnumeric cells |

The sheet dimensions are not an observation count: the 870 rows include a header and 869 commodity/category rows; 172 columns include three identifier/weight fields and 169 monthly fields.

## Categories, codes, weights, and values

The sheet records All commodities, three principal component groups, and a separate food index:

| Row | Category as recorded | Code | `COMM_WT` | April 2026 index |
|---:|---|---:|---:|---:|
| 2 | All commodities | 1000000000 | 100.00000 | 167.6 |
| 3 | I PRIMARY ARTICLES | 1100000000 | 22.61756 | 202.5 |
| 141 | II FUEL & POWER | 1200000000 | 13.15190 | 181.7 |
| 164 | III MANUFACTURED PRODUCTS | 1300000000 | 64.23054 | 152.4 |
| 870 | IV FOOD INDEX | 2000000000 | 24.37758 | 195.5 |

Primary Articles, Fuel & Power, and Manufactured Products weights sum to 100.0. `COMM_WT` is the workbook's field name and the component values are consistent with percentage-style weights, but the workbook does not document the unit or methodology; official definition remains pending.

### Category and subcategory labels observed

The sheet records these Primary Articles groups: Food Articles (Food Grains; Fruits & Vegetables; Milk; Eggs, Meat & Fish; Condiments & Spices; Other Food Articles), Non-Food Articles (Fibres; Oil Seeds; Other Non-Food Articles; Floriculture), Minerals (Metallic Minerals; Other Minerals), and Crude Petroleum & Natural Gas.

Fuel & Power is divided into Coal (Coking Coal; Non-Coking Coal; Lignite), Mineral Oils, and Electricity.

The Manufactured Products divisions recorded in the sheet are:

- Manufacture of Food Products
- Manufacture of Beverages
- Manufacture of Tobacco Products
- Manufacture of Textiles
- Manufacture of Wearing Apparel
- Manufacture of Leather and Related Products
- Manufacture of Wood and of Products of Wood and Cork
- Manufacture of Paper and Paper Products
- Printing and Reproduction of Recorded Media
- Manufacture of Chemicals and Chemical Products
- Manufacture of Pharmaceuticals, Medicinal Chemical and Botanical Products
- Manufacture of Rubber and Plastics Products
- Manufacture of Other Non-Metallic Mineral Products
- Manufacture of Basic Metals
- Manufacture of Fabricated Metal Products, Except Machinery and Equipment
- Manufacture of Computer, Electronic and Optical Products
- Manufacture of Electrical Equipment
- Manufacture of Machinery and Equipment
- Manufacture of Motor Vehicles, Trailers and Semi-Trailers
- Manufacture of Other Transport Equipment
- Manufacture of Furniture
- Other Manufacturing

These are labels transcribed from the workbook's `COMM_NAME` field; the workbook does not supply a separate taxonomy definition. The separate `IV FOOD INDEX` row is present in addition to the three commodity components.

The worksheet itself has no base-year or methodology note. The OEA/DPIIT April 2026 release identifies the series as WPI, base year 2011-12=100, and labels weights as percent. Index values display to one decimal place (`0.0` cell format); that is display precision, not the underlying calculation precision.

## Coverage and integrity checks

- Month headings parse from `INDX042012` to `INDX042026`; all 169 calendar months are present in order with no missing or duplicate month headers.
- All 869 labeled rows share the same 169 month columns.
- No duplicate `COMM_CODE` or `COMM_NAME` values were found.
- No blank or nonnumeric index cells and no negative index values were found.
- No constant series were found. Positive numeric values range from 25.9 to 1,077.1.
- There are 505 numeric zero entries, only in six commodity rows: Peas (Green), Cauliflower, Mango, Orange, Grapes, and Litchi. The workbook does not define whether zero denotes an unavailable/non-applicable observation or a genuine value. These are potential semantic anomalies, not confirmed missing values or errors.
- Economic movements, including large movements in detailed commodity series, have not been classified as outliers without a source definition or economic review.

## April 2026 discrepancy

- Exact source location: worksheet `MONTHLY_INDEX`, cell `FP2` (row 2, column 172).
- Row/category: `All commodities`, code `1000000000`.
- Month/header: April 2026, `INDX042026`.
- Stored value: numeric `167.6`; the cell display format is `0.0`.
- The OEA/DPIIT archived April 2026 press release, dated May 14, 2026, reports All Commodities = 167.0 as provisional (2011-12 base). Its note states provisional WPI figures are finalized after 10 weeks and frozen thereafter.
- The OEA's official current 2011-12-base monthly workbook linked from its download page (`monthly_index_202606.xls`) reports April 2026 = 167.6. The uploaded workbook matches that official workbook at every cell in `MONTHLY_INDEX` (870 × 172; zero cell-value differences).
- This establishes 167.0 as the contemporaneous provisional release value and 167.6 as the later official downloadable-series value. The difference is material, not rounding, and is consistent with a later revision. The reviewed evidence does not include a specific final/revised April press release or observation-level status marker, so the formal final status of 167.6 remains unverified. The local workbook has no per-cell revision timestamp/status.
- OEA April release: https://eaindustry.nic.in/archive_data/wpi_press_release_201112/summary_apr_2026.doc
- OEA 2011-12 series download page and current workbook link: https://eaindustry.nic.in/download_data_1112.asp and https://eaindustry.nic.in/indx_download_1112/monthly_index_202606.xls

## Usability conclusion

The workbook is readable, matches the later official OEA downloadable 2011-12-base workbook cell-for-cell, and has a structurally continuous monthly index matrix through April 2026. The 167.0/167.6 difference is a verified publication-vintage difference (contemporaneous provisional release versus subsequent official downloadable series); the formal final status of 167.6 is not verified. Analytical readiness remains conditional on documenting the six-series zero convention, establishing the local retrieval vintage, and selecting the vintage appropriate to each forecast origin. No preprocessing was performed.
