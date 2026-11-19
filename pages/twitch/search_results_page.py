from __future__ import annotations

import re

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement

from framework import waits
from framework.popup_handler import Locator
from pages.twitch.streamer_page import ContentGateBlocked, StreamerPage
from pages.twitch.twitch_base_page import TwitchBasePage

_CHANNEL_FROM_PREVIEW = re.compile(r"live_user_([^-/]+)-")


class SearchResultsPage(TwitchBasePage):
    path = "/search"

    # Channel cards are <button>s; a live one carries a 'live_user_<channel>' preview image.
    btn_live_channel_cards = (By.XPATH, '//button[.//img[contains(@src, "live_user_")]]')
    img_preview = (By.CSS_SELECTOR, 'img[src*="live_user_"]')
    ready_locator = btn_live_channel_cards

    def select_streamer(self, category: str | None = None, max_attempts: int = 3) -> StreamerPage:
        """Open a live streamer card, skipping channels behind a content gate that cannot be passed.

        Preference order keeps the choice deterministic:
        1. cards visible in the viewport whose text mentions ``category``
        2. other visible live cards
        3. remaining live cards on the page
        """
        candidates = self._candidate_channels(category)[:max_attempts]
        for attempt, channel in enumerate(candidates, 1):
            self.log.info("Selecting streamer '%s' (attempt %d/%d)", channel, attempt, len(candidates))
            self.click(self._card_of(channel))
            try:
                return self.go_to(StreamerPage, channel=channel)
            except ContentGateBlocked as exc:
                self.log.warning("%s; going back to pick another streamer", exc)
                self._back_to_results()
        raise ContentGateBlocked(f"All {len(candidates)} tried streamers are behind a content gate: {candidates}")

    def _candidate_channels(self, category: str | None) -> list[str]:
        cards = self.get_elements(self.btn_live_channel_cards)
        visible = [c for c in cards if self.is_in_viewport(c)]
        matching = [c for c in visible if category and category.lower() in c.text.lower()]
        ordered = matching + [c for c in visible if c not in matching] + [c for c in cards if c not in visible]
        channels = list(dict.fromkeys(self._channel_of(c) for c in ordered))
        self.log.info(
            "Streamer candidates %s (%d cards, %d visible, %d matching '%s')",
            channels,
            len(cards),
            len(visible),
            len(matching),
            category,
        )
        return channels

    def _card_of(self, channel: str) -> Locator:
        return By.XPATH, f'//button[.//img[contains(@src, "live_user_{channel}-")]]'

    def _back_to_results(self) -> None:
        self.driver.back()
        self.wait.until(waits.url_contains(self.path), "back to the search results URL")
        self.wait_until_loaded()

    def _channel_of(self, card: WebElement) -> str:
        src = card.find_element(*self.img_preview).get_attribute("src") or ""
        match = _CHANNEL_FROM_PREVIEW.search(src)
        return match.group(1) if match else "unknown"
