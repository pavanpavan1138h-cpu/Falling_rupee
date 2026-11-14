# POME EL Experiment Protocol

This protocol defines the required structure for future experiments in the POME EL workflow. It is intended to support reproducibility, traceability, and future MLflow integration without locking the project into unverifiable methodology.

## Core experiment record

| Field | Template entry |
| --- | --- |
| Experiment ID | [EXP-001] |
| Research stage | [Stage 1 / Stage 2 / Stage 3 / Stage 4 / Stage 5] |
| Research question | [State the research question or investigative objective.] |
| Hypothesis | [State the hypothesis being tested.] |
| Dataset versions | [List dataset IDs and record vintage or version information.] |
| Feature configuration | [Describe the feature set or experiment configuration.] |
| Model configuration | [Describe model family, hyperparameters, or method if applicable.] |
| Training period | [Start date - end date] |
| Validation period | [Start date - end date] |
| Test period | [Start date - end date] |
| Forecast horizon | [e.g., 1-month, 12-month, or other] |
| Validation method | [Expanding window / rolling origin / cross-validation / holdout] |
| Random seed | [Seed value, if used] |
| Evaluation metrics | [Metric names and definitions] |
| Synthetic-data usage | [None / Training-only / Validation-only / Test-only / Not applicable] |
| Software environment | [Python version, environment name, package versions] |
| Results location | [Path to experiment output or artifact directory] |
| Limitations | [Known constraints, data limitations, or methodological caveats.] |
| Reproducibility status | [Not yet reproducible / Reproducible / Requires review] |

## Blank example record

| Field | Example |
| --- | --- |
| Experiment ID | [EXP-001] |
| Research stage | [Stage 2] |
| Research question | [Does exchange-rate information improve one-step inflation forecasts?] |
| Hypothesis | [Exchange-rate variables add predictive value beyond CPI history.] |
| Dataset versions | [DATASET-001, DATASET-002, revision vintage: pending inspection] |
| Feature configuration | [C0 / C1 / C2 / C3, pending inspection] |
| Model configuration | [Model family pending inspection] |
| Training period | [YYYY-MM-DD to YYYY-MM-DD] |
| Validation period | [YYYY-MM-DD to YYYY-MM-DD] |
| Test period | [YYYY-MM-DD to YYYY-MM-DD] |
| Forecast horizon | [1M to 12M, pending inspection] |
| Validation method | [Expanding-window evaluation] |
| Random seed | [42] |
| Evaluation metrics | [MAE, RMSE, directional accuracy, calibration metrics if applicable] |
| Synthetic-data usage | [None] |
| Software environment | [Python 3.13.0, project-local .venv] |
| Results location | [artifacts/predictions/ or artifacts/metrics/] |
| Limitations | [Pending inspection] |
| Reproducibility status | [Pending documentation] |

## MLflow-ready architecture notes

- Keep experiment metadata in a structured format that can later be captured by MLflow.
- Record dataset identifiers, feature configurations, and environment metadata explicitly.
- Store outputs in a reproducible artifact directory and document their provenance.
- Maintain a separation between raw data, interim transformations, and model outputs.
- Keep the experiment record independent of any external platform so it remains portable.

## Governance rules

- Document each experiment before execution begins.
- Record forecast origin, dataset vintage, and validation design explicitly.
- Distinguish proposed configurations from verified implementations.
- Do not fabricate results or assumptions about schema.
- Use the final chronological test period only once the design is locked.
