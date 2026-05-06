import httpx
import pytest

from addictune_sdk.api.channels import ChannelsAPI
from addictune_sdk.exceptions import (
    AddictuneAPIError,
    AddictuneAuthError,
    AddictuneNotFoundError,
)
from addictune_sdk.models.channel import (
    Channel,
    LikedChannelID,
    ListenHistoryEntry,
    NowPlaying,
    TrackHistoryEntry,
)
from addictune_sdk.models.track import ChannelTracklist
from tests.conftest import make_response

# ── get_all ──────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_all_returns_channel_list(mocker, channels_response, channels_list):
    mocker.patch("addictune_sdk.api._helpers.cache.get_etag", return_value=(None, None))
    mocker.patch("addictune_sdk.api._helpers.cache.set_etag")

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
    mocker.patch("addictune_sdk.api._helpers.cache.get_etag", return_value=(None, None))
    mocker.patch("addictune_sdk.api._helpers.cache.set_etag")

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
    mocker.patch("addictune_sdk.api._helpers.cache.get_etag", return_value=(None, None))
    mock_set_etag = mocker.patch("addictune_sdk.api._helpers.cache.set_etag")

    mock_client = mocker.AsyncMock(spec=httpx.AsyncClient)
    mock_client.get.return_value = channels_response

    api = ChannelsAPI(mock_client, network="di")
    await api.get_all()

    mock_set_etag.assert_called_once_with(
        "/di/channels", '"abc123"', channels_list, ttl=300
    )


@pytest.mark.asyncio
async def test_get_all_sends_if_none_match_when_etag_cached(mocker, channels_response):
    mocker.patch("addictune_sdk.api._helpers.cache.get_etag", return_value=('"abc123"', []))
    mocker.patch("addictune_sdk.api._helpers.cache.set_etag")

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
        "addictune_sdk.api._helpers.cache.get_etag", return_value=('"abc123"', cached)
    )

    mock_client = mocker.AsyncMock(spec=httpx.AsyncClient)
    mock_client.get.return_value = make_response(304)

    api = ChannelsAPI(mock_client, network="di")
    result = await api.get_all()

    assert len(result) == 1
    assert result[0].key == channel_payload["key"]


@pytest.mark.asyncio
async def test_get_all_no_etag_header_skips_cache_write(mocker, channels_list):
    mocker.patch("addictune_sdk.api._helpers.cache.get_etag", return_value=(None, None))
    mock_set_etag = mocker.patch("addictune_sdk.api._helpers.cache.set_etag")

    mock_client = mocker.AsyncMock(spec=httpx.AsyncClient)
    mock_client.get.return_value = make_response(200, channels_list)

    api = ChannelsAPI(mock_client, network="di")
    await api.get_all()

    mock_set_etag.assert_not_called()


@pytest.mark.asyncio
async def test_get_all_raises_on_server_error(mocker):
    mocker.patch("addictune_sdk.api._helpers.cache.get_etag", return_value=(None, None))

    mock_client = mocker.AsyncMock(spec=httpx.AsyncClient)
    mock_client.get.return_value = make_response(500, text="Server Error")

    api = ChannelsAPI(mock_client, network="di")
    with pytest.raises(AddictuneAPIError):
        await api.get_all()


@pytest.mark.asyncio
async def test_get_all_raises_not_found(mocker):
    mocker.patch("addictune_sdk.api._helpers.cache.get_etag", return_value=(None, None))

    mock_client = mocker.AsyncMock(spec=httpx.AsyncClient)
    mock_client.get.return_value = make_response(404, text="Not Found")

    api = ChannelsAPI(mock_client, network="di")
    with pytest.raises(AddictuneNotFoundError):
        await api.get_all()


@pytest.mark.asyncio
async def test_get_all_channel_extra_fields_ignored(mocker):
    """Channel model has extra='ignore'; unknown fields from API should not raise."""
    mocker.patch("addictune_sdk.api._helpers.cache.get_etag", return_value=(None, None))
    mocker.patch("addictune_sdk.api._helpers.cache.set_etag")

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


