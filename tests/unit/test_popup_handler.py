import logging

import pytest
from selenium.common.exceptions import ElementClickInterceptedException
from selenium.webdriver.common.by import By

from framework.popup_handler import GENERIC_MODAL, Popup, PopupHandler

pytestmark = pytest.mark.unit

SHEET = (By.CSS_SELECTOR, "#sheet")
SHEET_CLOSE = (By.CSS_SELECTOR, "#sheet-close")
BANNER = (By.CSS_SELECTOR, "#banner")
BANNER_ACCEPT = (By.CSS_SELECTOR, "#banner-accept")
BANNER_PROCEED = (By.CSS_SELECTOR, "#banner-proceed")


class FakeElement:
    def __init__(self, page, removes=(), displayed=True, intercepted=False, label=None):
        self.page, self.removes, self.label = page, removes, label
        self.displayed, self.intercepted = displayed, intercepted

    def is_displayed(self):
        return self.displayed

    def click(self):
        if self.intercepted:
            raise ElementClickInterceptedException("covered")
        self.page.remove(*self.removes)

    def get_attribute(self, name):
        return self.label if name == "aria-label" else None


class FakeDriver:
    """Minimal page: a locator -> elements map; clicking a dismiss button removes its pop-up."""

    def __init__(self):
        self.elements: dict[tuple[str, str], list[FakeElement]] = {}
        self.js_clicks = 0

    def add(self, locator, **kwargs):
        element = FakeElement(self, **kwargs)
        self.elements.setdefault(locator, []).append(element)
        return element

    def remove(self, *locators):
        for locator in locators:
            self.elements.pop(locator, None)

    def find_elements(self, by, value):
        return list(self.elements.get((by, value), []))

    def execute_script(self, script, element):
        self.js_clicks += 1
        element.page.remove(*element.removes)


POPUPS = (
    Popup("sheet", detect=SHEET, dismiss=(SHEET_CLOSE,)),
    Popup("banner", detect=BANNER, dismiss=(BANNER_ACCEPT, BANNER_PROCEED)),
)


def show_sheet(driver, **kwargs):
    driver.add(SHEET)
    driver.add(SHEET_CLOSE, removes=(SHEET, SHEET_CLOSE), **kwargs)


def test_nothing_on_screen_dismisses_nothing():
    assert PopupHandler(FakeDriver(), POPUPS).dismiss_all() == []


def test_visible_popup_is_dismissed():
    driver = FakeDriver()
    show_sheet(driver)
    assert PopupHandler(driver, POPUPS).dismiss_all() == ["sheet"]
    assert driver.find_elements(*SHEET) == []


def test_hidden_popup_is_ignored():
    driver = FakeDriver()
    driver.add(SHEET, displayed=False)
    driver.add(SHEET_CLOSE, removes=(SHEET,))
    assert PopupHandler(driver, POPUPS).dismiss_all() == []


def test_falls_back_to_the_next_dismiss_control():
    driver = FakeDriver()
    driver.add(BANNER)
    driver.add(BANNER_PROCEED, removes=(BANNER, BANNER_PROCEED))  # GDPR variant: no "Accept"
    assert PopupHandler(driver, POPUPS).dismiss_all() == ["banner"]


def test_stacked_popups_are_all_dismissed():
    driver = FakeDriver()
    show_sheet(driver)
    driver.add(BANNER)
    driver.add(BANNER_ACCEPT, removes=(BANNER, BANNER_ACCEPT))
    assert sorted(PopupHandler(driver, POPUPS).dismiss_all()) == ["banner", "sheet"]


def test_intercepted_click_falls_back_to_javascript():
    driver = FakeDriver()
    show_sheet(driver, intercepted=True)
    assert PopupHandler(driver, POPUPS).dismiss_all() == ["sheet"]
    assert driver.js_clicks == 1


def test_detected_popup_without_clickable_control_is_reported(caplog):
    driver = FakeDriver()
    driver.add(SHEET)
    with caplog.at_level(logging.WARNING):
        assert PopupHandler(driver, POPUPS).dismiss_all() == []
    assert "'sheet' detected but no dismiss control" in caplog.text


def test_unregistered_modal_warns_once(caplog):
    driver = FakeDriver()
    driver.add(GENERIC_MODAL, label="Subscribe now")
    handler = PopupHandler(driver, POPUPS)
    with caplog.at_level(logging.WARNING):
        handler.dismiss_all()
        handler.dismiss_all()
    assert caplog.text.count("Unregistered modal on screen: Subscribe now") == 1
