"""Step definitions for features/search_streamer.feature (the 6-step WAP scenario from the task)."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from pytest_bdd import given, parsers, scenarios, then, when
from selenium.webdriver.remote.webdriver import WebDriver

from pages.twitch import BrowsePage, HomePage, SearchResultsPage, StreamerPage

scenarios("search_streamer.feature")


@given("I open Twitch mobile web")
def open_twitch(home_page: HomePage) -> HomePage:
    return home_page  # the fixture opens the site and dismisses pop-ups


@when("I tap the search icon", target_fixture="browse_page")
def tap_search_icon(home_page: HomePage) -> BrowsePage:
    return home_page.open_search()


@when(parsers.parse('I search for "{game}"'), target_fixture="results_page")
def search_for(browse_page: BrowsePage, game: str) -> SearchResultsPage:
    return browse_page.search(game)


@when(parsers.parse("I scroll down {scrolls:d} times"))
def scroll_down(results_page: SearchResultsPage, scrolls: int) -> None:
    results_page.scroll_down(times=scrolls)


@then(parsers.parse('the search results include live channels playing "{game}"'))
def results_include_game(results_page: SearchResultsPage, game: str) -> None:
    categories = results_page.live_card_categories()
    assert any((c or "").casefold() == game.casefold() for c in categories), (
        f"No live channel in '{game}' among the results; card categories: {categories}"
    )


@when(parsers.parse('I select a streamer playing "{game}"'), target_fixture="streamer_page")
def select_streamer(results_page: SearchResultsPage, game: str) -> StreamerPage:
    return results_page.select_streamer(category=game)  # returns once the page is fully loaded


@then("the streamer page is fully loaded on the mobile site")
def streamer_page_loaded(driver: WebDriver, streamer_page: StreamerPage) -> None:
    assert "m.twitch.tv" in driver.current_url, "Must stay on the mobile (WAP) site"
    assert f"/{streamer_page.channel}" in driver.current_url.lower(), f"Not on channel '{streamer_page.channel}'"
    assert streamer_page.is_video_playing(), "Live video should be playing"
    streamer_page.wait_for_viewport_images()


@then(parsers.parse('the selected streamer is playing "{game}"'))
def streamer_plays_game(streamer_page: StreamerPage, game: str) -> None:
    assert (streamer_page.category or "").casefold() == game.casefold(), (
        f"Selected '{streamer_page.channel}' is in '{streamer_page.category}', expected '{game}'"
    )


@then("I take a screenshot of the streamer page")
def take_streamer_screenshot(streamer_page: StreamerPage, screenshot: Callable[[str], Path]) -> None:
    path = screenshot(f"streamer_{streamer_page.channel}")
    assert path.exists() and path.stat().st_size > 0, f"Screenshot not written: {path}"
