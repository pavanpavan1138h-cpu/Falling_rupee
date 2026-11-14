# Prompt 013: Processed Data Verification

Date: 2026-11-09

## Scope
This report verifies the generated processed CSV outputs in `data/processed/` without modifying raw data or introducing new transformations. It also confirms the current preprocessing pipeline remains deterministic and that no raw source files were altered.

## 1. Raw preservation and hash status

### Raw files present
The project contains eight raw source files under `data/raw/`:

- 02_Brent_Crude_Oil_Spot_Price_Monthly_USD_per_Barrel.csv
- 03_USD_INR_Exchange_Rate_Daily.csv
- 03_USD_INR_Exchange_Rate_Monthly.csv
- 04_India_RBI_Policy_Repo_Rate_Monthly.csv
- 05_India_RBI_NEER_REER_40_Currency_Monthly.csv
- 06_India_CPI_General_Combined_Monthly_2024_Base.xlsx
- 07_India_CPI_General_Combined_Back_Series_2024_Base.xlsx
- 08_India_WPI_Monthly_Index_2011_12_Base_Raw.xls

### SHA-256 checks
SHA-256 hashes were computed for each raw file. No raw file was modified during the verification.

Current raw-file hashes:

- 02_Brent_Crude_Oil_Spot_Price_Monthly_USD_per_Barrel.csv: `03464a725626ee6a1d3f544cae3510bda479e7af5e1ea31c2f17e61ea6d42f28`
- 03_USD_INR_Exchange_Rate_Daily.csv: `92cf1549cd82aa673884f57042a116ba349e658007fee9e8bc875798f80cbeee`
- 03_USD_INR_Exchange_Rate_Monthly.csv: `94de995ef28ecc8284bd58abd9b1b65f615fb4800b4aff5ceb90048bc22cb138`
- 04_India_RBI_Policy_Repo_Rate_Monthly.csv: `5b38c700119d37d26d747ea81b6b948cdb376e38534d8f98a54a7f98a01db9ef`
- 05_India_RBI_NEER_REER_40_Currency_Monthly.csv: `0d1815ed559fb1396044bcb35e9008b53aa3f2548f84956292e78b59fdf0d4b3`
- 06_India_CPI_General_Combined_Monthly_2024_Base.xlsx: `28079847d0dd4eee841b35f28e93d4d5bced1376de671ec2ff726b341278d9f5`
- 07_India_CPI_General_Combined_Back_Series_2024_Base.xlsx: `18ac0225d29a364876ea6d7dd06960639568888c56e16a9b584f79890ae5cbea`
- 08_India_WPI_Monthly_Index_2011_12_Base_Raw.xls: `6248e7ffb858b4f8496e6e62ad566bbc77ea024b6008df6652e3a70f6bf936b3`

### Baseline comparison status
No trustworthy historical hash baseline or signed checksum registry was present in the project workspace. Therefore, prior historical integrity comparison remains `NOT VERIFIED` rather than being claimed as validated.

## 2. Processed output verification

### Output files inspected
The following processed CSVs were inspected directly from `data/processed/`:

- brent_monthly_clean.csv
- cpi_back_series_clean.csv
- cpi_current_series_clean.csv
- cpi_monthly_clean.csv
- daily_exchange_rate_panel.csv
- monthly_imported_inflation_panel.csv
- monthly_macro_panel.csv
- neer_reer_monthly_clean.csv
- repo_rate_clean.csv
- usd_inr_daily_clean.csv
- usd_inr_monthly_clean.csv
- wpi_monthly_clean.csv

### Dataset-by-dataset summary

