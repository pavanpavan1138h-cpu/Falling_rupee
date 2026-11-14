"""Basic validation that the project foundation has the required structure."""

from pathlib import Path

from config.settings import PROJECT_PATHS, RANDOM_SEED

REQUIRED_DIRECTORIES = (
    PROJECT_PATHS.raw,
    PROJECT_PATHS.interim,
    PROJECT_PATHS.processed,
    PROJECT_PATHS.synthetic,
    PROJECT_PATHS.notebooks,
    PROJECT_PATHS.models,
    PROJECT_PATHS.predictions,
    PROJECT_PATHS.metrics,
    PROJECT_PATHS.visualizations,
    PROJECT_PATHS.reports,
    PROJECT_PATHS.logs,
    PROJECT_PATHS.dashboard,
)


def test_required_directories_exist() -> None:
    for directory in REQUIRED_DIRECTORIES:
        assert directory.exists(), f"Missing required directory: {directory}"


def test_random_seed_is_configured() -> None:
    assert isinstance(RANDOM_SEED, int)
    assert RANDOM_SEED > 0


def test_top_level_files_exist() -> None:
    root = Path(__file__).resolve().parent.parent
    required_files = (
        "README.md",
        "requirements.txt",
        "pyproject.toml",
        ".gitignore",
        ".env.example",
    )
    for relative_path in required_files:
        assert (root / relative_path).exists(), f"Missing required file: {relative_path}"
