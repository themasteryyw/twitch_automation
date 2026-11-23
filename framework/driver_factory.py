"""WebDriver creation. Tests never build drivers themselves."""

from __future__ import annotations

from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.remote.webdriver import WebDriver

from config.devices import DeviceProfile, get_device
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
    if settings.headless:
        options.add_argument("--headless=new")
        options.add_argument(f"--window-size={device.width + 40},{device.height + 160}")
    else:
        # An app-style window has no tab strip or address bar, so it can shrink to the phone's
        # width; a normal Chrome window on macOS stops at 500pt and shows a grey strip beside it.
        # Final size is set in create_driver() once the window frame has been measured.
        options.add_argument("--app=data:,")
        options.add_argument(f"--window-size={device.width},{device.height}")
    options.set_capability("goog:loggingPrefs", {"browser": "ALL"})
    return options


def create_driver(settings: Settings, device_name: str | None = None) -> WebDriver:
    device_name = device_name or settings.device
    options = build_chrome_options(settings, device_name)
    if settings.remote_url:
        log.info("Starting remote Chrome at %s (device=%s)", settings.remote_url, device_name)
        driver: WebDriver = webdriver.Remote(command_executor=settings.remote_url, options=options)
    else:
        log.info("Starting Chrome (device=%s, headless=%s)", device_name, settings.headless)
        # Selenium Manager (bundled with Selenium >= 4.11) resolves chromedriver automatically.
        driver = webdriver.Chrome(options=options)
    driver.implicitly_wait(0)  # explicit waits only
    driver.set_page_load_timeout(settings.page_load_timeout)
    # Window fitting uses CDP, which only a local ChromeDriver exposes; remote nodes own their display.
    if not settings.headless and not settings.remote_url:
        _fit_window_to_device(driver, get_device(device_name))
    return driver


def _fit_window_to_device(driver: webdriver.Chrome, device: DeviceProfile) -> None:
    """Size the window so its content area equals the emulated viewport.

    The frame (title bar, automation info bar) differs per OS and Chrome version, so it is
    measured: drop the device override, compare window and content size, then restore it.
    """
    driver.execute_cdp_cmd("Emulation.clearDeviceMetricsOverride", {})
    inner_width, inner_height = driver.execute_script("return [window.innerWidth, window.innerHeight]")
    driver.execute_cdp_cmd(
        "Emulation.setDeviceMetricsOverride",
        {
            "width": device.width,
            "height": device.height,
            "deviceScaleFactor": device.pixel_ratio,
            "mobile": True,
        },
    )
    window = driver.get_window_size()
    frame_width, frame_height = window["width"] - inner_width, window["height"] - inner_height
    driver.set_window_size(device.width + frame_width, device.height + frame_height)
    log.info("Window fitted to %dx%d viewport (frame %dx%d)", device.width, device.height, frame_width, frame_height)
