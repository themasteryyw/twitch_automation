from __future__ import annotations

import re

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement

from framework import waits
from framework.popup_handler import Locator
from pages.twitch.streamer_page import ContentGateBlocked, StreamerPage
from pages.twitch.twitch_base_page import TwitchBasePage

_CHANNEL_FROM_PREVIEW = re.compile(r"live_user_([^-/]+)-")
_VIEWERS_LINE = re.compile(r"^[\d.,]+[KM]?\s+viewers?$", re.IGNORECASE)


def channel_from_preview(src: str) -> str:
    """'.../live_user_esl_sc2-440x248.jpg' -> 'esl_sc2'."""
    match = _CHANNEL_FROM_PREVIEW.search(src)
    return match.group(1) if match else "unknown"


def category_from_card_text(text: str) -> str | None:
    """A channel card reads '[LIVE] <channel> <category> <N viewers> ...'; the category is the line before viewers."""
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    for i, line in enumerate(lines):
        if _VIEWERS_LINE.match(line):
            return lines[i - 1] if i > 0 else None
    return None


class SearchResultsPage(TwitchBasePage):
    path = "/search"

    # Channel cards are <button>s; a live one carries a 'live_user_<channel>' preview image.
    btn_live_channel_cards = (By.XPATH, '//button[.//img[contains(@src, "live_user_")]]')
    img_preview = (By.CSS_SELECTOR, 'img[src*="live_user_"]')
    ready_locator = btn_live_channel_cards

    def select_streamer(self, category: str | None = None, max_attempts: int = 3) -> StreamerPage:
        """Open a live streamer card, skipping channels behind a content gate that cannot be passed.

        Preference order keeps the choice deterministic:
        1. visible cards whose category equals ``category``
        2. other cards whose category equals ``category``
        3. other visible live cards
        4. remaining live cards on the page
        """
        candidates = self._candidate_channels(category)[:max_attempts]
        for attempt, (channel, card_category) in enumerate(candidates, 1):
            self.log.info(
                "Selecting streamer '%s' [%s] (attempt %d/%d)", channel, card_category, attempt, len(candidates)
            )
            self.click(self._card_of(channel))
            try:
                return self.go_to(StreamerPage, channel=channel, category=card_category)
            except ContentGateBlocked as exc:
                self.log.warning("%s; going back to pick another streamer", exc)
                self._back_to_results()
        names = [channel for channel, _ in candidates]
        raise ContentGateBlocked(f"All {len(candidates)} tried streamers are behind a content gate: {names}")

    def live_card_categories(self) -> list[str | None]:
        return [category_from_card_text(card.text) for card in self.get_elements(self.btn_live_channel_cards)]

    def _candidate_channels(self, category: str | None) -> list[tuple[str, str | None]]:
        cards = [
            (self._channel_of(c), category_from_card_text(c.text), self.is_in_viewport(c))
            for c in self.get_elements(self.btn_live_channel_cards)
        ]
        wanted = (category or "").casefold()

        def rank(card: tuple[str, str | None, bool]) -> int:
            _, card_category, visible = card
            matches = bool(wanted) and (card_category or "").casefold() == wanted
            return (0 if matches else 2) + (0 if visible else 1)

        ordered = sorted(cards, key=rank)  # stable: keeps page order within a rank
        candidates = list(dict.fromkeys((channel, card_category) for channel, card_category, _ in ordered))
        self.log.info(
            "Streamer candidates %s (%d cards, %d matching '%s')",
            candidates,
            len(cards),
            sum(rank(c) < 2 for c in cards),
            category,
        )
        return candidates

    def _card_of(self, channel: str) -> Locator:
        return By.XPATH, f'//button[.//img[contains(@src, "live_user_{channel}-")]]'

    def _back_to_results(self) -> None:
        self.driver.back()
        self.wait.until(waits.url_contains(self.path), "back to the search results URL")
        self.wait_until_loaded()

    def _channel_of(self, card: WebElement) -> str:
        return channel_from_preview(card.find_element(*self.img_preview).get_attribute("src") or "")
