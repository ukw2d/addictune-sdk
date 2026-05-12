"""Shared models reused across multiple API domains."""

from __future__ import annotations

import re
from typing import Annotated

from pydantic import BaseModel, BeforeValidator

# ── URL types ─────────────────────────────────────────────────────────

_URI_TEMPLATE_RE = re.compile(r"\{[^}]*\}$")


def _normalize_url(url: str | None, *, strip_template: bool = False) -> str | None:
    if not url:
        return url
    if url.startswith("//"):
        url = f"https:{url}"
    if strip_template:
        url = _URI_TEMPLATE_RE.sub("", url)
    return url


AssetUrl = Annotated[str | None, BeforeValidator(_normalize_url)]
"""Asset URL — fixes ``//`` scheme only."""

ImageUrl = Annotated[
    str | None, BeforeValidator(lambda u: _normalize_url(u, strip_template=True))
]
"""Image URL — fixes ``//`` scheme **and** strips ``{?…}`` template suffix."""


# ── ImageSet ──────────────────────────────────────────────────────────


class ImageSet(BaseModel):
    """A set of image URLs in various sizes returned by the AudioAddict API.

    All fields are clean, ready-to-use ``https://`` URLs —
    protocol-relative schemes and URI-template suffixes are stripped
    automatically.  Use :meth:`url` to get sized CDN variants.

    Attributes:
        default: Default / landscape image.
        compact: Compact thumbnail.
        square: Square-cropped image.
        vertical: Portrait / vertical image.
        horizontal_banner: Wide horizontal banner.
        tall_banner: Tall vertical banner.
    """

    default: ImageUrl = None
    compact: ImageUrl = None
    square: ImageUrl = None
    vertical: ImageUrl = None
    horizontal_banner: ImageUrl = None
    tall_banner: ImageUrl = None

    model_config = {"extra": "ignore"}

    def url(
        self,
        variant: str = "default",
        *,
        size: int | None = None,
        height: int | None = None,
        width: int | None = None,
        quality: int | None = None,
        pad: bool | None = None,
    ) -> str | None:
        """Return a sized URL for the given image *variant*.

        The CDN supports query parameters to resize on the fly.

        Args:
            variant: Image field to use (``"default"``, ``"compact"``,
                ``"square"``, ``"vertical"``, ``"horizontal_banner"``,
                ``"tall_banner"``).
            size: Shortcut for square images.
            height: Height in pixels.
            width: Width in pixels.
            quality: JPEG/WebP quality (0–100).
            pad: Pad to requested dimensions.

        Returns:
            A full ``https://`` URL with query params, or ``None`` if
            the variant is unavailable.

        Example::

            images.url("square", size=300)
            # → "https://cdn-images.audioaddict.com/…/abc.png?size=300"
        """
        base = getattr(self, variant, None)
        if base is None:
            return None

        params = {
            k: str(v).lower() if isinstance(v, bool) else str(v)
            for k, v in (
                ("size", size),
                ("height", height),
                ("width", width),
                ("quality", quality),
                ("pad", pad),
            )
            if v is not None
        }

        if not params:
            return base

        sep = "&" if "?" in base else "?"
        return f"{base}{sep}{'&'.join(f'{k}={v}' for k, v in params.items())}"


# ── Other shared models ───────────────────────────────────────────────


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
