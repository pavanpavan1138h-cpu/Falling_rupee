"""Generate verified feature-engineering outputs from the processed datasets."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.features.feature_engineering import generate_feature_outputs  # noqa: E402


def main() -> None:
    """Generate feature outputs under data/processed/features."""
    project_root = Path(__file__).resolve().parents[2]
    outputs = generate_feature_outputs(project_root)
    print(
        "Feature engineering complete: "
        f"{len(outputs)} tables written to {project_root / 'data' / 'processed' / 'features'}"
    )


if __name__ == "__main__":
    main()
