"""Central project settings and path definitions for POME EL."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class ProjectPaths:
    """Strongly typed project directory references."""

    root: Path = PROJECT_ROOT
    config: Path = PROJECT_ROOT / "config"
    data: Path = PROJECT_ROOT / "data"
    raw: Path = data / "raw"
    interim: Path = data / "interim"
    processed: Path = data / "processed"
    synthetic: Path = data / "synthetic"
    notebooks: Path = PROJECT_ROOT / "notebooks"
    src: Path = PROJECT_ROOT / "src"
    tests: Path = PROJECT_ROOT / "tests"
    artifacts: Path = PROJECT_ROOT / "artifacts"
    models: Path = artifacts / "models"
    predictions: Path = artifacts / "predictions"
    metrics: Path = artifacts / "metrics"
    visualizations: Path = PROJECT_ROOT / "visualizations"
    reports: Path = PROJECT_ROOT / "reports"
    logs: Path = PROJECT_ROOT / "logs"
    dashboard: Path = PROJECT_ROOT / "dashboard"


PROJECT_PATHS = ProjectPaths()
RANDOM_SEED = 42


def ensure_project_directories() -> None:
    """Create project directories required during initialization."""

    required_directories = (
        PROJECT_PATHS.raw,
        PROJECT_PATHS.interim,
        PROJECT_PATHS.processed,
        PROJECT_PATHS.synthetic,
        PROJECT_PATHS.notebooks,
        PROJECT_PATHS.tests,
        PROJECT_PATHS.models,
        PROJECT_PATHS.predictions,
        PROJECT_PATHS.metrics,
        PROJECT_PATHS.visualizations,
        PROJECT_PATHS.reports,
        PROJECT_PATHS.logs,
        PROJECT_PATHS.dashboard,
    )

    for directory in required_directories:
        directory.mkdir(parents=True, exist_ok=True)
