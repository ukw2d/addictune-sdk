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


class Track(BaseModel):
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

    model_config = {"extra": "ignore"}

    @model_validator(mode="before")
    @classmethod
    def _hoist_content(cls, data: dict) -> dict:
        """Flatten the ``content`` dict into the top level.

        The API nests streamable assets and other metadata under a
        ``content`` key.  We merge it all up so consumers never need to
        dig into ``content``.  Top-level keys win on conflict.
        """
        if not isinstance(data, dict):
            return data
        content = data.pop("content", None)
        if isinstance(content, dict):
            # content fields are secondary — top-level wins on conflict
            return {**content, **data}
        return data


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
