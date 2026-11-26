"""Twitch-specific base page: registers the pop-ups Twitch can show on any page."""

from __future__ import annotations

from selenium.webdriver.common.by import By

from framework.base_page import BasePage
from framework.popup_handler import Popup

CONTENT_GATE = (By.CSS_SELECTOR, '[data-a-target*="content-classification-gate"]')
BTN_START_WATCHING = (By.CSS_SELECTOR, '[data-a-target*="start-watching-button"]')

TWITCH_POPUPS: tuple[Popup, ...] = (
    Popup(
        name="Open in App bottom sheet",
        detect=(By.CSS_SELECTOR, '[role="dialog"][aria-label*="Open in App"]'),
        dismiss=((By.XPATH, '//button[.//p[normalize-space()="Keep using web"]]'),),
    ),
    # Upsell sheets ("Get the Twitch app", "Create an account ...") are A/B variants with
    # no aria-label; the stable hook is their "Continue watching" button.
    Popup(
        name="Upsell bottom sheet",
        detect=(By.XPATH, '//*[@role="dialog"][.//button[normalize-space()="Continue watching"]]'),
        dismiss=(
            (By.XPATH, '//*[@role="dialog"]//button[normalize-space()="Continue watching"]'),
            (By.XPATH, '//*[@role="dialog"]//button[@aria-label="Activate to close dialog"]'),
        ),
    ),
    Popup(
        name="Mature content gate",
        detect=CONTENT_GATE,
        dismiss=(
            BTN_START_WATCHING,
            (By.XPATH, '//button[.//*[normalize-space()="Start Watching"]]'),
        ),
    ),
    Popup(
        name="Cookie consent banner",
        detect=(By.CSS_SELECTOR, '[data-a-target="consent-banner"], [data-a-target="consent-banner-accept"]'),
        dismiss=(
            (By.CSS_SELECTOR, '[data-a-target="consent-banner-accept"]'),
            # GDPR-region variant (seen from CI runners): the only accept control is "Proceed".
            (
                By.XPATH,
                '//*[@data-a-target="consent-banner"]//*[self::button or self::a or @role="button"]'
                '[normalize-space()="Proceed"]',
            ),
        ),
    ),
)


class TwitchBasePage(BasePage):
    popups = TWITCH_POPUPS
