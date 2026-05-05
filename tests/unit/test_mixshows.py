import httpx
import pytest

from addictune.api.mixshows import MixShowsAPI
from addictune.exceptions import AddictuneAPIError
from addictune.models.mixshow import MixShow, ShowEpisode
from tests.conftest import make_response

# ── get_by_id ────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_by_id_returns_mixshow(mocker, mixshow_payload):
    mocker.patch("addictune.api._helpers.cache.get_etag", return_value=(None, None))
    mocker.patch("addictune.api._helpers.cache.get_indexed", return_value=None)
    mocker.patch("addictune.api._helpers.cache.set_etag")

    mock_client = mocker.AsyncMock(spec=httpx.AsyncClient)
    mock_client.get.return_value = make_response(200, mixshow_payload)

    api = MixShowsAPI(mock_client, network="di")
    result = await api.get_by_id(123)

    assert isinstance(result, MixShow)
    assert result.id == 123
    assert result.name == "Global Trance Sounds"
    assert result.slug == "global-trance-sounds"
    assert result.active is True
    assert result.following is True
    assert result.followers_count == 15000
    assert result.upcoming_event is not None
    assert result.upcoming_event.id == 456
    assert len(result.channels) == 1
    assert result.channels[0].key == "trance"
    mock_client.get.assert_called_once_with("/di/shows/123", headers={})


@pytest.mark.asyncio
async def test_get_by_id_uses_network_in_url(mocker, mixshow_payload):
    mocker.patch("addictune.api._helpers.cache.get_etag", return_value=(None, None))
    mocker.patch("addictune.api._helpers.cache.get_indexed", return_value=None)
    mocker.patch("addictune.api._helpers.cache.set_etag")

    mock_client = mocker.AsyncMock(spec=httpx.AsyncClient)
    mock_client.get.return_value = make_response(200, mixshow_payload)

    api = MixShowsAPI(mock_client, network="rockradio")
    await api.get_by_id(123)

    call_url = mock_client.get.call_args[0][0]
    assert call_url == "/rockradio/shows/123"


# ── iter_shows ───────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_iter_shows_returns_shows(mocker, mixshows_list_payload):
    # Extract the items from the envelope for mocking _fetch_page
    items = mixshows_list_payload["results"]
    mocker.patch(
        "addictune.api._helpers._fetch_page",
        return_value=(items, 1),  # (items, total_pages)
    )

    mock_client = mocker.AsyncMock(spec=httpx.AsyncClient)

    api = MixShowsAPI(mock_client, network="di")
    results = [show async for show in api.iter_shows()]

    assert len(results) == 2
    assert all(isinstance(s, MixShow) for s in results)
    assert results[0].id == 123
    assert results[0].name == "Global Trance Sounds"
    assert results[1].id == 456
    assert results[1].name == "Techno Sessions"


@pytest.mark.asyncio
async def test_iter_shows_passes_unwrap_key(mocker, mixshows_list_payload):
    items = mixshows_list_payload["results"]
    mock_fetch = mocker.patch(
        "addictune.api._helpers._fetch_page",
        return_value=(items, 1),
    )

    mock_client = mocker.AsyncMock(spec=httpx.AsyncClient)

    api = MixShowsAPI(mock_client, network="di")
    _ = [show async for show in api.iter_shows()]

    # Verify _fetch_page was called with unwrap_key="results"
    call_kwargs = mock_fetch.call_args[1]
    assert call_kwargs["unwrap_key"] == "results"


@pytest.mark.asyncio
async def test_iter_shows_passes_active_param(mocker, mixshows_list_payload):
    items = mixshows_list_payload["results"]
    mock_fetch = mocker.patch(
        "addictune.api._helpers._fetch_page",
        return_value=(items, 1),
    )

    mock_client = mocker.AsyncMock(spec=httpx.AsyncClient)

    api = MixShowsAPI(mock_client, network="di")
    _ = [show async for show in api.iter_shows(active=False)]

    call_params = mock_fetch.call_args[1]["params"]
    assert call_params["active"] == "false"


# ── iter_episodes ────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_iter_episodes_returns_episodes(mocker, show_episodes_payload):
    mocker.patch(
        "addictune.api._helpers._fetch_page",
        return_value=(show_episodes_payload, 1),
    )

    mock_client = mocker.AsyncMock(spec=httpx.AsyncClient)

    api = MixShowsAPI(mock_client, network="di")
    results = [ep async for ep in api.iter_episodes(show_id=123)]

    assert len(results) == 2
    assert all(isinstance(ep, ShowEpisode) for ep in results)
    assert results[0].id == 789
    assert results[0].name == "Global Trance Sounds Episode 52"
    assert results[0].free is False
    assert results[0].show is not None
    assert results[0].show.id == 123
    assert len(results[0].tracks) == 2
    assert results[1].id == 790
    assert results[1].free is True