# ── get_by_id ────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_by_id_returns_channel(mocker, channel_payload):
    mocker.patch("addictune_sdk.api._helpers.cache.get_etag", return_value=(None, None))
    mocker.patch("addictune_sdk.api._helpers.cache.get_indexed", return_value=None)
    mocker.patch("addictune_sdk.api._helpers.cache.set_etag")

    mock_client = mocker.AsyncMock(spec=httpx.AsyncClient)
    mock_client.get.return_value = make_response(200, channel_payload)

    api = ChannelsAPI(mock_client, network="di")
    result = await api.get_by_id(1)

    assert isinstance(result, Channel)
    assert result.key == "trance"
    mock_client.get.assert_called_once_with("/di/channels/1", headers={})


@pytest.mark.asyncio
async def test_get_by_id_uses_etag_cache(mocker, channel_payload):
    mocker.patch(
        "addictune_sdk.api._helpers.cache.get_etag",
        return_value=('"v1"', channel_payload),
    )
    mocker.patch("addictune_sdk.api._helpers.cache.get_indexed", return_value=None)
    mocker.patch("addictune_sdk.api._helpers.cache.set_etag")

    mock_client = mocker.AsyncMock(spec=httpx.AsyncClient)
    mock_client.get.return_value = make_response(304)

    api = ChannelsAPI(mock_client, network="di")
    result = await api.get_by_id(1)

    assert result.key == "trance"
    call_headers = mock_client.get.call_args[1]["headers"]
    assert call_headers["If-None-Match"] == '"v1"'


# ── get_track_history ────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_track_history_returns_entries(mocker, track_history_payload):
    mocker.patch("addictune_sdk.api._helpers.cache.get_etag", return_value=(None, None))
    mocker.patch("addictune_sdk.api._helpers.cache.set_etag")

    mock_client = mocker.AsyncMock(spec=httpx.AsyncClient)
    mock_client.get.return_value = make_response(200, track_history_payload)

    api = ChannelsAPI(mock_client, network="di")
    result = await api.get_track_history(1)

    assert len(result) == 1
    assert isinstance(result[0], TrackHistoryEntry)
    assert result[0].track_id == 3153063
    assert result[0].votes.up == 7
    assert result[0].votes.down == 1
    mock_client.get.assert_called_once_with("/di/track_history/channel/1", headers={})


# ── get_currently_playing ────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_currently_playing_returns_entries(mocker, now_playing_payload):
    mocker.patch("addictune_sdk.api._helpers.cache.get_etag", return_value=(None, None))
    mocker.patch("addictune_sdk.api._helpers.cache.set_etag")

    mock_client = mocker.AsyncMock(spec=httpx.AsyncClient)
    mock_client.get.return_value = make_response(200, now_playing_payload)

    api = ChannelsAPI(mock_client, network="di")
    result = await api.get_currently_playing()

    assert len(result) == 2
    assert isinstance(result[0], NowPlaying)
    assert result[0].channel_id == 324
    assert result[0].channel_key == "00sclubhits"
    assert result[0].track.display_title == "Call on Me (Filterheadz Remix)"


# ── get_routine ──────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_routine_returns_routine(mocker):
    routine_data = {
        "routine_id": 99,
        "channel_id": 1,
        "expires_on": "2026-05-04T07:48:11-04:00",
        "tracks": [
            {
                "id": 79159,
                "title": "Test Track",
                "content_format_id": 5,
                "content_quality_id": 3,
            }
        ],
    }
    mock_client = mocker.AsyncMock(spec=httpx.AsyncClient)
    mock_client.get.return_value = make_response(200, routine_data)

    api = ChannelsAPI(mock_client, network="di")
    result = await api.get_routine(1, audio_token="abc123")

    assert isinstance(result, ChannelTracklist)
    assert result.routine_id == 99
    assert result.channel_id == 1
    assert len(result.tracks) == 1
    assert result.tracks[0].title == "Test Track"

    call_params = mock_client.get.call_args[1]["params"]
    assert call_params["audio_token"] == "abc123"
    assert call_params["tune_in"] == "true"


# ── add_listen_history ───────────────────────────────────────────────


@pytest.mark.asyncio
async def test_add_listen_history_succeeds(mocker):
    mock_client = mocker.AsyncMock(spec=httpx.AsyncClient)
    mock_client.post.return_value = make_response(201)

    api = ChannelsAPI(mock_client, network="di")
    await api.add_listen_history(channel_id=1, track_id=42)

    mock_client.post.assert_called_once_with(
        "/di/listen_history",
        json={"channel_id": 1, "track_id": 42},
    )


