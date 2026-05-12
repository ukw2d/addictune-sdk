"""Shared models reused across multiple API domains."""

from typing import Annotated

from pydantic import BaseModel, BeforeValidator


def _ensure_scheme(url: str | None) -> str | None:
    if url and url.startswith("//"):
        return f"https:{url}"
    return url


AssetUrl = Annotated[str | None, BeforeValidator(_ensure_scheme)]


class ImageSet(BaseModel):
    """A set of image URL templates returned by the AudioAddict API.

    Not all keys are present on every response.  URLs contain
    ``{?size,height,width,quality,pad}`` template suffixes that must
    be stripped or resolved by the consumer.
    """

    default: AssetUrl = None
    compact: AssetUrl = None
    square: AssetUrl = None
    vertical: AssetUrl = None
    horizontal_banner: AssetUrl = None
    tall_banner: AssetUrl = None

    model_config = {"extra": "ignore"}


class Votes(BaseModel):
    """Up/down vote counts for a track.

    Attributes:
        up: Number of upvotes.
        down: Number of downvotes.
    """

    up: int = 0
    down: int = 0

    model_config = {"extra": "ignore"}


class ContentAsset(BaseModel):
    """A single streamable asset inside a track's ``content.assets`` list.

    Attributes:
        content_format_id: Format identifier (e.g. MP3, AAC).
        content_quality_id: Quality tier identifier.
        size: Asset size in bytes.
        url: Direct URL to the streamable file.
    """

    content_format_id: int | None = None
    content_quality_id: int | None = None
    size: int | None = None
    url: AssetUrl = None

    model_config = {"extra": "ignore"}
