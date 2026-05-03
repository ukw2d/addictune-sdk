"""Tracks integration tests against the live AudioAddict API.

Run:
    uv run python tests/integration/tracks.py

Credentials are read from ADDICTUNE_EMAIL / ADDICTUNE_PASSWORD env vars
(or from a .env file via AddictuneSettings).  A cached session file is
reused between script runs so login only happens once per 12 hours.

Mutating tests (votes, preferred quality) capture pre-mutation state
and restore it, leaving your profile unchanged.
"""
import asyncio
import sys
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from addictune import AddictuneClient
from session import get_session

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


async def get_qualities(client: AddictuneClient) -> None:
    qualities = await client.tracks.get_qualities()
    assert len(qualities) > 0
    assert qualities[0].key
    assert qualities[0].content_quality


async def get_preferred_quality(client: AddictuneClient) -> None:
    pq = await client.tracks.get_preferred_quality(client._user_id)
    assert pq.quality_id
    assert pq.member_id == client._user_id


async def get_by_id(client: AddictuneClient) -> None:
    history = await client.channels.get_track_history(1)
    track_id = history[0].track_id
    await asyncio.sleep(PAUSE)
    track = await client.tracks.get_by_id(track_id)
    assert track.id == track_id
    assert track.title
    assert track.content_format_id
    assert track.content_quality_id


async def get_liked_tracks(client: AddictuneClient) -> None:
    tracks = await client.tracks.get_liked_tracks(client._user_id)
    assert isinstance(tracks, list)
    if tracks:
        assert tracks[0].id
        assert isinstance(tracks[0].up, bool)


# ── Mutations (with rollback) ─────────────────────────────────────────


async def vote_and_rollback(client: AddictuneClient) -> None:
    user_id = client._user_id

    history = await client.channels.get_track_history(1)
    track_id = history[0].track_id
    await asyncio.sleep(PAUSE)

    existing = await client.tracks.get_liked_track(user_id, track_id)
    was_up = existing.up if existing else False
    was_down = existing.down if existing else False

    await client.tracks.vote(track_id, direction="up")
    await asyncio.sleep(PAUSE)

    liked = await client.tracks.get_liked_track(user_id, track_id)
    assert liked is not None
    assert liked.up is True

    # rollback
    if not was_up and not was_down:
        await client.tracks.vote(track_id, direction="delete")
    elif was_down:
        await client.tracks.vote(track_id, direction="down")
    # was_up: already in the right state, nothing to do
    await asyncio.sleep(PAUSE)


async def set_preferred_quality_and_rollback(client: AddictuneClient) -> None:
    user_id = client._user_id

    original = await client.tracks.get_preferred_quality(user_id)
    original_quality_id = original.quality_id

    qualities = await client.tracks.get_qualities()
    other = next((q for q in qualities if q.id != original_quality_id), qualities[0])

    await asyncio.sleep(PAUSE)
    await client.tracks.set_preferred_quality(user_id, other.id)
    await asyncio.sleep(PAUSE)

    updated = await client.tracks.get_preferred_quality(user_id)
    assert updated.quality_id == other.id

    # rollback
    await client.tracks.set_preferred_quality(user_id, original_quality_id)
    await asyncio.sleep(PAUSE)

    restored = await client.tracks.get_preferred_quality(user_id)
    assert restored.quality_id == original_quality_id


# ── Runner ────────────────────────────────────────────────────────────


async def main() -> None:
    session = await get_session()

    async with AddictuneClient(
        session_key=session["session_key"],
        listen_key=session["listen_key"],
    ) as client:
        client._user_id = session["user_id"]

        print("\nTracks")
        print("─" * 40)

        tests = [
            ("get_qualities", get_qualities),
            ("get_preferred_quality", get_preferred_quality),
            ("get_by_id", get_by_id),
            ("get_liked_tracks", get_liked_tracks),
            ("vote_and_rollback", vote_and_rollback),
            ("set_preferred_quality_and_rollback", set_preferred_quality_and_rollback),
        ]

        for name, fn in tests:
            await _run(name, fn, client)
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
