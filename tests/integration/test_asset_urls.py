"""Integration test: verify all AssetUrl fields produce ready-to-use https:// URLs.

Run:
    ADDICTUNE_EMAIL=... ADDICTUNE_PASSWORD=... uv run python tests/integration/test_asset_urls.py
"""

import asyncio
import sys
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from session import get_session

from addictune_sdk import Client

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


def _assert_url(val, label: str) -> None:
    """Assert a single URL value is a proper https:// URL (not protocol-relative)."""
    if val is None:
        return  # None is acceptable for optional fields
    assert val.startswith("https://"), f"{label}: expected https:// URL, got {val!r}"


def _assert_imageset(images, label: str) -> None:
    """Assert every non-None field on an ImageSet starts with https://."""
    if images is None:
        return
    for field_name in (
        "default",
        "compact",
        "square",
        "vertical",
        "horizontal_banner",
        "tall_banner",
    ):
        val = getattr(images, field_name, None)
        if val is not None:
            _assert_url(val, f"{label}.images.{field_name}")


# ── Channel URLs ──────────────────────────────────────────────────────


async def channel_asset_urls(di) -> None:
    channels = await di.channels.get_all()
    assert len(channels) > 0, "no channels returned"
    # Spot-check a handful of channels
    for ch in channels[:10]:
        _assert_url(ch.asset_url, f"Channel(id={ch.id}, key={ch.key}).asset_url")
        _assert_url(ch.banner_url, f"Channel(id={ch.id}, key={ch.key}).banner_url")
        _assert_imageset(ch.images, f"Channel(id={ch.id}, key={ch.key})")


async def channel_by_id_asset_urls(di) -> None:
    ch = await di.channels.get_by_id(1)
    _assert_url(ch.asset_url, f"Channel(id={ch.id}).asset_url")
    _assert_url(ch.banner_url, f"Channel(id={ch.id}).banner_url")
    _assert_imageset(ch.images, f"Channel(id={ch.id})")
    # Check channel artists too
    if ch.artists:
        for artist in ch.artists[:5]:
            _assert_url(artist.asset_url, f"ChannelArtist(id={artist.id}).asset_url")
            _assert_imageset(artist.images, f"ChannelArtist(id={artist.id})")


async def track_history_asset_urls(di) -> None:
    history = await di.channels.get_track_history(1)
    assert len(history) > 0, "no track history returned"
    for entry in history[:5]:
        _assert_url(entry.art_url, f"TrackHistoryEntry(id={entry.id}).art_url")
        _assert_imageset(entry.images, f"TrackHistoryEntry(id={entry.id})")


async def currently_playing_asset_urls(di) -> None:
    now = await di.channels.get_currently_playing()
    assert len(now) > 0, "no currently playing data"
    for np in now[:5]:
        if np.track:
            _assert_url(np.track.art_url, "NowPlaying.track.art_url")
            _assert_imageset(np.track.images, "NowPlaying.track.images")


# ── Track URLs ────────────────────────────────────────────────────────


async def track_detail_asset_urls(di) -> None:
    history = await di.channels.get_track_history(1)
    if not history:
        return
    track_id = history[0].track_id
    track = await di.tracks.get_by_id(track_id)
    _assert_url(track.asset_url, f"Track(id={track.id}).asset_url")
    _assert_imageset(track.images, f"Track(id={track.id})")
    # Check artists on the track
    if track.artists:
        for artist in track.artists[:5]:
            _assert_url(artist.asset_url, f"Artist(id={artist.id}).asset_url")
            _assert_imageset(artist.images, f"Artist(id={artist.id})")
    # Check streaming asset URLs
    if track.assets:
        for asset in track.assets[:5]:
            _assert_url(
                asset.url, f"ContentAsset(format={asset.content_format_id}).url"
            )


async def liked_tracks_asset_urls(di, user_id) -> None:
    tracks = await di.tracks.get_liked_tracks(user_id)
    if not tracks:
        print("  (no liked tracks, skipping URL checks)")
        return
    for t in tracks[:5]:
        _assert_url(t.asset_url, f"LikedTrack(id={t.id}).asset_url")
        _assert_imageset(t.images, f"LikedTrack(id={t.id})")
        if t.artists:
            for artist in t.artists[:3]:
                _assert_url(artist.asset_url, f"Artist(id={artist.id}).asset_url")
                _assert_imageset(artist.images, f"Artist(id={artist.id})")


# ── Playlist URLs ──────────────────────────────────────────────────────


async def playlists_asset_urls(di) -> None:
    playlists = await di.playlists.get_featured()
    if not playlists:
        print("  (no playlists returned, skipping)")
        return
    for pl in playlists[:5]:
        _assert_imageset(pl.images, f"Playlist(id={pl.id}, name={pl.name})")


# ── MixShow URLs ───────────────────────────────────────────────────────


async def mixshows_asset_urls(di) -> None:
    shows = []
    async for show in di.mixshows.iter_shows():
        shows.append(show)
        if len(shows) >= 5:
            break
    if not shows:
        print("  (no mix shows returned, skipping)")
        return
    for show in shows:
        _assert_imageset(show.images, f"MixShow(id={show.id}, name={show.name})")
        if show.channels:
            for ch in show.channels[:3]:
                _assert_imageset(ch.images, f"ShowChannel(id={ch.id}).images")


# ── Runner ────────────────────────────────────────────────────────────


async def main() -> None:
    session = await get_session()

    async with Client(
        session_key=session["session_key"],
        listen_key=session["listen_key"],
    ) as client:
        di = client.network("di")
        user_id = session["user_id"]

        print("\nAsset URL Integration Tests")
        print("═" * 40)

        tests = [
            ("channel_asset_urls", channel_asset_urls, di),
            ("channel_by_id_asset_urls", channel_by_id_asset_urls, di),
            ("track_history_asset_urls", track_history_asset_urls, di),
            ("currently_playing_asset_urls", currently_playing_asset_urls, di),
            ("track_detail_asset_urls", track_detail_asset_urls, di),
            ("liked_tracks_asset_urls", liked_tracks_asset_urls, di, user_id),
            ("playlists_asset_urls", playlists_asset_urls, di),
            ("mixshows_asset_urls", mixshows_asset_urls, di),
        ]

        for name, fn, *args in tests:
            await _run(name, fn, *args)
            await asyncio.sleep(1.0)

    total = len(_results)
    passed = sum(1 for _, ok in _results if ok)
    failed = total - passed
    print("═" * 40)
    print(f"  {passed}/{total} passed" + (f"  ({failed} failed)" if failed else ""))

    if failed:
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
