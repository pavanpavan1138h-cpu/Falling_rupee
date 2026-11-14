"""Entry point for exchange-rate forecasting experiments."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main() -> None:
    from src.forecasting.exchange_rate.forecasting import run_stage1_forecasting

    predictions, metrics, _metadata = run_stage1_forecasting()
    message = (
        f"Forecast experiments complete: {len(predictions)} predictions across "
        f"{len(metrics)} model-horizon rows"
    )
    print(message)
    print(metrics.to_string(index=False))


if __name__ == "__main__":
    main()