@pytest.mark.asyncio
async def test_add_listen_history_raises_on_error(mocker):
    mock_client = mocker.AsyncMock(spec=httpx.AsyncClient)
    mock_client.post.return_value = make_response(500, text="Server Error")

    api = ChannelsAPI(mock_client, network="di")
    with pytest.raises(AddictuneAPIError):
        await api.add_listen_history(channel_id=1, track_id=42)


# ── get_listen_history ───────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_listen_history_returns_list(mocker):
    history_data = [
        {"track": {"id": 1, "title": "Foo"}, "played_at": "2026-01-01T00:00:00Z"}
    ]
    mock_client = mocker.AsyncMock(spec=httpx.AsyncClient)
    mock_client.get.return_value = make_response(200, history_data)

    api = ChannelsAPI(mock_client, network="di")
    result = await api.get_listen_history(1)

    assert len(result) == 1
    assert isinstance(result[0], ListenHistoryEntry)
    assert result[0].track.id == 1
    assert result[0].played_at == "2026-01-01T00:00:00Z"
    mock_client.get.assert_called_once_with("/di/listen_history/1")


# ── get_favorites ────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_favorites_returns_liked_channels(mocker, favorites_payload):
    mocker.patch("addictune_sdk.api._helpers.cache.get_etag", return_value=(None, None))
    mocker.patch("addictune_sdk.api._helpers.cache.set_etag")

    mock_client = mocker.AsyncMock(spec=httpx.AsyncClient)
    mock_client.get.return_value = make_response(200, favorites_payload)

    api = ChannelsAPI(mock_client, network="di")
    result = await api.get_favorites(user_id=13716939)

    assert len(result) == 3
    assert isinstance(result[0], LikedChannelID)
    assert result[0].channel_id == 522
    mock_client.get.assert_called_once_with(
        "/di/members/13716939/favorites/channels", headers={}
    )


@pytest.mark.asyncio
async def test_get_favorites_uses_etag_cache(mocker, favorites_payload):
    mocker.patch(
        "addictune_sdk.api._helpers.cache.get_etag",
        return_value=('"fav1"', favorites_payload),
    )
    mocker.patch("addictune_sdk.api._helpers.cache.set_etag")

    mock_client = mocker.AsyncMock(spec=httpx.AsyncClient)
    mock_client.get.return_value = make_response(304)

    api = ChannelsAPI(mock_client, network="di")
    result = await api.get_favorites(user_id=13716939)

    assert len(result) == 3
    assert result[0].channel_id == 522


# ── add_favorite ─────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_add_favorite_succeeds(mocker):
    mock_client = mocker.AsyncMock(spec=httpx.AsyncClient)
    mock_client.post.return_value = make_response(204)

    api = ChannelsAPI(mock_client, network="di")
    await api.add_favorite(user_id=13716939, channel_id=1)

    mock_client.post.assert_called_once_with(
        "/di/members/13716939/favorites/channel/1",
        json={"id": 1},
    )


@pytest.mark.asyncio
async def test_add_favorite_raises_on_error(mocker):
    mock_client = mocker.AsyncMock(spec=httpx.AsyncClient)
    mock_client.post.return_value = make_response(401, text="Unauthorized")

    api = ChannelsAPI(mock_client, network="di")
    with pytest.raises(AddictuneAuthError):
        await api.add_favorite(user_id=13716939, channel_id=1)


# ── remove_favorite ──────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_remove_favorite_succeeds(mocker):
    mock_client = mocker.AsyncMock(spec=httpx.AsyncClient)
    mock_client.delete.return_value = make_response(200)

    api = ChannelsAPI(mock_client, network="di")
    await api.remove_favorite(user_id=13716939, channel_id=1)

    mock_client.delete.assert_called_once_with(
        "/di/members/13716939/favorites/channel/1"
    )


@pytest.mark.asyncio
async def test_remove_favorite_raises_on_error(mocker):
    mock_client = mocker.AsyncMock(spec=httpx.AsyncClient)
    mock_client.delete.return_value = make_response(404, text="Not Found")

    api = ChannelsAPI(mock_client, network="di")
    with pytest.raises(AddictuneNotFoundError):
        await api.remove_favorite(user_id=13716939, channel_id=999)


