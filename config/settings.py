"""Run-time settings.

Resolution order for every value: CLI option > environment variable > default.
Settings are built once per session and are immutable afterwards.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, fields
from pathlib import Path
from typing import Any, Callable

from config.devices import DEFAULT_DEVICE, get_device

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _to_bool(value: str | bool) -> bool:
    if isinstance(value, bool):
        return value
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    base_url: str = "https://m.twitch.tv/"
    device: str = DEFAULT_DEVICE
    headless: bool = False
    language: str = "en-US"
    timeout: int = 15            # default explicit-wait timeout (s)
    page_load_timeout: int = 30  # driver page-load timeout (s)
    video_timeout: int = 45      # max wait for the live video to start (s)
    search_term: str = "StarCraft II"
    scroll_times: int = 2
    artifacts_dir: Path = PROJECT_ROOT / "artifacts"

    # name -> (env var, CLI option dest, caster)
    _SOURCES = {
        "base_url": ("TWITCH_BASE_URL", "base_url", str),
        "device": ("DEVICE", "device", str),
        "headless": ("HEADLESS", "headless", _to_bool),
        "language": ("BROWSER_LANG", None, str),
        "timeout": ("TIMEOUT", "timeout", int),
        "page_load_timeout": ("PAGE_LOAD_TIMEOUT", None, int),
        "video_timeout": ("VIDEO_TIMEOUT", None, int),
        "search_term": ("SEARCH_TERM", None, str),
        "scroll_times": ("SCROLL_TIMES", None, int),
        "artifacts_dir": ("ARTIFACTS_DIR", None, Path),
    }

    @classmethod
    def load(cls, cli_getter: Callable[[str], Any] | None = None) -> "Settings":
        values: dict[str, Any] = {}
        for f in fields(cls):
            env_name, cli_dest, cast = cls._SOURCES[f.name]
            cli_value = cli_getter(cli_dest) if (cli_getter and cli_dest) else None
            if cli_value not in (None, ""):
                values[f.name] = cast(cli_value)
            elif os.getenv(env_name) not in (None, ""):
                values[f.name] = cast(os.environ[env_name])
        settings = cls(**values)
        get_device(settings.device)  # fail fast on an unknown device
        return settings

    @property
    def screenshots_dir(self) -> Path:
        return self.artifacts_dir / "screenshots"

    @property
    def logs_dir(self) -> Path:
        return self.artifacts_dir / "logs"
