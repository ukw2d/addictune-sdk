from pydantic import BaseModel

from .common import ImageSet, Votes


class ChannelArtist(BaseModel):
    id: int
    name: str
    asset_url: str | None = None
    images: ImageSet | None = None

    model_config = {"extra": "ignore"}


class SimilarChannel(BaseModel):
    id: int
    similar_channel_id: int

    model_config = {"extra": "ignore"}


class Channel(BaseModel):
    id: int
    key: str
    name: str
    description: str | None = None
    description_short: str | None = None
    description_long: str | None = None
    network_id: int
    premium_id: int | None = None
    asset_url: str | None = None
    banner_url: str | None = None
    channel_director: str | None = None
    artists: list[ChannelArtist] = []
    similar_channels: list[SimilarChannel] = []
    channel_filter_ids: list[int] = []
    images: ImageSet | None = None
    public: bool | None = None
    created_at: str | None = None
    updated_at: str | None = None

    model_config = {"extra": "ignore"}


class TrackHistoryEntry(BaseModel):
    """Track as returned by track_history and currently_playing endpoints."""

    id: int | None = None
    track_id: int | None = None
    channel_id: int | None = None
    title: str | None = None
    display_title: str | None = None
    artist: str | None = None
    display_artist: str | None = None
    length: float | None = None
    duration: float | None = None
    started: int | None = None
    start_time: str | None = None
    votes: Votes | None = None
    art_url: str | None = None
    images: ImageSet | None = None

    model_config = {"extra": "ignore"}


class NowPlaying(BaseModel):
    """Single entry from the currently_playing endpoint."""

    channel_id: int
    channel_key: str
    track: TrackHistoryEntry

    model_config = {"extra": "ignore"}


class LikedChannelID(BaseModel):
    channel_id: int
    position: int | None = None

    model_config = {"extra": "ignore"}
