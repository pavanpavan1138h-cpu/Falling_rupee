"""Entry point for generating research-oriented exploratory-data-analysis outputs."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main() -> None:
    """Generate EDA charts and summary files for the established research feature set."""
    from src.visualization.eda import generate_eda_outputs

    outputs = generate_eda_outputs()
    for path in outputs.values():
        print(f"EDA output written: {path}")


if __name__ == "__main__":
    main()
