"""Site-agnostic Page Object base class.

Each page declares *what "loaded" means* (``ready_locator`` and, if needed, an
override of ``is_loaded``), and which pop-ups may cover it (``popups``).
Navigation between pages goes through ``go_to`` so every returned page object
is already loaded and verified.
"""

from __future__ import annotations

from typing import TypeVar
from urllib.parse import urljoin

from selenium.common.exceptions import ElementClickInterceptedException, TimeoutException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC

from config.settings import Settings
from framework import waits
from framework.logger import get_logger
from framework.popup_handler import Locator, Popup, PopupHandler

P = TypeVar("P", bound="BasePage")


class BasePage:
    path: str = "/"
    ready_locator: Locator | None = None
    popups: tuple[Popup, ...] = ()

    @property
    def ready_timeout(self) -> int | None:
        """Max wait for ``ready_locator``; None = the default explicit-wait timeout."""
        return None

    def __init__(self, driver: WebDriver, settings: Settings) -> None:
        self.driver = driver
        self.settings = settings
        self.wait = waits.Waiter(driver, settings.timeout)
        self.popup_handler = PopupHandler(driver, self.popups)
        self.log = get_logger(type(self).__name__)

    # ----------------------------- lifecycle ----------------------------- #

    @property
    def url(self) -> str:
        return urljoin(self.settings.base_url, self.path)

    def open(self: P) -> P:
        self.log.info("Opening %s", self.url)
        self.driver.get(self.url)
        return self.wait_until_loaded()

    def wait_until_loaded(self: P) -> P:
        self.wait.until(waits.document_ready, "document.readyState interactive/complete")
        self.dismiss_popups()
        if self.ready_locator is not None:
            self.get_element(self.ready_locator, timeout=self.ready_timeout)
        self.log.info("%s loaded", type(self).__name__)
        return self

    def go_to(self, page_cls: type[P], **kwargs) -> P:
        return page_cls(self.driver, self.settings, **kwargs).wait_until_loaded()

    def dismiss_popups(self) -> list[str]:
        return self.popup_handler.dismiss_all()

    # ------------------------------ elements ----------------------------- #

    def get_element(self, locator: Locator, clickable: bool = False, timeout: int | None = None) -> WebElement:
        condition = EC.element_to_be_clickable if clickable else EC.visibility_of_element_located
        return self.wait.until(
            condition(locator), f"element {locator} ({'clickable' if clickable else 'visible'})", timeout
        )

    def is_visible(self, locator: Locator) -> bool:
        """Non-waiting visibility check, safe to call on every poll of a wait."""
        return self.popup_handler.find_visible(locator) is not None

    def get_elements(self, locator: Locator) -> list[WebElement]:
        return self.wait.until(EC.presence_of_all_elements_located(locator), f"elements {locator}")

    def wait_until_interactable(self, target: Locator | WebElement) -> WebElement:
        """Wait until nothing covers the element, dismissing pop-ups on every poll.

        Pop-ups can render asynchronously after an SPA navigation, i.e. after the
        page already counted as loaded, so they are cleared right before acting.
        """
        element = target if isinstance(target, WebElement) else self.get_element(target, clickable=True)
        self.scroll_into_view(element)
        unobstructed = waits.element_unobstructed(element)

        def _ready(driver: WebDriver) -> WebElement | bool:
            self.dismiss_popups()
            return unobstructed(driver)

        return self.wait.until(
            _ready, f"{target if not isinstance(target, WebElement) else 'element'} to be unobstructed"
        )

    def click(self, target: Locator | WebElement) -> None:
        element = self.wait_until_interactable(target)
        try:
            element.click()
        except ElementClickInterceptedException:
            # An overlay appeared between the check and the click: wait it out once more.
            self.log.info("Click intercepted, waiting for the overlay to clear and retrying")
            self.wait_until_interactable(element).click()

    def click_to_navigate(self, target: Locator, url_fragment: str, attempts: int = 2) -> None:
        """Click a navigation control and verify the URL changed; re-click if the first click was lost."""
        for attempt in range(1, attempts + 1):
            self.click(target)
            try:
                self.wait.until(waits.url_contains(url_fragment), f"URL to contain '{url_fragment}'", timeout=5)
                return
            except TimeoutException:
                if attempt == attempts:
                    raise
                self.log.warning(
                    "Click on %s did not navigate to '%s' (attempt %d/%d), retrying",
                    target,
                    url_fragment,
                    attempt,
                    attempts,
                )

    def type_text(self, locator: Locator, text: str, submit: bool = False) -> None:
        element = self.wait_until_interactable(locator)
        element.click()
        element.clear()
        element.send_keys(text + (Keys.ENTER if submit else ""))
        self.log.info("Typed '%s'%s", text, " + ENTER" if submit else "")

    # ------------------------------ viewport ----------------------------- #

    def scroll_into_view(self, element: WebElement) -> None:
        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)

    def scroll_down(self, times: int = 1, viewport_ratio: float = 0.8) -> None:
        for i in range(1, times + 1):
            before = self.driver.execute_script("return window.scrollY")
            self.driver.execute_script("window.scrollBy(0, window.innerHeight * arguments[0]);", viewport_ratio)
            self.wait.until(waits.scroll_settled(), "scroll position to settle")
            after, max_y = self.driver.execute_script(
                "return [window.scrollY, document.scrollingElement.scrollHeight - window.innerHeight]"
            )
            self.log.info("Scrolled down %d/%d (scrollY %s -> %s, max %s)", i, times, before, after, max_y)
            if after <= before:
                self.log.warning("Scroll %d/%d did not move: already at the bottom of the page", i, times)

    def is_in_viewport(self, element: WebElement) -> bool:
        return bool(
            self.driver.execute_script(
                "const r = arguments[0].getBoundingClientRect();"
                "return r.top >= 0 && r.bottom <= window.innerHeight && r.width > 0;",
                element,
            )
        )
