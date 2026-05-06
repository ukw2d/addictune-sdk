"""MixShows integration tests against the live AudioAddict API.

Run:
    uv run python tests/integration/mixshows.py

Credentials are read from ADDICTUNE_EMAIL / ADDICTUNE_PASSWORD env vars
(or from a .env file via AddictuneSettings).  A cached session file is
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


async def iter_shows(di) -> None:
    shows = []
    async for show in di.mixshows.iter_shows(end_page=1):
        shows.append(show)
    assert len(shows) >= 1, f"expected at least 1 show, got {len(shows)}"
    assert shows[0].id
    assert shows[0].name
    assert shows[0].slug


async def get_by_id(di) -> None:
    # Get first show from iter_shows
    first_show = None
    async for show in di.mixshows.iter_shows(end_page=1):
        first_show = show
        break
    assert first_show is not None, "no shows found"

    await asyncio.sleep(PAUSE)
    fetched = await di.mixshows.get_by_id(first_show.id)
    assert fetched.id == first_show.id
    assert fetched.name == first_show.name
    assert fetched.slug == first_show.slug


async def get_upcoming(di) -> None:
    upcoming = await di.mixshows.get_upcoming(limit=5)
    assert isinstance(upcoming, list)
    if upcoming:
        assert upcoming[0].id
        assert upcoming[0].start_at


async def iter_episodes(di) -> None:
    # Get first show
    first_show = None
    async for show in di.mixshows.iter_shows(end_page=1):
        first_show = show
        break
    assert first_show is not None, "no shows found"

    await asyncio.sleep(PAUSE)
    episodes = []
    async for ep in di.mixshows.iter_episodes(first_show.id, end_page=1):
        episodes.append(ep)
    # Episodes may be empty for some shows
    if episodes:
        assert episodes[0].id
        assert episodes[0].name


async def iter_followed(di, user_id) -> None:
    followed = []
    async for show in di.mixshows.iter_followed(user_id, end_page=1):
        followed.append(show)
    # May be empty for some users, just verify it's iterable
    assert isinstance(followed, list)


# ── Runner ────────────────────────────────────────────────────────────


async def main() -> None:
    session = await get_session()

    async with Client(
        session_key=session["session_key"],
        listen_key=session["listen_key"],
    ) as client:
        di = client.network("di")
        user_id = session["user_id"]

        print("\nMixShows")
        print("─" * 40)

        tests = [
            ("iter_shows", iter_shows, di),
            ("get_by_id", get_by_id, di),
            ("get_upcoming", get_upcoming, di),
            ("iter_episodes", iter_episodes, di),
            ("iter_followed", iter_followed, di, user_id),
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
