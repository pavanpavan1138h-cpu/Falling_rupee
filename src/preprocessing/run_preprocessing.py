"""Entry point for the POME EL preprocessing pipeline."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config.settings import PROJECT_PATHS  # noqa: E402
from src.preprocessing.pipeline import run_preprocessing  # noqa: E402


def main() -> None:
    """Execute the preprocessing pipeline from the project root."""
    outputs = run_preprocessing(PROJECT_PATHS.root)
    print(
        "Preprocessing complete: "
        f"{len(outputs)} dataset tables written to "
        f"{PROJECT_PATHS.processed}"
    )


if __name__ == "__main__":
    main()
