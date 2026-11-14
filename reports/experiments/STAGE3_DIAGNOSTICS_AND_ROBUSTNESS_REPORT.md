# Stage 3 Diagnostics and Robustness Report

## Residual and stability checks

| outcome                                  | model               | observations | breusch_godfrey_lm_pvalue | ljung_box_12_pvalue | breusch_pagan_lm_pvalue | ramsey_reset_pvalue | jarque_bera_pvalue | cusum_pvalue | condition_number |
| ---------------------------------------- | ------------------- | ------------ | ------------------------- | ------------------- | ----------------------- | ------------------- | ------------------ | ------------ | ---------------- |
| cpi_annual_log_inflation                 | symmetric_baseline  | 126          | 0.41554                   | 5.2e-05             | 0.208352                | 0.132271            | 0.000317           | 0.117114     | 36.881573        |
| cpi_annual_log_inflation                 | asymmetric_baseline | 126          | 0.379375                  | 5.1e-05             | 0.307634                | 0.132389            | 0.000232           | 0.128088     | 40.529658        |
| wpi_all_commodities_annual_log_inflation | symmetric_baseline  | 126          | 0.382064                  | 0.00283             | 0.495009                | 0.215086            | 0.492236           | 0.510773     | 23.066429        |
| wpi_all_commodities_annual_log_inflation | asymmetric_baseline | 126          | 0.582816                  | 0.0024              | 0.318496                | 0.221439            | 0.564482           | 0.614984     | 23.693491        |
| wpi_fuel_power_annual_log_inflation      | symmetric_baseline  | 126          | 0.417057                  | 0.010812            | 0.767793                | 0.542192            | 0.014282           | 0.471277     | 30.668204        |
| wpi_fuel_power_annual_log_inflation      | asymmetric_baseline | 126          | 0.473348                  | 0.010593            | 0.889151                | 0.531858            | 0.015312           | 0.518486     | 67.515025        |
| wpi_manufactured_annual_log_inflation    | symmetric_baseline  | 126          | 0.065693                  | 4e-06               | 0.021282                | 0.733349            | 0.034948           | 0.75446      | 32.657053        |
| wpi_manufactured_annual_log_inflation    | asymmetric_baseline | 126          | 0.0581                    | 3e-06               | 0.025088                | 0.745244            | 0.034663           | 0.727888     | 32.760153        |

Full numerical results are in
`artifacts/metrics/pass_through/stage3_diagnostics.csv`; influential rows and recursive
coefficient paths are in the corresponding Stage 3 metrics files. Breusch–Godfrey and
Ljung–Box assess residual serial correlation, Breusch–Pagan assesses heteroskedasticity,
RESET is a functional-form diagnostic, Jarque–Bera describes residual shape, and CUSUM assesses
parameter stability. None is a validity certificate, and HAC covariance does not resolve
endogeneity, omitted variables, or vintage uncertainty.

Largest absolute Cook's-distance observations in the reported diagnostic models:

| row | dfb_const | dfb_outcome_lag_1 | dfb_outcome_lag_2 | dfb_outcome_lag_3 | dfb_fx_lag_0 | cooks_d  | standard_resid | hat_diag | dffits_internal | student_resid | dffits    | date                | outcome                                  | model               | dfb_depreciation_lag_0 | dfb_appreciation_lag_0 |
| --- | --------- | ----------------- | ----------------- | ----------------- | ------------ | -------- | -------------- | -------- | --------------- | ------------- | --------- | ------------------- | ---------------------------------------- | ------------------- | ---------------------- | ---------------------- |
| 71  | 0.408665  | -0.790196         | 0.245381          | 0.273262          | -0.082841    | 0.278646 | 3.706534       | 0.092074 | 1.180353        | 3.920455      | 1.248476  | 2020-06-01 00:00:00 | wpi_fuel_power_annual_log_inflation      | symmetric_baseline  |                        |                        |
| 71  | 0.433828  | -0.777698         | 0.25201           | 0.25602           |              | 0.237035 | 3.686043       | 0.094756 | 1.192565        | 3.897951      | 1.261125  | 2020-06-01 00:00:00 | wpi_fuel_power_annual_log_inflation      | asymmetric_baseline | -0.214051              | 0.154958               |
| 82  | -0.109446 | -0.544469         | 0.591494          | -0.27254          |              | 0.218729 | 3.556061       | 0.094024 | 1.14559         | 3.743973      | 1.206126  | 2021-05-01 00:00:00 | cpi_annual_log_inflation                 | asymmetric_baseline | 0.049616               | -0.913716              |
| 82  | 0.150841  | -0.596372         | 0.609408          | -0.299112         | -0.651316    | 0.163926 | 3.471554       | 0.063679 | 0.905336        | 3.643378      | 0.950145  | 2021-05-01 00:00:00 | cpi_annual_log_inflation                 | symmetric_baseline  |                        |                        |
| 91  | -0.156405 | 0.049348          | -0.273908         | 0.535109          | 0.088229     | 0.163922 | 2.963428       | 0.085363 | 0.905324        | 3.064457      | 0.936188  | 2022-02-01 00:00:00 | wpi_manufactured_annual_log_inflation    | symmetric_baseline  |                        |                        |
| 83  | -0.21112  | -0.552975         | 0.171718          | 0.186971          | -0.061701    | 0.145826 | -2.763318      | 0.087164 | -0.853892       | -2.843045     | -0.878528 | 2021-06-01 00:00:00 | wpi_fuel_power_annual_log_inflation      | symmetric_baseline  |                        |                        |
| 91  | 0.021838  | 0.057617          | -0.281102         | 0.544752          |              | 0.144091 | 2.948924       | 0.090427 | 0.92981         | 3.049172      | 0.961419  | 2022-02-01 00:00:00 | wpi_manufactured_annual_log_inflation    | asymmetric_baseline | -0.111719              | 0.243064               |
| 108 | 0.360281  | 0.253082          | -0.56521          | 0.6911            | -0.026311    | 0.139859 | 2.95146        | 0.074311 | 0.836238        | 3.051119      | 0.864474  | 2023-07-01 00:00:00 | wpi_all_commodities_annual_log_inflation | symmetric_baseline  |                        |                        |
| 83  | -0.356899 | -0.57212          | 0.163424          | 0.210091          |              | 0.137972 | -2.787079      | 0.096308 | -0.909852       | -2.869882     | -0.936883 | 2021-06-01 00:00:00 | wpi_fuel_power_annual_log_inflation      | asymmetric_baseline | 0.176192               | -0.287084              |
| 109 | -0.210474 | -0.713748         | 0.698088          | -0.478192         | -0.218389    | 0.128795 | -2.115337      | 0.12581  | -0.80248        | -2.146643     | -0.814357 | 2023-08-01 00:00:00 | wpi_all_commodities_annual_log_inflation | symmetric_baseline  |                        |                        |

