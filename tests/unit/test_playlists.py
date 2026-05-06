import httpx
import pytest

from addictune.api.playlists import PlaylistsAPI
from addictune.exceptions import AddictuneAPIError
from addictune.models.playlist import Playlist, PlaylistTracks
from tests.conftest import make_response

# ── get_featured ─────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_featured_returns_playlists(mocker, playlists_featured_payload):
    mocker.patch("addictune.api._helpers.cache.get_etag", return_value=(None, None))
    mocker.patch("addictune.api._helpers.cache.set_etag")
    mocker.patch("addictune.api._helpers.cache.index_list")

    mock_client = mocker.AsyncMock(spec=httpx.AsyncClient)
    mock_client.get.return_value = make_response(200, playlists_featured_payload)

    api = PlaylistsAPI(mock_client, network="di")
    result = await api.get_featured()

    assert len(result) == 2
    assert all(isinstance(p, Playlist) for p in result)
    assert result[0].id == 68656
    assert result[0].name == "Top Vocal Trance Hits"
    assert result[0].slug == "top-vocal-trance-hits"
    assert result[0].channel_id is None
    assert result[0].track_count == 121
    assert result[0].popularity == 0.96
    assert len(result[0].tags) == 2
    assert result[0].tags[0].name == "Vocal Trance"
    assert result[1].id == 63853
    mock_client.get.assert_called_once_with(
        "/di/playlist_collections/name/homepage-featured", headers={}
    )


@pytest.mark.asyncio
async def test_get_featured_uses_network_in_url(mocker, playlists_featured_payload):
    mocker.patch("addictune.api._helpers.cache.get_etag", return_value=(None, None))
    mocker.patch("addictune.api._helpers.cache.set_etag")
    mocker.patch("addictune.api._helpers.cache.index_list")

    mock_client = mocker.AsyncMock(spec=httpx.AsyncClient)
    mock_client.get.return_value = make_response(200, playlists_featured_payload)

    api = PlaylistsAPI(mock_client, network="rockradio")
    await api.get_featured()

    call_url = mock_client.get.call_args[0][0]
    assert call_url == "/rockradio/playlist_collections/name/homepage-featured"


# ── iter_playlists ───────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_iter_playlists_returns_playlists(mocker, playlists_featured_payload):
    mocker.patch(
        "addictune.api._helpers._fetch_page",
        return_value=(playlists_featured_payload, 1),
    )

    mock_client = mocker.AsyncMock(spec=httpx.AsyncClient)

    api = PlaylistsAPI(mock_client, network="di")
    results = [p async for p in api.iter_playlists()]

    assert len(results) == 2
    assert all(isinstance(p, Playlist) for p in results)
    assert results[0].id == 68656
    assert results[1].id == 63853


@pytest.mark.asyncio
async def test_iter_playlists_passes_params(mocker, playlists_featured_payload):
    mock_fetch = mocker.patch(
        "addictune.api._helpers._fetch_page",
        return_value=(playlists_featured_payload, 1),
    )

    mock_client = mocker.AsyncMock(spec=httpx.AsyncClient)

    api = PlaylistsAPI(mock_client, network="di")
    _ = [p async for p in api.iter_playlists(order_by="newest", per_page=10)]

    call_url = mock_fetch.call_args[0][1]
    assert call_url == "/di/playlists"

    call_params = mock_fetch.call_args[1]["params"]
    assert call_params["order_by"] == "newest"
    assert call_params["legacy_result"] == "false"
    assert call_params["per_page"] == 10


@pytest.mark.asyncio
async def test_iter_playlists_rejects_bad_order_by(mocker):
    mock_client = mocker.AsyncMock(spec=httpx.AsyncClient)
    api = PlaylistsAPI(mock_client, network="di")

    with pytest.raises(ValueError, match="Invalid order_by"):
        _ = [p async for p in api.iter_playlists(order_by="bad")]


@pytest.mark.asyncio
async def test_iter_playlists_rejects_bad_per_page(mocker):
    mock_client = mocker.AsyncMock(spec=httpx.AsyncClient)
    api = PlaylistsAPI(mock_client, network="di")

    with pytest.raises(ValueError, match="per_page"):
        _ = [p async for p in api.iter_playlists(per_page=50)]


