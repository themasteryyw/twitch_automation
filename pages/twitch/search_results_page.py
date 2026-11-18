from __future__ import annotations

import re

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement

from pages.twitch.streamer_page import StreamerPage
from pages.twitch.twitch_base_page import TwitchBasePage

_CHANNEL_FROM_PREVIEW = re.compile(r"live_user_([^-/]+)-")


class SearchResultsPage(TwitchBasePage):
    path = "/search"

    # Channel cards are <button>s; a live one carries a 'live_user_<channel>' preview image.
    btn_live_channel_cards = (By.XPATH, '//button[.//img[contains(@src, "live_user_")]]')
    img_preview = (By.CSS_SELECTOR, 'img[src*="live_user_"]')
    ready_locator = btn_live_channel_cards

    def select_streamer(self, category: str | None = None) -> StreamerPage:
        """Open a live streamer card.

        Preference order keeps the choice deterministic:
        1. first card visible in the viewport whose text mentions ``category``
        2. first visible live card
        3. first live card on the page (scrolled into view)
        """
        cards = self.get_elements(self.btn_live_channel_cards)
        visible = [c for c in cards if self.is_in_viewport(c)]
        matching = [c for c in visible if category and category.lower() in c.text.lower()]
        card = (matching or visible or cards)[0]

        channel = self._channel_of(card)
        self.log.info("Selecting streamer '%s' (%d cards, %d visible, %d matching '%s')",
                      channel, len(cards), len(visible), len(matching), category)
        self.click(card)
        return self.go_to(StreamerPage, channel=channel)

    def _channel_of(self, card: WebElement) -> str:
        src = card.find_element(*self.img_preview).get_attribute("src") or ""
        match = _CHANNEL_FROM_PREVIEW.search(src)
        return match.group(1) if match else "unknown"
