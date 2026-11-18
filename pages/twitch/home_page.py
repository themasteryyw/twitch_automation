from __future__ import annotations

from selenium.webdriver.common.by import By

from pages.twitch.browse_page import BrowsePage
from pages.twitch.twitch_base_page import TwitchBasePage


class HomePage(TwitchBasePage):
    path = "/"

    # On m.twitch.tv the search (magnifier) icon lives in the bottom nav as "Browse".
    btn_search_icon = (By.XPATH, '//a[@href="/directory"][.//*[normalize-space()="Browse"]]')
    ready_locator = btn_search_icon

    def open_search(self) -> BrowsePage:
        self.log.info("Clicking the search icon")
        self.click_to_navigate(self.btn_search_icon, BrowsePage.path)
        return self.go_to(BrowsePage)