@pytest.mark.asyncio
async def test_iter_episodes_uses_show_id_in_url(mocker, show_episodes_payload):
    mock_fetch = mocker.patch(
        "addictune.api._helpers._fetch_page",
        return_value=(show_episodes_payload, 1),
    )

    mock_client = mocker.AsyncMock(spec=httpx.AsyncClient)

    api = MixShowsAPI(mock_client, network="di")
    _ = [ep async for ep in api.iter_episodes(show_id=999)]

    call_url = mock_fetch.call_args[0][1]
    assert call_url == "/di/shows/999/episodes"


# ── get_upcoming ──────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_upcoming_returns_episodes(mocker, upcoming_episodes_payload):
    mock_client = mocker.AsyncMock(spec=httpx.AsyncClient)
    mock_client.get.return_value = make_response(200, upcoming_episodes_payload)

    api = MixShowsAPI(mock_client, network="di")
    result = await api.get_upcoming()

    assert len(result) == 2
    assert all(isinstance(ep, ShowEpisode) for ep in result)
    assert result[0].id == 801
    assert result[0].name == "Upcoming Show Episode 1"
    assert result[0].free is True
    assert result[1].id == 802
    assert result[1].free is False


@pytest.mark.asyncio
async def test_get_upcoming_passes_limit_param(mocker, upcoming_episodes_payload):
    mock_client = mocker.AsyncMock(spec=httpx.AsyncClient)
    mock_client.get.return_value = make_response(200, upcoming_episodes_payload)

    api = MixShowsAPI(mock_client, network="di")
    await api.get_upcoming(limit=50)

    call_params = mock_client.get.call_args[1]["params"]
    assert call_params == {"limit": 50}


@pytest.mark.asyncio
async def test_get_upcoming_uses_network_in_url(mocker, upcoming_episodes_payload):
    mock_client = mocker.AsyncMock(spec=httpx.AsyncClient)
    mock_client.get.return_value = make_response(200, upcoming_episodes_payload)

    api = MixShowsAPI(mock_client, network="rockradio")
    await api.get_upcoming()

    call_url = mock_client.get.call_args[0][0]
    assert call_url == "/rockradio/events/upcoming"


@pytest.mark.asyncio
async def test_get_upcoming_raises_on_error(mocker):
    mock_client = mocker.AsyncMock(spec=httpx.AsyncClient)
    mock_client.get.return_value = make_response(500, text="Internal Server Error")

    api = MixShowsAPI(mock_client, network="di")
    with pytest.raises(AddictuneAPIError):
        await api.get_upcoming()


# ── iter_followed ────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_iter_followed_returns_shows(mocker, mixshows_list_payload):
    items = mixshows_list_payload["results"]
    mocker.patch(
        "addictune.api._helpers._fetch_page",
        return_value=(items, 1),
    )

    mock_client = mocker.AsyncMock(spec=httpx.AsyncClient)

    api = MixShowsAPI(mock_client, network="di")
    results = [show async for show in api.iter_followed(user_id=13716939)]

    assert len(results) == 2
    assert all(isinstance(s, MixShow) for s in results)
    assert results[0].id == 123
    assert results[1].id == 456


@pytest.mark.asyncio
async def test_iter_followed_uses_user_id_in_url(mocker, mixshows_list_payload):
    items = mixshows_list_payload["results"]
    mock_fetch = mocker.patch(
        "addictune.api._helpers._fetch_page",
        return_value=(items, 1),
    )

    mock_client = mocker.AsyncMock(spec=httpx.AsyncClient)

    api = MixShowsAPI(mock_client, network="di")
    _ = [show async for show in api.iter_followed(user_id=99999)]

    call_url = mock_fetch.call_args[0][1]
    assert call_url == "/di/members/99999/followed_items/show"


@pytest.mark.asyncio
async def test_iter_followed_passes_active_param(mocker, mixshows_list_payload):
    items = mixshows_list_payload["results"]
    mock_fetch = mocker.patch(
        "addictune.api._helpers._fetch_page",
        return_value=(items, 1),
    )

    mock_client = mocker.AsyncMock(spec=httpx.AsyncClient)

    api = MixShowsAPI(mock_client, network="di")
    _ = [show async for show in api.iter_followed(user_id=13716939, active=False)]

    call_params = mock_fetch.call_args[1]["params"]
    assert call_params["active"] == "false"
