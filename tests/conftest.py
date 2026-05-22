import json
from pathlib import Path

import httpx
import pytest

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def load_fixture(name: str) -> dict:
    return json.loads((FIXTURES_DIR / name).read_text())


def make_response(
    status_code: int,
    json_data=None,
    text: str = "",
    headers: dict | None = None,
) -> httpx.Response:
    """Build a minimal httpx.Response for use in tests."""
    if json_data is not None:
        content = json.dumps(json_data).encode()
        default_headers = {"content-type": "application/json"}
    else:
        content = text.encode()
        default_headers = {"content-type": "text/plain"}

    return httpx.Response(
        status_code=status_code,
        content=content,
        headers={**default_headers, **(headers or {})},
    )


@pytest.fixture
def auth_payload():
    return load_fixture("auth.json")


@pytest.fixture
def channel_payload():
    return load_fixture("channel.json")


@pytest.fixture
def channel_payload_minimal():
    return load_fixture("channel_minimal.json")


@pytest.fixture
def channels_list(channel_payload, channel_payload_minimal):
    return [channel_payload, channel_payload_minimal]


@pytest.fixture
def channel_filter_payload(channels_list):
    return {
        "id": 89,
        "description_text": "",
        "description_title": "",
        "display": True,
        "display_description": False,
        "genre": False,
        "key": "popular",
        "meta": True,
        "name": "Popular",
        "position": 1,
        "network_id": 1,
        "created_at": None,
        "updated_at": "2024-02-21T10:00:42-05:00",
        "images": {},
        "channels": channels_list,
    }


@pytest.fixture
def auth_response(auth_payload):
    return make_response(200, auth_payload)


@pytest.fixture
def channels_response(channels_list):
    return make_response(
        200,
        channels_list,
        headers={"etag": '"abc123"', "cache-control": "max-age=300", "age": "0"},
    )


@pytest.fixture
def track_history_payload():
    return load_fixture("track_history.json")


@pytest.fixture
def now_playing_payload():
    return load_fixture("now_playing.json")


@pytest.fixture
def favorites_payload():
    return load_fixture("favorites.json")


@pytest.fixture
def track_payload():
    return load_fixture("track.json")


@pytest.fixture
def liked_track_payload():
    return load_fixture("liked_track.json")


@pytest.fixture
def liked_tracks_payload():
    return load_fixture("liked_tracks.json")


@pytest.fixture
def qualities_payload():
    return load_fixture("qualities.json")


@pytest.fixture
def preferred_quality_payload():
    return load_fixture("preferred_quality.json")


@pytest.fixture
def mixshow_payload():
    return load_fixture("mixshow.json")


@pytest.fixture
def mixshows_list_payload():
    return load_fixture("mixshows_list.json")


@pytest.fixture
def show_episodes_payload():
    return load_fixture("show_episodes.json")


@pytest.fixture
def upcoming_episodes_payload():
    return load_fixture("upcoming_episodes.json")


@pytest.fixture
def playlists_featured_payload():
    return load_fixture("playlists_featured.json")


@pytest.fixture
def playlist_payload():
    return load_fixture("playlist.json")


@pytest.fixture
def playlist_content_payload():
    return load_fixture("playlist_content.json")


@pytest.fixture
def playlists_followed_payload():
    return load_fixture("playlists_followed.json")


@pytest.fixture
def playlist_listen_history_payload():
    return load_fixture("playlist_listen_history.json")


@pytest.fixture
def ping_payload():
    return load_fixture("ping.json")


@pytest.fixture
def payment_method_payload():
    return load_fixture("payment_method.json")


@pytest.fixture
def premium_status_payload():
    return load_fixture("premium_status.json")
