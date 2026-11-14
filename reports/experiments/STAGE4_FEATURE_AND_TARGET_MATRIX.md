# Stage 4 Feature and Target Matrix

**Purpose:** Define candidate labels and predictors for design review; no features were
recomputed and no model was trained.  
**Evidence cutoff:** 2026-11-10.

Evidence labels used below:

- **Verified:** observed in project files or prior-stage audit reports.
- **Proposed:** recommended design choice, requiring researcher approval before implementation.
- **Conditional:** eligible only after its stated provenance/timing issue is resolved.

## 1. Target matrix

Let \(y_m\) be the published All India / Combined / CPI (General) `inflation_value`, in percent,
for month \(m\). Let \(t\) be the forecast-origin month, with a notional end-of-month cutoff.
The proposed label is \(Y^{(h)}_t=\mathbb{1}(y_{t+h}>6.0)\).

| Horizon | CPI reference month classified | Positive label | Negative label | Eligible target months / N | Elevated / non-elevated |
|---|---|---|---|---:|---:|
| 1 month (primary) | \(t+1\) | published CPI > 6.0% | published CPI <= 6.0% | Feb 2015-Dec 2024 / 119 | 29 / 90 |
| 3 months | \(t+3\) | published CPI > 6.0% | published CPI <= 6.0% | Apr 2015-Dec 2024 / 117 | 29 / 88 |
| 6 months | \(t+6\) | published CPI > 6.0% | published CPI <= 6.0% | Jul 2015-Dec 2024 / 114 | 29 / 85 |

The 6% rule is strict: a value equal to 6.0 is non-elevated. This is future-month
classification, not the current month's label and not an “any month during the horizon” event.
**Verified:** the underlying published-CPI segment is 132 consecutive observations from Jan
2014 through Dec 2024; eight >6% observations in 2014 are outside the proposed eligible target
windows because of the one-year CPI-history start.

### Threshold sensitivities (descriptive; not alternate primary labels)

| Threshold | Full Jan 2014-Dec 2024 elevated | Eligible 1-month | Eligible 3-month | Eligible 6-month | Design use |
|---|---:|---:|---:|---:|---|
| >4% | 101/132 | 89/119 | 87/117 | 84/114 | Optional sensitivity; captures above-midpoint inflation and makes the positive class dominant. |
| >6% (primary) | 37/132 | 29/119 | 29/117 | 29/114 | Upper edge of the 4% +/-2 tolerance band; primary warning definition. |
| >8% | 4/132 | 0/119 | 0/117 | 0/114 | Descriptive only; no eligible positive labels, so classification is infeasible. |

The primary threshold is not selected or retuned from the observed data. The 4% and 8%
alternatives must not be substituted after observing model performance.

## 2. Origin-time availability rule

**Proposed:** for a forecast made at origin month \(t\), make the information cutoff explicit
and use only source observations dated through \(t-1\). For any rolling feature, its right edge
must be \(t-1\); no centered windows, backward fills, full-sample normalization, or realized
target-month observations are allowed. This convention is conservative by reference month but
does not establish publication by the origin because release timestamps and historical vintages
are unavailable.

Each feature row must retain `forecast_origin`, `feature_observation_end`, and `target_month`.
Assert `feature_observation_end < forecast_origin < target_month` and
`target_month == forecast_origin + horizon months`. Keep the 2025 published-CPI gap and separate
2026 segment disconnected.

## 3. Feature eligibility matrix

