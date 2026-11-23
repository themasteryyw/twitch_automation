"""Explicit waits and reusable page conditions.

The framework never uses ``time.sleep`` or implicit waits: every wait polls a
named condition with ``WebDriverWait`` so failures say *what* never happened.
Conditions are plain callables ``(driver) -> truthy`` and can be composed.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from selenium.common.exceptions import StaleElementReferenceException, TimeoutException
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import WebDriverWait

from framework.logger import get_logger

Condition = Callable[[WebDriver], Any]
log = get_logger(__name__)


class Waiter:
    def __init__(self, driver: WebDriver, default_timeout: int, poll: float = 0.25) -> None:
        self.driver = driver
        self.default_timeout = default_timeout
        self.poll = poll

    def until(self, condition: Condition, message: str, timeout: int | None = None) -> Any:
        timeout = timeout or self.default_timeout
        wait = WebDriverWait(
            self.driver,
            timeout,
            poll_frequency=self.poll,
            ignored_exceptions=(StaleElementReferenceException,),
        )
        try:
            return wait.until(condition)
        except TimeoutException as exc:
            raise TimeoutException(f"Timed out after {timeout}s waiting for: {message}") from exc


# --------------------------------------------------------------------------- #
# Page conditions (JavaScript predicates)
# --------------------------------------------------------------------------- #


def document_ready(driver: WebDriver) -> bool:
    """True once the DOM is parsed ('interactive' or 'complete').

    Matches the 'eager' page-load strategy: live previews and autoplay video can
    keep the window 'load' event (readyState 'complete') pending indefinitely,
    so page readiness is decided by each page's ready_locator instead.
    """
    return driver.execute_script("return document.readyState") in ("interactive", "complete")


def video_playing() -> Condition:
    """Condition factory: True once the player has data, is not paused and its time advanced between two polls.

    A frozen or stalled stream keeps ``currentTime`` fixed, so a single ``currentTime > 0`` check is not enough.
    """
    last: dict[str, float | None] = {"t": None}

    def _condition(driver: WebDriver) -> bool:
        t = driver.execute_script(
            """
            const v = document.querySelector('video');
            return v && v.readyState >= 3 && !v.paused ? v.currentTime : null;
            """
        )
        advancing = t is not None and last["t"] is not None and t > last["t"]
        last["t"] = t
        return advancing

    return _condition


def viewport_images_loaded(driver: WebDriver) -> bool:
    """True when every <img> currently on screen has finished decoding."""
    return bool(
        driver.execute_script(
            """
            return [...document.images]
              .filter(img => {
                const r = img.getBoundingClientRect();
                return r.width > 0 && r.height > 0 && r.bottom > 0 && r.top < innerHeight;
              })
              .every(img => img.complete && img.naturalWidth > 0);
            """
        )
    )


def scroll_settled() -> Condition:
    """Condition factory: True once the scroll position is identical on two polls."""
    last: dict[str, float | None] = {"y": None}

    def _condition(driver: WebDriver) -> bool:
        y = driver.execute_script("return window.scrollY")
        settled = last["y"] is not None and y == last["y"]
        last["y"] = y
        return settled

    return _condition


def element_unobstructed(element: WebElement) -> Condition:
    """Condition factory: the element itself (or a child) is the hit target at its centre.

    ``element_to_be_clickable`` only checks displayed + enabled, so it passes even
    when an overlay (bottom sheet, modal backdrop) covers the element.
    """

    def _condition(driver: WebDriver) -> WebElement | bool:
        hit = driver.execute_script(
            """
            const el = arguments[0], r = el.getBoundingClientRect();
            if (!r.width || !r.height) return false;
            const x = r.left + r.width / 2, y = r.top + r.height / 2;
            if (x < 0 || y < 0 || x > innerWidth || y > innerHeight) return false;
            const top = document.elementFromPoint(x, y);
            return !!top && (top === el || el.contains(top));
            """,
            element,
        )
        return element if hit else False

    return _condition


def url_contains(fragment: str) -> Condition:
    return lambda driver: fragment.lower() in driver.current_url.lower()


def all_of(*conditions: Condition) -> Condition:
    return lambda driver: all(condition(driver) for condition in conditions)