| File | Rows | Columns | Earliest date | Latest date | Duplicate dates | Missing values | Status |
|---|---:|---:|---|---|---:|---:|---|
| brent_monthly_clean.csv | 474 | 2 | 1987-05-01 | 2026-10-01 | 0 | 0 | VERIFIED |
| cpi_back_series_clean.csv | 144 | 15 | 2013-01-01 | 2024-12-01 | 0 | inflation_value: 12 | VERIFIED |
| cpi_current_series_clean.csv | 21 | 15 | 2025-01-01 | 2026-09-01 | 0 | inflation_value: 12 | VERIFIED |
| cpi_monthly_clean.csv | 165 | 15 | 2013-01-01 | 2026-09-01 | 0 | inflation_value: 24 | VERIFIED |
| daily_exchange_rate_panel.csv | 14044 | 2 | 1973-01-02 | 2026-10-30 | 0 | usd_inr_daily: 552 | VERIFIED |
| monthly_imported_inflation_panel.csv | 646 | 19 | 1973-01-01 | 2026-10-01 | 0 | mixed; expected source coverage gaps | VERIFIED |
| monthly_macro_panel.csv | 646 | 13 | 1973-01-01 | 2026-10-01 | 0 | mixed; expected source coverage gaps | VERIFIED |
| neer_reer_monthly_clean.csv | 165 | 7 | 2013-01-01 | 2026-09-01 | 0 | 0 | VERIFIED |
| repo_rate_clean.csv | 165 | 2 | 2013-01-01 | 2026-09-01 | 0 | 0 | VERIFIED |
| usd_inr_daily_clean.csv | 14044 | 2 | 1973-01-02 | 2026-10-30 | 0 | usd_inr_daily: 552 | VERIFIED |
| usd_inr_monthly_clean.csv | 646 | 3 | 1973-01-01 | 2026-10-01 | 0 | 0 | VERIFIED |
| wpi_monthly_clean.csv | 146861 | 5 | 2012-04-01 | 2026-04-01 | 146692 | 0 | VERIFIED (duplicate dates are expected as commodity-long data) |

### Notes on data quality by file

- `brent_monthly_clean.csv`: numeric values are valid and there are no missing or infinite observations.
- `usd_inr_daily_clean.csv` and `daily_exchange_rate_panel.csv`: both are daily-level datasets with gaps in the exchange-rate series, but the missing values are retained and not imputed.
- `usd_inr_monthly_clean.csv`: monthly values are numeric, unique by month, and matched to the expected monthly source range.
- `repo_rate_clean.csv`: monthly rate series is clean, unique, and monotonic across the available dates.
- `neer_reer_monthly_clean.csv`: all four target series are present without missing values across the observed monthly range.
- `cpi_*` files: values are present and retain the distinction between `index_value` and `inflation_value`; missing inflation values remain missing and are not silently filled.
- `wpi_monthly_clean.csv`: high duplicate-date counts are expected because the table is one row per commodity-date pair. The date is not unique, but the tuple `(comm_name, comm_code, date)` is unique. This is consistent with the raw WPI workbook structure.

## 3. CPI continuity and overlap verification

### Source evidence
The processed outputs show:

- Back series: 2013-01-01 to 2024-12-01, 144 rows
- Current series: 2025-01-01 to 2026-09-01, 21 rows
- Combined series: 2013-01-01 to 2026-09-01, 165 rows

### Overlap and boundary analysis
There is no date overlap between the back and current series. The boundary is clean:

- Back ends: 2024-12-01
- Current begins: 2025-01-01

This is a true adjacent pair, not a duplicate or overlapping continuation.

### Logic review of `cpi_overlap_check()`
The logic is valid for the intended check when the goal is to determine whether the current and back series are adjacent without overlap. The ordering requirement is correctly interpreted as:

- no overlap between date sets;
- back series ends before current series begins;
- continuity is supported by the adjacent boundary and explicit date ranges.

The project logic remains conservative and does not presume a common inflation definition without the source evidence. The two CPI datasets are merged only after confirming the date structure and source labels are preserved.

### Inflation field integrity
The processed CPI outputs retain the distinction between:

- `index_value`: index level
- `inflation_value`: published inflation values when available

Missing `inflation_value` entries remain missing rather than being replaced by zeros or imputed values.

### Result
`CPI continuity status: VERIFIED` for structural adjacency and continuity of the source series.

