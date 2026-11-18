"""Generic pop-up / modal handling.

Pop-ups are declared as data (``Popup``), not code: each site registers a
tuple of known pop-ups and the handler dismisses whichever are on screen.
Detection uses ``find_elements`` (returns immediately), so calling
``dismiss_all()`` on every poll of a wait is cheap - that is how late
interstitials (e.g. a mature-content gate shown after the player mounts) are
caught.
"""

from __future__ import annotations

from dataclasses import dataclass

from selenium.common.exceptions import (
    ElementClickInterceptedException,
    ElementNotInteractableException,
    StaleElementReferenceException,
)
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement

from framework.logger import get_logger

Locator = tuple[str, str]
log = get_logger(__name__)

GENERIC_MODAL: Locator = (By.CSS_SELECTOR, '[aria-modal="true"]')


@dataclass(frozen=True)
class Popup:
    name: str
    detect: Locator
    dismiss: tuple[Locator, ...]  # tried in order until one is clickable


class PopupHandler:
    def __init__(self, driver: WebDriver, popups: tuple[Popup, ...]) -> None:
        self.driver = driver
        self.popups = popups
        self._warned_unknown = False

    def dismiss_all(self, max_rounds: int = 5) -> list[str]:
        """Dismiss every known pop-up on screen; pop-ups can stack, so loop a few rounds."""
        dismissed: list[str] = []
        for _ in range(max_rounds):
            handled = [p.name for p in self.popups if self._try_dismiss(p)]
            if not handled:
                break
            dismissed.extend(handled)
        if not dismissed:
            self._warn_on_unknown_modal()
        return dismissed

    # ------------------------------------------------------------------ #

    def _visible(self, locator: Locator) -> WebElement | None:
        for element in self.driver.find_elements(*locator):
            try:
                if element.is_displayed():
                    return element
            except StaleElementReferenceException:
                continue
        return None

    def _try_dismiss(self, popup: Popup) -> bool:
        if self._visible(popup.detect) is None:
            return False
        for locator in popup.dismiss:
            button = self._visible(locator)
            if button is None:
                continue
            try:
                button.click()
            except (ElementClickInterceptedException, ElementNotInteractableException):
                self.driver.execute_script("arguments[0].click();", button)
            except StaleElementReferenceException:
                return False
            log.info("Dismissed pop-up: %s", popup.name)
            return True
        log.warning("Pop-up '%s' detected but no dismiss control was clickable", popup.name)
        return False

    def _warn_on_unknown_modal(self) -> None:
        if self._warned_unknown:
            return
        modal = self._visible(GENERIC_MODAL)
        if modal is None:
            return
        # The modal may have rendered between the registered checks and this one; re-check before warning.
        if any(self._visible(p.detect) is not None for p in self.popups):
            return
        self._warned_unknown = True
        label = modal.get_attribute("aria-label") or "<no aria-label>"
        log.warning("Unregistered modal on screen: %s - consider adding it to the pop-up table", label)
