from __future__ import annotations

from selenium.webdriver.common.by import By

from framework import waits
from pages.twitch.search_results_page import SearchResultsPage
from pages.twitch.twitch_base_page import TwitchBasePage


class BrowsePage(TwitchBasePage):
    path = "/directory"

    input_search = (By.CSS_SELECTOR, 'input[type="search"]')
    ready_locator = input_search

    def search(self, term: str) -> SearchResultsPage:
        self.type_text(self.input_search, term, submit=True)
        self.wait.until(waits.url_contains("/search"), "search results URL")
        return self.go_to(SearchResultsPage)
