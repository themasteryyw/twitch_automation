"""Named, timestamped screenshots that are safe under parallel runs."""

from __future__ import annotations

import os
import re
from datetime import datetime
from pathlib import Path

from selenium.webdriver.remote.webdriver import WebDriver

from framework.logger import get_logger

log = get_logger(__name__)


def _safe(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", name).strip("_") or "screenshot"


def take_screenshot(driver: WebDriver, directory: Path, name: str) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    worker = os.getenv("PYTEST_XDIST_WORKER", "main")
    path = directory / f"{datetime.now():%Y%m%d_%H%M%S}_{worker}_{_safe(name)}.png"
    if not driver.save_screenshot(str(path)):
        raise RuntimeError(f"Failed to save screenshot to {path}")
    log.info("Screenshot saved: %s", path)
    return path
