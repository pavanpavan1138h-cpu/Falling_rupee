# POME EL

POME EL is a research and software engineering foundation for studying how the Indian rupee exchange rate, imported prices, and inflation interact in the Indian economy.

## Research direction

The project is organized around a five-stage research workflow:

1. USD/INR exchange-rate forecasting
2. Indian CPI inflation forecasting
3. Asymmetric exchange-rate pass-through analysis
4. High-inflation early-warning classification
5. Inflation persistence and WPI analysis

The work emphasizes reproducible methods, transparent diagnostics, and explainable AI for macroeconomic research.

## Repository structure

- `config/`: Centralized project configuration and settings
- `data/`: Raw, interim, processed and synthetic data storage
- `notebooks/`: Research notebooks and exploratory analyses
- `src/`: Source code for data, preprocessing, features, forecasting, evaluation, dashboarding and explainability
- `tests/`: Pytest suite for project validation
- `artifacts/`: Saved models, predictions and metrics
- `visualizations/`: Research-quality plots and figure outputs
- `reports/`: Audit and experiment documentation
- `logs/`: Runtime and diagnostic logs
- `dashboard/`: Streamlit app assets and dashboard entrypoints

## Working principles

- Do not modify or overwrite original datasets without explicit workflow controls.
- Keep analysis reproducible by centralizing project paths and random seeds.
- Maintain modular architecture to support future research stages.
- Avoid inventing findings, model outputs, or assumptions about schemas.

## Development environment

This project is designed for Python on Windows and follows a standard scientific Python stack. Dependency installation is intentionally deferred until the project foundation is in place.

## Quality and validation

- `pytest` for automated validation
- `ruff` for linting and formatting checks
- `mypy` for static type checking where practical

## Getting started

1. Create and activate a virtual environment.
2. Install dependencies from `requirements.txt`.
3. Use the project configuration in `config/settings.py` for paths and random seeds.
4. Run tests with `pytest`.

## License

This project is intended for research and internal development use unless otherwise specified by the owner.
