# Stage 3 Model Estimation Report

## Estimation design

The primary family is a parsimonious distributed-lag autoregression of index-derived annual
inflation. Model A replaces signed FX terms with the total monthly USD/INR log change. Model B
includes separate nonnegative depreciation and nonpositive appreciation changes. These are
conditional associations; contemporaneous (`j=0`) coefficients are not real-time information
claims. HAC/Newey-West covariance uses 12 lags because the 12-month inflation outcomes overlap,
with a Bartlett kernel and small-sample correction.

Candidate `p` values are 1–3 and `q` values 0–3. A restricted `p=1, q=6` model is the
pre-specified slower-pass-through sensitivity. The common CPI/WPI All Commodities lag pair is
selected by summed BIC for each model family. AIC is retained as a sensitivity. Candidate
models use a common maximum-lag sample; every candidate is screened to retain at least
7.5 observations per parameter. The selected asymmetric pair is
`p=3`, `q=0`;
the separately BIC-selected symmetric pair is
`p=3`, `q=0`.

## Selected lag structures

| model                       | selected_p | selected_q |
| --------------------------- | ---------- | ---------- |
| symmetric                   | 3          | 0          |
| asymmetric                  | 3          | 0          |
| asymmetric_aic              | 3          | 0          |
| asymmetric_slow_sensitivity | 1          | 6          |

## Primary model fit

| model               | outcome                                  | p | q | control | covariance     | observations | parameters | r_squared | adjusted_r_squared | aic        | bic        | residual_degrees_freedom | residual_std_error |
| ------------------- | ---------------------------------------- | - | - | ------- | -------------- | ------------ | ---------- | --------- | ------------------ | ---------- | ---------- | ------------------------ | ------------------ |
| symmetric_baseline  | cpi_annual_log_inflation                 | 3 | 0 | none    | HAC/Newey-West | 126          | 5          | 0.7615    | 0.753615           | 258.932303 | 273.113713 | 121                      | 0.663076           |
| asymmetric_baseline | cpi_annual_log_inflation                 | 3 | 0 | none    | HAC/Newey-West | 126          | 6          | 0.761598  | 0.751665           | 260.880291 | 277.897982 | 120                      | 0.665695           |
| symmetric_matched   | cpi_annual_log_inflation                 | 3 | 0 | none    | HAC/Newey-West | 126          | 5          | 0.7615    | 0.753615           | 258.932303 | 273.113713 | 121                      | 0.663076           |
| symmetric_baseline  | wpi_all_commodities_annual_log_inflation | 3 | 0 | none    | HAC/Newey-West | 126          | 5          | 0.966951  | 0.965858           | 334.578741 | 348.76015  | 121                      | 0.895223           |
| asymmetric_baseline | wpi_all_commodities_annual_log_inflation | 3 | 0 | none    | HAC/Newey-West | 126          | 6          | 0.967011  | 0.965636           | 336.350915 | 353.368606 | 120                      | 0.898133           |
| symmetric_matched   | wpi_all_commodities_annual_log_inflation | 3 | 0 | none    | HAC/Newey-West | 126          | 5          | 0.966951  | 0.965858           | 334.578741 | 348.76015  | 121                      | 0.895223           |
| symmetric_baseline  | wpi_fuel_power_annual_log_inflation      | 3 | 0 | none    | HAC/Newey-West | 126          | 5          | 0.949905  | 0.948249           | 694.600949 | 708.782359 | 121                      | 3.735858           |
| asymmetric_baseline | wpi_fuel_power_annual_log_inflation      | 3 | 0 | none    | HAC/Newey-West | 126          | 6          | 0.949923  | 0.947836           | 696.555971 | 713.573662 | 120                      | 3.750723           |
| symmetric_matched   | wpi_fuel_power_annual_log_inflation      | 3 | 0 | none    | HAC/Newey-West | 126          | 5          | 0.949905  | 0.948249           | 694.600949 | 708.782359 | 121                      | 3.735858           |
| symmetric_baseline  | wpi_manufactured_annual_log_inflation    | 3 | 0 | none    | HAC/Newey-West | 126          | 5          | 0.980058  | 0.979398           | 203.256475 | 217.437885 | 121                      | 0.531633           |
| asymmetric_baseline | wpi_manufactured_annual_log_inflation    | 3 | 0 | none    | HAC/Newey-West | 126          | 6          | 0.980061  | 0.97923            | 205.234924 | 222.252616 | 120                      | 0.533798           |
| symmetric_matched   | wpi_manufactured_annual_log_inflation    | 3 | 0 | none    | HAC/Newey-West | 126          | 5          | 0.980058  | 0.979398           | 203.256475 | 217.437885 | 121                      | 0.531633           |

