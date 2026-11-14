# Stage 3 Variable and Hypothesis Matrix

**Status:** Proposed definitions for researcher review; no model estimates or test results.

## 1. Variable dictionary

| Variable | Definition / unit | Role | Availability and treatment |
|---|---|---|---|
| \(E_t\) | USD/INR monthly rate, INR per USD | Exchange-rate level | `data/processed/usd_inr_monthly_clean.csv`; positive monthly observations, Jan 1973–Oct 2026 (646). Higher = rupee depreciation. Local vintage/aggregation details remain subject to provenance audit. |
| \(\Delta e_t\) | \(100[\ln(E_t)-\ln(E_{t-1})]\), log percent | FX movement | Compute from consecutive monthly rates, using Dec 2013 as the pre-sample value for Jan 2014. Positive = depreciation. |
| \(Dep_t\) | \(\max(\Delta e_t,0)\), log-percent points | Positive FX movement | Primary asymmetric regressor. Zero for appreciation months. |
| \(App_t\) | \(\min(\Delta e_t,0)\), log-percent points | Negative FX movement | Primary asymmetric regressor. Retain its negative sign; do not negate or recode without a separately labelled alternative. |
| \(POS_t\) | \(\sum_{Jan2014}^{t} Dep_j\), initialized at zero before Jan 2014 | Positive partial sum | NARDL candidate only. |
| \(NEG_t\) | \(\sum_{Jan2014}^{t} App_j\), initialized at zero before Jan 2014 | Negative partial sum | NARDL candidate only; values are non-positive. |
| CPI index \(P^{CPI}_t\) | CPI (General), All India, Combined index | Consumer price level | `data/processed/cpi_monthly_clean.csv`; 165 months Jan 2013–Sep 2026, index complete. Main sample uses 2014–2024 before the base transition. |
| CPI published inflation | Publisher-supplied `inflation_value`, percent | CPI sensitivity outcome | 132 contiguous values Jan 2014–Dec 2024; no published values in 2025; separate Jan–Sep 2026 segment with 9 values. Do not fill or join over gap. |
| CPI index-derived annual log inflation \(\pi^{CPI}_t\) | \(100[\ln(P_t)-\ln(P_{t-12})]\), log percent | Primary CPI outcome | Explicitly calculated from index levels; not published inflation. Use only a clearly labelled derived measure. |
| WPI All Commodities index | Official index level, base 2011–12=100 per prior audit | Primary wholesale price level | WPI long file: 169 monthly values Apr 2012–Apr 2026; selected headline series has no missing or zero values. |
| WPI Fuel & Power index | Series `II FUEL & POWER`, index level | Secondary WPI outcome | 169 monthly values Apr 2012–Apr 2026; no missing or zero values in this series. Confirm hierarchy/label before implementation. |
| WPI Manufactured Products index | Series `III   MANUFACTURED PRODUCTS`, index level | Secondary WPI outcome | 169 monthly values Apr 2012–Apr 2026; no missing or zero values in this series. Confirm hierarchy/label before implementation. |
| WPI index-derived annual log inflation | \(100[\ln(P_t)-\ln(P_{t-12})]\) | Primary WPI outcome | Calculate consistently for selected WPI indices and label as index-derived; processed WPI file has no published inflation column. |
| Brent USD price \(B_t\) | Brent crude USD/barrel level | Imported-cost control/extension | `data/processed/brent_monthly_clean.csv`; 474 months May 1987–Oct 2026. Use log changes; verify exact source, monthly construction, and vintage before inference. |
| Brent-INR proxy | Existing engineered product-based rupee crude-cost proxy | Alternative imported-cost extension | Approximation only, not landed import cost. Use in place of Brent USD in an alternate specification, not jointly with FX components and Brent USD. |
| Repo rate \(R_t\) | Repo-rate level, percentage points | Optional monetary-policy control | `data/processed/repo_rate_clean.csv`; 165 months Jan 2013–Sep 2026. Use changes only after confirming monthly date convention and exact source series. |
| Trade NEER / REER | Effective exchange-rate index levels | Optional robustness control | 165 months Jan 2013–Sep 2026. Transform to log changes; local source/vintage not matched to dated export. Do not include NEER and REER together in the baseline. |

Primary annual index-derived inflation is a 12-month log change, not the exact simple-percent
formula used by every publisher. A separately labelled simple index-derived rate
\(100(P_t/P_{t-12}-1)\) is a required robustness definition. No derived measure may be called
officially published.

## 2. Hypothesis testing matrix

