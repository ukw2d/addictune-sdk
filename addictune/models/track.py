from __future__ import annotations

from pydantic import BaseModel, model_validator

from .common import ContentAsset, ImageSet, Votes


class Artist(BaseModel):
    id: int
    name: str
    slug: str | None = None
    asset_url: str | None = None
    images: ImageSet | None = None

    model_config = {"extra": "ignore"}


class Track(ContentAsset):
    """A track returned by the API.

    The API nests streamable assets under ``content.assets`` and track
    length under ``content.length``.  The ``_hoist_content`` validator
    flattens the first asset's fields (``content_format_id``,
    ``content_quality_id``, ``size``, ``url``) directly onto the
    Track (via ContentAsset inheritance), hoists ``content.length``,
    and stores the full assets list at the top level.
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
        """Flatten ``content`` dict into the top level.

        The API nests streamable assets and other metadata under a
        ``content`` key.  We:

        1. Hoist ``content.length`` to ``length``.
        2. Merge the first asset's fields (``content_format_id``,
           ``content_quality_id``, ``size``, ``url``) into the top
           level so they populate the ContentAsset base class fields.
        3. Preserve the full ``content.assets`` list as ``assets``.
        4. Top-level keys win on conflict.
        """
        if not isinstance(data, dict):
            return data

        content = data.pop("content", None)
        if not isinstance(content, dict):
            return data

        # Hoist content-level fields (e.g. length)
        if "length" in content and "length" not in data:
            data["length"] = content["length"]

        # Flatten the first asset's fields into the top level
        assets = content.get("assets", [])
        if assets and isinstance(assets, list):
            first_asset = assets[0]
            if isinstance(first_asset, dict):
                # Asset fields are secondary — top-level wins on conflict
                data = {**first_asset, **data}

            # Store the full assets list at the top level
            data["assets"] = assets

        return data


class LikedTrack(Track):
    """Wraps a track returned from vote/liked-track endpoints.

    The API returns ``{up: bool, down: bool, track: {...}}``.
    A ``model_validator`` flattens this into a plain :class:`Track`
    with the vote flags merged in.
    """

    @model_validator(mode="before")
    @classmethod
    def _unwrap_nested_track(cls, data: dict) -> dict:
        if not isinstance(data, dict) or "track" not in data:
            return data
        track_data = {**data.pop("track"), **data}
        return track_data


class SkipEvent(BaseModel):
    """Payload sent to the ``skip_events`` endpoint."""

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
    routine_id: int
    channel_id: int
    expires_on: str | None = None
    tracks: list[Track] = []

    model_config = {"extra": "ignore"}


class AudioFormat(BaseModel):
    id: int
    key: str
    name: str
    extension: str
    mime_type: str

    model_config = {"extra": "ignore"}


class AudioQualityDetail(BaseModel):
    id: int
    key: str
    name: str
    kilo_bitrate: int

    model_config = {"extra": "ignore"}


class AudioQuality(BaseModel):
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
    id: int
    network_id: int
    member_id: int
    quality_id: int
    created_at: str | None = None
    updated_at: str | None = None

    model_config = {"extra": "ignore"}
