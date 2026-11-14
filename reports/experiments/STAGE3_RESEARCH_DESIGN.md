# Stage 3 Research Design: Asymmetric Exchange-Rate Pass-Through

**Status:** Approved research blueprint; Stage 3 implementation authorized by the researcher's explicit request on 2026-11-10. No Stage 3 model has yet been implemented or estimated.  
**Prepared:** 2026-11-10  
**Approval:** Approved with limitations for implementation; retrospective and associational claims only.

## 1. Research question and scope

Does a change in the rupee's value have different magnitude, timing, and persistence when the
rupee depreciates versus appreciates? Does the relationship differ for Indian consumer prices
(CPI) and wholesale prices (WPI), including WPI Fuel & Power and Manufactured Products? Are
these associations different under imported-cost conditions, especially changes in Brent crude?

USD/INR is rupees per US dollar. An increase in USD/INR is rupee depreciation; a decrease is
appreciation. Asymmetry is a testable possibility, not a maintained conclusion. All proposed
coefficients describe conditional statistical relationships. The design does not identify a
causal pass-through effect.

This blueprint authorizes only the Stage 3 econometric implementation. It does not authorize
modification of source datasets, synthetic research observations, Stage 4, SHAP, or dashboard
work.

## 2. Recommended primary specification

Use a parsimonious **asymmetric distributed-lag model of annual index-derived inflation** on a
common CPI/WPI sample. Use the same calendar months, transformation, baseline lag protocol, and
exchange-rate terms for each outcome:

\[
\pi^{s}_t = \alpha_s + \sum_{i=1}^{p}\rho_{s,i}\pi^{s}_{t-i}
 + \sum_{j=0}^{q}\beta^{+}_{s,j}Dep_{t-j}
 + \sum_{j=0}^{q}\beta^{-}_{s,j}App_{t-j}
 + \delta_s' Z_t + \varepsilon^{s}_t ,
\]

where \(s\) identifies CPI or a selected WPI index, \(\pi^s_t =
100[\ln(P^s_t)-\ln(P^s_{t-12})]\), \(Dep_t=\max(\Delta e_t,0)\), and
\(App_t=\min(\Delta e_t,0)\). `App` is negative by construction. Under a symmetric linear
response, \(\beta^+_j=\beta^-_j\): equal-size positive and negative exchange-rate movements
then have equal coefficient magnitudes and opposite signed effects. Do not compare the two
coefficients as if `App` were positive.

This is the recommended primary model because it tests short-run asymmetry directly while
avoiding a cointegration claim between an inflation rate and accumulated exchange-rate changes.
The CPI and WPI index-derived outcomes are constructed with the same formula; they are not
presented as official published inflation. The primary specification starts with exchange-rate
terms and outcome lags. Add at most one imported-cost control in a pre-specified extension,
subject to the provenance and collinearity rules below.

The maximum lag length should be conservative for the 132-month common sample. Compare a
small candidate set (maximum lags 3 and 6) using BIC as the primary selection criterion and
AIC as a sensitivity check, while enforcing the parameter-to-observation limits and retaining
the same selected lag structure across CPI/WPI comparisons where feasible. Treat 12-month
lag structures as exploratory only, with an explicit effective-sample and parameter-count
review. Freeze the lag-selection rule before examining final coefficient significance.

### Response interpretation

- Short-run asymmetry: joint Wald test of \(H_0:\beta^+_j=\beta^-_j\) for all selected
  exchange-rate lags.
- Timing: compare the lag-specific response paths and cumulative dynamic multipliers at
  1, 3, and 6 months. Confidence intervals should account for serial dependence.
- Persistence: report the impulse/dynamic response path implied by the outcome autoregressive
  terms, including the horizon at which the response becomes small or indistinguishable from
  zero. Do not label the cumulative response of an inflation-rate equation a cointegrating
  long-run elasticity.
- Same-month terms (`j=0`) are contemporaneous association, not evidence that the observation
  was available before the month's CPI/WPI price formation or publication. Include a lag-only
  robustness specification to assess this timing sensitivity.

## 3. Dependent variables and sample decision

### Primary comparable outcomes

Use the general CPI index and WPI index levels to calculate consistent annual log changes:

\[
\pi^{s,\mathrm{index}}_t=100\{\ln(P^s_t)-\ln(P^s_{t-12})\}.
\]

For the main CPI/WPI comparison, use **January 2014–December 2024**, the 132-month common
calendar. The CPI and WPI aggregate and selected major-group index values are positive and
complete on these dates. The preceding 2013 CPI index observations allow the first annual
change in January 2014 to be calculated without filling a missing value. Report the exact
effective estimation observations after model lags are formed; 132 is the available outcome
calendar, not the lag-adjusted regression sample size.

Keep these outcomes explicitly labelled `index-derived annual log inflation`. They are not
publisher-reported inflation rates. For a formula-comparability sensitivity, calculate simple
year-on-year percent changes from the same index levels and label those separately.