| Feature family / candidate | Formula or construction | Required lag / availability at origin | Economic rationale | Leakage / data risk | Eligibility |
|---|---|---|---|---|---|
| CPI published inflation lags | \(y_{t-1}, y_{t-3}, y_{t-6}, y_{t-12}\) | All reference months <= \(t-1\); a full prior year is required for 12-month lag | Inflation persistence and recent price momentum | Do not use current \(y_t\) if its release is not known at cutoff; CPI release dates/vintages absent | CPI-only baseline |
| CPI inflation change | \(y_{t-1}-y_{t-2}\), optionally a three-month change \(y_{t-1}-y_{t-4}\) | Right edge \(t-1\) | Acceleration/deceleration can precede continued elevated inflation | Must use published rates and contiguous observations; do not substitute current CPI-index change silently | CPI-only baseline, limited prespecified set |
| CPI rolling mean | Mean of \(y_{t-1},\dots,y_{t-k}\), \(k=3\) or 6 | Trailing window ends \(t-1\) | Smoothed persistence level | Window must be trailing, not centered; no use across missing 2025 gap | CPI-only baseline |
| CPI rolling volatility | Sample SD of published CPI inflation over trailing 6 or 12 months ending \(t-1\) | All window values available by cutoff | Recent instability may signal elevated-risk regimes | Short sample and overlapping CPI rates; avoid including many correlated window summaries | CPI-only baseline sensitivity |
| CPI persistence indicator | Count of months >6% in trailing 3 or 6 observations, or a run-length indicator calculated only through \(t-1\) | Requires all trailing labels to be observed | Captures continuation of an already elevated episode | Deterministic target-history feature; must not use a future episode boundary or future labels | Baseline sensitivity; not a new target |
| Monthly USD/INR log return | \(r_j=100[\ln(FX_j)-\ln(FX_{j-1})]\); positive means INR depreciation | Use \(r_{t-1}\) and selected lags; monthly rate is INR per USD | Captures recent bilateral depreciation/appreciation | Historical monthly source vintage and publication timing unverified; never include \(r_t\) or future FX | CPI+FX extended group |
| Depreciation / appreciation | \(d_j=\max(r_j,0)\), \(a_j=\min(r_j,0)\) (signed negative appreciation); a magnitude convention is acceptable only if named and fixed | Through \(t-1\) | Separates direction and permits asymmetric warning associations | Existing engineered appreciation is positive magnitude whereas Stage 3 used signed negative values; normalize convention before use | CPI+FX extended group |
| Cumulative depreciation and appreciation | \(\sum_{j=t-k}^{t-1} d_j\) and \(\sum a_j\), \(k=3,6\); alternatively report net log change with clear units | Trailing window ends \(t-1\) | Captures accumulated movement beyond a one-month shock | Avoid overlapping redundant windows; ensure all monthly returns are consecutive | CPI+FX, prespecified small subset |
| FX volatility | SD of monthly \(r_j\) over trailing 6 or 12 months through \(t-1\) | Trailing window ends \(t-1\) | Currency instability may signal imported-cost uncertainty | Calculate from consecutive monthly returns; no future window values | CPI+FX sensitivity |
| Brent USD change | \(100\Delta\ln(Brent_j)\) at \(t-1\), plus at most one 3- or 6-month cumulative change | Through \(t-1\) | International crude-price movements can be an imported-cost signal | Local extraction vintage, monthly aggregation, and release timing unverified; avoid current month and target-month Brent | Conditional CPI+FX+Brent model |
| Brent volatility | SD of monthly Brent log returns over trailing six months ending \(t-1\) | Trailing window ends \(t-1\) | Captures uncertainty in commodity-price pressure | Existing engineered `brent_6m_rolling_volatility` appears scaled by an additional factor of 100; recompute/validate before use | Conditional only after correction |
| Brent-INR approximate proxy | \(Brent\;USD/barrel \times USD/INR\); use lagged log change or cumulative change | Construct each month from same-month source levels, then use no later than \(t-1\) | Approximate rupee cost of an oil barrel | Not landed import cost; excludes freight, insurance, taxes, contracts, quality, and pass-through; mechanically embeds FX | Alternative imported-cost model, not simultaneous primary Brent+FX interaction |
| Repo level and change | Repo level at \(t-1\); \(\Delta repo_{t-1}\) in percentage points; optional prior 3-month change | Through \(t-1\), after date convention is authenticated | Monetary-policy stance may condition inflation risk | Existing monthly date convention may not equal month-end setting; source mapping and release timing unresolved | Conditional extension only |
| NEER/REER changes | Prefer one validated trade-weighted series; \(100\Delta\ln(index_{t-1})\), optionally a trailing 3-month change | Through \(t-1\) | Broad external competitiveness differs from bilateral USD/INR | Local series identity, vintage, and direction/source mapping unresolved; four candidate indices are redundant | Conditional extension only |
| WPI inflation | Index-derived All Commodities annual change, explicitly not publisher-reported inflation; use only through \(t-1\) | Lagged at least one full reference month; release timestamps needed | Wholesale prices may provide an upstream price-pressure signal | WPI monthly values are revisions/vintage-sensitive; not a published inflation series; never use \(WPI_{t+h}\) | Conditional extension only |
| Stage 1/2 forecast outputs | Do not use test predictions, actuals, residuals, or fitted values as predictors | Not a feature at origin | Prior-stage model outputs do not represent independent economic indicators | Prediction archive coverage is limited; prediction fields may encode future-target information | Excluded from primary features |
| Stage 2 historical FX forecast archive | Optional, separate experiment only: origin-generated FX path with provenance and fixed specification | Match exact origin/horizon; ensure generated without future FX | Forecasted FX might be a distinct risk signal | Adds a nested forecast and model uncertainty; archive is retrospective and not a real-time vintage | Excluded from primary feature set |