Complete candidate BIC/AIC results are in
`artifacts/metrics/pass_through/stage3_lag_selection.csv`. All coefficient estimates, HAC
standard errors, p-values, confidence intervals, and terms are in
`artifacts/metrics/pass_through/stage3_coefficients.csv`. Fitted values and residuals are in
`artifacts/predictions/pass_through/stage3_fitted_values.csv`.

## Coefficients and interpretation

| model               | outcome                                  | term               | coefficient | hac_standard_error | p_value  | ci_95_lower | ci_95_upper | p | q | control | observations | sample_start | sample_end |
| ------------------- | ---------------------------------------- | ------------------ | ----------- | ------------------ | -------- | ----------- | ----------- | - | - | ------- | ------------ | ------------ | ---------- |
| symmetric_baseline  | cpi_annual_log_inflation                 | const              | 0.674889    | 0.240769           | 0.005062 | 0.202991    | 1.146788    | 3 | 0 | none    | 126          | 2014-07-01   | 2024-12-01 |
| symmetric_baseline  | cpi_annual_log_inflation                 | outcome_lag_1      | 1.1108      | 0.084021           | 0.0      | 0.946121    | 1.275479    | 3 | 0 | none    | 126          | 2014-07-01   | 2024-12-01 |
| symmetric_baseline  | cpi_annual_log_inflation                 | outcome_lag_2      | -0.500545   | 0.111518           | 7e-06    | -0.719117   | -0.281973   | 3 | 0 | none    | 126          | 2014-07-01   | 2024-12-01 |
| symmetric_baseline  | cpi_annual_log_inflation                 | outcome_lag_3      | 0.249529    | 0.077962           | 0.001371 | 0.096726    | 0.402333    | 3 | 0 | none    | 126          | 2014-07-01   | 2024-12-01 |
| symmetric_baseline  | cpi_annual_log_inflation                 | fx_lag_0           | 0.004143    | 0.043431           | 0.923996 | -0.080979   | 0.089266    | 3 | 0 | none    | 126          | 2014-07-01   | 2024-12-01 |
| asymmetric_baseline | cpi_annual_log_inflation                 | const              | 0.696639    | 0.201812           | 0.000557 | 0.301095    | 1.092182    | 3 | 0 | none    | 126          | 2014-07-01   | 2024-12-01 |
| asymmetric_baseline | cpi_annual_log_inflation                 | outcome_lag_1      | 1.108655    | 0.079164           | 0.0      | 0.953496    | 1.263814    | 3 | 0 | none    | 126          | 2014-07-01   | 2024-12-01 |
| asymmetric_baseline | cpi_annual_log_inflation                 | outcome_lag_2      | -0.498754   | 0.109017           | 5e-06    | -0.712423   | -0.285085   | 3 | 0 | none    | 126          | 2014-07-01   | 2024-12-01 |
| asymmetric_baseline | cpi_annual_log_inflation                 | outcome_lag_3      | 0.248425    | 0.076601           | 0.001182 | 0.098289    | 0.39856     | 3 | 0 | none    | 126          | 2014-07-01   | 2024-12-01 |
| asymmetric_baseline | cpi_annual_log_inflation                 | depreciation_lag_0 | -0.008713   | 0.053568           | 0.870798 | -0.113703   | 0.096278    | 3 | 0 | none    | 126          | 2014-07-01   | 2024-12-01 |
| asymmetric_baseline | cpi_annual_log_inflation                 | appreciation_lag_0 | 0.02817     | 0.128774           | 0.82684  | -0.224223   | 0.280563    | 3 | 0 | none    | 126          | 2014-07-01   | 2024-12-01 |
| symmetric_matched   | cpi_annual_log_inflation                 | const              | 0.674889    | 0.240769           | 0.005062 | 0.202991    | 1.146788    | 3 | 0 | none    | 126          | 2014-07-01   | 2024-12-01 |
| symmetric_matched   | cpi_annual_log_inflation                 | outcome_lag_1      | 1.1108      | 0.084021           | 0.0      | 0.946121    | 1.275479    | 3 | 0 | none    | 126          | 2014-07-01   | 2024-12-01 |
| symmetric_matched   | cpi_annual_log_inflation                 | outcome_lag_2      | -0.500545   | 0.111518           | 7e-06    | -0.719117   | -0.281973   | 3 | 0 | none    | 126          | 2014-07-01   | 2024-12-01 |
| symmetric_matched   | cpi_annual_log_inflation                 | outcome_lag_3      | 0.249529    | 0.077962           | 0.001371 | 0.096726    | 0.402333    | 3 | 0 | none    | 126          | 2014-07-01   | 2024-12-01 |
| symmetric_matched   | cpi_annual_log_inflation                 | fx_lag_0           | 0.004143    | 0.043431           | 0.923996 | -0.080979   | 0.089266    | 3 | 0 | none    | 126          | 2014-07-01   | 2024-12-01 |
| symmetric_baseline  | wpi_all_commodities_annual_log_inflation | const              | 0.081235    | 0.088748           | 0.360007 | -0.092707   | 0.255178    | 3 | 0 | none    | 126          | 2014-07-01   | 2024-12-01 |
| symmetric_baseline  | wpi_all_commodities_annual_log_inflation | outcome_lag_1      | 1.70183     | 0.06216            | 0.0      | 1.579998    | 1.823661    | 3 | 0 | none    | 126          | 2014-07-01   | 2024-12-01 |
| symmetric_baseline  | wpi_all_commodities_annual_log_inflation | outcome_lag_2      | -0.979555   | 0.09708            | 0.0      | -1.169829   | -0.789282   | 3 | 0 | none    | 126          | 2014-07-01   | 2024-12-01 |
| symmetric_baseline  | wpi_all_commodities_annual_log_inflation | outcome_lag_3      | 0.243086    | 0.067587           | 0.000322 | 0.110619    | 0.375554    | 3 | 0 | none    | 126          | 2014-07-01   | 2024-12-01 |
| symmetric_baseline  | wpi_all_commodities_annual_log_inflation | fx_lag_0           | 0.066926    | 0.056416           | 0.235506 | -0.043647   | 0.177498    | 3 | 0 | none    | 126          | 2014-07-01   | 2024-12-01 |
| asymmetric_baseline | wpi_all_commodities_annual_log_inflation | const              | 0.120068    | 0.108444           | 0.268212 | -0.092478   | 0.332613    | 3 | 0 | none    | 126          | 2014-07-01   | 2024-12-01 |
| asymmetric_baseline | wpi_all_commodities_annual_log_inflation | outcome_lag_1      | 1.702022    | 0.061531           | 0.0      | 1.581423    | 1.82262     | 3 | 0 | none    | 126          | 2014-07-01   | 2024-12-01 |
| asymmetric_baseline | wpi_all_commodities_annual_log_inflation | outcome_lag_2      | -0.976354   | 0.0953             | 0.0      | -1.163139   | -0.789569   | 3 | 0 | none    | 126          | 2014-07-01   | 2024-12-01 |
| asymmetric_baseline | wpi_all_commodities_annual_log_inflation | outcome_lag_3      | 0.240616    | 0.066921           | 0.000324 | 0.109453    | 0.371779    | 3 | 0 | none    | 126          | 2014-07-01   | 2024-12-01 |
| asymmetric_baseline | wpi_all_commodities_annual_log_inflation | depreciation_lag_0 | 0.029772    | 0.086318           | 0.730162 | -0.139408   | 0.198952    | 3 | 0 | none    | 126          | 2014-07-01   | 2024-12-01 |
| asymmetric_baseline | wpi_all_commodities_annual_log_inflation | appreciation_lag_0 | 0.133921    | 0.092892           | 0.149391 | -0.048144   | 0.315986    | 3 | 0 | none    | 126          | 2014-07-01   | 2024-12-01 |
| symmetric_matched   | wpi_all_commodities_annual_log_inflation | const              | 0.081235    | 0.088748           | 0.360007 | -0.092707   | 0.255178    | 3 | 0 | none    | 126          | 2014-07-01   | 2024-12-01 |
| symmetric_matched   | wpi_all_commodities_annual_log_inflation | outcome_lag_1      | 1.70183     | 0.06216            | 0.0      | 1.579998    | 1.823661    | 3 | 0 | none    | 126          | 2014-07-01   | 2024-12-01 |
| symmetric_matched   | wpi_all_commodities_annual_log_inflation | outcome_lag_2      | -0.979555   | 0.09708            | 0.0      | -1.169829   | -0.789282   | 3 | 0 | none    | 126          | 2014-07-01   | 2024-12-01 |
| symmetric_matched   | wpi_all_commodities_annual_log_inflation | outcome_lag_3      | 0.243086    | 0.067587           | 0.000322 | 0.110619    | 0.375554    | 3 | 0 | none    | 126          | 2014-07-01   | 2024-12-01 |
| symmetric_matched   | wpi_all_commodities_annual_log_inflation | fx_lag_0           | 0.066926    | 0.056416           | 0.235506 | -0.043647   | 0.177498    | 3 | 0 | none    | 126          | 2014-07-01   | 2024-12-01 |
| symmetric_baseline  | wpi_fuel_power_annual_log_inflation      | const              | 0.033389    | 0.37354            | 0.928775 | -0.698735   | 0.765514    | 3 | 0 | none    | 126          | 2014-07-01   | 2024-12-01 |
| symmetric_baseline  | wpi_fuel_power_annual_log_inflation      | outcome_lag_1      | 1.574457    | 0.058175           | 0.0      | 1.460436    | 1.688478    | 3 | 0 | none    | 126          | 2014-07-01   | 2024-12-01 |
| symmetric_baseline  | wpi_fuel_power_annual_log_inflation      | outcome_lag_2      | -0.80683    | 0.102797           | 0.0      | -1.008309   | -0.605351   | 3 | 0 | none    | 126          | 2014-07-01   | 2024-12-01 |
| symmetric_baseline  | wpi_fuel_power_annual_log_inflation      | outcome_lag_3      | 0.185817    | 0.073116           | 0.011041 | 0.042512    | 0.329122    | 3 | 0 | none    | 126          | 2014-07-01   | 2024-12-01 |
| symmetric_baseline  | wpi_fuel_power_annual_log_inflation      | fx_lag_0           | 0.219426    | 0.229296           | 0.338589 | -0.229985   | 0.668838    | 3 | 0 | none    | 126          | 2014-07-01   | 2024-12-01 |
| asymmetric_baseline | wpi_fuel_power_annual_log_inflation      | const              | 0.109476    | 0.455786           | 0.810182 | -0.783849   | 1.002801    | 3 | 0 | none    | 126          | 2014-07-01   | 2024-12-01 |
| asymmetric_baseline | wpi_fuel_power_annual_log_inflation      | outcome_lag_1      | 1.5752      | 0.058619           | 0.0      | 1.46031     | 1.69009     | 3 | 0 | none    | 126          | 2014-07-01   | 2024-12-01 |
| asymmetric_baseline | wpi_fuel_power_annual_log_inflation      | outcome_lag_2      | -0.805664   | 0.101082           | 0.0      | -1.00378    | -0.607547   | 3 | 0 | none    | 126          | 2014-07-01   | 2024-12-01 |
| asymmetric_baseline | wpi_fuel_power_annual_log_inflation      | outcome_lag_3      | 0.184473    | 0.071073           | 0.009444 | 0.045173    | 0.323772    | 3 | 0 | none    | 126          | 2014-07-01   | 2024-12-01 |
| asymmetric_baseline | wpi_fuel_power_annual_log_inflation      | depreciation_lag_0 | 0.150142    | 0.46027            | 0.744269 | -0.751971   | 1.052256    | 3 | 0 | none    | 126          | 2014-07-01   | 2024-12-01 |
| asymmetric_baseline | wpi_fuel_power_annual_log_inflation      | appreciation_lag_0 | 0.34434     | 0.586975           | 0.557449 | -0.806111   | 1.494791    | 3 | 0 | none    | 126          | 2014-07-01   | 2024-12-01 |
| symmetric_matched   | wpi_fuel_power_annual_log_inflation      | const              | 0.033389    | 0.37354            | 0.928775 | -0.698735   | 0.765514    | 3 | 0 | none    | 126          | 2014-07-01   | 2024-12-01 |
| symmetric_matched   | wpi_fuel_power_annual_log_inflation      | outcome_lag_1      | 1.574457    | 0.058175           | 0.0      | 1.460436    | 1.688478    | 3 | 0 | none    | 126          | 2014-07-01   | 2024-12-01 |
| symmetric_matched   | wpi_fuel_power_annual_log_inflation      | outcome_lag_2      | -0.80683    | 0.102797           | 0.0      | -1.008309   | -0.605351   | 3 | 0 | none    | 126          | 2014-07-01   | 2024-12-01 |
| symmetric_matched   | wpi_fuel_power_annual_log_inflation      | outcome_lag_3      | 0.185817    | 0.073116           | 0.011041 | 0.042512    | 0.329122    | 3 | 0 | none    | 126          | 2014-07-01   | 2024-12-01 |
| symmetric_matched   | wpi_fuel_power_annual_log_inflation      | fx_lag_0           | 0.219426    | 0.229296           | 0.338589 | -0.229985   | 0.668838    | 3 | 0 | none    | 126          | 2014-07-01   | 2024-12-01 |
| symmetric_baseline  | wpi_manufactured_annual_log_inflation    | const              | 0.053593    | 0.047534           | 0.259548 | -0.039572   | 0.146758    | 3 | 0 | none    | 126          | 2014-07-01   | 2024-12-01 |
| symmetric_baseline  | wpi_manufactured_annual_log_inflation    | outcome_lag_1      | 1.655569    | 0.074166           | 0.0      | 1.510206    | 1.800931    | 3 | 0 | none    | 126          | 2014-07-01   | 2024-12-01 |
| symmetric_baseline  | wpi_manufactured_annual_log_inflation    | outcome_lag_2      | -0.743611   | 0.157745           | 2e-06    | -1.052786   | -0.434436   | 3 | 0 | none    | 126          | 2014-07-01   | 2024-12-01 |
| symmetric_baseline  | wpi_manufactured_annual_log_inflation    | outcome_lag_3      | 0.060845    | 0.100537           | 0.545045 | -0.136204   | 0.257895    | 3 | 0 | none    | 126          | 2014-07-01   | 2024-12-01 |
| symmetric_baseline  | wpi_manufactured_annual_log_inflation    | fx_lag_0           | 0.028212    | 0.027274           | 0.300952 | -0.025244   | 0.081668    | 3 | 0 | none    | 126          | 2014-07-01   | 2024-12-01 |
| asymmetric_baseline | wpi_manufactured_annual_log_inflation    | const              | 0.060382    | 0.05791            | 0.297097 | -0.05312    | 0.173884    | 3 | 0 | none    | 126          | 2014-07-01   | 2024-12-01 |
| asymmetric_baseline | wpi_manufactured_annual_log_inflation    | outcome_lag_1      | 1.656058    | 0.074996           | 0.0      | 1.509069    | 1.803046    | 3 | 0 | none    | 126          | 2014-07-01   | 2024-12-01 |
| asymmetric_baseline | wpi_manufactured_annual_log_inflation    | outcome_lag_2      | -0.744437   | 0.159089           | 3e-06    | -1.056245   | -0.432629   | 3 | 0 | none    | 126          | 2014-07-01   | 2024-12-01 |
| asymmetric_baseline | wpi_manufactured_annual_log_inflation    | outcome_lag_3      | 0.061509    | 0.101634           | 0.545045 | -0.13769    | 0.260709    | 3 | 0 | none    | 126          | 2014-07-01   | 2024-12-01 |
| asymmetric_baseline | wpi_manufactured_annual_log_inflation    | depreciation_lag_0 | 0.021423    | 0.03777            | 0.570573 | -0.052604   | 0.095451    | 3 | 0 | none    | 126          | 2014-07-01   | 2024-12-01 |
| asymmetric_baseline | wpi_manufactured_annual_log_inflation    | appreciation_lag_0 | 0.040529    | 0.058868           | 0.491158 | -0.074851   | 0.155909    | 3 | 0 | none    | 126          | 2014-07-01   | 2024-12-01 |
| symmetric_matched   | wpi_manufactured_annual_log_inflation    | const              | 0.053593    | 0.047534           | 0.259548 | -0.039572   | 0.146758    | 3 | 0 | none    | 126          | 2014-07-01   | 2024-12-01 |
| symmetric_matched   | wpi_manufactured_annual_log_inflation    | outcome_lag_1      | 1.655569    | 0.074166           | 0.0      | 1.510206    | 1.800931    | 3 | 0 | none    | 126          | 2014-07-01   | 2024-12-01 |
| symmetric_matched   | wpi_manufactured_annual_log_inflation    | outcome_lag_2      | -0.743611   | 0.157745           | 2e-06    | -1.052786   | -0.434436   | 3 | 0 | none    | 126          | 2014-07-01   | 2024-12-01 |
| symmetric_matched   | wpi_manufactured_annual_log_inflation    | outcome_lag_3      | 0.060845    | 0.100537           | 0.545045 | -0.136204   | 0.257895    | 3 | 0 | none    | 126          | 2014-07-01   | 2024-12-01 |
| symmetric_matched   | wpi_manufactured_annual_log_inflation    | fx_lag_0           | 0.028212    | 0.027274           | 0.300952 | -0.025244   | 0.081668    | 3 | 0 | none    | 126          | 2014-07-01   | 2024-12-01 |

