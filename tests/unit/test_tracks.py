import httpx
import pytest

from addictune_sdk.api.tracks import TracksAPI
from addictune_sdk.exceptions import AddictuneAPIError, AddictuneNotFoundError
from addictune_sdk.models.track import (
    AudioQuality,
    CurrentAudioQuality,
    Track,
)
from tests.conftest import make_response

# ── get_qualities ────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_qualities_returns_list(mocker, qualities_payload):
    mocker.patch("addictune_sdk.api._helpers.cache.get_etag", return_value=(None, None))
    mocker.patch("addictune_sdk.api._helpers.cache.set_etag")

    mock_client = mocker.AsyncMock(spec=httpx.AsyncClient)
    mock_client.get.return_value = make_response(
        200,
        qualities_payload,
        headers={"etag": '"q1"', "cache-control": "max-age=300", "age": "0"},
    )

    api = TracksAPI(mock_client, network="di")
    result = await api.get_qualities()

    assert len(result) == 3
    assert all(isinstance(q, AudioQuality) for q in result)
    assert result[0].key == "high"
    assert result[0].premium_only is True
    assert result[2].default is True
    assert result[0].content_quality.kilo_bitrate == 320


@pytest.mark.asyncio
async def test_get_qualities_uses_network_in_url(mocker, qualities_payload):
    mocker.patch("addictune_sdk.api._helpers.cache.get_etag", return_value=(None, None))
    mocker.patch("addictune_sdk.api._helpers.cache.set_etag")

    mock_client = mocker.AsyncMock(spec=httpx.AsyncClient)
    mock_client.get.return_value = make_response(200, qualities_payload)

    api = TracksAPI(mock_client, network="rockradio")
    await api.get_qualities()

    call_url = mock_client.get.call_args[0][0]
    assert call_url == "/rockradio/qualities"


# ── get_preferred_quality ────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_preferred_quality_returns_model(mocker, preferred_quality_payload):
    mocker.patch("addictune_sdk.api._helpers.cache.get_etag", return_value=(None, None))
    mocker.patch("addictune_sdk.api._helpers.cache.set_etag")

    mock_client = mocker.AsyncMock(spec=httpx.AsyncClient)
    mock_client.get.return_value = make_response(200, preferred_quality_payload)

    api = TracksAPI(mock_client, network="di")
    result = await api.get_preferred_quality(user_id=13716939)

    assert isinstance(result, CurrentAudioQuality)
    assert result.quality_id == 1
    assert result.member_id == 13716939
    mock_client.get.assert_called_once_with(
        "/di/members/13716939/preferred_quality", headers={}
    )


# ── set_preferred_quality ────────────────────────────────────────────


@pytest.mark.asyncio
async def test_set_preferred_quality_succeeds(mocker):
    mock_client = mocker.AsyncMock(spec=httpx.AsyncClient)
    mock_client.post.return_value = make_response(200)

    api = TracksAPI(mock_client, network="di")
    await api.set_preferred_quality(user_id=13716939, quality_id=1)

    mock_client.post.assert_called_once_with(
        "/di/members/13716939/preferred_quality",
        content="quality_id=1",
    )


@pytest.mark.asyncio
async def test_set_preferred_quality_raises_on_error(mocker):
    mock_client = mocker.AsyncMock(spec=httpx.AsyncClient)
    mock_client.post.return_value = make_response(500, text="Server Error")

    api = TracksAPI(mock_client, network="di")
    with pytest.raises(AddictuneAPIError):
        await api.set_preferred_quality(user_id=13716939, quality_id=1)


# ── get_by_id ────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_by_id_returns_track(mocker, track_payload):
    mocker.patch("addictune_sdk.api._helpers.cache.get_etag", return_value=(None, None))
    mocker.patch("addictune_sdk.api._helpers.cache.get_indexed", return_value=None)
    mocker.patch("addictune_sdk.api._helpers.cache.set_etag")

    mock_client = mocker.AsyncMock(spec=httpx.AsyncClient)
    mock_client.get.return_value = make_response(200, track_payload)

    api = TracksAPI(mock_client, network="di")
    result = await api.get_by_id(2027566)

    assert isinstance(result, Track)
    assert result.id == 2027566
    assert result.title == "Adagio for Strings"
    # ContentAsset fields flattened from content.assets[0]
    assert result.content_quality_id == 3
    assert result.size == 6789123
    assert result.url is not None
    # content.length hoisted
    assert result.length == 424
    # Full assets list preserved
    assert len(result.assets) == 2
    assert result.assets[1].content_quality_id == 5
    mock_client.get.assert_called_once_with("/di/tracks/2027566", headers={})


