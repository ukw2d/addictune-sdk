from pydantic import BaseModel

from .common import AssetUrl, ImageSet, Votes


class ChannelArtist(BaseModel):
    """Artist associated with a channel.

    Attributes:
        id: Artist identifier.
        name: Artist display name.
        asset_url: URL template for the artist's artwork.
        images: Optional set of image URL templates.
    """

    id: int
    name: str
    asset_url: AssetUrl = None
    images: ImageSet | None = None

    model_config = {"extra": "ignore"}


class SimilarChannel(BaseModel):
    """Relationship between a channel and a similar channel.

    Attributes:
        id: The source channel's ID.
        similar_channel_id: The recommended channel's ID.
    """

    id: int
    similar_channel_id: int

    model_config = {"extra": "ignore"}


class Channel(BaseModel):
    """A radio channel on an AudioAddict network.

    Attributes:
        id: Numeric channel identifier.
        key: URL-friendly channel key (e.g. ``"trance"``).
        name: Human-readable channel name.
        description: Channel description.
        network_id: ID of the parent network.
        artists: Artists associated with this channel.
        similar_channels: Channels recommended as similar.
        images: Channel artwork in various sizes.
    """

    id: int
    key: str
    name: str
    description: str | None = None
    description_short: str | None = None
    description_long: str | None = None
    network_id: int
    premium_id: int | None = None
    asset_url: AssetUrl = None
    banner_url: AssetUrl = None
    channel_director: str | None = None
    artists: list[ChannelArtist] = []
    similar_channels: list[SimilarChannel] = []
    channel_filter_ids: list[int] = []
    images: ImageSet | None = None
    public: bool | None = None
    created_at: str | None = None
    updated_at: str | None = None

    model_config = {"extra": "ignore"}


class ChannelFilter(BaseModel):
    """A channel filter/grouping returned by the channel_filters endpoint.

    Attributes:
        id: Numeric channel filter identifier.
        key: URL-friendly filter key (e.g. ``"popular"``).
        name: Human-readable filter name.
        channels: Channels included in this filter, in API-provided order.
    """

    id: int
    key: str
    name: str
    network_id: int
    description_text: str | None = None
    description_title: str | None = None
    display: bool | None = None
    display_description: bool | None = None
    genre: bool | None = None
    meta: bool | None = None
    position: int | None = None
    images: ImageSet | None = None
    channels: list[Channel] = []
    created_at: str | None = None
    updated_at: str | None = None

    model_config = {"extra": "ignore"}


class TrackHistoryEntry(BaseModel):
    """Track as returned by track_history and currently_playing endpoints.

    Attributes:
        id: The track identifier as returned by currently_playing.
        track_id: The track's identifier.
        channel_id: The channel it played on.
        title: Track title.
        artist: Track artist name.
        started: Unix timestamp of when the track started playing.
        votes: Up/down vote counts.
        images: Track artwork.
    """

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
    art_url: AssetUrl = None
    images: ImageSet | None = None

    model_config = {"extra": "ignore"}

    @property
    def resolved_track_id(self) -> int | None:
        """Return the track ID across track-history and now-playing payloads."""
        return self.track_id or self.id


class NowPlaying(BaseModel):
    """Single entry from the currently_playing endpoint.

    Attributes:
        channel_id: The channel's numeric ID.
        channel_key: The channel's key (e.g. ``"trance"``).
        track: The currently playing track.
    """

    channel_id: int
    channel_key: str
    track: TrackHistoryEntry | None = None

    model_config = {"extra": "ignore"}


class LikedChannelID(BaseModel):
    """A favorited channel reference returned by favorites endpoints.

    Attributes:
        channel_id: The favorited channel's ID.
        position: Sort position in the user's favorites list.
    """

    channel_id: int
    position: int | None = None

    model_config = {"extra": "ignore"}


class ListenHistoryEntry(BaseModel):
    """A single entry from channel listen history.

    Attributes:
        track: The track that was listened to.
        played_at: ISO timestamp of when it played.
    """

    track: TrackHistoryEntry
    played_at: str | None = None

    model_config = {"extra": "ignore"}