### Published-inflation sensitivity

The CPI file has 132 consecutive published inflation observations from January 2014 through
December 2024, no published values during 2025, and a separate nine-observation segment from
January through September 2026. Do not interpolate, calculate replacements for, or concatenate
the 2026 segment across the gap. Re-estimate a CPI-only sensitivity using the published CPI
inflation field, and report it distinctly from index-derived CPI inflation.

The processed WPI file contains index values, not a publisher-reported inflation field. The
existing feature panel includes calculated WPI year-on-year inflation, but it is a derived
measure, not a published WPI inflation observation. Do not describe the CPI-published/WPI-derived
comparison as perfectly like-for-like. For cross-outcome coefficient comparisons, use the common
index-derived definitions above.

### Outcome set

1. CPI General All India Combined index (primary consumer-price outcome).
2. WPI All Commodities index (primary wholesale-price outcome).
3. WPI `II FUEL & POWER` and `III MANUFACTURED PRODUCTS` (pre-specified secondary outcomes,
   subject to confirmation of series definitions and no-zero/positive-level checks).

Compare CPI and WPI coefficients using the same months and model terms. WPI's wholesale and
upstream composition differs from the consumer basket; differences in estimates are not, by
themselves, evidence of household welfare or causal transmission differences.

## 4. Exchange-rate asymmetry construction

For the monthly USD/INR rate \(E_t>0\), use:

\[
\Delta e_t=100[\ln(E_t)-\ln(E_{t-1})],\quad
Dep_t=\max(\Delta e_t,0),\quad
App_t=\min(\Delta e_t,0).
\]

Thus positive \(\Delta e_t\) means depreciation and negative \(\Delta e_t\) means appreciation.
Retain appreciation as a negative-valued regressor; document coefficient and response signs
accordingly. Compute the December 2013-to-January 2014 FX change using the observed December
2013 monthly rate. Initialize the positive and negative cumulative sums at zero immediately
before the first in-sample increment:

\[
POS_{Dec\,2013}=NEG_{Dec\,2013}=0,\quad
POS_t=\sum_{j=Jan\,2014}^{t}Dep_j,\quad
NEG_t=\sum_{j=Jan\,2014}^{t}App_j.
\]

The partial sums are principally for the conditional NARDL design. A sensitivity may use simple
percentage changes \(100(E_t/E_{t-1}-1)\); do not change the primary transformation after
reviewing results.

## 5. Alternative specifications

### Symmetric distributed-lag benchmark

Estimate the same outcome dynamics and controls but replace the two signed components with the
total \(\Delta e_t\):

\[
\pi^s_t=\alpha_s+\sum_{i=1}^{p}\rho_{s,i}\pi^s_{t-i}
+\sum_{j=0}^{q}\beta_{s,j}\Delta e_{t-j}+\delta_s'Z_t+\varepsilon^s_t .
\]

This is the required parsimonious symmetry benchmark and is nested in the asymmetric model
under the coefficient equality restrictions. Report its fit and the joint Wald test for
asymmetry; do not select asymmetry solely because it improves in-sample fit.

### Conditional NARDL / asymmetric error-correction extension

Consider a NARDL only if pre-estimation evidence supports the integration assumptions and
cointegration is tested rather than presumed. Its long-run equation uses the log price index
\(\ln P^s_t\), the USD/INR positive and negative partial sums, and only defensible controls:

\[
\ln P^s_t=c+\theta^+ POS_t+\theta^- NEG_t+\gamma'W_t+u_t.
\]

The corresponding conditional error-correction form includes the lagged disequilibrium term,
short-run differences of the price index, positive/negative partial-sum changes, and controls.
Short-run asymmetry concerns the coefficients on differenced partial sums; long-run asymmetry
tests \(H_0:\theta^+=\theta^-\), because `NEG` is negative-valued. Use an error-correction
interpretation only if a stable long-run relation is supported.

Before any ARDL bounds test, establish that every included series is at most I(1). An I(2)
variable invalidates the standard bounds critical values. A mix of I(0)/I(1) variables may be
allowed under the bounds framework, but it does not waive deterministic-term specification,
small-sample, or structural-break concerns. With at most 132 common monthly observations,
keep the NARDL lag structure very small, report finite-sample/bootstrap bounds inference where
available, and treat it as secondary to the primary inflation-rate distributed-lag design.
If integration or cointegration requirements fail, do not report NARDL long-run multipliers;
retain the stationary-change/inflation-rate models.

## 6. Controls and imported-cost design

Use a staged, low-dimensional control strategy. Brent USD monthly log changes are the leading
imported-cost extension after its source definition/vintage is documented. Estimate separate
specifications with Brent USD changes and with the Brent-INR proxy; do not include both in the
same small model with exchange-rate terms. The proxy is the product-based Brent-in-rupees
approximation, not actual landed import cost. Since its change mechanically contains the FX
change, adding it beside positive/negative FX components can create strong mechanical
collinearity and obscure interpretation.