@pytest.mark.asyncio
async def test_get_by_id_uses_etag_cache(mocker, track_payload):
    mocker.patch(
        "addictune_sdk.api._helpers.cache.get_etag",
        return_value=('"t1"', track_payload),
    )
    mocker.patch("addictune_sdk.api._helpers.cache.get_indexed", return_value=None)
    mocker.patch("addictune_sdk.api._helpers.cache.set_etag")

    mock_client = mocker.AsyncMock(spec=httpx.AsyncClient)
    mock_client.get.return_value = make_response(304)

    api = TracksAPI(mock_client, network="di")
    result = await api.get_by_id(2027566)

    assert result.id == 2027566
    call_headers = mock_client.get.call_args[1]["headers"]
    assert call_headers["If-None-Match"] == '"t1"'


# ── get_liked_track ──────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_liked_track_returns_track(mocker, liked_track_payload):
    mock_client = mocker.AsyncMock(spec=httpx.AsyncClient)
    mock_client.get.return_value = make_response(200, [liked_track_payload])

    api = TracksAPI(mock_client, network="di")
    result = await api.get_liked_track(user_id=13716939, track_id=2027566)

    assert isinstance(result, Track)
    assert result.id == 2027566
    assert result.title == "Adagio for Strings"
    # Vote flags flattened from the nested structure
    assert result.up is True
    assert result.down is False
    # ContentAsset fields still work
    assert result.content_quality_id == 3
    assert result.length == 424
    mock_client.get.assert_called_once_with("/di/members/13716939/track_votes/2027566")


@pytest.mark.asyncio
async def test_get_liked_track_returns_none_when_empty(mocker):
    mock_client = mocker.AsyncMock(spec=httpx.AsyncClient)
    mock_client.get.return_value = make_response(200, [])

    api = TracksAPI(mock_client, network="di")
    result = await api.get_liked_track(user_id=13716939, track_id=999)

    assert result is None


@pytest.mark.asyncio
async def test_get_liked_track_handles_single_object(mocker, liked_track_payload):
    mock_client = mocker.AsyncMock(spec=httpx.AsyncClient)
    mock_client.get.return_value = make_response(200, liked_track_payload)

    api = TracksAPI(mock_client, network="di")
    result = await api.get_liked_track(user_id=13716939, track_id=2027566)

    assert isinstance(result, Track)
    assert result.id == 2027566


@pytest.mark.asyncio
async def test_get_liked_track_preserves_track_id_over_vote_row_id(mocker, liked_track_payload):
    """The outer ``id`` (vote-row id) must not overwrite ``track.id``.

    The live ``track_votes`` payload returns outer vote metadata with its
    own ``id`` and ``track_id``, alongside a nested ``track`` object.  The
    SDK must surface the *track* id as ``LikedTrack.id`` and keep the
    vote-row id on a separate field.
    """
    from addictune_sdk.models.track import LikedTrack

    mock_client = mocker.AsyncMock(spec=httpx.AsyncClient)
    mock_client.get.return_value = make_response(200, [liked_track_payload])

    api = TracksAPI(mock_client, network="di")
    result = await api.get_liked_track(user_id=13716939, track_id=2027566)

    assert isinstance(result, LikedTrack)
    # ``id`` is the *track* id, not the vote-row id.
    assert result.id == 2027566
    assert result.id != 999999
    # Vote-row id is preserved separately.
    assert result.track_vote_id == 999999
    # Outer track_id mirrors the nested track id.
    assert result.track_id == 2027566
    # Outer metadata is preserved for filtering.
    assert result.channel_id == 1
    assert result.network_id == 1
    assert result.position == 5
    assert result.created_at == "2024-03-10T14:22:01-04:00"
    assert result.updated_at == "2024-03-10T14:22:01-04:00"
    # Nested track content still works.
    assert result.title == "Adagio for Strings"
    assert result.length == 424
    assert result.up is True


@pytest.mark.asyncio
async def test_get_liked_track_handles_null_channel_id(mocker, liked_tracks_payload):
    """``channel_id`` from the live API can be ``None`` for some rows."""
    from addictune_sdk.models.track import LikedTrack

    mock_client = mocker.AsyncMock(spec=httpx.AsyncClient)
    mock_client.get.return_value = make_response(200, liked_tracks_payload)

    api = TracksAPI(mock_client, network="di")
    results = await api.get_liked_tracks(user_id=13716939)

    assert len(results) == 2
    assert all(isinstance(t, LikedTrack) for t in results)
    # First row has a channel id, second doesn't (live API can return None).
    assert results[0].channel_id == 1
    assert results[1].channel_id is None
    # Both ids must be the track ids, not the vote-row ids.
    assert results[0].id == 2027566
    assert results[0].track_vote_id == 999998
    assert results[1].id == 3153063
    assert results[1].track_vote_id == 999999


@pytest.mark.asyncio
async def test_get_liked_track_handles_single_object(mocker, liked_track_payload):
    mock_client = mocker.AsyncMock(spec=httpx.AsyncClient)
    mock_client.get.return_value = make_response(200, liked_track_payload)

    api = TracksAPI(mock_client, network="di")
    result = await api.get_liked_track(user_id=13716939, track_id=2027566)

    assert isinstance(result, Track)
    assert result.id == 2027566