# ── get_favorite ──────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_favorite_returns_liked_channel(mocker):
    payload = {"channel_id": 1, "position": 0}
    mock_client = mocker.AsyncMock(spec=httpx.AsyncClient)
    mock_client.get.return_value = make_response(200, payload)

    api = ChannelsAPI(mock_client, network="di")
    result = await api.get_favorite(user_id=13716939, channel_id=1)

    assert isinstance(result, LikedChannelID)
    assert result.channel_id == 1
    assert result.position == 0
    mock_client.get.assert_called_once_with("/di/members/13716939/favorites/channel/1")


@pytest.mark.asyncio
async def test_get_favorite_returns_none_on_404(mocker):
    mock_client = mocker.AsyncMock(spec=httpx.AsyncClient)
    mock_client.get.return_value = make_response(404, text="Not Found")

    api = ChannelsAPI(mock_client, network="di")
    result = await api.get_favorite(user_id=13716939, channel_id=999)

    assert result is None


@pytest.mark.asyncio
async def test_get_favorite_returns_none_on_empty_response(mocker):
    mock_client = mocker.AsyncMock(spec=httpx.AsyncClient)
    mock_client.get.return_value = make_response(200, [])

    api = ChannelsAPI(mock_client, network="di")
    result = await api.get_favorite(user_id=13716939, channel_id=999)

    assert result is None


@pytest.mark.asyncio
async def test_get_favorite_handles_list_response(mocker):
    payload = [{"channel_id": 1, "position": 0}]
    mock_client = mocker.AsyncMock(spec=httpx.AsyncClient)
    mock_client.get.return_value = make_response(200, payload)

    api = ChannelsAPI(mock_client, network="di")
    result = await api.get_favorite(user_id=13716939, channel_id=1)

    assert isinstance(result, LikedChannelID)
    assert result.channel_id == 1


# ── get_stream_url ────────────────────────────────────────────────────


def test_get_stream_url_di_hi(mocker):
    api = ChannelsAPI(
        mocker.AsyncMock(),
        network="di",
        listen_base="http://prem2.di.fm:80",
        stream_suffixes={"hi": "_hi", "aac": ""},
    )
    assert (
        api.get_stream_url("progressive", "abc123", quality="hi")
        == "http://prem2.di.fm:80/progressive_hi?abc123"
    )


def test_get_stream_url_di_aac(mocker):
    api = ChannelsAPI(
        mocker.AsyncMock(),
        network="di",
        listen_base="http://prem2.di.fm:80",
        stream_suffixes={"hi": "_hi", "aac": ""},
    )
    assert (
        api.get_stream_url("progressive", "abc123", quality="aac")
        == "http://prem2.di.fm:80/progressive?abc123"
    )


def test_get_stream_url_rockradio_hi(mocker):
    api = ChannelsAPI(
        mocker.AsyncMock(),
        network="rockradio",
        listen_base="http://prem2.rockradio.com:80",
        stream_suffixes={"hi": "", "aac": "_aac"},
    )
    assert (
        api.get_stream_url("classichardrock", "key99", quality="hi")
        == "http://prem2.rockradio.com:80/classichardrock?key99"
    )


def test_get_stream_url_rockradio_aac(mocker):
    api = ChannelsAPI(
        mocker.AsyncMock(),
        network="rockradio",
        listen_base="http://prem2.rockradio.com:80",
        stream_suffixes={"hi": "", "aac": "_aac"},
    )
    assert (
        api.get_stream_url("classichardrock", "key99", quality="aac")
        == "http://prem2.rockradio.com:80/classichardrock_aac?key99"
    )


def test_get_stream_url_default_quality_is_hi(mocker):
    api = ChannelsAPI(
        mocker.AsyncMock(),
        network="di",
        listen_base="http://prem2.di.fm:80",
        stream_suffixes={"hi": "_hi", "aac": ""},
    )
    # Default quality is "hi"
    assert (
        api.get_stream_url("trance", "abc123")
        == "http://prem2.di.fm:80/trance_hi?abc123"
    )


def test_get_stream_url_unknown_quality_uses_empty_suffix(mocker):
    api = ChannelsAPI(
        mocker.AsyncMock(),
        network="di",
        listen_base="http://prem2.di.fm:80",
        stream_suffixes={"hi": "_hi", "aac": ""},
    )
    assert (
        api.get_stream_url("trance", "abc123", quality="unknown")
        == "http://prem2.di.fm:80/trance?abc123"
    )
