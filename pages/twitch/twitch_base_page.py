"""Twitch-specific base page: registers the pop-ups Twitch can show on any page."""

from __future__ import annotations

from selenium.webdriver.common.by import By

from framework.base_page import BasePage
from framework.popup_handler import Popup

TWITCH_POPUPS: tuple[Popup, ...] = (
    Popup(
        name="Open in App bottom sheet",
        detect=(By.CSS_SELECTOR, '[role="dialog"][aria-label*="Open in App"]'),
        dismiss=((By.XPATH, '//button[.//p[normalize-space()="Keep using web"]]'),),
    ),
    Popup(
        name="Mature content gate",
        detect=(
            By.CSS_SELECTOR,
            '[data-a-target*="content-classification-gate"], [data-a-target*="start-watching-button"]',
        ),
        dismiss=(
            (By.CSS_SELECTOR, '[data-a-target*="start-watching-button"]'),
            (By.XPATH, '//button[.//*[normalize-space()="Start Watching"]]'),
        ),
    ),
    Popup(
        name="Cookie consent banner",
        detect=(By.CSS_SELECTOR, '[data-a-target="consent-banner"], [data-a-target="consent-banner-accept"]'),
        dismiss=((By.CSS_SELECTOR, '[data-a-target="consent-banner-accept"]'),),
    ),
)


class TwitchBasePage(BasePage):
    popups = TWITCH_POPUPS
