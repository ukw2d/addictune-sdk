<div align="center">

# 📻 addictune-sdk

**Async Python SDK for the AudioAddict radio platform**

DI.FM · RadioTunes · RockRadio · JazzRadio · ClassicalRadio · ZenRadio

[![PyPI version](https://img.shields.io/pypi/v/addictune-sdk?label=PyPI&color=blue)](https://pypi.org/project/addictune-sdk/)
[![Python](https://img.shields.io/pypi/pyversions/addictune-sdk?label=Python&logo=python&logoColor=white)](https://pypi.org/project/addictune-sdk/)
[![License](https://img.shields.io/pypi/l/addictune-sdk?label=License&color=green)](https://github.com/ukw2d/addictune-sdk/blob/main/LICENSE)
[![CI](https://img.shields.io/github/actions/workflow/status/ukw2d/addictune-sdk/ci.yml?label=CI&logo=github)](https://github.com/ukw2d/addictune-sdk/actions)

</div>

---

## Features

- **Fully async** — built on `httpx` with `async/await` throughout
- **6 networks** — DI.FM, RadioTunes, RockRadio, JazzRadio, ClassicalRadio, ZenRadio out of the box
- **Typed models** — Pydantic v2 models for every API response, with IDE autocomplete and validation
- **ETag caching** — automatic HTTP `If-None-Match` / `304` handling backed by SQLite
- **Auto-pagination** — `async for` iterators that transparently walk pages
- **Resilient transport** — retry with exponential backoff + jitter, circuit breaker
- **Auth helpers** — session and direct login, `SecretStr`-guarded internal storage
- **Minimal dependencies** — only `httpx` and `pydantic`
- **Zero-config** — sensible defaults, override via constructor, JSON file, or auto-discovery

### API coverage

| Domain       | What you can do                                                                  |
|--------------|----------------------------------------------------------------------------------|
| **Auth**     | Login (session or direct), retrieve API key + listen key                         |
| **Channels** | Browse all channels, get by ID, track history, now playing, stream URLs, favorites |
| **Tracks**   | Get by ID, liked tracks, vote up/down/delete, skip events, audio quality prefs   |
| **Playlists**| Featured playlists, browse by popularity/newest, get tracks, follow, listen history |
| **Mix Shows**| Browse shows, iterate episodes, upcoming events, followed shows                  |
| **User**     | Ping API, check premium status, payment methods                                  |

---

## Installation

=== "pip"

    ```bash
    pip install addictune-sdk
    ```

=== "uv"

    ```bash
    uv add addictune-sdk
    ```

=== "poetry"

    ```bash
    poetry add addictune-sdk
    ```

=== "pipx" *(for scripts)*

    ```bash
    pipx inject my-tool addictune-sdk
    ```

Requires **Python 3.12+**.

---

## Quick start

```python
import asyncio
from addictune_sdk import Client

async def main():
    async with Client() as client:
        di = client.network("di")
        channels = await di.channels.get_all()
        for ch in channels:
            print(ch.name)

asyncio.run(main())
```

---

## Authentication

```python
from addictune_sdk import Client

async with Client() as client:
    auth = await client.login("you@example.com", "your-password")
    print(f"Logged in as user {auth.user_id}")
```

Or pass a pre-existing session key:

```python
async with Client(session_key="your-session-key") as client:
    ...
```

---

## Network-scoped APIs

Every network is accessed via `client.network(slug)` and exposes namespaced APIs:

```python
di = client.network("di")
```

### Channels

```python
# List all channels
channels = await di.channels.get_all()

# Single channel by ID
channel = await di.channels.get_by_id(123)

# What's playing right now across all channels
now = await di.channels.get_currently_playing()

# Build a direct stream URL
url = di.channels.get_stream_url("trance", "your-listen-key", quality="hi")

# Favorites
await di.channels.add_favorite(user_id, channel_id)
favs = await di.channels.get_favorites(user_id)
```

### Tracks

```python
# Fetch a track
track = await di.tracks.get_by_id(12345)

# Like / unlike
await di.tracks.vote(12345, direction="up")
await di.tracks.vote(12345, direction="delete")

# Iterate all liked tracks (auto-paginated)
async for track in di.tracks.iter_liked_tracks(user_id):
    print(track.title)

# Audio quality
qualities = await di.tracks.get_qualities()
await di.tracks.set_preferred_quality(user_id, quality_id=3)
```

### Playlists

```python
# Featured playlists
featured = await di.playlists.get_featured()

# Browse with auto-pagination
async for pl in di.playlists.iter_playlists(order_by="newest"):
    print(pl.name)

# Get playable tracks for a playlist
content = await di.playlists.get_content(playlist_id)

# Followed playlists
async for pl in di.playlists.iter_followed(user_id):
    print(pl.name)
```

### Mix Shows

```python
# Browse shows (auto-paginated)
async for show in di.mixshows.iter_shows(active=True):
    print(show.name)

# Episodes for a specific show
async for ep in di.mixshows.iter_episodes(show_id):
    print(ep.name)

# Upcoming events
upcoming = await di.mixshows.get_upcoming(limit=10)
```

### User

```python
# Health check
ping = await client.user.ping()
print(f"API v{ping.api_version} — {ping.country}")

# Premium status for a network
status = await client.user.check_premium_status("di")
print(status.listener_type, status.skips_remaining)
```

---

## Built-in networks

| Slug              | Name            |
|-------------------|-----------------|
| `di`              | DI.FM           |
| `radiotunes`      | RadioTunes      |
| `rockradio`       | RockRadio       |
| `jazzradio`       | JazzRadio       |
| `classicalradio`  | ClassicalRadio  |
| `zenradio`        | ZenRadio        |

Add custom networks via the `custom_networks` parameter on `Client`.

---

## Configuration

The SDK uses a frozen dataclass (`AddictuneConfig`) with sensible defaults. Configuration is explicit and controlled entirely by the host application.

`AddictuneConfig` is a plain Python `frozen=True` dataclass — every field has a default, so it works out of the box with zero setup. Override only what you need, using whichever approach fits your application.

There are four ways to configure the SDK, in order of precedence:

| Approach | When to use |
|----------|-------------|
| **No config** | Scripts, prototypes — defaults are production-ready |
| **Programmatic** | Desktop apps with their own settings layer (QSettings, NSUserDefaults, etc.) |
| **JSON file** | File-based settings, shared configs, deployment overrides |
| **Auto-discovery** | Let the SDK find a config file in standard OS locations automatically |

### Defaults only

No config object needed — every field ships with a sensible default:

```python
from addictune_sdk import Client

async with Client() as client:
    # Uses AddictuneConfig() under the hood:
    #   api_base  = "https://api.audioaddict.com/v1"
    #   network   = "di"
    #   timeout   = 30.0
    #   retry     = RetryConfig()   (3 attempts, exponential backoff)
    #   circuit   = CircuitConfig() (5 failures → open, 60s recovery)
    di = client.network("di")
    channels = await di.channels.get_all()
```

### Programmatic override

#### Override top-level fields

Pass an `AddictuneConfig` to the `Client` constructor with just the fields you want to change:

```python
from addictune_sdk import Client, AddictuneConfig

config = AddictuneConfig(
    network="radiotunes",   # default to RadioTunes instead of DI.FM
    timeout=15.0,           # shorter timeout for latency-sensitive apps
)

async with Client(config=config) as client:
    # client.login() will authenticate against the "radiotunes" network
    auth = await client.login("you@example.com", "password")
```

#### Override retry and circuit-breaker settings

`AddictuneConfig` has two nested dataclasses — `RetryConfig` and `CircuitConfig` — that control resilient transport behaviour:

```python
from addictune_sdk import AddictuneConfig, RetryConfig, CircuitConfig

config = AddictuneConfig(
    retry=RetryConfig(
        max_attempts=5,       # retry up to 5 times before giving up
        wait_min=1.0,         # wait at least 1s between retries
        wait_max=30.0,        # cap backoff at 30s
        wait_jitter=2.0,      # add up to 2s random jitter
    ),
    circuit=CircuitConfig(
        failure_threshold=10,  # tolerate more failures before tripping
        recovery_timeout=30.0, # recover faster (30s instead of 60s)
    ),
)
```

**How retry works:** on each failed attempt the delay is `wait_multiplier × 2^(attempt-1)`, clamped to `[wait_min, wait_max]`, then a random jitter in `[0, wait_jitter]` is added. With defaults (multiplier `1.0`, min `2.0`, max `10.0`) the delays are approximately 2s → 4s → 8s plus jitter.

**How the circuit breaker works:** consecutive failures are tracked. Once they reach `failure_threshold`, the circuit opens and all requests are immediately rejected. After `recovery_timeout` seconds the circuit closes and new requests are allowed through.

#### Use `dataclasses.replace` for small tweaks

If you only need to change one or two fields, use `dataclasses.replace` on the default instance:

```python
from dataclasses import replace
from addictune_sdk import AddictuneConfig

config = replace(AddictuneConfig(), timeout=10.0, network="jazzradio")
```

This is equivalent to `AddictuneConfig(timeout=10.0, network="jazzradio")` but reads more naturally when you're overriding a value you already have.

### JSON config file

Load config from a JSON file when your application prefers file-based settings:

```python
from addictune_sdk import Client, AddictuneConfig

config = AddictuneConfig.from_json("~/.config/myapp/addictune.json")
async with Client(config=config) as client:
    ...
```

All fields are optional — missing keys fall back to their defaults, so your JSON only needs the overrides:

```json
{
  "network": "di",
  "timeout": 15.0
}
```

Full example with every field:

```json
{
  "api_base": "https://api.audioaddict.com/v1",
  "network": "di",
  "timeout": 30.0,
  "retry": {
    "max_attempts": 3,
    "wait_multiplier": 1.0,
    "wait_min": 2.0,
    "wait_max": 10.0,
    "wait_jitter": 1.0
  },
  "circuit": {
    "failure_threshold": 5,
    "recovery_timeout": 60.0
  }
}
```

#### Write a config file from code

Persist settings for later use:

```python
from addictune_sdk import AddictuneConfig

config = AddictuneConfig(timeout=15.0, network="rockradio")
config.to_json("path/to/config.json")
```

`to_json` creates parent directories automatically if they don't exist.

#### Round-trip: read → modify → write

```python
from addictune_sdk import AddictuneConfig

# Load existing config
config = AddictuneConfig.from_json("config.json")

# Modify with dataclasses.replace
from dataclasses import replace
config = replace(config, timeout=20.0)

# Save back
config.to_json("config.json")
```

### Auto-discovery

`load_config()` searches standard OS config locations in order and returns the first file it finds. If nothing exists, it returns a default `AddictuneConfig()` — so your code never needs to handle "no config found" as a special case.

| Platform | Search paths (in order) |
|----------|-------------------------|
| Linux / macOS | `$XDG_CONFIG_HOME/addictune/config.json`, `~/.addictune/config.json` |
| Windows | `%APPDATA%\addictune\config.json` |

```python
from addictune_sdk import Client, load_config

# Searches standard paths; falls back to defaults if no file exists
config = load_config()

async with Client(config=config) as client:
    ...
```

Pass an explicit path to skip auto-discovery:

```python
config = load_config("/etc/myapp/addictune.json")
```

### Configuration reference

#### `AddictuneConfig`

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `api_base` | `str` | `https://api.audioaddict.com/v1` | API base URL |
| `network` | `str` | `di` | Default network slug used by `Client.login()` |
| `timeout` | `float` | `30.0` | HTTP request timeout (seconds) |
| `retry` | `RetryConfig` | `RetryConfig()` | Retry behaviour (see below) |
| `circuit` | `CircuitConfig` | `CircuitConfig()` | Circuit-breaker behaviour (see below) |

#### `RetryConfig`

Controls automatic retry with exponential backoff + jitter.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `max_attempts` | `int` | `3` | Max attempts per request (including initial). Set to `1` to disable retries. |
| `wait_multiplier` | `float` | `1.0` | Exponential backoff multiplier |
| `wait_min` | `float` | `2.0` | Minimum delay between retries (seconds) |
| `wait_max` | `float` | `10.0` | Maximum delay between retries (seconds) |
| `wait_jitter` | `float` | `1.0` | Upper bound of random jitter added to each delay (seconds) |

#### `CircuitConfig`

Controls the circuit-breaker that protects against cascading failures.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `failure_threshold` | `int` | `5` | Consecutive failures before the circuit opens |
| `recovery_timeout` | `float` | `60.0` | Seconds before a tripped circuit allows a retry |
| `name` | `str \| None` | `None` | Optional label for logging / metrics |

---

## Logging

The SDK uses Python's standard `logging` library under the `addictune_sdk` namespace. It does not configure handlers or formatters — that's the host application's responsibility. By default only `WARNING` and above is visible.

### Quick setup

The simplest way to see SDK log output:

```python
import logging

logging.basicConfig(level=logging.DEBUG)
```

### Target just the SDK

To control SDK logging independently of the rest of your application:

```python
import logging

logging.getLogger("addictune_sdk").setLevel(logging.DEBUG)
```

Or use a dedicated handler with a custom format:

```python
import logging

handler = logging.StreamHandler()
handler.setFormatter(
    logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
)
sdk_logger = logging.getLogger("addictune_sdk")
sdk_logger.setLevel(logging.DEBUG)
sdk_logger.addHandler(handler)
```

### Log levels by component

| Component | `DEBUG` | `INFO` | `WARNING` | `ERROR` |
|-----------|---------|--------|-----------|---------|
| **Transport** (retry / circuit breaker) | Each retry attempt with wait time | Retry succeeded; circuit recovered | Circuit tripped open; request rejected by circuit | All attempts exhausted |
| **Cache** (ETag / SQLite) | Cache hit, miss, expired, stored, indexed | — | — | — |
| **Client** | Init, connection close | Successful login | — | — |

**Recommended levels:**

- **Production:** `WARNING` (default) — only circuit-breaker trips and exhausted retries
- **Development:** `INFO` — adds login events and retry recoveries
- **Debugging:** `DEBUG` — full visibility into cache behaviour and every retry attempt

---

## License

[MIT](LICENSE) © ukw2d
