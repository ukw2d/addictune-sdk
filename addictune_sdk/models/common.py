"""Shared models reused across multiple API domains."""

from pydantic import BaseModel


class ImageSet(BaseModel):
    """A set of image URL templates returned by the AudioAddict API.

    Not all keys are present on every response.  URLs contain
    ``{?size,height,width,quality,pad}`` template suffixes that must
    be stripped or resolved by the consumer.
    """

    default: str | None = None
    compact: str | None = None
    square: str | None = None
    vertical: str | None = None
    horizontal_banner: str | None = None
    tall_banner: str | None = None

    model_config = {"extra": "ignore"}


class Votes(BaseModel):
    up: int = 0
    down: int = 0

    model_config = {"extra": "ignore"}


class ContentAsset(BaseModel):
    """A single streamable asset inside a track's ``content.assets`` list."""

    content_format_id: int | None = None
    content_quality_id: int | None = None
    size: int | None = None
    url: str | None = None

    model_config = {"extra": "ignore"}
