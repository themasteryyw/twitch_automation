"""Root conftest: CLI options, session settings, logging and failure artifacts."""

from __future__ import annotations

import base64
import json

import pytest

from config.devices import DEVICES
from config.settings import Settings
from framework.logger import get_logger, setup_file_logging

log = get_logger(__name__)
SETTINGS_KEY = pytest.StashKey[Settings]()


def pytest_addoption(parser: pytest.Parser) -> None:
    group = parser.getgroup("twitch", "Twitch WAP automation")
    group.addoption("--base-url", action="store", default=None, help="Site under test (default https://m.twitch.tv/)")
    group.addoption("--device", action="store", default=None, choices=sorted(DEVICES), help="Emulated device")
    group.addoption("--headless", action="store_true", default=None, help="Run Chrome headless")
    group.addoption("--timeout", action="store", default=None, help="Default explicit wait timeout (s)")


@pytest.hookimpl(tryfirst=True)
def pytest_configure(config: pytest.Config) -> None:
    settings = Settings.load(config.getoption)
    config.stash[SETTINGS_KEY] = settings
    # HTML report is optional: enable it only when pytest-html is installed and
    # the user did not pass their own --html path.
    if config.pluginmanager.hasplugin("html") and not getattr(config.option, "htmlpath", None):
        config.option.htmlpath = str(settings.artifacts_dir / "report.html")
        config.option.self_contained_html = True
    log_file = setup_file_logging(settings.logs_dir)
    log.info("Settings: %s", settings)
    log.info("Log file: %s", log_file)
    config.addinivalue_line("markers", "device(name): run this test on a specific emulated device")


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    """Keep the default run to the task's scenario: 'extra' cases run only when -m asks for them."""
    if "extra" in (config.getoption("markexpr") or ""):
        return
    extra = [item for item in items if item.get_closest_marker("extra")]
    if extra:
        items[:] = [item for item in items if item not in extra]
        config.hook.pytest_deselected(items=extra)


@pytest.fixture(scope="session")
def settings(pytestconfig: pytest.Config) -> Settings:
    return pytestconfig.stash[SETTINGS_KEY]


# Expose each phase's report on the item so fixtures can react to failures.
@pytest.hookimpl(hookwrapper=True, tryfirst=True)
def pytest_runtest_makereport(item: pytest.Item, call: pytest.CallInfo):
    outcome = yield
    report = outcome.get_result()
    setattr(item, f"rep_{report.when}", report)

    driver = getattr(item, "_driver", None)
    if report.when in ("setup", "call") and report.failed:
        if call.excinfo is not None:
            log.error("%s failed in %s: %s", item.name, report.when, call.excinfo.exconly().splitlines()[0])
        if driver is not None:
            _attach_failure_artifacts(item, report, driver)


def _attach_failure_artifacts(item: pytest.Item, report: pytest.TestReport, driver) -> None:
    from framework.screenshot import take_screenshot

    settings: Settings = item.config.stash[SETTINGS_KEY]
    extras = getattr(report, "extras", [])
    try:
        path = take_screenshot(driver, settings.screenshots_dir, f"FAILED_{report.when}_{item.name}")
        log.error("Test failed at %s - screenshot: %s", driver.current_url, path)
        html = _pytest_html(item)
        if html:
            extras.append(html.extras.png(base64.b64encode(path.read_bytes()).decode(), "Failure screenshot"))
            extras.append(html.extras.url(driver.current_url, "Failure URL"))
            console = driver.get_log("browser")[-20:]
            if console:
                extras.append(html.extras.text(json.dumps(console, indent=2), "Browser console (last 20)"))
    except Exception as exc:  # artifacts must never hide the real failure
        log.warning("Could not collect failure artifacts: %s", exc)
    report.extras = extras


def _pytest_html(item: pytest.Item):
    """Return the pytest_html module if the plugin is active, else None (report extras are optional)."""
    if not item.config.pluginmanager.hasplugin("html"):
        return None
    try:
        import pytest_html
    except ImportError:
        return None
    return pytest_html
