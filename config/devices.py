"""Device profiles for Chrome mobile emulation.

Single source of truth for every emulated device. Adding a device is a
one-entry change here; tests pick it with ``--device`` or
``@pytest.mark.device("<name>")``.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DeviceProfile:
    name: str
    width: int
    height: int
    pixel_ratio: float
    user_agent: str

    def to_mobile_emulation(self) -> dict:
        """Return the dict ChromeDriver expects for the ``mobileEmulation`` option."""
        return {
            "deviceMetrics": {
                "width": self.width,
                "height": self.height,
                "pixelRatio": self.pixel_ratio,
                "touch": True,
            },
            "userAgent": self.user_agent,
        }


_ANDROID_UA = (
    "Mozilla/5.0 (Linux; Android 14; {model}) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Mobile Safari/537.36"
)
_IOS_UA = (
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
)

DEVICES: dict[str, DeviceProfile] = {
    profile.name: profile
    for profile in (
        DeviceProfile("Pixel 7", 412, 915, 2.625, _ANDROID_UA.format(model="Pixel 7")),
        DeviceProfile("Galaxy S20", 360, 800, 3.0, _ANDROID_UA.format(model="SM-G981B")),
        DeviceProfile("iPhone 14 Pro", 393, 852, 3.0, _IOS_UA),
    )
}

DEFAULT_DEVICE = "Pixel 7"


def get_device(name: str) -> DeviceProfile:
    try:
        return DEVICES[name]
    except KeyError:
        known = ", ".join(sorted(DEVICES))
        raise ValueError(f"Unknown device '{name}'. Known devices: {known}") from None
