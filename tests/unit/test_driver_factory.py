import pytest

from config.settings import Settings
from framework import driver_factory

pytestmark = pytest.mark.unit


class FakeDriver:
    def __init__(self, **kwargs):
        self.kwargs, self.calls = kwargs, []

    def implicitly_wait(self, seconds):
        self.calls.append(("implicitly_wait", seconds))

    def set_page_load_timeout(self, seconds):
        self.calls.append(("page_load_timeout", seconds))


@pytest.fixture
def started(monkeypatch):
    """Record which WebDriver class create_driver() starts, without launching a browser."""
    started = {}

    def fake(kind):
        def _start(**kwargs):
            started[kind] = FakeDriver(**kwargs)
            return started[kind]

        return _start

    monkeypatch.setattr(driver_factory.webdriver, "Chrome", fake("local"))
    monkeypatch.setattr(driver_factory.webdriver, "Remote", fake("remote"))
    monkeypatch.setattr(driver_factory, "_fit_window_to_device", lambda *_: started.setdefault("fitted", True))
    return started


def test_local_chrome_by_default(started):
    driver_factory.create_driver(Settings(headless=True))
    assert set(started) == {"local"}
    assert ("implicitly_wait", 0) in started["local"].calls


def test_remote_url_starts_a_remote_driver_with_the_same_emulation(started):
    driver_factory.create_driver(Settings(remote_url="http://grid:4444/wd/hub"))
    remote = started["remote"]
    assert remote.kwargs["command_executor"] == "http://grid:4444/wd/hub"
    assert "mobileEmulation" in remote.kwargs["options"].experimental_options
    assert "fitted" not in started  # CDP window fitting is local-only


def test_remote_url_resolves_from_cli_over_env(monkeypatch):
    monkeypatch.setenv("SELENIUM_REMOTE_URL", "http://env:4444")
    cli = {"remote_url": "http://cli:4444"}
    assert Settings.load(cli.get).remote_url == "http://cli:4444"
