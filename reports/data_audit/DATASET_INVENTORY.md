# POME EL Dataset Inventory

This inventory records files found in `data/raw/`. Inspection is read-only. File dimensions are spreadsheet dimensions where applicable; they are not necessarily observation counts.

| Dataset | File | Format / sheets | File size (KB) | Physical rows × columns | Verified observation coverage | Meaningful missingness / status |
|---|---|---|---:|---:|---|---|
| Brent spot price | `02_Brent_Crude_Oil_Spot_Price_Monthly_USD_per_Barrel.csv` | CSV | 7.96 | 474 × 2 | 1987-05 to 2026-10; 474 monthly rows | No missing values or duplicate dates detected |
| USD/INR daily | `03_USD_INR_Exchange_Rate_Daily.csv` | CSV | 254.31 | 14,044 × 2 | 1973-01-02 to 2026-10-30; daily observations | 552 missing values in the numeric series; review non-trading-day/gap semantics |
| USD/INR monthly | `03_USD_INR_Exchange_Rate_Monthly.csv` | CSV | 11.89 | 646 × 2 | 1973-01 to 2026-10; 646 monthly rows | No missing values or duplicate dates detected |
| RBI repo rate | `04_India_RBI_Policy_Repo_Rate_Monthly.csv` | CSV | 2.55 | 165 × 2 | 2013-01 to 2026-09; 165 monthly rows | No missing values or duplicate dates detected; source/units pending verification |
| NEER/REER | `05_India_RBI_NEER_REER_40_Currency_Monthly.csv` | CSV, metadata rows plus table | 8.29 | 173 × 7 physical rows | Actual table: 2013-01 to 2026-09; 165 monthly rows | Four index series are present and complete in the table; seven initial non-observation rows account for the apparent raw CSV missingness |
| CPI current | `06_India_CPI_General_Combined_Monthly_2024_Base.xlsx` | XLSX, `CPI Data` | 22.63 | 21 × 15 | 2025-01 to 2026-09; 21 monthly rows | Index complete; inflation blank in 12 records; five all-empty detail columns are unused for this aggregate table |
| CPI back series | `07_India_CPI_General_Combined_Back_Series_2024_Base.xlsx` | XLSX, `CPI Data` | 64.46 | 144 × 15 | 2013-01 to 2024-12; 144 monthly rows | Index complete; inflation blank in 12 records; five all-empty detail columns are unused for this aggregate table |
| WPI | `08_India_WPI_Monthly_Index_2011_12_Base_Raw.xls` | XLS, `MONTHLY_INDEX` | 1,308.50 | 870 × 172 | 2012-04 to 2026-04; 169 monthly columns across 869 labeled series rows | 146,861 index cells are populated; 505 are numeric zero in six commodity rows. Zero semantics are undocumented and require review. |

## WPI table summary

The WPI sheet has one header row (`COMM_NAME`, `COMM_CODE`, `COMM_WT`, followed by month-coded `INDXMMYYYY` columns) and 869 labeled rows. All 169 monthly columns run consecutively from April 2012 through April 2026. Major rows are All commodities, Primary Articles, Fuel & Power, and Manufactured Products. A separate `IV FOOD INDEX` row is also present. See [WPI_DEEP_INSPECTION.md](./WPI_DEEP_INSPECTION.md) for cell-level and quality details.

## Inventory qualifications

- The CPI workbooks have a physical width of 15 columns, but `group`, `class`, `sub_class`, `item`, and `code` are entirely blank for the aggregate All India/Combined/General records. They are not missing observation variables for the aggregate series.
- The WPI spreadsheet's 870 × 172 dimension includes its header row. The analytical date span contains 169 monthly periods, not 870 observations.
- Official source definitions are now verified for the Federal Reserve FX series, EIA Brent, RBI's NEER/REER methodology, MoSPI's CPI design, and OEA WPI. The repo file is not reconciled to an exact RBI series. Except for WPI sheet-content agreement with a later OEA download, these source checks do not authenticate the local files or establish their retrieval dates and vintages. See [OFFICIAL_SOURCE_VERIFICATION.md](./OFFICIAL_SOURCE_VERIFICATION.md).
