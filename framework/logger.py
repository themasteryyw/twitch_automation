"""Logging setup: one log file per run plus console output (via pytest log_cli).

All framework loggers are children of ``automation`` so a single handler
captures everything: ``get_logger(__name__)`` -> ``automation.<module>``.
"""

from __future__ import annotations

import logging
import os
from datetime import datetime
from pathlib import Path

ROOT_LOGGER = "automation"
LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"


def get_logger(name: str) -> logging.Logger:
    short = name.rsplit(".", 1)[-1]
    return logging.getLogger(f"{ROOT_LOGGER}.{short}")


def setup_file_logging(logs_dir: Path, level: int = logging.DEBUG) -> Path:
    """Attach a per-run file handler to the framework root logger (idempotent)."""
    root = logging.getLogger(ROOT_LOGGER)
    root.setLevel(level)
    for handler in root.handlers:
        if isinstance(handler, logging.FileHandler):
            return Path(handler.baseFilename)

    logs_dir.mkdir(parents=True, exist_ok=True)
    worker = os.getenv("PYTEST_XDIST_WORKER", "main")
    log_file = logs_dir / f"run_{datetime.now():%Y%m%d_%H%M%S}_{worker}.log"
    handler = logging.FileHandler(log_file, encoding="utf-8")
    handler.setFormatter(logging.Formatter(LOG_FORMAT))
    root.addHandler(handler)
    return log_file
