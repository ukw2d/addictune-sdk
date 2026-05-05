"""Models for the MixShows API domain."""

from __future__ import annotations

from pydantic import BaseModel

from .common import ImageSet


class ShowChannel(BaseModel):
    """Minimal channel reference embedded in show data."""

    id: int
    name: str
    key: str | None = None
    images: ImageSet | None = None

    model_config = {"extra": "ignore"}


class UpcomingEvent(BaseModel):
    """Lightweight upcoming event embedded in a MixShow."""

    id: int
    name: str
    slug: str | None = None
    start_at: str | None = None
    end_at: str | None = None

    model_config = {"extra": "ignore"}


class MixShow(BaseModel):
    """A mix show (show series)."""

    id: int
    name: str
    slug: str
    description: str | None = None
    duration: int | None = None
    active: bool = False
    human_readable_schedule: list[str] = []
    next_start_at: str | None = None
    next_end_at: str | None = None
    ondemand_episode_count: int | None = None
    artists: list[dict] = []
    now_playing: bool = False
    upcoming_event: UpcomingEvent | None = None
    following: bool = False
    followers_count: int | None = None
    channels: list[ShowChannel] = []
    images: ImageSet | None = None

    model_config = {"extra": "ignore"}


class ShowEpisode(BaseModel):
    """A single episode of a mix show."""

    id: int
    name: str
    free: bool = False
    start_at: str | None = None
    end_at: str | None = None
    show: MixShow | None = None
    tracks: list[dict] = []

    model_config = {"extra": "ignore"}
