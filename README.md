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
- **ETag caching** — automatic HTTP `If-None-Match` / `304` handling backed by `diskcache`
- **Auto-pagination** — `async for` iterators that transparently walk pages
- **Resilient transport** — retry with exponential backoff + jitter, circuit breaker
- **Auth helpers** — session and direct login, `SecretStr`-guarded internal storage
- **Zero-config** — sensible defaults, override anything via env vars or `.env`

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

Settings are loaded from environment variables (prefix `ADDICTUNE_`) or a `.env` file:

| Variable | Default | Description |
|----------|---------|-------------|
| `ADDICTUNE_API_BASE` | `https://api.audioaddict.com/v1` | API base URL |
| `ADDICTUNE_NETWORK` | `di` | Default network slug |
| `ADDICTUNE_TIMEOUT` | `30.0` | HTTP timeout (seconds) |

Transport resilience can also be tuned:

| Variable | Default | Description |
|----------|---------|-------------|
| `ADDICTUNE_RETRY__MAX_ATTEMPTS` | `3` | Max retry attempts |
| `ADDICTUNE_RETRY__WAIT_MIN` | `2.0` | Minimum backoff (seconds) |
| `ADDICTUNE_RETRY__WAIT_MAX` | `10.0` | Maximum backoff (seconds) |
| `ADDICTUNE_CIRCUIT__FAILURE_THRESHOLD` | `5` | Failures before circuit opens |
| `ADDICTUNE_CIRCUIT__RECOVERY_TIMEOUT` | `60.0` | Seconds before circuit half-opens |

Or pass a configured `AddictuneSettings` / `TransportConfig` directly:

```python
from addictune_sdk import Client, AddictuneSettings

settings = AddictuneSettings(api_base="https://api.audioaddict.com/v1", timeout=10.0)
async with Client(settings=settings) as client:
    ...
```

---

## License

[MIT](LICENSE) © ukw2d
