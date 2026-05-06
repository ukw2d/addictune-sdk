"""Models for the Playlists API domain."""

from __future__ import annotations

from pydantic import BaseModel, model_validator

from .common import ImageSet


class PlaylistTag(BaseModel):
    id: int
    name: str

    model_config = {"extra": "ignore"}


class Playlist(BaseModel):
    id: int
    name: str
    slug: str | None = None
    description: str | None = None
    images: ImageSet | None = None
    tags: list[PlaylistTag] = []
    following: bool = False
    channel_id: int | None = None
    track_count: int = 0
    playlists_count: int | None = None
    play_count: int = 0
    follow_count: int | None = None
    length: int = 0
    duration: str | None = None
    popularity: float | None = None

    model_config = {"extra": "ignore"}


class PlaylistProgress(BaseModel):
    played_tracks: int
    remaining_tracks: int
    percent_complete: float

    model_config = {"extra": "ignore"}


class PlaylistTracks(BaseModel):
    id: int
    tracks: list[dict] = []
    last_tracks: list[dict] = []
    current_progress: PlaylistProgress | None = None

    model_config = {"extra": "ignore"}

    @model_validator(mode="before")
    @classmethod
    def _coerce_lists(cls, data: dict) -> dict:
        if isinstance(data, dict):
            for key in ("tracks", "last_tracks"):
                val = data.get(key)
                if not isinstance(val, list):
                    data[key] = []
        return data


class PlaylistListenHistoryEntry(BaseModel):
    track: Track
    played_at: int | str | None = None

    model_config = {"extra": "ignore"}

    class Track(BaseModel):
        id: int
        title: str | None = None
        display_title: str | None = None
        display_artist: str | None = None
        length: int | None = None
        mix: bool = False
        images: ImageSet | None = None

        model_config = {"extra": "ignore"}