## 4. Proposed feature groups and controls

**Proposed CPI baseline:** a deliberately small set of lagged published-CPI information:
inflation at lags 1, 3, 6, and 12; one recent change; one trailing mean; and one trailing
volatility or persistence measure. Because these are correlated and the training block is small,
feature selection among them must be prespecified or regularized inside training folds.

**Proposed incremental groups:**

| Model label | Included information | Comparison purpose |
|---|---|---|
| B0 | CPI history | Persistence-only benchmark |
| B1 | B0 + limited signed USD/INR changes/cumulative movement | Incremental value of FX indicators |
| B2 | B1 + lagged Brent USD change/volatility | Incremental international oil signal |
| B3 | B1 + Brent-INR approximate proxy instead of Brent USD | Alternative combined-cost proxy; not landed cost |
| B4 | B1/B2 plus validated repo or one validated NEER/REER measure | Conditional monetary/external extension |
| B5 | B1/B2 plus lagged WPI | Conditional wholesale-price extension |

Use paired comparisons on the same origins and target months. The B3 proxy mechanically
includes FX; changes in B3 performance cannot isolate FX from Brent.

## 5. Existing feature-file cautions

**Verified from source inspection; no corrections made:**

1. `../../src/features/feature_engineering.py` computes monthly log changes as
   `100 * diff(log(level))`. Its Brent rolling-volatility field then takes the SD of that
   already-percent-scaled return and multiplies by another 100. Its units are therefore 100
   times the standard deviation in percentage points; without units documentation, treat this
   as a scale ambiguity (possibly basis-point-like), not as a ready-to-use volatility measure.
2. The same `_log_change` helper filters to positive observations before differencing; if a
   missing/nonpositive month occurs, it can difference across the gap rather than reject or
   preserve a missing return. The inspected 2014-2024 Brent/FX source values are complete and
   positive, so this gap behavior is a future eligibility risk, not evidence that the present
   common sample has such a gap.
3. `repo_rate_change_indicator` is made with `.ne(0)` before a missing first difference is
   handled; the first unavailable change can be marked as a change. Do not use this indicator
   without rebuilding it with missing values preserved.
4. Existing CPI index-derived changes and WPI changes are not interchangeable with published
   CPI inflation. Use the actual `inflation_value` only for the target and CPI-history features.

These are logged in `../ISSUE_LOG.md`. They are not fixed as part of this design-only task.

## 6. Interpretation boundary

Coefficients, permutation importance, grouped ablation, and model-specific explanations identify
patterns used by a fitted predictor. They do not establish that exchange rates, Brent, WPI, repo,
or NEER/REER cause CPI inflation. The Brent-INR product remains a proxy and Stage 3's
association findings do not establish classifier utility.
