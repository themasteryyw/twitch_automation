"""WAP scenario: search StarCraft II on Twitch mobile web and open a live streamer."""

from __future__ import annotations

import pytest

from framework import waits


@pytest.mark.p0
@pytest.mark.wap
def test_search_starcraft_and_open_streamer(driver, home_page, settings, screenshot):
    # 1. Go to Twitch                       -> home_page fixture (opened + pop-ups dismissed)
    # 2. Click the search icon
    browse = home_page.open_search()

    # 3. Input "StarCraft II"
    results = browse.search(settings.search_term)

    # 4. Scroll down 2 times
    results.scroll_down(times=settings.scroll_times)

    # 5. Select one streamer
    streamer = results.select_streamer(category=settings.search_term)

    # 6. Wait until everything is loaded (done by the page object), then take a screenshot
    path = screenshot(f"streamer_{streamer.channel}")

    assert "m.twitch.tv" in driver.current_url, "Must stay on the mobile (WAP) site"
    assert streamer.is_video_playing(), "Live video should be playing"
    assert waits.viewport_images_loaded(driver), "On-screen images should be loaded"
    assert path.exists() and path.stat().st_size > 0, f"Screenshot not written: {path}"
