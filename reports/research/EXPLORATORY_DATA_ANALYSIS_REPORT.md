# Exploratory Data Analysis Report

## Scope

This report documents the exploratory data analysis (EDA) performed on the verified processed datasets and the engineered feature outputs. The analysis is descriptive and diagnostic only. It does not estimate forecasting models, pass-through models, early-warning classifiers, or any causal effects. All visualizations and summary tables were generated from the actual processed outputs under `data/processed/` and `data/processed/features/`.

## Research questions

1. What are the empirical levels, distributions, and volatility patterns of exchange rates, commodity prices, CPI, repo rates, NEER/REER, and WPI across the available monthly sample?
2. Which macro series show strong contemporaneous or lagged associations with CPI inflation and imported-inflation proxies?
3. Are the variable families stationary, trend-dominated, or persistent over time?
4. Which historical periods stand out as substantial depreciation or inflation episodes, and how should those episodes be interpreted?
5. Which missingness and sample-coverage limitations affect stage-specific analyses?

## Dataset coverage and variable mapping

The EDA used the following actual sources:

- Exchange rate: `data/processed/features/exchange_rate_features.csv`
- Brent: `data/processed/features/brent_features.csv`
- Brent-INR proxy: `data/processed/features/brent_inr_proxy_features.csv`
- CPI: `data/processed/features/cpi_features.csv`
- Repo rate: `data/processed/features/repo_rate_features.csv`
- NEER/REER: `data/processed/features/neer_reer_features.csv`
- WPI: `data/processed/features/wpi_features.csv`
- Master panel: `data/processed/features/research_master_feature_panel.csv`

These feature families were already aligned to the verified processed source series and preserved the original economic units. The EDA did not replace missing observations or modify any raw or feature data.

## Descriptive statistics

Key descriptive statistics from `reports/research/EDA_DESCRIPTIVE_STATISTICS.csv` are summarized below.

| Category | Variable | n | Mean | Median | Std. dev. | Min | Max |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Exchange rate | `usd_inr_level` | 646 | 39.14 | 42.52 | 25.04 | 7.27 | 95.86 |
| Exchange rate | `usd_inr_mom_pct_change` | 645 | 0.40 | 0.17 | 1.75 | -5.76 | 21.61 |
| Exchange rate | `usd_inr_depreciation_log_change` | 645 | 0.74 | 0.17 | 1.34 | 0.00 | 19.56 |
| Brent price | `brent_usd_per_barrel_level` | 474 | 51.79 | 46.56 | 33.05 | 9.82 | 132.72 |
| Brent-INR proxy | `brent_inr_proxy_level` | 474 | 2992.90 | 2621.04 | 2478.66 | 182.68 | 11837.38 |
| CPI | `cpi_index_level` | 165 | 80.53 | 78.30 | 15.39 | 55.10 | 109.49 |
| CPI | `cpi_published_inflation` | 141 | 5.08 | 5.03 | 1.51 | 1.46 | 8.60 |
| Repo rate | `repo_rate_level` | 165 | 6.06 | 6.25 | 1.17 | 4.00 | 8.00 |
| NEER/REER | `Trade_NEER_level` | 165 | 94.88 | 94.81 | 6.17 | 77.19 | 105.64 |
| WPI | `wpi_all_commodities_index` | 169 | 127.99 | 120.40 | 18.47 | 104.70 | 167.60 |
| WPI | `wpi_all_commodities_yoy_inflation` | 157 | 3.09 | 2.45 | 4.70 | -6.14 | 16.63 |

Notable observations:

- The exchange-rate level is highly dispersed, with a mean of 39.14 INR/USD and a maximum of 95.86; this reflects long-run depreciation episodes and regime changes.
- Monthly exchange-rate percentage changes are highly skewed (skewness approx 3.26), with outlier positive changes reaching 21.6 percent in the sample.
- CPI published inflation is concentrated in a relatively moderate range, with an average of 5.08 percent and a 75th percentile of 6.07 percent; the 90th-percentile threshold used for the episode analysis lies above the usual moderate inflation range.
- WPI all-commodities inflation has a higher mean and volatility than CPI inflation in the common sample, with a mean year-on-year inflation of 3.09 percent and a maximum of 16.63 percent.
- The Brent-INR proxy is highly variable, with mean approx INR 2,993 per barrel and a large spread; this supports its use as an imported-cost exposure variable rather than as a domestic pricing series.

## Distribution and outlier analysis

The EDA charts in `visualizations/eda/` show that:

- USD/INR monthly percentage changes cluster around near-zero values but have a long right tail associated with large depreciation episodes.
- Depreciation and appreciation decomposition shows that positive monthly depreciation movements are more variable than appreciation movements, consistent with the higher skewness in the raw exchange-rate change distribution.
- Brent price changes are right-skewed but less asymmetric than exchange-rate changes in percent terms.
- CPI and WPI inflation distributions are concentrated around moderate positive values but have persistent high-inflation tails.
- Repo-rate changes are typically small and clustered around zero, with some discrete hikes and cuts.