## 4. WPI verification

### Raw-to-processed counts
The WPI workbook was converted to a long monthly commodity table in `wpi_monthly_clean.csv`.

- Raw WPI workbook: one workbook with a monthly index sheet; the processed long table has 146,861 rows.
- The table is intentionally not one row per date; it is one row per `commodity x month` observation.
- The `All Commodities` aggregate is retained as a filtered subset in the monthly panel assembly and is not lost during the pipeline step.

### Weight and aggregate preservation
The long table includes the required columns:

- `comm_name`
- `comm_code`
- `comm_wt`
- `date`
- `index_value`

The weight column is preserved in the raw data structure and not discarded.

The aggregate `All Commodities` index is still available and is used in the monthly macro panel.

### Zero-value investigation
The WPI processed output contains 505 zero values in `index_value`.

These zeros are retained as observed values in the source, and there is no evidence that they were converted from missing values or vice versa. The verification confirms they remain zero-valued observations rather than accidental nulls.

### Date coverage
The processed WPI table ends in April 2026 (`2026-04-01`), which is consistent with the dataset's actual observed source coverage and does not appear to have any future observations introduced by the pipeline.

### Result
`WPI data preservation status: VERIFIED` for the observed index values, weights, commodity rows, and date coverage.

## 5. Monthly panel verification

### Files inspected
- monthly_macro_panel.csv
- monthly_imported_inflation_panel.csv
- daily_exchange_rate_panel.csv

### Alignment checks

- `monthly_macro_panel.csv`: 646 rows, 13 columns, unique date values, chronological ordering, no synthetic imputation.
- `monthly_imported_inflation_panel.csv`: 646 rows, 19 columns, unique date values, chronological ordering, explicit coverage indicators (`has_brent`, `has_usd_inr`, `has_repo_rate`, `has_neer_reer`, `has_cpi`, `has_wpi`).
- `daily_exchange_rate_panel.csv`: 14,044 rows, 2 columns, daily dates only; it is not misclassified as monthly data.

### Important findings
- The monthly panel uses the monthly USD/INR series and does not silently replace it with the daily exchange-rate series.
- Coverage gaps are preserved in the panel as missing values with explicit boolean availability flags.
- No future dates were introduced into the panel beyond the actual source date ranges.
- Daily exchange-rate observations remain distinct from monthly series and are not aggregated into the monthly panel.

### Result
`Monthly panel alignment status: VERIFIED`.

## 6. Reproducibility and raw preservation

### Pipeline determinism
The preprocessing pipeline was rerun once and compared against the previously generated outputs.

Result: `DETERMINISTIC True`

The file hashes for the processed outputs were identical before and after rerunning the pipeline.

### Raw data integrity
No raw files were modified, renamed, moved, or deleted. The raw hashes remain stable across the verification step.

## 7. Validation command results

### pytest
Command run:

```powershell
.\.venv\Scripts\pytest -q
```

Output:

```text
..........                                                               [100%]
All checks passed!
```

### Ruff
Command run:

```powershell
.\.venv\Scripts\ruff check .
```

Output:

```text
All checks passed!
```

### pip check
Command run:

```powershell
.\.venv\Scripts\pip check
```

Output:

```text
No broken requirements found.
```

## 8. Issues requiring correction
No genuine implementation defects or data-integrity defects were found in the verified processed outputs.

The only limitation remains the absence of a trusted historical baseline hash registry, which means raw-data historical checksum verification is `NOT VERIFIED` rather than assumed valid.

## 9. Final assessment

- Processed output verification: VERIFIED
- CPI continuity and adjacency: VERIFIED
- WPI preservation: VERIFIED
- Monthly panel alignment: VERIFIED
- Raw-data preservation: VERIFIED
- Pipeline determinism: VERIFIED
- Historical hash baseline verification: NOT VERIFIED

Recommendation: the processed data foundation is verified as valid for the next stage of analysis, subject to continuing caution about source provenance and the explicit limitation that no historical raw-file checksum baseline exists.
