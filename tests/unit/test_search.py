import httpx
import pytest

from addictune_sdk.api.search import SearchAPI
from addictune_sdk.models.mixshow import MixShow
from addictune_sdk.models.playlist import Playlist
from addictune_sdk.models.search import SearchResults
from tests.conftest import make_response


@pytest.mark.asyncio
async def test_query_returns_grouped_results(mocker, mixshow_payload, playlist_payload):
    payload = {
        "channels": {"total": 0, "items": []},
        "shows": {"total": 1, "items": [mixshow_payload]},
        "playlists": {"total": 1, "items": [playlist_payload]},
        "tracks": {"total": 0, "items": []},
    }
    mock_client = mocker.AsyncMock(spec=httpx.AsyncClient)
    mock_client.get.return_value = make_response(200, payload)

    result = await SearchAPI(mock_client, network="di").query("state of trance")

    assert isinstance(result, SearchResults)
    assert isinstance(result.shows.items[0], MixShow)
    assert isinstance(result.playlists.items[0], Playlist)
    assert result.shows.total == 1
    mock_client.get.assert_called_once_with(
        "/di/search", params={"q": "state of trance"}
    )


@pytest.mark.asyncio
async def test_query_uses_configured_network_and_strips_query(mocker):
    mock_client = mocker.AsyncMock(spec=httpx.AsyncClient)
    mock_client.get.return_value = make_response(200, {})

    await SearchAPI(mock_client, network="rockradio").query("  rock  ")

    mock_client.get.assert_called_once_with("/rockradio/search", params={"q": "rock"})


@pytest.mark.asyncio
async def test_query_rejects_blank_query(mocker):
    mock_client = mocker.AsyncMock(spec=httpx.AsyncClient)

    with pytest.raises(ValueError, match="query must not be empty"):
        await SearchAPI(mock_client).query("  ")

    mock_client.get.assert_not_called()

