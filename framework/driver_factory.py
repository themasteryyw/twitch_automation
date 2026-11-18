"""WebDriver creation. Tests never build drivers themselves."""

from __future__ import annotations

from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions

from config.devices import get_device
from config.settings import Settings
from framework.logger import get_logger

log = get_logger(__name__)


def build_chrome_options(settings: Settings, device_name: str) -> ChromeOptions:
    device = get_device(device_name)
    options = ChromeOptions()
    options.add_experimental_option("mobileEmulation", device.to_mobile_emulation())
    options.add_experimental_option("prefs", {"intl.accept_languages": settings.language})
    # Live video keeps the 'load' event busy; DOM-ready is enough, explicit waits do the rest.
    options.page_load_strategy = "eager"
    options.add_argument(f"--lang={settings.language}")
    options.add_argument("--mute-audio")
    options.add_argument("--autoplay-policy=no-user-gesture-required")
    options.add_argument("--disable-notifications")
    # Window wide enough to host the emulated viewport (+ room for DevTools-free chrome).
    options.add_argument(f"--window-size={device.width + 40},{device.height + 160}")
    if settings.headless:
        options.add_argument("--headless=new")
    options.set_capability("goog:loggingPrefs", {"browser": "ALL"})
    return options


def create_driver(settings: Settings, device_name: str | None = None) -> webdriver.Chrome:
    device_name = device_name or settings.device
    log.info("Starting Chrome (device=%s, headless=%s)", device_name, settings.headless)
    # Selenium Manager (bundled with Selenium >= 4.11) resolves chromedriver automatically.
    driver = webdriver.Chrome(options=build_chrome_options(settings, device_name))
    driver.implicitly_wait(0)  # explicit waits only
    driver.set_page_load_timeout(settings.page_load_timeout)
    return driver
