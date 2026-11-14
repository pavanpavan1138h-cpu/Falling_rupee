# CPI Continuity and Linkage Audit

## Objective

This audit evaluates whether the two CPI workbooks can be treated as a coherent monthly series for the project and whether the published inflation fields remain usable across the 2024-base transition.

## Official evidence reviewed

- MoSPI, *First Press Release of Consumer Price Index on Base 2024=100*, 12 February 2026.
- MoSPI, *Frequently Asked Questions (FAQs) on CPI 2024 Series*.

Official source URLs are recorded in `OFFICIAL_SOURCE_VERIFICATION.md` and `DATA_DEFINITION_AND_METHODOLOGY.md`.

## Verified facts

1. MoSPI states that the 2024-base CPI uses 2024=100 and weights from the HCES 2023-24 survey.
2. MoSPI states that all-India rural, urban, and combined general-index back data exist from January 2013 to December 2024.
3. The current 2024-base series begins in January 2025 and continues onward.
4. The general-index linkage uses 2025 as the overlap year with factors of 0.5267 for the combined series, 0.5222 for rural, and 0.5320 for urban.
5. MoSPI explicitly states that direct linkage is valid only at the general-index level because the old and new series use different classifications.
6. The local CPI workbooks contain 12 blank published inflation cells in each file and several all-empty detail columns; these are not missing index observations.

## Index continuity

The two local workbooks cover:

- `06_India_CPI_General_Combined_Monthly_2024_Base.xlsx`: 2025-01 to 2026-09
- `07_India_CPI_General_Combined_Back_Series_2024_Base.xlsx`: 2013-01 to 2024-12

This produces a continuous general-index calendar from 2013-01 to 2026-09 with no overlapping months and no missing month within the combined span. This is the strongest validated continuity claim.

## Published inflation continuity

This is weaker than index continuity.

- The published inflation field is blank in 12 rows of each workbook.
- The local files do not explain why those values are blank.
- MoSPI's stated formula is year-over-year inflation: `(CPI_t - CPI_{t-12}) / CPI_{t-12} * 100`.
- The local files do not provide enough evidence to determine whether those blanks reflect a publication rule, a missing release, or a structural limitation of the workbook.

Therefore, the local published inflation series is not automatically comparable across the transition. Only the index series has a documented continuity claim.

## Component-level continuity

MoSPI explicitly warns that the old and new CPI series use different classifications. The general-index level is directly linkable, but detailed components and group/class/item mappings are not directly continuous. This means the stored index can be used in aggregate form, but the detailed CPI disaggregation should not be treated as a single continuous historical series without a documented bridge.

## Forecast-time availability

The data calendar satisfies continuity, but the user still needs a point-in-time release strategy:

- The current series starts in January 2025 and is not necessarily available for the same calendars as the back series.
- The historical publication date and workbook extraction date are not recorded in the local files.
- The back series and current series are not authenticated as exact official file downloads, even though their labels and coverage align with MoSPI's design.

## Conclusion

The project can defensibly retain the two CPI files as a continuous general-index series only under the following disclosure:

- Retain the series as an aggregate index continuity reference.
- Do not claim direct continuity of published inflation rates across the base-year break without a dated official release and a documented formula or revision rule.
- Do not claim component-level continuity unless MoSPI's link factors are applied and explained at the exact aggregation level being used.
- Do not treat the local workbook values as official downloaded source files without a dated extract match.

In short: the CPI index series is analytically usable at the aggregate general-index level, but the inflation field and detailed component continuity require disclosure and caution.