| Hypothesis | Null | Alternative | Variables / model terms | Primary test | Interpretation |
|---|---|---|---|---|---|
| H1: Depreciation and appreciation have distinguishable pass-through | In the asymmetric distributed-lag model, \(H_0:\beta^+_j=\beta^-_j\) for all selected lags | At least one positive/negative lag coefficient differs | \(Dep_{t-j}\), signed \(App_{t-j}\), CPI/WPI annual index-derived inflation | Joint Wald test of all lag-specific equalities; HAC covariance; block-bootstrap interval as sensitivity | Rejecting supports conditional short-run asymmetry in this sample/model, not causality. Failure to reject is insufficient evidence against symmetry, not proof of symmetry. |
| H2: Timing and persistence differ across horizons | Positive- and negative-shock dynamic responses are equal at pre-specified 1-, 3-, and 6-month horizons | At least one response-path contrast differs | Estimated ARDL dynamic multipliers for equal-sized depreciation/appreciation shocks | Joint Wald/delta-method contrasts and moving-block-bootstrap confidence bands for cumulative response paths | Report timing, cumulative response, and uncertainty. A different point estimate without a confidence interval is not evidence of different timing. |
| H3: Pass-through differs between CPI and WPI | CPI and WPI positive/negative FX response vectors are equal under identical dates/specification | At least one outcome-specific FX response differs | Outcome indicator × \(Dep\)/\(App\) and lags; CPI and WPI index-derived annual inflation | Joint cross-equation interaction Wald test or paired moving-block bootstrap over common months | Difference is an outcome association; CPI consumer basket and WPI upstream weights differ. Do not infer household burden or causal transmission solely from it. |
| H4: Imported-cost conditions are associated with pass-through variation | FX × Brent interaction coefficients are jointly zero | At least one interaction differs from zero | \(Dep\), \(App\), lagged Brent log change and a small pre-specified set of interactions | Joint Wald test of interaction block; HAC/block-bootstrap intervals; multiplicity disclosure | Significant interaction indicates conditional association in the specified sample, not that Brent causes asymmetry. Insignificance does not establish no imported-cost role. |

For all hypotheses, report the test statistic, degrees of freedom, p-value, coefficient/effect
size, confidence interval, sample dates and observations, selected lag structure, covariance
method, and any multiplicity adjustment. Pre-specify a primary outcome and test family; treat
remaining groups and interaction models as secondary.

## 3. Sign and response conventions

For a one-unit depreciation movement \(d>0\), the immediate distributed-lag term is
\(\beta^+d\). For an equal-size appreciation, `App` changes by \(-d\), so its immediate term is
\(-\beta^-d\). Symmetry on the signed-change scale is \(\beta^+=\beta^-\); it produces
opposite-signed effects with equal magnitudes under equal-and-opposite FX movements. Explain
this convention in every results table.

For partial-sum NARDL, `NEG` is also negative-valued. Long-run symmetry on the signed-change
scale is \(\theta^+=\theta^-\). Do not test equality of positive and negative absolute response
magnitudes using the wrong sign restriction.

## 4. Imported-cost and control roles

| Variable | Economic rationale | Expected sign/role | Lag / status | Constraint |
|---|---|---|---|---|
| Brent USD change | International crude price can affect imported energy and production/transport costs | A positive oil-price shock is expected to raise domestic cost pressure, but the realized sign/magnitude can differ with taxes, administered prices, and timing | Lagged change, parsimonious distributed lags; leading extension after provenance check | Do not imply causality; avoid excess controls. |
| Brent-INR proxy change | Combines oil USD price and rupee conversion into an approximate local-currency crude measure | Positive proxy change is expected to raise domestic imported-cost pressure, subject to pass-through frictions | Alternate specification replacing Brent USD; use only after checking formula | Mechanically includes FX; do not include alongside the split FX terms and Brent USD in a small model. |
| Repo-rate change | Monetary policy may respond to inflation and influence demand/expectations | Lagged tightening may reduce inflation pressure, while contemporaneous policy reaction can correlate positively with inflation; net reduced-form sign is ambiguous | Optional robustness after source/date-key verification | No causal interpretation; exact monthly convention is unresolved. |
| Trade NEER/REER change | Broad external value/competitiveness measure may capture non-USD currency movements and relative prices | If the documented index direction is higher = rupee appreciation, appreciation is expected to lower imported-cost inflation; confirm series direction before sign interpretation | One series at a time, lagged | Local mapping and vintage unresolved; overlaps conceptually with bilateral FX. |

No control should be included solely because it is available. Report a base model, a single-control
extension, and sensitivity results rather than a saturated specification.