Important caution: these are descriptive distributions only. The presence of an extreme observation does not imply an error; it may instead represent a historically unusual depreciation, oil-price shock, or policy regime shift.

## Correlation and relationship analysis

The `EDA_CORRELATION_RESULTS.csv` file reports the correlations across the common non-missing windows used for each paired comparison.

| Left variable | Right variable | Common observations | Pearson | Spearman |
| --- | --- | ---: | ---: | ---: |
| `usd_inr_mom_change` | `cpi_published_inflation` | 141 | -0.0001 | 0.0137 |
| `usd_inr_depreciation_log_change` | `cpi_published_inflation` | 141 | -0.0302 | 0.0138 |
| `brent_mom_pct_change` | `cpi_published_inflation` | 141 | -0.0157 | -0.0330 |
| `brent_inr_proxy_mom_pct_change` | `cpi_published_inflation` | 141 | -0.0186 | -0.0311 |
| `Trade_NEER_mom_pct_change` | `cpi_published_inflation` | 141 | 0.0630 | 0.0588 |
| `Trade_REER_mom_pct_change` | `cpi_published_inflation` | 141 | 0.1217 | 0.0938 |
| `repo_rate_change_pp` | `cpi_published_inflation` | 141 | 0.2266 | 0.2412 |
| `wpi_all_commodities_mom_pct_change` | `cpi_published_inflation` | 136 | 0.0976 | 0.0891 |

Key interpretation:

- The contemporaneous exchange-rate and Brent correlations with CPI inflation are weak in the common sample, with absolute Pearson correlations below about 0.03 for the exchange-rate and crude-oil comparisons.
- The repo-rate change and CPI inflation association is the strongest among these contemporaneous comparisons, with Pearson r = 0.2266 and Spearman rho = 0.2412.
- The REER change association with CPI inflation is modestly positive but remains well below a level that would justify causal conclusions.
- None of the correlations here justify a causal claim. They are descriptive associations only and will require stage-specific and vintage-aware modelling later.

## Lagged relationships

The EDA did not select final lag structures for the forecast models. Instead, it checked the relationship between exchange-rate movements and inflation using common-period, historically observed values only. The analysis uses the actual aligned monthly series and distinguishes between symmetric exchange-rate changes and asymmetric depreciation/appreciation variables.

The feature outputs include explicit lag structures such as `cpi_1m_inflation_lag`, `cpi_3m_inflation_lag`, and the cumulative change features for exchange rate and crude oil. The degree of lagged association should be treated as exploratory evidence only, not as a completed pass-through estimate.

## Time-series diagnostics

Stationarity diagnostics were computed using ADF and KPSS tests on the level series in `EDA_STATIONARITY_RESULTS.csv`.

| Variable | n | ADF p-value | KPSS p-value |
| --- | ---: | ---: | ---: |
| `usd_inr_level` | 646 | 0.9978 | 0.01 |
| `brent_usd_per_barrel_level` | 474 | 0.4664 | 0.01 |
| `cpi_index_level` | 165 | 0.9974 | 0.01 |
| `wpi_all_commodities_index` | 169 | 0.9939 | 0.01 |
| `Trade_NEER_level` | 165 | 0.8961 | 0.01 |

Interpretation:

- ADF p-values are all well above 0.05, which is consistent with non-stationarity in the levels for these macro series.
- KPSS p-values of 0.01 indicate rejection of the null of stationarity for the same variables under the standard test setup.
- This suggests that these series display trend and persistence. The evidence is consistent with the economic expectation that exchange rates, prices, and the policy rate are non-stationary over multidecade macro samples.
- The EDA does not conclude that every transformed series is non-stationary; the results are limited to the tested level series and are not a substitute for a full time-series modelling strategy.

## Depreciation and inflation episodes

Episode thresholds were defined in a transparent descriptive way using the 90th percentile of each relevant series within the observed sample. This is not a model-based classification; it is a descriptive episode summary.

Examples from `EDA_EPISODE_SUMMARY.csv` include:

- Depreciation episodes: recurring periods such as 1973-08 to 1974-01, 1978-12 to 1978-12, 1981-02 to 1981-07, and later continued episodes corresponding to large monthly exchange-rate jumps, with a threshold of 2.07 percent monthly change.
- Brent high-price episodes: the 90th-percentile threshold for a monthly Brent level was 107.03 USD/barrel, with multiple episodes such as 2013-07 to 2014-06 and 2022-03 to 2022-07.