`appreciation` remains negative-valued. Under the signed-scale symmetry null,
`beta_depreciation = beta_appreciation`; a one-unit appreciation shock contributes
`-beta_appreciation`. The symmetric model with the asymmetric-selected lag pair is included so
the nested comparison uses matching terms and observations. AIC/BIC and R-squared describe
in-sample fit and do not establish predictive value, causality, or stable structural pass-through.

Brent USD changes enter only as a lagged imported-cost extension. The interaction model is
exploratory. The Brent-INR proxy is estimated as a separate proxy-only alternative because it
mechanically includes FX; it is not actual landed import cost. Repo and NEER/REER were not
estimated as controls because their local source/date semantics are unresolved.

## Conditional NARDL assessment

| status                                                                                                                                         | dependent_series                                                   | integration_classifications                                                                                                                                                                                                                                             | finite_sample_bounds_test                                                                                                                                                                                                  | long_run_coefficients                               | gate_details                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             |
| ---------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| cpi_annual_log_inflation: between bounds: inconclusive; wpi_all_commodities_annual_log_inflation: below lower bound: no cointegration evidence | cpi_annual_log_inflation; wpi_all_commodities_annual_log_inflation | cpi_annual_log_inflation=I(1)-consistent; fx_positive_partial_sum=I(1)-consistent; fx_negative_partial_sum=I(1)-consistent | wpi_all_commodities_annual_log_inflation=I(0)-consistent; fx_positive_partial_sum=I(1)-consistent; fx_negative_partial_sum=I(1)-consistent | cpi_annual_log_inflation: stat=4.151217738081686, 95% bounds=(3.841728922809435, 4.850032317925827) | wpi_all_commodities_annual_log_inflation: stat=2.8874527180211054, 95% bounds=(3.841728922809435, 4.850032317925827) | not reported; no established cointegrating relation | [{"bounds_f_statistic": 4.151217738081686, "bounds_lower_95": 3.841728922809435, "bounds_pvalue_lower": 0.036, "bounds_pvalue_upper": 0.1004, "bounds_upper_95": 4.850032317925827, "dependent_series": "cpi_annual_log_inflation", "finite_sample_simulations": 10000, "integration_classifications": "cpi_annual_log_inflation=I(1)-consistent; fx_positive_partial_sum=I(1)-consistent; fx_negative_partial_sum=I(1)-consistent", "long_run_coefficients": "not reported unless the upper bound is exceeded", "model": "ARDL converted to UECM; unrestricted intercept, no trend (PSS case 3)", "observations": 132, "p": 3, "q": 1, "sample_end": "2024-12-01", "sample_start": "2014-01-01", "simulation_seed": 42, "status": "between bounds: inconclusive"}, {"bounds_f_statistic": 2.8874527180211054, "bounds_lower_95": 3.841728922809435, "bounds_pvalue_lower": 0.1357, "bounds_pvalue_upper": 0.2904, "bounds_upper_95": 4.850032317925827, "dependent_series": "wpi_all_commodities_annual_log_inflation", "finite_sample_simulations": 10000, "integration_classifications": "wpi_all_commodities_annual_log_inflation=I(0)-consistent; fx_positive_partial_sum=I(1)-consistent; fx_negative_partial_sum=I(1)-consistent", "long_run_coefficients": "not reported unless the upper bound is exceeded", "model": "ARDL converted to UECM; unrestricted intercept, no trend (PSS case 3)", "observations": 132, "p": 3, "q": 1, "sample_end": "2024-12-01", "sample_start": "2014-01-01", "simulation_seed": 42, "status": "below lower bound: no cointegration evidence"}] |

The NARDL/UECM bounds procedure is conditional; an unsupported or inconclusive bounds result is
not converted into a long-run claim. In particular, a relation involving annual inflation and
cumulative exchange-rate movements is not labelled a long-run elasticity.