@pytest.mark.asyncio
async def test_iter_playlists_rejects_zero_per_page(mocker):
    mock_client = mocker.AsyncMock(spec=httpx.AsyncClient)
    api = PlaylistsAPI(mock_client, network="di")

    with pytest.raises(ValueError, match="per_page"):
        _ = [p async for p in api.iter_playlists(per_page=0)]


# ── get_by_id ────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_by_id_returns_playlist(mocker, playlist_payload):
    mocker.patch("addictune.api._helpers.cache.get_etag", return_value=(None, None))
    mocker.patch("addictune.api._helpers.cache.get_indexed", return_value=None)
    mocker.patch("addictune.api._helpers.cache.set_etag")

    mock_client = mocker.AsyncMock(spec=httpx.AsyncClient)
    mock_client.get.return_value = make_response(200, playlist_payload)

    api = PlaylistsAPI(mock_client, network="di")
    result = await api.get_by_id(68656)

    assert isinstance(result, Playlist)
    assert result.id == 68656
    assert result.name == "Top Vocal Trance Hits"
    assert result.slug == "top-vocal-trance-hits"
    assert result.following is True
    assert result.channel_id is None
    assert result.length == 44171
    mock_client.get.assert_called_once_with("/di/playlists/68656", headers={})


@pytest.mark.asyncio
async def test_get_by_id_uses_network_in_url(mocker, playlist_payload):
    mocker.patch("addictune.api._helpers.cache.get_etag", return_value=(None, None))
    mocker.patch("addictune.api._helpers.cache.get_indexed", return_value=None)
    mocker.patch("addictune.api._helpers.cache.set_etag")

    mock_client = mocker.AsyncMock(spec=httpx.AsyncClient)
    mock_client.get.return_value = make_response(200, playlist_payload)

    api = PlaylistsAPI(mock_client, network="jazzradio")
    await api.get_by_id(68656)

    call_url = mock_client.get.call_args[0][0]
    assert call_url == "/jazzradio/playlists/68656"


# ── get_content ──────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_content_returns_tracks(mocker, playlist_content_payload):
    mock_client = mocker.AsyncMock(spec=httpx.AsyncClient)
    mock_client.post.return_value = make_response(200, playlist_content_payload)

    api = PlaylistsAPI(mock_client, network="di")
    result = await api.get_content(63662)

    assert isinstance(result, PlaylistTracks)
    assert result.id == 63662
    assert len(result.tracks) == 1
    assert result.last_tracks == []
    assert result.current_progress is not None
    assert result.current_progress.played_tracks == 1
    assert result.current_progress.remaining_tracks == 286
    mock_client.post.assert_called_once_with("/di/playlists/63662/play")


@pytest.mark.asyncio
async def test_get_content_coerces_last_tracks_false(mocker):
    payload = {
        "id": 123,
        "tracks": [],
        "last_tracks": False,
        "current_progress": None,
    }
    mock_client = mocker.AsyncMock(spec=httpx.AsyncClient)
    mock_client.post.return_value = make_response(200, payload)

    api = PlaylistsAPI(mock_client, network="di")
    result = await api.get_content(123)

    assert result.last_tracks == []


@pytest.mark.asyncio
async def test_get_content_raises_on_error(mocker):
    mock_client = mocker.AsyncMock(spec=httpx.AsyncClient)
    mock_client.post.return_value = make_response(500, text="Internal Server Error")

    api = PlaylistsAPI(mock_client, network="di")
    with pytest.raises(AddictuneAPIError):
        await api.get_content(123)


# ── iter_followed ────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_iter_followed_returns_playlists(mocker, playlists_followed_payload):
    mocker.patch(
        "addictune.api._helpers._fetch_page",
        return_value=(playlists_followed_payload, 1),
    )

    mock_client = mocker.AsyncMock(spec=httpx.AsyncClient)

    api = PlaylistsAPI(mock_client, network="di")
    results = [p async for p in api.iter_followed(user_id=13716939)]

    assert len(results) == 1
    assert isinstance(results[0], Playlist)
    assert results[0].id == 65974
    assert results[0].name == "Melodic Progressive Vocals"
    assert results[0].slug == "melodic-progressive-vocals"
    assert results[0].following is True


