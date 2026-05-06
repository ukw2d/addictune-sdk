"""Playlists integration tests against the live AudioAddict API.

Run:
    ADDICTUNE_EMAIL=kromerx@gmail.com ADDICTUNE_PASSWORD=ukw2dDIFM \
      uv run python tests/integration/playlists.py

Credentials can also be set in .env.  A cached session file is
reused between script runs so login only happens once per 12 hours.
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


async def get_featured(di) -> None:
    playlists = await di.playlists.get_featured()
    assert len(playlists) > 0, f"expected featured playlists, got {len(playlists)}"
    assert playlists[0].id
    assert playlists[0].name


async def iter_playlists(di) -> None:
    """Test pagination — fetch 2 pages of 5 items each."""
    page1 = []
    async for p in di.playlists.iter_playlists(
        order_by="popularity", per_page=5, end_page=1
    ):
        page1.append(p)

    assert len(page1) > 0, "page 1 should have items"
    assert all(p.id for p in page1), "every playlist must have an id"

    await asyncio.sleep(PAUSE)

    page2 = []
    async for p in di.playlists.iter_playlists(
        order_by="popularity", per_page=5, start_page=2, end_page=2
    ):
        page2.append(p)

    # Pages should differ (at least in order or content)
    page1_ids = {p.id for p in page1}
    page2_ids = {p.id for p in page2}
    print(f"    page1: {len(page1)} items, page2: {len(page2)} items")
    print(f"    overlap: {page1_ids & page2_ids or 'none'}")


async def iter_playlists_newest(di) -> None:
    playlists = []
    async for p in di.playlists.iter_playlists(
        order_by="newest", per_page=5, end_page=1
    ):
        playlists.append(p)
    assert len(playlists) > 0, "expected newest playlists"


async def get_by_id(di) -> None:
    # Grab a real playlist ID first
    first = None
    async for p in di.playlists.iter_playlists(per_page=1, end_page=1):
        first = p
        break
    assert first is not None, "no playlists to test get_by_id"

    await asyncio.sleep(PAUSE)
    fetched = await di.playlists.get_by_id(first.id)
    assert fetched.id == first.id
    assert fetched.name


async def get_content(di) -> None:
    # Get a playlist and fetch its content
    first = None
    async for p in di.playlists.iter_playlists(per_page=1, end_page=1):
        first = p
        break
    assert first is not None, "no playlists to test get_content"

    await asyncio.sleep(PAUSE)
    content = await di.playlists.get_content(first.id)
    assert content.id == first.id
    print(f"    tracks: {len(content.tracks)}, progress: {content.current_progress}")


async def iter_followed(di, user_id) -> None:
    followed = []
    async for p in di.playlists.iter_followed(user_id, end_page=1):
        followed.append(p)
    print(f"    followed playlists: {len(followed)}")
    assert isinstance(followed, list)


async def get_listen_history(di) -> None:
    # Get a playlist and check listen history
    first = None
    async for p in di.playlists.iter_playlists(per_page=1, end_page=1):
        first = p
        break
    assert first is not None, "no playlists to test listen history"

    await asyncio.sleep(PAUSE)
    history = await di.playlists.get_listen_history(first.id)
    print(f"    history entries: {len(history)}")
    assert isinstance(history, list)


async def add_listen_history(di) -> None:
    # Get a playlist with content, then record a play
    first = None
    async for p in di.playlists.iter_playlists(per_page=1, end_page=1):
        first = p
        break
    assert first is not None

    await asyncio.sleep(PAUSE)
    content = await di.playlists.get_content(first.id)
    if not content.tracks:
        print("    (skipped — no tracks in playlist)")
        return

    track = content.tracks[0]
    track_id = track.get("id") if isinstance(track, dict) else track.id
    assert track_id

    await asyncio.sleep(PAUSE)
    await di.playlists.add_listen_history(first.id, track_id)
    print(f"    recorded play: playlist={first.id}, track={track_id}")


# ── Runner ────────────────────────────────────────────────────────────


async def main() -> None:
    session = await get_session()

    async with Client(
        session_key=session["session_key"],
        listen_key=session["listen_key"],
    ) as client:
        di = client.network("di")
        user_id = session["user_id"]

        print("\nPlaylists")
        print("─" * 40)

        tests = [
            ("get_featured", get_featured, di),
            ("iter_playlists (pagination)", iter_playlists, di),
            ("iter_playlists (newest)", iter_playlists_newest, di),
            ("get_by_id", get_by_id, di),
            ("get_content", get_content, di),
            ("iter_followed", iter_followed, di, user_id),
            ("get_listen_history", get_listen_history, di),
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
