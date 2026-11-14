# Stage 3 Data Validation Report

**Scope:** Read-only source loading and Stage 3 derived variables. No source dataset was changed.

## Sources and target identity

The All India / Combined / CPI (General) record was selected by its explicit fields. The
selected sample labels are `Back` and base year(s)
`2024.0`.
The primary CPI and all WPI outcomes below are **index-derived annual log inflation**, not
publisher-reported inflation. The publisher CPI `inflation_value` remains a separate series;
its values were not filled or replaced.

The common source calendar is **132 consecutive months**
(2014-01-01 to 2024-12-01). The 12-month transformation uses
the prior-year index observation; USD/INR January 2014 change uses December 2013. After the
maximum pre-specified outcome/FX lag construction (six months for the slow-pass-through
sensitivity), each common-sample model has
126 candidate observations before any
control-specific loss.
No missing values were interpolated.

| series                                   | nonmissing | missing |
| ---------------------------------------- | ---------- | ------- |
| fx_log_change_pct                        | 132        | 0       |
| cpi_annual_log_inflation                 | 132        | 0       |
| wpi_all_commodities_annual_log_inflation | 132        | 0       |
| wpi_fuel_power_annual_log_inflation      | 132        | 0       |
| wpi_manufactured_annual_log_inflation    | 132        | 0       |

### CPI published inflation

The source file has 0 missing published inflation
values in the common 2014–2024 sample. The known 2025 gap and separate 2026 segment were not
bridged. Published inflation was modeled only as a distinct CPI sensitivity.

## WPI zero-value investigation

The full WPI table contains **505 numeric zeros** across
6 detailed series. Source values were preserved. The local workbook and prior
data issue register do not establish whether these zeros are published values, missing-value
codes, structural non-applicability, or another convention. They were not changed or logged.
Exact zero dates for every affected row are in
`data/processed/stage3/stage3_wpi_zero_observations.csv`.

- **Cauliflower** (code `1101020108`): 56 zero observations, 2012-05 through 2025-08.
- **Grapes** (code `1101020208`): 70 zero observations, 2012-05 through 2025-09.
- **Litchi** (code `1101020211`): 141 zero observations, 2012-04 through 2026-04.
- **Mango** (code `1101020202`): 98 zero observations, 2012-09 through 2026-03.
- **Orange** (code `1101020204`): 56 zero observations, 2012-07 through 2025-10.
- **Peas (Green)** (code `1101020106`): 84 zero observations, 2012-05 through 2025-10.

The selected WPI outcomes were checked independently:

| series                      | code       | weight   | observations | missing | zeros | nonpositive | minimum | maximum |
| --------------------------- | ---------- | -------- | ------------ | ------- | ----- | ----------- | ------- | ------- |
| All commodities             | 1000000000 | 100.0    | 132          | 0       | 0     | 0           | 107.1   | 156.7   |
| II FUEL & POWER             | 1200000000 | 13.1519  | 132          | 0       | 0     | 0           | 75.5    | 167.1   |
| III   MANUFACTURED PRODUCTS | 1300000000 | 64.23054 | 132          | 0       | 0     | 0           | 108.0   | 145.0   |

Only the selected headline and major-group series, all positive and complete in this sample,
were used for logarithms. Affected detailed commodity rows were not used.

## Constructed variables and information timing

- USD/INR log change is `100 * diff(log(USD/INR))`; positive values indicate rupee depreciation.
- `depreciation = max(change, 0)` is nonnegative; `appreciation = min(change, 0)` retains its
  negative sign.
- Positive and negative partial sums start at zero immediately before January 2014 and cumulate
  only in-sample changes.
- CPI General, WPI All Commodities, Fuel & Power, and Manufactured Products annual outcomes use
  `100 * (ln(index_t) - ln(index_t-12))`. Their simple annual index changes are separate
  robustness variables.
- Brent USD and Brent-INR proxy changes, repo changes, and NEER/REER changes were constructed
  from the existing processed inputs. The Brent-INR field is an approximate product proxy, not
  actual landed import cost.

## Provenance and limitations

Prior project audits still leave local FX, CPI, Brent, repo, and NEER/REER vintages or date
semantics incompletely authenticated. The CPI record's 2024-base series transition and the
WPI detailed-series zero convention remain source-level limitations. Therefore the analysis is
retrospective and observation-date based, not a real-time or causal pass-through study.
Repo and NEER/REER controls were not included in the primary models because their source/date
conventions remain unverified.
