"""Gate handling without a browser: Twitch did not show a real gate on mobile web (see README)."""

import pytest
from selenium.common.exceptions import TimeoutException

from config.settings import Settings
from pages.twitch.search_results_page import SearchResultsPage
from pages.twitch.streamer_page import ContentGateBlocked, StreamerPage
from pages.twitch.twitch_base_page import BTN_START_WATCHING, CONTENT_GATE

pytestmark = pytest.mark.unit


def _streamer_page(monkeypatch, visible: set) -> StreamerPage:
    page = StreamerPage(driver=None, settings=Settings(), channel="gated")
    monkeypatch.setattr(page, "is_visible", lambda locator: locator in visible)
    return page


def test_gate_without_start_watching_blocks_playback(monkeypatch):
    page = _streamer_page(monkeypatch, {CONTENT_GATE})

    def time_out(*_, **__):
        raise TimeoutException

    monkeypatch.setattr(page.wait, "until", time_out)
    assert page._gate_blocks_playback()


@pytest.mark.parametrize("visible", [set(), {CONTENT_GATE, BTN_START_WATCHING}])
def test_no_gate_or_passable_gate_does_not_block(monkeypatch, visible):
    assert not _streamer_page(monkeypatch, visible)._gate_blocks_playback()


class _Results(SearchResultsPage):
    """Search results with scripted candidates; channels in ``gated`` raise ContentGateBlocked on open."""

    def __init__(self, candidates, gated):
        super().__init__(driver=None, settings=Settings())
        self.candidates, self.gated, self.opened, self.backs = candidates, gated, [], 0

    def _candidate_channels(self, category):
        return self.candidates

    def click(self, target):
        pass

    def go_to(self, page_cls, channel, category):
        self.opened.append(channel)
        if channel in self.gated:
            raise ContentGateBlocked(channel)
        return f"page:{channel}"

    def _back_to_results(self):
        self.backs += 1


def test_select_streamer_skips_a_gated_channel():
    page = _Results([("gated", "StarCraft II"), ("open", "StarCraft II")], gated={"gated"})
    assert page.select_streamer(category="StarCraft II") == "page:open"
    assert page.opened == ["gated", "open"] and page.backs == 1


def test_select_streamer_gives_up_after_max_attempts():
    names = ["a", "b", "c", "d"]
    page = _Results([(n, "StarCraft II") for n in names], gated=set(names))
    with pytest.raises(ContentGateBlocked, match=r"All 3 tried streamers"):
        page.select_streamer(category="StarCraft II", max_attempts=3)
    assert page.opened == ["a", "b", "c"]
