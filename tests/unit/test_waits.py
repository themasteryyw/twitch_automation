import pytest
from selenium.common.exceptions import TimeoutException

from framework import waits

pytestmark = pytest.mark.unit


class ScriptedDriver:
    """Returns the next scripted value for each execute_script call."""

    def __init__(self, *values, url="https://m.twitch.tv/"):
        self.values, self.current_url = list(values), url

    def execute_script(self, *_):
        return self.values.pop(0) if len(self.values) > 1 else self.values[0]


@pytest.mark.parametrize(("state", "ready"), [("loading", False), ("interactive", True), ("complete", True)])
def test_document_ready_accepts_interactive(state, ready):
    assert waits.document_ready(ScriptedDriver(state)) is ready


def test_scroll_settled_needs_two_equal_positions():
    condition, driver = waits.scroll_settled(), ScriptedDriver(0, 400, 800, 800)
    assert [condition(driver) for _ in range(4)] == [False, False, False, True]


def test_url_contains_is_case_insensitive():
    assert waits.url_contains("/ESL_SC2")(ScriptedDriver(url="https://m.twitch.tv/esl_sc2"))


def test_all_of_requires_every_condition():
    driver = ScriptedDriver()
    assert waits.all_of(lambda d: True, lambda d: 1)(driver)
    assert not waits.all_of(lambda d: True, lambda d: False)(driver)


def test_waiter_returns_the_condition_value():
    assert waits.Waiter(ScriptedDriver(), default_timeout=1).until(lambda d: "el", "element") == "el"


def test_waiter_timeout_names_what_never_happened():
    waiter = waits.Waiter(ScriptedDriver(), default_timeout=1, poll=0.05)
    with pytest.raises(TimeoutException, match=r"Timed out after 0.2s waiting for: live video"):
        waiter.until(lambda d: False, "live video", timeout=0.2)
