from __future__ import annotations

from pydantic import BaseModel, model_validator

from .common import ContentAsset, ImageSet, Votes


class Artist(BaseModel):
    """An artist associated with a track.

    Attributes:
        id: Artist identifier.
        name: Artist display name.
        slug: URL-friendly slug.
        images: Artist artwork.
    """

    id: int
    name: str
    slug: str | None = None
    asset_url: str | None = None
    images: ImageSet | None = None

    model_config = {"extra": "ignore"}


class Track(ContentAsset):
    """A track returned by the API.

    Streamable assets nested under the API's ``content`` key are
    automatically hoisted to the top level by the ``_hoist_content``
    validator.

    Attributes:
        id: Track identifier.
        title: Track title.
        display_artist: Primary artist name for display.
        length: Track duration in seconds.
        artists: Full list of associated artists.
        votes: Up/down vote counts.
        images: Track artwork.
        assets: All available streaming assets.
    """

    id: int
    title: str
    display_artist: str | None = None
    display_title: str | None = None
    length: int | None = None
    mix: bool = False
    artists: list[Artist] = []
    votes: Votes | None = None
    images: ImageSet | None = None
    assets: list[ContentAsset] = []
    is_show_asset: bool = False
    asset_url: str | None = None
    up: bool = False
    down: bool = False

    model_config = {"extra": "ignore"}

    @model_validator(mode="before")
    @classmethod
    def _hoist_content(cls, data: dict) -> dict:
        if not isinstance(data, dict):
            return data

        content = data.pop("content", None)
        if not isinstance(content, dict):
            return data

        if "length" in content and "length" not in data:
            data["length"] = content["length"]

        assets = content.get("assets", [])
        if assets and isinstance(assets, list):
            first_asset = assets[0]
            if isinstance(first_asset, dict):
                data = {**first_asset, **data}

            data["assets"] = assets

        return data


class LikedTrack(Track):
    """A track returned from vote/liked-track endpoints.

    The API wraps the track in ``{up: bool, down: bool, track: {...}}``.
    The ``_unwrap_nested_track`` validator flattens this into a plain
    :class:`Track` with the vote flags merged in.
    """

    @model_validator(mode="before")
    @classmethod
    def _unwrap_nested_track(cls, data: dict) -> dict:
        if not isinstance(data, dict) or "track" not in data:
            return data
        track_data = {**data.pop("track"), **data}
        return track_data


class SkipEvent(BaseModel):
    """Payload sent to the ``skip_events`` endpoint.

    Attributes:
        track_id: The track that was skipped.
        channel_id: Channel the track played on, if applicable.
        playlist_id: Playlist the track played from, if applicable.
        skipped_at: Unix timestamp of when the skip occurred.
        length: Seconds into the track when it was skipped.
        created_at: ISO timestamp (auto-set if not provided).
    """

    track_id: int
    channel_id: int | None = None
    playlist_id: int | None = None
    skipped_at: int | None = None
    length: int | None = None
    created_at: str | None = None

    model_config = {"extra": "ignore"}

    @model_validator(mode="after")
    def _set_created_at(self) -> SkipEvent:
        if self.created_at is None:
            from datetime import datetime, timezone

            self.created_at = datetime.now(timezone.utc).isoformat()
        return self


class ChannelTracklist(BaseModel):
    """The current routine/tracklist for a live channel.

    Attributes:
        routine_id: The routine identifier.
        channel_id: The channel this routine belongs to.
        expires_on: When the routine expires.
        tracks: Ordered list of tracks in the routine.
    """

    routine_id: int
    channel_id: int
    expires_on: str | None = None
    tracks: list[Track] = []

    model_config = {"extra": "ignore"}


class AudioFormat(BaseModel):
    """An audio format (e.g. MP3, AAC).

    Attributes:
        id: Format identifier.
        key: Machine-readable key (e.g. ``"mp3"``).
        name: Human-readable name.
        extension: File extension (e.g. ``".mp3"``).
        mime_type: MIME type (e.g. ``"audio/mpeg"``).
    """

    id: int
    key: str
    name: str
    extension: str
    mime_type: str

    model_config = {"extra": "ignore"}


class AudioQualityDetail(BaseModel):
    """Quality tier details (bitrate).

    Attributes:
        id: Quality detail identifier.
        key: Machine-readable key.
        name: Human-readable name.
        kilo_bitrate: Bitrate in kbps.
    """

    id: int
    key: str
    name: str
    kilo_bitrate: int

    model_config = {"extra": "ignore"}


class AudioQuality(BaseModel):
    """An available audio quality tier on a network.

    Attributes:
        id: Quality tier identifier.
        name: Human-readable name (e.g. ``"High"``).
        key: Machine-readable key.
        premium_only: Whether this quality requires a premium subscription.
        default: Whether this is the default quality.
        content_format: The audio format for this tier.
        content_quality: The quality details (bitrate, etc.).
    """

    id: int
    name: str
    position: int
    premium_only: bool = False
    key: str
    default: bool = False
    content_format: AudioFormat | None = None
    content_quality: AudioQualityDetail | None = None

    model_config = {"extra": "ignore"}


class CurrentAudioQuality(BaseModel):
    """The user's currently selected audio quality preference.

    Attributes:
        id: Preference record identifier.
        network_id: The network this preference applies to.
        member_id: The user's ID.
        quality_id: The selected quality tier ID.
    """

    id: int
    network_id: int
    member_id: int
    quality_id: int
    created_at: str | None = None
    updated_at: str | None = None

    model_config = {"extra": "ignore"}
