import pytest

from pages.twitch.search_results_page import category_from_card_text, channel_from_preview

pytestmark = pytest.mark.unit

# Card texts captured from m.twitch.tv search results on 2026-11-20.
LIVE_FIRST = "LIVE\nESL_SC2\nStarCraft II\n36 viewers\nRERUN: Maru vs. herO - ESL SC2 Masters"
LIVE_LAST = "Wintergaming\nChivalry 2\n387 viewers\nLIVE"


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        (LIVE_FIRST, "StarCraft II"),
        (LIVE_LAST, "Chivalry 2"),
        ("iopg\nStarCraft\n1 viewer\nLIVE", "StarCraft"),
        ("Streamer\nJust Chatting\n12.5K viewers", "Just Chatting"),
        ("  Streamer \n\n  Dota 2  \n 1,204 viewers ", "Dota 2"),
    ],
)
def test_category_is_the_line_before_viewer_count(text, expected):
    assert category_from_card_text(text) == expected


@pytest.mark.parametrize("text", ["", "LIVE\nchannel only", "1 viewer\nLIVE"])
def test_category_is_none_without_a_preceding_line(text):
    assert category_from_card_text(text) is None


def test_title_mentioning_viewers_is_not_mistaken_for_the_count():
    assert category_from_card_text("Chan\nFortnite\n5 viewers\nThanks 100 viewers!") == "Fortnite"


@pytest.mark.parametrize(
    ("src", "expected"),
    [
        ("https://static-cdn.jtvnw.net/previews-ttv/live_user_esl_sc2-440x248.jpg", "esl_sc2"),
        ("https://static-cdn.jtvnw.net/previews-ttv/live_user_morelowko-{width}x{height}.jpg", "morelowko"),
        ("https://static-cdn.jtvnw.net/ttv-boxart/123.jpg", "unknown"),
        ("", "unknown"),
    ],
)
def test_channel_from_preview_url(src, expected):
    assert channel_from_preview(src) == expected