Repo-rate changes and NEER/REER changes are optional sensitivity controls only after source,
date-key, and vintage verification. Do not include both NEER and REER, both trade and export
series, multiple Brent variants, and repo dynamics in a single short-sample baseline. The repo
file's month-start key does not establish whether the value is a month-end setting or average.
The NEER/REER file's methodology is known in prior audit material, but the local values and
vintage are not matched to a dated export.

For conditional imported-cost asymmetry, add one pre-specified interaction between the FX
positive/negative components and lagged Brent price changes (or a training-independent,
predefined oil-state measure). Test the interaction block jointly. Treat it as exploratory,
limit interactions to avoid overfitting, and do not infer that oil causes pass-through changes.

## 7. CPI/WPI comparison

First estimate matching CPI and WPI equations over the common 2014–2024 index-derived sample.
Then compare the exchange-rate response paths using a stacked model with outcome-by-FX-component
interactions and time-clustered/HAC inference, or a paired moving-block bootstrap over months.
The comparison must account for the fact that CPI and WPI outcomes in the same month are not
independent. Report separate equations and the formal cross-outcome coefficient contrast.

Keep Fuel & Power and Manufactured Products as secondary WPI outcomes, not as replacements for
the headline series. Account for the family of secondary tests (for example, Holm adjustment) and
avoid strong interpretation when confidence intervals are wide.

## 8. Estimation, inference, and diagnostics

- Preserve monthly ordering; do not shuffle observations.
- Confirm each regression's exact dates, complete-case count, lag losses, and any excluded
  observations before estimation.
- Use HAC/Newey–West standard errors with a pre-specified lag rule that is at least adequate
  for the selected dynamic horizon; compare with a moving-block bootstrap confidence interval.
- Report coefficient estimates, 95% confidence intervals, joint Wald tests, and effect sizes.
- Test short-run symmetry jointly; test equality of cumulative dynamic responses at 1, 3, and
  6 months; for NARDL only, test long-run equality after establishing cointegration.
- Use residual serial-correlation LM/Ljung–Box checks, heteroskedasticity tests, RESET or another
  functional-form diagnostic, residual distribution plots/tests, recursive/CUSUM stability
  checks, and structural-break sensitivity. No single residual-normality test is a model-validity
  certificate.
- Check variance inflation/condition indices for the split FX terms and controls; use alternate,
  not simultaneous, Brent/Brent-INR specifications.
- Pre-specify any break dates and supplement with unknown-break tests cautiously; multiple
  break searches are low-powered with this sample.

Failure to reject an asymmetry restriction means the data do not provide sufficient evidence
against symmetry under the chosen model and sample. It does not prove equal pass-through.
Conversely, a significant asymmetry estimate does not establish causality or a stable structural
relationship.

## 9. Robustness and planned reporting

Essential sensitivities:

1. Published CPI inflation versus index-derived CPI inflation; retain distinct labels.
2. Log annual index change versus simple annual percent change for both CPI and WPI.
3. Log USD/INR change versus simple percentage change.
4. Lag maxima and BIC/AIC choice under the frozen candidate rule.
5. Same-month FX term versus lag-only FX terms.
6. Headline WPI versus Fuel & Power and Manufactured Products.
7. Baseline without imported-cost controls versus Brent USD change and, separately, Brent-INR
   proxy.
8. Full 2014–2024 common sample versus pre-specified subperiod/break sensitivity; do not choose
   windows based on desired significance.
9. Extreme depreciation observations retained, flagged, and omitted in a sensitivity only;
   define the threshold from a stated historical rule and disclose the reduced sample.
10. CPI published-inflation sample alone; never extend it across its 2025 gap.

Planned tables: data/variable coverage; descriptive statistics; integration tests; lag selection;
primary symmetric/asymmetric coefficients; short-run joint tests and response multipliers;
CPI/WPI contrasts; Brent and proxy extensions; diagnostics and robustness.

Planned figures (to be generated only from actual Stage 3 estimates): depreciation/appreciation
changes and partial sums; index-derived CPI/WPI inflation with FX changes; lag coefficient
paths; cumulative response functions with confidence bands; CPI/WPI coefficient contrasts;
structural-stability and residual diagnostics. No illustrative or fabricated empirical charts
are authorized by this design.

## 10. Critical risks and readiness

The principal risks are: CPI published-rate discontinuity in 2025; lack of WPI published
inflation in the processed file; WPI zero semantics in six disaggregated commodity series;
unresolved local source/vintage metadata for CPI, FX, Brent, repo, and NEER/REER; possible
contemporaneous simultaneity; and a short common sample relative to a high-dimensional dynamic
model.

**Design readiness: READY WITH LIMITATIONS.** A retrospective, non-causal primary design is
feasible using the 2014–2024 index-derived common sample and headline/major-group WPI series.
The researcher authorized implementation while retaining the documented source-vintage and
interpretation limitations. Real-time or causal claims are not ready without a source-vintage
strategy and a defensible identification design.
