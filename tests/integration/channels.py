"""Channels integration tests against the live AudioAddict API.

Run:
    uv run python tests/integration/channels.py

Credentials are read from ADDICTUNE_EMAIL / ADDICTUNE_PASSWORD env vars
A cached session file is
reused between script runs so login only happens once per 12 hours.

Mutating tests (favorites) capture pre-mutation state and restore it,
leaving your profile unchanged.
"""

import asyncio
import sys
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from session import get_session

from addictune_sdk import Client

PAUSE = 1.5

_results: list[tuple[str, bool]] = []


async def _run(name: str, fn, *args) -> bool:
    try:
        await fn(*args)
        print(f"  PASS  {name}")
        _results.append((name, True))
        return True
    except Exception as e:
        print(f"  FAIL  {name}: {e}")
        traceback.print_exc()
        _results.append((name, False))
        return False


# ── Read-only ─────────────────────────────────────────────────────────


async def get_all(di) -> None:
    channels = await di.channels.get_all()
    assert len(channels) > 50, f"expected >50 channels, got {len(channels)}"
    assert all(ch.id for ch in channels)
    assert all(ch.key for ch in channels)


async def get_by_id(di) -> None:
    channel = await di.channels.get_by_id(1)
    assert channel.id == 1
    assert channel.key == "trance"


async def get_track_history(di) -> None:
    history = await di.channels.get_track_history(1)
    assert len(history) > 0
    assert history[0].track_id


async def get_currently_playing(di) -> None:
    now = await di.channels.get_currently_playing()
    assert len(now) > 0
    assert now[0].channel_id
    assert now[0].track


# ── Stream URL ───────────────────────────────────────────────────────


async def get_stream_url(di, client) -> None:
    url = di.channels.get_stream_url("trance", client.listen_key, quality="hi")
    assert url.startswith("http://"), f"unexpected url: {url}"
    assert "trance_hi" in url, f"channel key+suffix missing from url: {url}"
    assert client.listen_key in url, f"listen key missing from url: {url}"


# ── Mutations (with rollback) ─────────────────────────────────────────


async def add_remove_favorite(di, user_id) -> None:
    # Pick a real channel that isn't already favorited
    channels = await di.channels.get_all()
    favorites = await di.channels.get_favorites(user_id)
    fav_ids = {f.channel_id for f in favorites}
    test_channel = next(ch for ch in reversed(channels) if ch.id not in fav_ids)
    channel_id = test_channel.id

    await asyncio.sleep(PAUSE)
    was = await di.channels.get_favorite(user_id, channel_id)

    if was is not None:
        await di.channels.remove_favorite(user_id, channel_id)
        await asyncio.sleep(PAUSE)

    await di.channels.add_favorite(user_id, channel_id)
    await asyncio.sleep(PAUSE)

    result = await di.channels.get_favorite(user_id, channel_id)
    assert result is not None
    assert result.channel_id == channel_id

    # rollback
    if was is None:
        await di.channels.remove_favorite(user_id, channel_id)
    else:
        await di.channels.add_favorite(user_id, channel_id)
    await asyncio.sleep(PAUSE)

    restored = await di.channels.get_favorite(user_id, channel_id)
    assert (restored is not None) == (was is not None)


async def add_listen_history(di) -> None:
    history = await di.channels.get_track_history(1)
    track_id = history[0].track_id
    await asyncio.sleep(PAUSE)
    await di.channels.add_listen_history(1, track_id)


# ── Runner ────────────────────────────────────────────────────────────


async def main() -> None:
    session = await get_session()

    async with Client(
        session_key=session["session_key"],
        listen_key=session["listen_key"],
    ) as client:
        di = client.network("di")
        user_id = session["user_id"]

        print("\nChannels")
        print("─" * 40)

        tests = [
            ("get_all", get_all, di),
            ("get_by_id", get_by_id, di),
            ("get_track_history", get_track_history, di),
            ("get_currently_playing", get_currently_playing, di),
            ("get_stream_url", get_stream_url, di, client),
            ("add_remove_favorite", add_remove_favorite, di, user_id),
            ("add_listen_history", add_listen_history, di),
        ]

        for name, fn, *args in tests:
            await _run(name, fn, *args)
            await asyncio.sleep(PAUSE)

    total = len(_results)
    passed = sum(1 for _, ok in _results if ok)
    failed = total - passed
    print("─" * 40)
    print(f"  {passed}/{total} passed" + (f"  ({failed} failed)" if failed else ""))

    if failed:
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
