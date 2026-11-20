import pytest

from config.devices import DEFAULT_DEVICE, DEVICES, get_device
from config.settings import Settings

pytestmark = pytest.mark.unit

ENV_VARS = ("TWITCH_BASE_URL", "DEVICE", "HEADLESS", "TIMEOUT", "VIDEO_TIMEOUT", "ARTIFACTS_DIR")


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    for name in ENV_VARS:
        monkeypatch.delenv(name, raising=False)


def cli(**options):
    return lambda dest: options.get(dest)


def test_defaults_without_cli_or_env():
    s = Settings.load()
    assert (s.base_url, s.device, s.headless, s.timeout) == ("https://m.twitch.tv/", DEFAULT_DEVICE, False, 15)


def test_env_overrides_default_and_is_cast(monkeypatch):
    monkeypatch.setenv("TIMEOUT", "30")
    monkeypatch.setenv("HEADLESS", "yes")
    s = Settings.load()
    assert s.timeout == 30 and s.headless is True


def test_cli_overrides_env(monkeypatch):
    monkeypatch.setenv("DEVICE", "Pixel 7")
    assert Settings.load(cli(device="iPhone 14 Pro")).device == "iPhone 14 Pro"


def test_empty_cli_value_falls_back_to_env(monkeypatch):
    monkeypatch.setenv("TIMEOUT", "20")
    assert Settings.load(cli(timeout="")).timeout == 20


@pytest.mark.parametrize(("raw", "expected"), [("1", True), ("TRUE", True), ("on", True), ("0", False), ("no", False)])
def test_headless_env_parsing(monkeypatch, raw, expected):
    monkeypatch.setenv("HEADLESS", raw)
    assert Settings.load().headless is expected


def test_unknown_device_fails_fast(monkeypatch):
    monkeypatch.setenv("DEVICE", "Nokia 3310")
    with pytest.raises(ValueError, match="Unknown device 'Nokia 3310'"):
        Settings.load()


def test_artifact_subdirectories(tmp_path, monkeypatch):
    monkeypatch.setenv("ARTIFACTS_DIR", str(tmp_path))
    s = Settings.load()
    assert s.screenshots_dir == tmp_path / "screenshots" and s.logs_dir == tmp_path / "logs"


def test_settings_are_immutable():
    with pytest.raises(AttributeError):
        Settings.load().timeout = 1


def test_default_device_is_registered():
    assert DEFAULT_DEVICE in DEVICES


@pytest.mark.parametrize("name", sorted(DEVICES))
def test_every_device_emulates_a_touch_mobile_browser(name):
    emulation = get_device(name).to_mobile_emulation()
    assert emulation["deviceMetrics"]["touch"] is True
    assert emulation["deviceMetrics"]["width"] <= 600, "phone-sized viewport expected"
    assert "Mobile" in emulation["userAgent"]


def test_get_device_error_lists_known_devices():
    with pytest.raises(ValueError) as exc:
        get_device("nope")
    assert all(name in str(exc.value) for name in DEVICES)
