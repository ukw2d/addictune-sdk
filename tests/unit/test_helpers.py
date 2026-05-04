import httpx
import pytest

from addictune.api._helpers import cached_get_list, cached_get_object
from addictune.models.channel import Channel, LikedChannelID
from tests.conftest import make_response

# ── cached_get_list ──────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_cached_get_list_fresh_response(mocker):
    mocker.patch("addictune.api._helpers.cache.get_etag", return_value=(None, None))
    mocker.patch("addictune.api._helpers.cache.set_etag")

    payload = [{"id": 1, "key": "trance", "name": "Trance", "network_id": 1}]
    mock_client = mocker.AsyncMock(spec=httpx.AsyncClient)
    mock_client.get.return_value = make_response(200, payload)

    result = await cached_get_list(mock_client, "/di/channels", Channel)

    assert len(result) == 1
    assert result[0].key == "trance"


@pytest.mark.asyncio
async def test_cached_get_list_304_returns_cached(mocker):
    cached = [{"id": 1, "key": "trance", "name": "Trance", "network_id": 1}]
    mocker.patch("addictune.api._helpers.cache.get_etag", return_value=('"v1"', cached))

    mock_client = mocker.AsyncMock(spec=httpx.AsyncClient)
    mock_client.get.return_value = make_response(304)

    result = await cached_get_list(mock_client, "/di/channels", Channel)

    assert len(result) == 1
    assert result[0].key == "trance"
    # Verify If-None-Match was sent
    call_headers = mock_client.get.call_args[1]["headers"]
    assert call_headers["If-None-Match"] == '"v1"'


@pytest.mark.asyncio
async def test_cached_get_list_stores_etag(mocker):
    mocker.patch("addictune.api._helpers.cache.get_etag", return_value=(None, None))
    mock_set_etag = mocker.patch("addictune.api._helpers.cache.set_etag")

    payload = [{"channel_id": 1, "position": 0}]
    mock_client = mocker.AsyncMock(spec=httpx.AsyncClient)
    mock_client.get.return_value = make_response(
        200, payload, headers={"etag": '"e1"', "cache-control": "max-age=60"}
    )

    result = await cached_get_list(mock_client, "/di/favs", LikedChannelID)

    assert result[0].channel_id == 1
    mock_set_etag.assert_called_once_with("/di/favs", '"e1"', payload, ttl=60)


@pytest.mark.asyncio
async def test_cached_get_list_no_etag_skips_cache_write(mocker):
    mocker.patch("addictune.api._helpers.cache.get_etag", return_value=(None, None))
    mock_set_etag = mocker.patch("addictune.api._helpers.cache.set_etag")

    payload = [{"id": 1, "key": "trance", "name": "Trance", "network_id": 1}]
    mock_client = mocker.AsyncMock(spec=httpx.AsyncClient)
    mock_client.get.return_value = make_response(200, payload)

    result = await cached_get_list(mock_client, "/di/channels", Channel)

    assert len(result) == 1
    mock_set_etag.assert_not_called()


# ── cached_get_object ────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_cached_get_object_fresh_response(mocker, channel_payload):
    mocker.patch("addictune.api._helpers.cache.get_etag", return_value=(None, None))
    mocker.patch("addictune.api._helpers.cache.set_etag")

    mock_client = mocker.AsyncMock(spec=httpx.AsyncClient)
    mock_client.get.return_value = make_response(200, channel_payload)

    result = await cached_get_object(mock_client, "/di/channels/1", Channel)

    assert isinstance(result, Channel)
    assert result.key == "trance"


@pytest.mark.asyncio
async def test_cached_get_object_304_returns_cached(mocker, channel_payload):
    mocker.patch(
        "addictune.api._helpers.cache.get_etag",
        return_value=('"v1"', channel_payload),
    )

    mock_client = mocker.AsyncMock(spec=httpx.AsyncClient)
    mock_client.get.return_value = make_response(304)

    result = await cached_get_object(mock_client, "/di/channels/1", Channel)

    assert result.key == "trance"


# ── list→object index caching ────────────────────────────────────────


@pytest.mark.asyncio
async def test_cached_get_list_indexes_items_when_id_field_given(mocker):
    mocker.patch("addictune.api._helpers.cache.get_etag", return_value=(None, None))
    mocker.patch("addictune.api._helpers.cache.set_etag")
    mock_index = mocker.patch("addictune.api._helpers.cache.index_list")

    payload = [{"id": 1, "key": "trance", "name": "Trance", "network_id": 1}]
    mock_client = mocker.AsyncMock(spec=httpx.AsyncClient)
    mock_client.get.return_value = make_response(
        200, payload, headers={"etag": '"e1"', "cache-control": "max-age=300"}
    )

    await cached_get_list(mock_client, "/di/channels", Channel, id_field="id")

    mock_index.assert_called_once_with("/di/channels", payload, id_field="id", ttl=300)


@pytest.mark.asyncio
async def test_cached_get_list_skips_index_when_no_id_field(mocker):
    mocker.patch("addictune.api._helpers.cache.get_etag", return_value=(None, None))
    mocker.patch("addictune.api._helpers.cache.set_etag")
    mock_index = mocker.patch("addictune.api._helpers.cache.index_list")

    payload = [{"id": 1, "key": "trance", "name": "Trance", "network_id": 1}]
    mock_client = mocker.AsyncMock(spec=httpx.AsyncClient)
    mock_client.get.return_value = make_response(
        200, payload, headers={"etag": '"e1"', "cache-control": "max-age=300"}
    )

    await cached_get_list(mock_client, "/di/channels", Channel)

    mock_index.assert_not_called()


@pytest.mark.asyncio
async def test_cached_get_object_uses_index_before_http(mocker):
    indexed_data = {"id": 1, "key": "trance", "name": "Trance", "network_id": 1}
    mocker.patch("addictune.api._helpers.cache.get_indexed", return_value=indexed_data)
    mock_get_etag = mocker.patch("addictune.api._helpers.cache.get_etag")

    mock_client = mocker.AsyncMock(spec=httpx.AsyncClient)

    result = await cached_get_object(
        mock_client, "/di/channels/1", Channel, index_key="/di/channels/id=1"
    )

    assert isinstance(result, Channel)
    assert result.key == "trance"
    # No HTTP call made
    mock_client.get.assert_not_called()
    mock_get_etag.assert_not_called()


@pytest.mark.asyncio
async def test_cached_get_object_falls_back_when_index_miss(mocker):
    mocker.patch("addictune.api._helpers.cache.get_indexed", return_value=None)
    mocker.patch("addictune.api._helpers.cache.get_etag", return_value=(None, None))
    mocker.patch("addictune.api._helpers.cache.set_etag")

    payload = {"id": 1, "key": "trance", "name": "Trance", "network_id": 1}
    mock_client = mocker.AsyncMock(spec=httpx.AsyncClient)
    mock_client.get.return_value = make_response(200, payload)

    result = await cached_get_object(
        mock_client, "/di/channels/1", Channel, index_key="/di/channels/id=1"
    )

    assert result.key == "trance"
    mock_client.get.assert_called_once()
