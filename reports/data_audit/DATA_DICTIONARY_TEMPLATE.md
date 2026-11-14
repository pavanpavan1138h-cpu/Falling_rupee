# POME EL Data Dictionary Template

This template provides the minimum structure for documenting dataset variables in a traceable and reproducible research workflow. It is intended for future data ingestion and transformation work only and should not assume verified schemas.

## Variable template

| Field | Template entry |
| --- | --- |
| Variable name | [variable_name] |
| Variable description | [Short description of the variable and its economic meaning.] |
| Economic interpretation | [How the variable is used in the research context.] |
| Measurement unit | [Units, index level, percent, INR, etc.] |
| Data type | [float / int / string / date / datetime / categorical / boolean] |
| Frequency | [Daily / Monthly / Quarterly / Annual / Other] |
| Source | [Original source dataset or institution] |
| Missing-value conventions | [null / blank / NA / not available / other] |
| Transformation history | [Original form, derived transformations, conversions, re-indexing] |
| Expected direction or interpretation | [Positive/negative relationship or interpretation, if justified.] |
| Known limitations | [Any known caveats, aggregation issues, or measurement constraints.] |

## Example blank row

| Field | Example |
| --- | --- |
| Variable name | [exchange_rate_inr_usd] |
| Variable description | [Monthly USD/INR exchange rate.] |
| Economic interpretation | [Value of INR relative to USD.] |
| Measurement unit | [INR per USD] |
| Data type | [float] |
| Frequency | [Monthly] |
| Source | [Pending inspection] |
| Missing-value conventions | [null / not available] |
| Transformation history | [Original source values, no derived transformation yet] |
| Expected direction or interpretation | [Higher values indicate depreciation of INR.] |
| Known limitations | [Pending inspection] |

## Governance notes

- Do not infer variable meanings without source documentation.
- Record transformations explicitly rather than silently altering values.
- Distinguish raw variables from derived variables.
- Mark unknown fields as pending inspection.
- For macroeconomic data, document timing and release conventions where relevant.
