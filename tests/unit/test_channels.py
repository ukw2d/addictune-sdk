import httpx
import pytest

from addictune.api.channels import ChannelsAPI
from addictune.exceptions import AddictuneAPIError, AddictuneNotFoundError
from addictune.models.channel import Channel
from tests.conftest import make_response


@pytest.mark.asyncio
async def test_get_all_returns_channel_list(mocker, channels_response, channels_list):
    mocker.patch("addictune.api.channels.cache.get_etag", return_value=(None, None))
    mocker.patch("addictune.api.channels.cache.set_etag")

    mock_client = mocker.AsyncMock(spec=httpx.AsyncClient)
    mock_client.get.return_value = channels_response

    api = ChannelsAPI(mock_client, network="di")
    result = await api.get_all()

    assert len(result) == len(channels_list)
    assert all(isinstance(ch, Channel) for ch in result)
    assert result[0].key == "trance"
    assert result[1].key == "house"


@pytest.mark.asyncio
async def test_get_all_uses_network_in_url(mocker, channels_response):
    mocker.patch("addictune.api.channels.cache.get_etag", return_value=(None, None))
    mocker.patch("addictune.api.channels.cache.set_etag")

    mock_client = mocker.AsyncMock(spec=httpx.AsyncClient)
    mock_client.get.return_value = channels_response

    api = ChannelsAPI(mock_client, network="rockradio")
    await api.get_all()

    call_url = mock_client.get.call_args[0][0]
    assert call_url == "/rockradio/channels"


@pytest.mark.asyncio
async def test_get_all_stores_etag_when_present(
    mocker, channels_response, channels_list
):
    mocker.patch("addictune.api.channels.cache.get_etag", return_value=(None, None))
    mock_set_etag = mocker.patch("addictune.api.channels.cache.set_etag")

    mock_client = mocker.AsyncMock(spec=httpx.AsyncClient)
    mock_client.get.return_value = channels_response

    api = ChannelsAPI(mock_client, network="di")
    await api.get_all()

    mock_set_etag.assert_called_once_with(
        "/di/channels", '"abc123"', channels_list, ttl=300
    )


@pytest.mark.asyncio
async def test_get_all_sends_if_none_match_when_etag_cached(mocker, channels_response):
    mocker.patch("addictune.api.channels.cache.get_etag", return_value=('"abc123"', []))
    mocker.patch("addictune.api.channels.cache.set_etag")

    mock_client = mocker.AsyncMock(spec=httpx.AsyncClient)
    mock_client.get.return_value = channels_response

    api = ChannelsAPI(mock_client, network="di")
    await api.get_all()

    call_headers = mock_client.get.call_args[1]["headers"]
    assert call_headers.get("If-None-Match") == '"abc123"'


@pytest.mark.asyncio
async def test_get_all_returns_cached_data_on_304(mocker, channel_payload):
    cached = [channel_payload]
    mocker.patch(
        "addictune.api.channels.cache.get_etag", return_value=('"abc123"', cached)
    )

    mock_client = mocker.AsyncMock(spec=httpx.AsyncClient)
    mock_client.get.return_value = make_response(304)

    api = ChannelsAPI(mock_client, network="di")
    result = await api.get_all()

    assert len(result) == 1
    assert result[0].key == channel_payload["key"]


@pytest.mark.asyncio
async def test_get_all_no_etag_header_skips_cache_write(mocker, channels_list):
    mocker.patch("addictune.api.channels.cache.get_etag", return_value=(None, None))
    mock_set_etag = mocker.patch("addictune.api.channels.cache.set_etag")

    mock_client = mocker.AsyncMock(spec=httpx.AsyncClient)
    mock_client.get.return_value = make_response(200, channels_list)

    api = ChannelsAPI(mock_client, network="di")
    await api.get_all()

    mock_set_etag.assert_not_called()


@pytest.mark.asyncio
async def test_get_all_raises_on_server_error(mocker):
    mocker.patch("addictune.api.channels.cache.get_etag", return_value=(None, None))

    mock_client = mocker.AsyncMock(spec=httpx.AsyncClient)
    mock_client.get.return_value = make_response(500, text="Server Error")

    api = ChannelsAPI(mock_client, network="di")
    with pytest.raises(AddictuneAPIError):
        await api.get_all()


@pytest.mark.asyncio
async def test_get_all_raises_not_found(mocker):
    mocker.patch("addictune.api.channels.cache.get_etag", return_value=(None, None))

    mock_client = mocker.AsyncMock(spec=httpx.AsyncClient)
    mock_client.get.return_value = make_response(404, text="Not Found")

    api = ChannelsAPI(mock_client, network="di")
    with pytest.raises(AddictuneNotFoundError):
        await api.get_all()


@pytest.mark.asyncio
async def test_get_all_channel_extra_fields_ignored(mocker):
    """Channel model has extra='ignore'; unknown fields from API should not raise."""
    mocker.patch("addictune.api.channels.cache.get_etag", return_value=(None, None))
    mocker.patch("addictune.api.channels.cache.set_etag")

    payload = [
        {
            "id": 3,
            "key": "ambient",
            "name": "Ambient",
            "network_id": 1,
            "unknown_field": "surprise",
        }
    ]
    mock_client = mocker.AsyncMock(spec=httpx.AsyncClient)
    mock_client.get.return_value = make_response(200, payload)

    api = ChannelsAPI(mock_client, network="di")
    result = await api.get_all()

    assert result[0].name == "Ambient"
    assert not hasattr(result[0], "unknown_field")
