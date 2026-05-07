"""Models for the MixShows API domain."""

from __future__ import annotations

from pydantic import BaseModel

from .common import ImageSet


class ShowChannel(BaseModel):
    """Minimal channel reference embedded in show data.

    Attributes:
        id: Channel identifier.
        name: Channel display name.
        key: URL-friendly channel key.
        images: Channel artwork.
    """

    id: int
    name: str
    key: str | None = None
    images: ImageSet | None = None

    model_config = {"extra": "ignore"}


class UpcomingEvent(BaseModel):
    """Lightweight upcoming event embedded in a MixShow.

    Attributes:
        id: Event identifier.
        name: Event name.
        slug: URL-friendly slug.
        start_at: ISO timestamp of when the event starts.
        end_at: ISO timestamp of when the event ends.
    """

    id: int
    name: str
    slug: str | None = None
    start_at: str | None = None
    end_at: str | None = None

    model_config = {"extra": "ignore"}


class MixShow(BaseModel):
    """A mix show (show series).

    Attributes:
        id: Show identifier.
        name: Show display name.
        slug: URL-friendly slug.
        description: Show description.
        active: Whether the show is currently active.
        channels: Channels this show airs on.
        upcoming_event: The next scheduled event, if any.
        images: Show artwork.
    """

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
    """A single episode of a mix show.

    Attributes:
        id: Episode identifier.
        name: Episode display name.
        free: Whether the episode is free to listen to.
        start_at: ISO timestamp of when the episode starts.
        end_at: ISO timestamp of when the episode ends.
        show: The parent :class:`MixShow`, if embedded.
    """

    id: int
    name: str
    free: bool = False
    start_at: str | None = None
    end_at: str | None = None
    show: MixShow | None = None
    tracks: list[dict] = []

    model_config = {"extra": "ignore"}
