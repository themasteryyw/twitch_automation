"""Test fixtures: settings -> driver -> pages, plus an on-demand screenshot factory."""

from __future__ import annotations

from pathlib import Path
from typing import Callable, Iterator

import pytest
from selenium.webdriver.remote.webdriver import WebDriver

from config.settings import Settings
from framework.driver_factory import create_driver
from framework.screenshot import take_screenshot
from pages.twitch import HomePage


@pytest.fixture
def driver(request: pytest.FixtureRequest, settings: Settings) -> Iterator[WebDriver]:
    """Fresh browser per test for isolation. ``@pytest.mark.device(name)`` overrides --device."""
    marker = request.node.get_closest_marker("device")
    driver = create_driver(settings, device_name=marker.args[0] if marker else None)
    request.node._driver = driver  # used by the failure hook in the root conftest
    yield driver
    try:
        driver.quit()
    except Exception:
        pass


@pytest.fixture
def home_page(driver: WebDriver, settings: Settings) -> HomePage:
    return HomePage(driver, settings).open()


@pytest.fixture
def screenshot(driver: WebDriver, settings: Settings) -> Callable[[str], Path]:
    """Usage: ``path = screenshot("streamer_page")``."""
    return lambda name: take_screenshot(driver, settings.screenshots_dir, name)
