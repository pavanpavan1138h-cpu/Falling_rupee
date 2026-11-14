"""Project logging configuration and reusable logger accessors."""

from __future__ import annotations

import logging
from pathlib import Path


def configure_logging(
    log_dir: str | Path | None = None,
    level: int = logging.INFO,
) -> logging.Logger:
    """Configure a project logger with both console and file handlers."""

    root = Path(__file__).resolve().parents[2]
    log_path = Path(log_dir) if log_dir else root / "logs"
    log_path.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger("pome_el")
    logger.setLevel(level)
    logger.propagate = False
    logger.handlers.clear()

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(level)
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    file_handler = logging.FileHandler(log_path / "pome_el.log", encoding="utf-8")
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger


def get_logger(name: str) -> logging.Logger:
    """Return a namespaced logger from the project logger hierarchy."""

    return logging.getLogger(f"pome_el.{name}")
