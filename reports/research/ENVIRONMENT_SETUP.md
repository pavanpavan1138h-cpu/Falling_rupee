# POME EL Environment Setup

## Selected Python interpreter

- Python version selected: 3.13.0
- Interpreter source: `py -3.13`
- Virtual environment path: `.venv` under the project root
- Environment: Windows PowerShell

## Project-local virtual environment

```powershell
cd C:\Users\Ram Charan. R\Documents\POME_EL
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -V
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## Dependency installation notes

The project uses the scientific Python stack required for the POME EL research foundation. The dependency list in `requirements.txt` is consistent with the project plan and includes:

- pandas, numpy, scipy
- statsmodels
- scikit-learn, xgboost
- shap
- matplotlib, seaborn, plotly
- streamlit
- openpyxl
- xlrd
- PyYAML
- pytest, ruff, mypy

No duplicate or unnecessary packages were introduced during environment setup.

## Package verification and version capture

The complete installed environment was captured from the active `.venv` using `python -m pip freeze`; see [dependency_snapshot.txt](./dependency_snapshot.txt). The snapshot contains 71 distribution entries and is the authoritative version record. Selected verified versions include:

- pandas==3.1.1
- numpy==2.5.4
- scipy==1.18.1
- statsmodels==0.15.0
- scikit-learn==1.9.1
- xgboost==3.4.1
- shap==0.54.1
- matplotlib==3.11.2
- seaborn==0.13.2
- plotly==7.1.0
- streamlit==1.67.0
- openpyxl==3.1.5
- xlrd==2.0.2
- PyYAML==6.0.3
- pytest==9.2.0
- ruff==0.17.4
- mypy==2.4.1

## Approved dependency installation

The following dependencies were installed into the existing project-local `.venv` under explicit approval:

- `xlrd` for legacy Excel workbook reading
- `PyYAML` for validating `config/data_contracts.yaml`

Validation results:

- `import xlrd` succeeded
- `import yaml` succeeded
- `pip check` reported no broken requirements
- Legacy WPI workbook readability using pandas with the `xlrd` engine succeeded
- The WPI sheet inspected read-only has 870 rows × 172 columns; see `reports/data_audit/WPI_DEEP_INSPECTION.md`.
- The dependency snapshot was regenerated directly from the installed environment. No unrelated packages were upgraded during this task.

## VS Code configuration

The project uses a workspace-level interpreter and test configuration in `.vscode/settings.json`.

```json
{
  "python.defaultInterpreterPath": "${workspaceFolder}\\.venv\\Scripts\\python.exe",
  "python.terminal.activateEnvironment": true,
  "python.testing.pytestEnabled": true,
  "python.testing.pytestArgs": [
    "tests"
  ],
  "python.analysis.typeCheckingMode": "basic"
}
```

## Quality checks

Use the following commands to verify the environment:

```powershell
cd C:\Users\Ram Charan. R\Documents\POME_EL
.\.venv\Scripts\Activate.ps1
python -m pytest -q
ruff check .
python -m compileall .
```

## Compatibility notes

- Python 3.11 or 3.12 was not present in the local environment.
- Python 3.13 was selected as the available compatible interpreter for the project stack.
- This environment is intended for the setup and validation phase only; no data processing or research implementation was performed.

## Reproduction instructions

1. Ensure the target Windows machine has Python 3.13 available via `py`.
2. Create the project-local virtual environment under `.venv`.
3. Activate it in PowerShell.
4. Install dependencies from `requirements.txt`.
5. Use the workspace settings in `.vscode/settings.json`.
6. Run pytest, ruff, and compile checks before any downstream research work.