## Robustness comparisons

| specification                                                                             | status    | observations | p | q | bic        | bic_delta | r_squared | note                                                                                  |
| ----------------------------------------------------------------------------------------- | --------- | ------------ | - | - | ---------- | --------- | --------- | ------------------------------------------------------------------------------------- |
| CPI baseline asymmetric log/log                                                           | estimated | 126          | 3 | 0 | 277.897982 | 0.0       | 0.761598  |                                                                                       |
| CPI lag-only FX                                                                           | estimated | 126          | 3 | 1 | 275.928734 | -1.969249 | 0.765295  | Excludes same-month FX; lag structure remains preselected.                            |
| CPI six-month FX lag sensitivity (p=1,q=6)                                                | estimated | 126          | 1 | 6 | 335.809562 | 57.91158  | 0.742829  | Pre-specified slower-pass-through sensitivity; not used for primary selection.        |
| CPI publisher-reported inflation                                                          | estimated | 126          | 3 | 0 | 292.707004 |           | 0.75792   | Separate CPI published-rate outcome; no 2025 gap filling.                             |
| CPI simple annual percent and simple FX percent                                           | estimated | 126          | 3 | 0 | 290.780248 |           | 0.759957  | Distinct robustness transformations.                                                  |
| WPI All Commodities simple annual percent and simple FX percent                           | estimated | 126          | 3 | 0 | 360.603234 |           | 0.968386  | Distinct robustness transformations.                                                  |
| CPI Brent USD lagged change                                                               | estimated | 126          | 3 | 0 | 282.273755 | 4.375772  | 0.762468  | Lagged imported-cost extension; local vintage remains unauthenticated.                |
| CPI Brent-INR proxy-only                                                                  | estimated | 126          | 3 | 0 | 272.431031 | -5.466952 | 0.762788  | Approximate proxy only; no FX split terms due mechanical FX content.                  |
| WPI All Commodities Brent USD lagged change                                               | estimated | 126          | 3 | 0 | 346.102625 | -7.265981 | 0.970032  | Lagged imported-cost extension; local vintage remains unauthenticated.                |
| WPI All Commodities Brent-INR proxy-only                                                  | estimated | 126          | 3 | 0 | 337.849176 | -15.51943 | 0.969692  | Approximate proxy only; no FX split terms due mechanical FX content.                  |
| cpi_annual_log_inflation: omit historical 95th-percentile extreme changes                 | estimated | 125          | 3 | 0 | 276.867302 |           | 0.760729  | Threshold 4.07802% from 1990-2013; 1 Stage 3 months flagged across the common sample. |
| wpi_all_commodities_annual_log_inflation: omit historical 95th-percentile extreme changes | estimated | 125          | 3 | 0 | 350.444648 |           | 0.967284  | Threshold 4.07802% from 1990-2013; 1 Stage 3 months flagged across the common sample. |
| cpi_annual_log_inflation: pre-2020 (restricted p=1,q=1)                                   | estimated | 68           | 1 | 1 | 149.871927 |           | 0.777477  | Exploratory; period-specific estimation has limited power.                            |
| cpi_annual_log_inflation: 2020-onward (restricted p=1,q=1)                                | estimated | 58           | 1 | 1 | 149.069908 |           | 0.468575  | Exploratory; period-specific estimation has limited power.                            |
| wpi_all_commodities_annual_log_inflation: pre-2020 (restricted p=1,q=1)                   | estimated | 68           | 1 | 1 | 199.343398 |           | 0.918826  | Exploratory; period-specific estimation has limited power.                            |
| wpi_all_commodities_annual_log_inflation: 2020-onward (restricted p=1,q=1)                | estimated | 58           | 1 | 1 | 215.392019 |           | 0.951311  | Exploratory; period-specific estimation has limited power.                            |

The extreme-movement cutoff is the 95th percentile of absolute monthly USD/INR log changes in
1990–2013, computed before the Stage 3 estimation window. The pandemic subperiod is defined
before estimation as March 2020 onward; subperiod fits use a restricted `p=1, q=1` specification
and have low power. Brent and proxy analyses are separate. Optional repo/NEER/REER control fits
were not run because their local series mapping/date conventions remain unverified.
No synthetic empirical observations were generated.
