import httpx
import pytest

from addictune_sdk.api.playlists import PlaylistsAPI
from addictune_sdk.exceptions import AddictuneAPIError
from addictune_sdk.models.playlist import Playlist, PlaylistTracks
from tests.conftest import make_response

# ── iter_playlists ───────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_iter_playlists_returns_playlists(mocker, playlists_featured_payload):
    mocker.patch(
        "addictune_sdk.api._helpers._fetch_page",
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
        "addictune_sdk.api._helpers._fetch_page",
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
        "addictune_sdk.api._helpers._fetch_page",
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
        "addictune_sdk.api._helpers._fetch_page",
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
        "addictune_sdk.api._helpers._fetch_page",
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
