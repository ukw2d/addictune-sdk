"""Models for cross-entity search results."""

from typing import Generic, TypeVar

from pydantic import BaseModel, Field

from .channel import Channel
from .mixshow import MixShow
from .playlist import Playlist
from .track import Track

T = TypeVar("T")


class SearchBucket(BaseModel, Generic[T]):
    """Search results for one entity type."""

    total: int = 0
    items: list[T] = Field(default_factory=list)

    model_config = {"extra": "ignore"}


class SearchResults(BaseModel):
    """Search results grouped by AudioAddict entity type."""

    channels: SearchBucket[Channel] = Field(default_factory=SearchBucket)
    shows: SearchBucket[MixShow] = Field(default_factory=SearchBucket)
    playlists: SearchBucket[Playlist] = Field(default_factory=SearchBucket)
    tracks: SearchBucket[Track] = Field(default_factory=SearchBucket)

    model_config = {"extra": "ignore"}

