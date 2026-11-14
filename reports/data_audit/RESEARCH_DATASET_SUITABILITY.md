# Research Dataset Suitability Review

## Decision summary

**The dataset foundation is not ready for preprocessing or modeling.** The files provide useful coverage for exploratory research planning, but file-level source provenance and vintage alignment are incomplete, the repo-rate convention is inferred rather than verified, the WPI zero convention is unknown, and strict point-in-time availability is unsupported. This is a readiness assessment, not authorization to proceed.

## Stage-by-stage assessment

| Research stage | Potentially relevant data | Coverage available | Suitability and blockers |
|---|---|---|---|
| 1. USD/INR exchange-rate forecasting | USD/INR daily and monthly | Daily: 1973-01-02–2026-10-30, 14,044 rows. Monthly: 1973-01–2026-10, 646 observations. | Series identifiers and official quote definitions are available (daily noon buying rate; monthly average of available daily rates). The daily file has 552 numeric nulls whose causes are unclassified. Local retrieval dates/vintages are absent, and the two frequencies are not interchangeable. No forecast evaluation design or preprocessing is authorized. |
| 2. Indian CPI inflation forecasting | CPI combined general-index back and current workbooks | Continuous calendar span 2013-01–2026-09, 165 months; back/current files are adjacent and non-overlapping. | MoSPI verifies 2024=100 design and general-index back-series scope. The local workbooks' source/vintage is not authenticated. Blank published inflation cells must remain distinct from index observations; do not silently substitute calculated rates. General-index back linkage does not support detailed-group continuity. |
| 3. Asymmetric exchange-rate pass-through | USD/INR, CPI, WPI, Brent; NEER/REER may be a separate exchange-rate/competitiveness measure | Common dates across FX, Brent, repo, CPI, and NEER/REER: 2013-01–2026-09 (165 months). Adding WPI: 2013-01–2026-04 (160 months). | Calendar overlap exists, but monthly average FX, month-end repo setting, CPI/WPI concepts, Brent benchmark, differing bases and vintages are not yet aligned. Point-in-time availability and lag conventions are not established. No causal inference or model suitability is claimed. |
| 4. High-inflation early-warning classification | CPI general index/inflation, potentially WPI and external indicators | CPI shared monthly span starts 2013-01; WPI ends 2026-04. | No high-inflation threshold, target definition, lead horizon, class-label timing, or real-time release/vintage protocol has been approved. The current files cannot support a defensible early-warning assessment without those research decisions and source-time records. |
| 5. Inflation persistence and WPI analysis | CPI general index and WPI categories | CPI 2013-01–2026-09; WPI 2012-04–2026-04; shared span 2013-01–2026-04 (160 months). | WPI's 2011–12 base and publisher/source match are verified, but 505 numeric zeros across six detailed series have undefined semantics. April 2026 differs by publication vintage (167.0 provisional versus 167.6 later official download); CPI's 2024-base back series is linked only at the general-index level. Provenance and vintage selections remain pending. |

## Coverage is not usability

The date intersections above are arithmetic calendar intersections only. They do not prove that records were publicly available on each forecast origin, that units/definitions are harmonized, or that apparent monthly keys represent the same within-month measurement time. Daily FX null values are not automatically economic gaps. WPI's complete month columns do not resolve the meaning of zeros in component series.

## Required approvals and evidence before preprocessing

1. Obtain and preserve attributable source extracts, retrieval dates, series IDs, and revision/vintage records for daily/monthly USD/INR, Brent, RBI repo, NEER/REER, and both CPI workbooks.
2. Verify the repo-rate series definition, unit, source, and monthly date-key/observation rule against RBI metadata.
3. Obtain an authoritative definition for WPI numeric zeros and confirm whether the April 2026 later-download value is formally finalized.
4. Define the research-stage observation timing and release-lag policy, including treatment of provisional/revised values.
5. Record explicit approval before any preprocessing, transformation, joining, or model development.

No data were transformed, joined, imputed, or modeled in this review.
