# POME EL Data Validation Protocol

This protocol defines the minimum systematic validation workflow for future data ingestion and analysis. It distinguishes between automated validation failures and economic interpretation issues that require analyst judgment.

## Validation categories

### 1. File readability
- Confirm the file can be opened by the project-supported reader.
- Check for encoding, corruption, or unreadable workbook conditions.
- Record whether the file is a raw source file or a derived file.
- Automated validation outcome: file readable or unreadable.
- Economic interpretation: not applicable until the file is readable.

### 2. Schema consistency
- Check whether expected columns or fields are present in the file.
- Confirm that field names are consistent across releases and vintages.
- Distinguish between known schema drift and a missing file component.
- Automated validation outcome: schema matches expectation or deviates.
- Economic interpretation: assess whether the deviation indicates a real conceptual change or a formatting issue.

### 3. Duplicate observations
- Identify duplicate date-value combinations or exact row duplicates.
- Check for repeated observations within the same date and variable space.
- Automated validation outcome: duplicate count and affected rows.
- Economic interpretation: determine whether duplication represents a true repeated release or a data ingestion issue.

### 4. Missing values
- Quantify missing observations by column, date, and dataset.
- Record whether missing values are structural or transient.
- Automated validation outcome: missing-value counts and rates.
- Economic interpretation: evaluate whether missingness is economically meaningful or merely a release lag issue.

### 5. Invalid values
- Screen for impossible numeric values, negative values where not justified, or undefined categorical values.
- Validate against documented measurement units and indicator definitions.
- Automated validation outcome: numeric range check results.
- Economic interpretation: decide whether a value is meaningful but unusual or a genuine data anomaly.

### 6. Date continuity
- Check for gaps, duplicates, or unsorted dates.
- Validate date ordering and temporal continuity within expected frequency windows.
- Automated validation outcome: total gaps, duplicates, sorting issues.
- Economic interpretation: determine whether gaps reflect market holidays, missing reporting, or a process issue.

### 7. Frequency consistency
- Confirm the dataset conforms to the expected observation frequency.
- Verify that transformations do not inadvertently mix daily and monthly reports.
- Automated validation outcome: frequency mismatch detection.
- Economic interpretation: confirm whether a changed frequency is legitimate or indicates a reporting change.

### 8. Unit consistency
- Check measurement units across files, revisions, and transformations.
- Ensure conversions are explicit and reversible when required.
- Automated validation outcome: unit mismatch or conversion check.
- Economic interpretation: determine whether unit changes reflect policy or methodology changes.

### 9. Outlier investigation
- Identify extreme values relative to expected ranges or historical distributions.
- Record whether outliers are due to genuine shocks or reporting problems.
- Automated validation outcome: flagged anomalies.
- Economic interpretation: economic context and event-based explanation are required before labeling a value as valid.

### 10. Structural breaks
- Identify changes in mean, variance, regime, or measurement methodology over time.
- Compare revisions of the same series across releases.
- Automated validation outcome: break-detection summary.
- Economic interpretation: structural breaks may reflect policy changes, redefinitions, or underlying macroeconomic shifts.

### 11. Source reconciliation
- Check consistency between source files, file names, and documented metadata.
- Ensure the provenance record matches the actual stored data files.
- Automated validation outcome: source-match check.
- Economic interpretation: differences may indicate changed releases, revised datasets, or data ownership changes.

### 12. Data revision detection
- Compare release vintages and identify differences in the same historical series.
- Record whether revisions are backdated or affect only recent periods.
- Automated validation outcome: revision count and magnitude.
- Economic interpretation: assess whether revisions affect the research question or estimation design.

### 13. Chronological integrity
- Validate that observations follow the correct order for time-series work.
- Ensure date alignment is respected across merged series.
- Automated validation outcome: sort order and alignment checks.
- Economic interpretation: chronology problems may invalidate comparisons or forecast origins if not corrected deliberately.

## Required documentation outputs

Each validation run should record:

- File name and storage path.
- Dataset identifier.
- Validation timestamp.
- Check result and severity.
- Whether the issue is automated or requires economic interpretation.
- Follow-up action required.

## Example validation log entry

| Check | Result | Severity | Interpretation |
| --- | --- | --- | --- |
| File readability | PASS | Low | File opened successfully. |
| Duplicate observations | FAIL | Medium | Duplicate records detected; review required. |
| Date continuity | WARN | Medium | Potential reporting gap; investigate context. |
| Unit consistency | PASS | Low | Units remain aligned with documented source. |

## Governance rules

- Automated checks do not replace economic judgment.
- Document both the technical outcome and the interpretation.
- Do not overwrite raw data during validation.
- Mark unknown issues as pending inspection until confirmed.
