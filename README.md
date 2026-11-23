# Twitch WAP Automation

[![CI](https://github.com/themasteryyw/twitch_automation/actions/workflows/ci.yml/badge.svg)](https://github.com/themasteryyw/twitch_automation/actions/workflows/ci.yml)

UI test framework for the Twitch mobile web site (**m.twitch.tv**), built with
**Python + Selenium 4 + pytest + pytest-bdd**, running on **Google Chrome's mobile emulator**.

![Test run](docs/demo.gif)

---

## Scenario

The task's six steps are written in Gherkin in
[`features/search_streamer.feature`](features/search_streamer.feature); step
definitions live in `tests/e2e/test_search_streamer.py` and only call page objects.

```gherkin
Scenario Outline: Search "<game>" and open one of its live streamers
  Given I open Twitch mobile web
  When I tap the search icon
  And I search for "<game>"
  And I scroll down <scrolls> times
  Then the search results include live channels playing "<game>"
  When I select a streamer playing "<game>"
  Then the streamer page is fully loaded on the mobile site
  And the selected streamer is playing "<game>"
  And I take a screenshot of the streamer page

  Examples: Task scenario
    | game         | scrolls |
    | StarCraft II | 2       |

  @extra
  Examples: Extra search case, opt-in with -m extra
    | game              | scrolls |
    | League of Legends | 2       |
```

| # | Task step | Where it lives |
|---|------|----------------|
| 1 | Go to Twitch | `home_page` fixture → `HomePage.open()` |
| 2 | Click the search icon | `HomePage.open_search()` |
| 3 | Input "StarCraft II" | `BrowsePage.search()` |
| 4 | Scroll down 2 times | `SearchResultsPage.scroll_down(times=2)` |
| 5 | Select one streamer | `SearchResultsPage.select_streamer(category=game)` |
| 6 | Wait until everything is loaded, take a screenshot | `StreamerPage.wait_until_loaded()` + `screenshot` fixture |

`StarCraft II` is the task's scenario and the only case in a default run. The
`@extra` table shows that a new search case is one line of data; it runs only
when asked for (`pytest -m extra`, or `-m "extra or not extra"` for everything). A streamer counts as relevant when the
category on its result card equals the searched game (case-insensitive), and
both the result list and the chosen streamer are asserted on that.

Pop-ups that can block the flow ("Open in App" bottom sheet, mature-content
gate, cookie banner) are handled automatically on every page. A mature-content
gate that cannot be passed makes the test pick another streamer.

## Quick start

Requirements: Python and Google Chrome. Verified on macOS with Python 3.15.2,
Chrome 158, Selenium 4.53, pytest 9.2 and pytest-bdd 9.0. ChromeDriver is resolved
automatically by Selenium Manager. The scenario passes on all emulated devices:
Galaxy S20 (default), Pixel 7 and iPhone 14 Pro.

```bash
git clone https://github.com/themasteryyw/twitch_automation.git
cd twitch_automation
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

pytest                                   # unit + the task's e2e scenario
pytest -m extra                          # extra search cases only (League of Legends)
pytest -m unit                           # offline framework tests, < 1 s
pytest -m p0                             # critical path only
pytest --device "iPhone 14 Pro"          # another emulated device
pytest --headless                        # CI mode
pytest -n 2                              # parallel (pytest-xdist)
```

Lint and format (config in `pyproject.toml`):

```bash
ruff check .
ruff format --check .
```

### CI

`.github/workflows/ci.yml` runs on every push to `main`, on pull requests and
nightly (so a Twitch UI change is caught even without a push):

1. **lint-and-unit**: `ruff check`, `ruff format --check` and `pytest -m unit`
   (no browser or network, so a Twitch outage cannot hide a framework regression)
2. **test**: `pytest -m "not unit" --headless` on Ubuntu with Chrome, once per
   emulated device (Galaxy S20, Pixel 7, iPhone 14 Pro) as parallel matrix jobs;
   each job uploads its `artifacts/` (report, logs, screenshots) even when it fails

### Configuration

Every value resolves as **CLI option > environment variable > default**
(`config/settings.py`).

| Setting | CLI | Env var | Default |
|---|---|---|---|
| Site under test | `--base-url` | `TWITCH_BASE_URL` | `https://m.twitch.tv/` |
| Emulated device | `--device` | `DEVICE` | `Galaxy S20` |
| Headless | `--headless` | `HEADLESS` | `false` |
| Explicit-wait timeout (s) | `--timeout` | `TIMEOUT` | `15` |
| Video start timeout (s) | – | `VIDEO_TIMEOUT` | `45` |
| Remote WebDriver hub | `--remote-url` | `SELENIUM_REMOTE_URL` | empty (local Chrome) |

A single test can pin a device with `@pytest.mark.device("Galaxy S20")`.

`--remote-url` sends the same Chrome options (including mobile emulation) to a
Selenium Grid or cloud hub instead of starting Chrome locally, so the suite can
scale beyond one machine without code changes:

```bash
pytest --headless --remote-url http://localhost:4444/wd/hub -n 4
```

Headed runs open Chrome as an app-style window (no tab strip or address bar) sized
to the emulated phone, because a normal Chrome window on macOS cannot be narrower
than 500pt and would show a grey strip beside the 360pt viewport.

### Artifacts

Written to `artifacts/` (git-ignored):

- `screenshots/` – step screenshots and `FAILED_*` screenshots
- `logs/run_<timestamp>_<worker>.log` – full DEBUG log per run
- `report.html` – self-contained pytest-html report; failures (in fixture
  setup or in the test body) embed the screenshot, URL and the last 20 browser
  console entries, and the exception is written to the run log

## Project structure

```
twitch_automation/
├── config/
│   ├── settings.py        # immutable Settings: CLI > env > default
│   └── devices.py         # device registry for Chrome mobileEmulation
├── framework/             # site-agnostic core, reusable for any web app
│   ├── driver_factory.py  # local or remote Chrome + mobile emulation, eager load
│   ├── base_page.py       # BasePage: "loaded" contract, element helpers, go_to()
│   ├── waits.py           # Waiter + named JS conditions (no sleeps)
│   ├── popup_handler.py   # data-driven pop-up table + handler
│   ├── screenshot.py      # named, timestamped, xdist-safe screenshots
│   └── logger.py          # per-run log file + console
├── pages/
│   └── twitch/            # Twitch page objects (locators + actions only)
│       ├── twitch_base_page.py   # registers Twitch pop-ups
│       ├── home_page.py          # home -> tap the search (Browse) icon
│       ├── browse_page.py        # type the search term
│       ├── search_results_page.py  # scroll, pick a streamer (skips gated channels)
│       └── streamer_page.py      # wait until the live video time is advancing
├── features/
│   └── search_streamer.feature  # the 6-step scenario in Gherkin (test data in Examples)
├── tests/
│   ├── conftest.py        # fixtures: driver -> pages, screenshot factory
│   ├── e2e/
│   │   └── test_search_streamer.py  # pytest-bdd step definitions
│   └── unit/              # offline tests: card parsing, settings, devices, pop-ups, waits, gate, driver
├── .github/workflows/ci.yml  # lint + unit, then headless e2e per device; push / PR / nightly
├── conftest.py            # CLI options, settings, logging, failure artifacts
├── pytest.ini             # markers (p0 / p1 / wap / unit / extra), feature dir, live log format
├── pyproject.toml         # ruff lint/format config
├── requirements.txt
├── docs/                  # demo GIF for this README
└── artifacts/             # run output (git-ignored): screenshots/, logs/, report.html
```

Layering: the feature file describes *what* the scenario does, page objects describe *how*
to act on each page, and `framework/` owns waiting, pop-ups, the driver and
reporting. A change in one layer does not ripple into the others.

## Observations on the live site

Verified on m.twitch.tv with Chrome mobile emulation:

- **Search icon.** The current mobile home page has no search icon in the top
  bar; the magnifier icon lives in the bottom navigation ("Browse"), which
  opens `/directory` with the search box. Step 2 clicks that icon.
- **Scroll down 2 times.** On the default "Top" results tab the page is only
  slightly taller than the viewport, so the first scroll already reaches the
  bottom. Both scrolls are still performed as the scenario requires;
  `scroll_down()` logs the before/after position and a WARNING when a scroll
  cannot move, so this is visible in the run log.
- **Mature-content gate not seen on m.twitch.tv** (checked on GTA V and other
  mature categories). The handling is defensive and not verified against a
  real gate on mobile web. Locators follow FrankerFaceZ
  (`content-classification-gate-overlay-start-watching-button`); a logged-out
  viewer may get only "Log In" / "Sign Up", so gated channels are skipped. The
  skip path is covered by `tests/unit/test_content_gate.py`.
