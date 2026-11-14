# Real-Time Backtesting Feasibility

## Objective

Assess whether the project can realistically reconstruct point-in-time historical vintages for each dataset and whether strict real-time forecasting is feasible using the local files.

## Classification system

- FEASIBLE: sufficient official vintages and release timestamps.
- PARTIALLY FEASIBLE: some historical vintages exist, but coverage is incomplete.
- NOT FEASIBLE: only current revised historical series are available.
- UNKNOWN: evidence insufficient.

## Dataset-by-dataset assessment

| Dataset | Current source availability | Historical release archive availability | Feasibility | Assessment |
|---|---|---|---|---|
| Brent monthly | Official FRED/EIA monthly series available | Historical vintages are available in official archives, but not all release metadata are local | PARTIALLY FEASIBLE | Good for some historical analysis if archive timing is preserved |
| USD/INR daily | Official H.10 series available through FRED | Historical daily vintages can be retrieved, but point-in-time archival needs careful handling | PARTIALLY FEASIBLE | Daily data can be valid if release-date rules are preserved |
| USD/INR monthly | Official G.5 series available | Historical monthly vintages are publicly retrievable | PARTIALLY FEASIBLE | Monthly data are feasible if current-month preliminary values are treated correctly |
| RBI repo rate | Official RBI/DBIE access exists but no exact local series match was verified | Unknown at this stage | UNKNOWN | Not ready for strict real-time claims |
| NEER/REER | Official RBI methodology exists; exact local export not matched | Historical archives likely exist but were not matched here | UNKNOWN | Data may be usable, but exact point-in-time vintage is not proven |
| CPI current/back | MoSPI source design and scope are verified | Historical release archives likely exist, but exact workbook provenance is not verified | PARTIALLY FEASIBLE | Useful for aggregate index continuity, not strict real-time evaluation |
| WPI | OEA provisional and later official workbook values exist | Historical revisions appear available, but local date and archive evidence are incomplete | PARTIALLY FEASIBLE | Strong historical release evidence, but final-status semantics need caution |

## Key implication

No dataset is yet in a state to support strict real-time backtesting without explicit vintage selection, release-timing logic, and documented revision rules. The evidence supports calendar coverage and source-definition verification, but not full point-in-time reconstruction for all variables.

## Recommendation

The data foundation is sufficient for research planning and policy analysis, but not for strict forecasting backtests or causal evaluation until vintage and release-time metadata are gathered for each input.
