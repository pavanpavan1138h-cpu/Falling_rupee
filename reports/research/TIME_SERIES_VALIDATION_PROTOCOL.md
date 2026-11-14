# POME EL Time-Series Validation and Leakage Prevention Protocol

This protocol defines the mandatory principles for time-series validation and leakage prevention across the five research stages. It is a governance document for future empirical analysis and does not describe implemented models or results.

## Core principles

### 1. Chronological train-validation-test separation
- Data must respect temporal ordering across all stages.
- The model or method must not use future information to evaluate past performance.
- Historical observations should be assigned to training, validation, and test periods only according to their chronology.
- The temporal split must be documented for each experiment.

### 2. Expanding-window evaluation
- When appropriate, evaluation windows should expand as new information becomes available.
- Historical training periods should expand with time rather than re-randomize over the full sample.
- This approach better reflects genuine forecasting conditions and avoids look-ahead bias.

### 3. Rolling-origin backtesting
- Forecast origins should move forward in time to assess performance across evolving historical conditions.
- Rolling-origin validation is preferable when directional performance and time consistency matter.
- The evaluation design must state the origin step and forecast horizon explicitly.

### 4. Untouched final chronological test period
- The final test period must remain entirely untouched until all model and feature decisions are finalized.
- No tuning or selection decisions should be made using the final test segment.
- This preserves an out-of-sample assessment of the chosen design.

### 5. Training-only fitting of scalers and transformations
- Standardization, normalization, and similar transformations must be fitted using training data only.
- Validation and test data must be transformed using parameters derived from the training sample.
- This prevents information leakage from the future into the model pipeline.

### 6. Training-only feature selection
- Feature selection procedures must be fitted in training data only.
- Validation and test periods must not influence variable selection.
- Feature-screening choices must be fixed before the final test window is used.

### 7. Training-only synthetic data generation
- Synthetic observations, if used, must be generated within a well-defined training-only workflow and not leak future patterns into evaluation.
- Synthetic usage must be explicitly documented in the experiment protocol.
- This protocol does not authorize synthetic-data generation during the current stage.

### 8. No future information in historical predictions
- A prediction at time t must only use information available at or before time t.
- No future releases, revisions, or final data values should be used to construct historical predictions.
- This is a required principle for forecast-origin integrity.

### 9. Appropriate handling of macroeconomic release delays
- Macroeconomic indicators may be released with a delay or revised after publication.
- Forecast origins must reflect data that was available at the time of prediction, not the later revised final dataset.
- This is a data-vintage issue and must be tracked explicitly.

### 10. Data-vintage awareness
- Vintage-aware design means validating what information was available at the forecast origin.
- Historical analyses should document the vintage used and the revision status of the underlying data.
- This is necessary for a legitimate out-of-sample evaluation.

### 11. Consistent forecast horizons
- Forecast horizons must be defined clearly and consistently across experiments.
- A single horizon or multiple horizons must be stated before evaluation begins.
- Horizon definitions must be stable and documented.

### 12. Genuine out-of-sample predictions between research stages
- Each research stage must maintain a clear distinction between historical estimation work and genuine out-of-sample evaluation.
- This prevents accidental use of stage outputs as if they were ex ante predictions.
- Results and metrics must reflect the actual forecast period used.

## Informational principle: determining what was available at each forecast origin

At each forecast origin time t, the analyst must determine:

- Which raw observations were available by time t.
- Which revisions were available by time t.
- Whether the data source was released with a lag or revised later.
- Whether a feature was constructed using only data available at t.
- Whether transformations and scalers were fit using only training-period information.
- Whether the feature set is valid for the chosen forecast horizon.

The decision is not merely technical; it is a research governance requirement. If the analyst cannot justify the information set available at the origin, the pipeline is not valid for chronological evaluation.

## Required documentation checks

Each research stage should include the following in its experiment documentation:

- Forecast origin date or period.
- Data vintage used at that origin.
- Forecast horizon used.
- Feature list and transformation rules.
- Whether the pipeline uses look-ahead or future leakage.
- Validation and testing windows.
- Any release-delay assumptions.

## Key working rules

- Never validate on a future period that was used to tune the model.
- Never claim an out-of-sample result when an earlier period has been used for selection.
- Keep the final test period untouched until all model specifications are finalized.
- Distinguish reporting-vintage data from revised final data.
- Record all assumptions around macroeconomic release timing.
