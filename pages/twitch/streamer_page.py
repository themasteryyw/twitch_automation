from __future__ import annotations

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

from config.settings import Settings
from framework import waits
from pages.twitch.twitch_base_page import BTN_START_WATCHING, CONTENT_GATE, TwitchBasePage


class ContentGateBlocked(Exception):
    """The channel's content-classification gate offers no way past it.

    A logged-out viewer may get the gate with only "Log In" / "Sign Up" and no
    "Start Watching" button, so the stream cannot be watched without an account.
    """


class StreamerPage(TwitchBasePage):
    video_player = (By.CSS_SELECTOR, '[data-a-target="video-player"]')
    ready_locator = video_player
    start_watching_grace = 3  # s to wait for "Start Watching" after the gate renders

    def __init__(self, driver: WebDriver, settings: Settings, channel: str = "") -> None:
        super().__init__(driver, settings)
        self.channel = channel
        self.path = f"/{channel}" if channel else "/"

    @property
    def ready_timeout(self) -> int:
        """The player mounts as part of video start-up, so it shares the video budget."""
        return self.settings.video_timeout

    def wait_until_loaded(self) -> StreamerPage:
        """'Fully loaded' = channel URL, player mounted, live video playing, on-screen images decoded.

        Pop-ups (e.g. the mature-content gate) can appear *after* the player mounts,
        so they are dismissed on every poll of the video wait.

        Raises ``ContentGateBlocked`` if the gate has no "Start Watching" button.
        """
        if self.channel:
            self.wait.until(waits.url_contains(f"/{self.channel}"), f"URL of channel '{self.channel}'")
        super().wait_until_loaded()

        def _video_ready(driver: WebDriver) -> bool:
            self.dismiss_popups()
            if self._gate_blocks_playback():
                raise ContentGateBlocked(f"Channel '{self.channel}' is behind a content gate with no way past it")
            return waits.video_playing(driver)

        self.wait.until(_video_ready, "live video to start playing", timeout=self.settings.video_timeout)
        self.wait.until(waits.viewport_images_loaded, "on-screen images to finish loading")
        self.log.info("Streamer page for '%s' fully loaded", self.channel)
        return self

    def is_video_playing(self) -> bool:
        return waits.video_playing(self.driver)

    def _gate_blocks_playback(self) -> bool:
        """Gate on screen and its "Start Watching" button does not show up within a short grace period."""
        if not self.is_visible(CONTENT_GATE) or self.is_visible(BTN_START_WATCHING):
            return False
        try:
            self.wait.until(
                lambda d: self.is_visible(BTN_START_WATCHING) or not self.is_visible(CONTENT_GATE),
                "'Start Watching' button on the content gate",
                timeout=self.start_watching_grace,
            )
            return False
        except TimeoutException:
            return True
