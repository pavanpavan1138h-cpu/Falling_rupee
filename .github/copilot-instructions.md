# Copilot instructions for POME EL

This repository is a research and engineering foundation for studying the relationship between rupee depreciation, imported inflation, and domestic inflation in India.

## Operating constraints

- Do not train machine learning models during this phase.
- Do not generate or fabricate synthetic datasets.
- Do not assume dataset schemas or column names without explicit project inputs.
- Do not preprocess external datasets or modify source data files.
- Do not download external data automatically.
- Do not invent model metrics, charts, forecasts, or results.
- Do not proceed beyond the project initialization stage without explicit approval.

## Engineering expectations

- Follow Pythonic, modular, maintainable code structures.
- Use pathlib-based paths and keep Windows compatibility in mind.
- Keep project configuration centralized.
- Add type hints, docstrings, and clear naming where appropriate.
- Prefer reproducible, explainable, and testable code.
- Keep research artifacts and configuration explicit rather than implicit.

## Data safety

- Never silently overwrite original datasets.
- Preserve source data integrity and maintain separate working directories for derived outputs.
- Keep all processed or generated files in the configured `data/` and `artifacts/` spaces.

## Validation and quality

- Use pytest for validation when adding tests.
- Keep code lint-friendly and reasonably typed.
- Log important technical issues in the configured project logger rather than suppressing them.