These episodes highlight periods in which exchange-rate depreciation and imported-cost pressure coincided, but they do not establish a causal mechanism. They are useful for identifying the historical periods that warrant closer research-stage analysis.

## Missingness and coverage analysis

Missingness is not uniform across the feature families:

- `cpi_published_inflation` has 24 missing values in the CPI feature table.
- `wpi_all_commodities_yoy_inflation` has 12 missing values.
- Repo rate and exchange rate have relatively modest missingness, mostly at the boundaries or in the earliest periods of sparse coverage.
- The master panel preserves all source coverage through an outer-merge design, which is appropriate for retaining economically meaningful dates but also leads to many partially missing rows when a variable is absent in a given month.

This means that stage-specific analyses should not always rely on a single common sample. For instance, the CPI inflation correlation sample includes 141 common observations, while WPI versus CPI inflation uses 136. These differences should be explicitly acknowledged in later modelling work.

## Stage-specific EDA implications

### Stage 1: USD/INR forecasting

- The monthly USD/INR level exhibits strong persistence and is clearly non-stationary in the levels.
- Volatility spikes are visible in large depreciation episodes, and the long right tail of monthly changes is economically meaningful.
- The EDA supports a stage-1 focus on trend, volatility, and regime-like movements rather than on a simplistic stationary model.

### Stage 2: CPI forecasting

- CPI inflation is centered around moderate values but includes episodes of rising inflation.
- The repo rate change shows the strongest contemporaneous correlation with CPI inflation in the common sample, while exchange-rate and Brent links are weaker in the raw contemporaneous correlations.
- The distributional results support continued examination of lagged inflation persistence and imported-cost exposure but do not establish a final predictor set.

### Stage 3: Asymmetric pass-through

- The exchange-rate decomposition variables show that depreciation and appreciation are not symmetric in the sample.
- The relevant EDA question is whether depreciation episodes, rather than symmetric exchange-rate moves, align more strongly with subsequent inflation dynamics.
- This remains exploratory and should not be interpreted as a pass-through estimate.

### Stage 4: Early warning

- The inflation distribution provides a basis for defining extreme inflation states descriptively, but the current EDA does not create a final warning classifier.
- The episode analysis suggests a reasonable data-driven framework for evaluating high-inflation periods.
- The stage-4 design should remain explicit about forecast origin, threshold choice, and sample coverage.

### Stage 5: Persistence and WPI analysis

- WPI all-commodities inflation shows a larger range and stronger tail behaviour than CPI inflation in the same sample window.
- The WPI and CPI series should remain distinct in both interpretation and modelling design, because a producer-price index is not identical to a consumer-price index.
- The broad WPI contours and volatility patterns support a persistence and producer-cost analysis framework without making causal claims.

## Visualization outputs

The following EDA visualization outputs were created under `visualizations/eda/`:

- `exchange_rate/usd_inr_overview.png`
- `brent/brent_and_proxy.png`
- `inflation/cpi_and_repo.png`
- `wpi/neer_reer_and_wpi.png`
- `correlations/pearson_heatmap.png`
- `missingness/feature_missingness_heatmap.png`

Additional subdirectories were created for organized EDA products, including `exchange_rate/`, `brent/`, `inflation/`, `pass_through/`, `wpi/`, `correlations/`, `diagnostics/`, and `missingness/`.

## Reproducibility and validation

The EDA workflow is implemented in:

- `src/visualization/eda.py`
- `src/visualization/run_eda.py`

The generated reports and summary tables are saved here:

- `reports/research/EDA_DESCRIPTIVE_STATISTICS.csv`
- `reports/research/EDA_CORRELATION_RESULTS.csv`
- `reports/research/EDA_STATIONARITY_RESULTS.csv`
- `reports/research/EDA_EPISODE_SUMMARY.csv`
- `reports/research/EDA_MISSINGNESS_SUMMARY.csv`

Validation results from the project-level checks were:

- `pytest -q`: PASS
- `ruff check .`: PASS
- `pip check`: PASS

## Interpretation cautions

1. Correlation is not causation. The descriptive associations here do not identify the structure of import pass-through or policy transmission.
2. Missingness and different sample windows matter. Common-sample correlations should always be interpreted alongside the actual number of aligned observations.
3. The EDA highlights empirical patterns and periods of interest, but it does not decide the final forecasting design or warning threshold.
4. Stationarity tests are often sensitive to level definitions, sample period, and trend structure. They should be read as diagnostic evidence for stage-specific modelling, not as final proof of a particular model specification.

## Final assessment

The exploratory data analysis establishes the empirical baseline needed before the next model-development phase: the data show meaningful macro variation, persistent non-stationary levels, periodic depreciation episodes, moderate inflation clustering, and a need for careful stage-specific sample construction. The analysis supports the next phase of model design as a structured, evidence-based step rather than as a purely data-mining exercise.
