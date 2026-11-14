"""Lightweight environment verification for the POME EL project."""

from __future__ import annotations

import subprocess
import sys
from importlib import metadata
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

REQUIRED_IMPORTS = {
    "pandas": "pandas",
    "numpy": "numpy",
    "scipy": "scipy",
    "statsmodels": "statsmodels",
    "sklearn": "sklearn",
    "xgboost": "xgboost",
    "shap": "shap",
    "matplotlib": "matplotlib",
    "seaborn": "seaborn",
    "plotly": "plotly",
    "streamlit": "streamlit",
    "openpyxl": "openpyxl",
    "pytest": "pytest",
    "ruff": "ruff",
    "mypy": "mypy",
}


def verify_python() -> dict[str, str]:
    """Return interpreter and environment metadata."""
    return {
        "executable": sys.executable,
        "version": sys.version.split()[0],
        "project_root": str(PROJECT_ROOT),
        "in_virtualenv": hasattr(sys, "base_prefix") and sys.base_prefix != sys.prefix,
    }


def verify_imports() -> dict[str, str]:
    """Attempt to import required packages and capture versions."""
    versions: dict[str, str] = {}
    for label, module_name in REQUIRED_IMPORTS.items():
        try:
            __import__(module_name)
            try:
                versions[label] = metadata.version(module_name)
            except metadata.PackageNotFoundError:
                module = sys.modules.get(module_name)
                versions[label] = getattr(module, "__version__", "unknown") if module else "unknown"
        except Exception as exc:  # pragma: no cover - environment diagnostic only
            versions[label] = f"IMPORT_ERROR: {exc.__class__.__name__}: {exc}"
    return versions


def run_command(command: list[str]) -> tuple[int, str]:
    """Execute a subprocess command and return the exit code plus output."""
    result = subprocess.run(command, cwd=str(PROJECT_ROOT), capture_output=True, text=True)
    return result.returncode, (result.stdout + result.stderr).strip()


def main() -> int:
    """Validate the environment and print a compact status summary."""
    print("POME EL Environment Verification")
    python_info = verify_python()
    print(f"Interpreter: {python_info['executable']}")
    print(f"Version: {python_info['version']}")
    print(f"Project root: {python_info['project_root']}")
    print(f"Virtual environment: {python_info['in_virtualenv']}")

    imports = verify_imports()
    failed_imports = [key for key, value in imports.items() if value.startswith("IMPORT_ERROR")]
    for name, version in imports.items():
        print(f"{name}: {version}")

    print("\nRunning Ruff check...")
    ruff_code, ruff_output = run_command([sys.executable, "-m", "ruff", "check", "."])
    print(ruff_output if ruff_output else "Ruff check completed without output.")
    print(f"Ruff exit code: {ruff_code}")

    print("\nRunning pytest...")
    pytest_code, pytest_output = run_command([sys.executable, "-m", "pytest", "-q"])
    print(pytest_output if pytest_output else "Pytest completed without output.")
    print(f"Pytest exit code: {pytest_code}")

    print("\nRunning compileall...")
    compile_code, compile_output = run_command([sys.executable, "-m", "compileall", "."])
    print(compile_output if compile_output else "Compileall completed without output.")
    print(f"Compileall exit code: {compile_code}")

    if failed_imports:
        print(f"\nImport failures: {failed_imports}")
        return 1
    if ruff_code != 0:
        print("\nRuff check failed.")
        return 1
    if pytest_code != 0:
        print("\nPytest failed.")
        return 1
    if compile_code != 0:
        print("\nCompileall failed.")
        return 1

    print("\nEnvironment verification passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