# ── get_liked_tracks ─────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_liked_tracks_returns_list(mocker, liked_tracks_payload):
    mock_client = mocker.AsyncMock(spec=httpx.AsyncClient)
    mock_client.get.return_value = make_response(200, liked_tracks_payload)

    api = TracksAPI(mock_client, network="di")
    result = await api.get_liked_tracks(user_id=13716939)

    assert len(result) == 2
    assert all(isinstance(t, Track) for t in result)
    assert result[0].id == 2027566
    assert result[0].up is True
    assert result[0].down is False
    assert result[1].id == 3153063
    assert result[1].up is False
    assert result[1].down is True


@pytest.mark.asyncio
async def test_get_liked_tracks_passes_params(mocker, liked_tracks_payload):
    mock_client = mocker.AsyncMock(spec=httpx.AsyncClient)
    mock_client.get.return_value = make_response(200, liked_tracks_payload)

    api = TracksAPI(mock_client, network="di")
    await api.get_liked_tracks(user_id=13716939, vote_type="down", per_page=10)

    call_params = mock_client.get.call_args[1]["params"]
    assert call_params == {"vote_type": "down", "per_page": 10, "page": 1}


# ── vote ──────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_vote_up_succeeds(mocker):
    mock_client = mocker.AsyncMock(spec=httpx.AsyncClient)
    mock_client.post.return_value = make_response(200)

    api = TracksAPI(mock_client, network="di")
    await api.vote(track_id=2027566, direction="up")

    mock_client.post.assert_called_once_with(
        "/di/tracks/2027566/vote/up",
        json={"direction": "up"},
    )


@pytest.mark.asyncio
async def test_vote_down_succeeds(mocker):
    mock_client = mocker.AsyncMock(spec=httpx.AsyncClient)
    mock_client.post.return_value = make_response(200)

    api = TracksAPI(mock_client, network="di")
    await api.vote(track_id=2027566, direction="down")

    mock_client.post.assert_called_once_with(
        "/di/tracks/2027566/vote/down",
        json={"direction": "down"},
    )


@pytest.mark.asyncio
async def test_vote_delete_succeeds(mocker):
    mock_client = mocker.AsyncMock(spec=httpx.AsyncClient)
    mock_client.delete.return_value = make_response(200)

    api = TracksAPI(mock_client, network="di")
    await api.vote(track_id=2027566, direction="delete")

    mock_client.delete.assert_called_once_with("/di/tracks/2027566/vote")


@pytest.mark.asyncio
async def test_vote_invalid_direction_raises(mocker):
    mock_client = mocker.AsyncMock(spec=httpx.AsyncClient)

    api = TracksAPI(mock_client, network="di")
    with pytest.raises(ValueError, match="Invalid vote direction"):
        await api.vote(track_id=2027566, direction="sideways")


@pytest.mark.asyncio
async def test_vote_raises_on_error(mocker):
    mock_client = mocker.AsyncMock(spec=httpx.AsyncClient)
    mock_client.post.return_value = make_response(401, text="Unauthorized")

    api = TracksAPI(mock_client, network="di")
    from addictune_sdk.exceptions import AddictuneAuthError

    with pytest.raises(AddictuneAuthError):
        await api.vote(track_id=2027566, direction="up")


# ── skip_track ────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_skip_track_succeeds(mocker):
    mock_client = mocker.AsyncMock(spec=httpx.AsyncClient)
    mock_client.post.return_value = make_response(201)

    api = TracksAPI(mock_client, network="di")
    await api.skip_track(track_id=42, channel_id=1)

    call_json = mock_client.post.call_args[1]["json"]
    assert call_json["track_id"] == 42
    assert call_json["channel_id"] == 1
    assert "created_at" in call_json
    # None fields excluded
    assert "playlist_id" not in call_json
    assert "skipped_at" not in call_json


@pytest.mark.asyncio
async def test_skip_track_with_all_fields(mocker):
    mock_client = mocker.AsyncMock(spec=httpx.AsyncClient)
    mock_client.post.return_value = make_response(201)

    api = TracksAPI(mock_client, network="di")
    await api.skip_track(
        track_id=42,
        channel_id=1,
        playlist_id=5,
        skipped_at=1777806000,
        length=240,
    )

    call_json = mock_client.post.call_args[1]["json"]
    assert call_json["track_id"] == 42
    assert call_json["channel_id"] == 1
    assert call_json["playlist_id"] == 5
    assert call_json["skipped_at"] == 1777806000
    assert call_json["length"] == 240
    assert "created_at" in call_json


@pytest.mark.asyncio
async def test_skip_track_raises_on_error(mocker):
    mock_client = mocker.AsyncMock(spec=httpx.AsyncClient)
    mock_client.post.return_value = make_response(404, text="Not Found")

    api = TracksAPI(mock_client, network="di")
    with pytest.raises(AddictuneNotFoundError):
        await api.skip_track(track_id=42)