@pytest.mark.asyncio
async def test_iter_followed_uses_user_id_in_url(mocker, playlists_followed_payload):
    mock_fetch = mocker.patch(
        "addictune.api._helpers._fetch_page",
        return_value=(playlists_followed_payload, 1),
    )

    mock_client = mocker.AsyncMock(spec=httpx.AsyncClient)

    api = PlaylistsAPI(mock_client, network="di")
    _ = [p async for p in api.iter_followed(user_id=99999)]

    call_url = mock_fetch.call_args[0][1]
    assert call_url == "/di/members/99999/followed_items/playlist"


@pytest.mark.asyncio
async def test_iter_followed_passes_params(mocker, playlists_followed_payload):
    mock_fetch = mocker.patch(
        "addictune.api._helpers._fetch_page",
        return_value=(playlists_followed_payload, 1),
    )

    mock_client = mocker.AsyncMock(spec=httpx.AsyncClient)

    api = PlaylistsAPI(mock_client, network="di")
    _ = [p async for p in api.iter_followed(user_id=13716939, limit=5)]

    call_params = mock_fetch.call_args[1]["params"]
    assert call_params["order_by"] == "follow_date"
    assert call_params["limit"] == "5"
    assert call_params["per_page"] == 5


@pytest.mark.asyncio
async def test_iter_followed_rejects_bad_limit(mocker):
    mock_client = mocker.AsyncMock(spec=httpx.AsyncClient)
    api = PlaylistsAPI(mock_client, network="di")

    with pytest.raises(ValueError, match="limit"):
        _ = [p async for p in api.iter_followed(user_id=1, limit=20)]

    with pytest.raises(ValueError, match="limit"):
        _ = [p async for p in api.iter_followed(user_id=1, limit=0)]


# ── get_listen_history ───────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_listen_history_returns_entries(
    mocker, playlist_listen_history_payload
):
    mock_client = mocker.AsyncMock(spec=httpx.AsyncClient)
    mock_client.get.return_value = make_response(200, playlist_listen_history_payload)

    api = PlaylistsAPI(mock_client, network="di")
    result = await api.get_listen_history(63662)

    assert len(result) == 1
    assert result[0]["track"]["id"] == 3120758
    assert result[0]["played_at"] == 1778081692
    mock_client.get.assert_called_once_with(
        "/di/listen_history", params={"playlist_id": 63662}
    )


@pytest.mark.asyncio
async def test_get_listen_history_returns_empty_list(mocker):
    mock_client = mocker.AsyncMock(spec=httpx.AsyncClient)
    mock_client.get.return_value = make_response(200, [])

    api = PlaylistsAPI(mock_client, network="di")
    result = await api.get_listen_history(99999)

    assert result == []


# ── add_listen_history ───────────────────────────────────────────────


@pytest.mark.asyncio
async def test_add_listen_history_success(mocker):
    mock_client = mocker.AsyncMock(spec=httpx.AsyncClient)
    mock_client.post.return_value = make_response(201, text="")

    api = PlaylistsAPI(mock_client, network="di")
    await api.add_listen_history(playlist_id=63662, track_id=3120758)

    mock_client.post.assert_called_once_with(
        "/di/listen_history",
        json={"playlist_id": 63662, "track_id": 3120758},
    )


@pytest.mark.asyncio
async def test_add_listen_history_accepts_204(mocker):
    mock_client = mocker.AsyncMock(spec=httpx.AsyncClient)
    mock_client.post.return_value = make_response(204, text="")

    api = PlaylistsAPI(mock_client, network="di")
    await api.add_listen_history(playlist_id=63662, track_id=3120758)


@pytest.mark.asyncio
async def test_add_listen_history_raises_on_error(mocker):
    mock_client = mocker.AsyncMock(spec=httpx.AsyncClient)
    mock_client.post.return_value = make_response(500, text="Internal Server Error")

    api = PlaylistsAPI(mock_client, network="di")
    with pytest.raises(AddictuneAPIError):
        await api.add_listen_history(playlist_id=63662, track_id=3120758)
