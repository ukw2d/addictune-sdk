"""ETag-aware response header parser.

Normalises HTTP response headers (ETag, Cache-Control, pagination)
into a typed :class:`ResponseHeaders` model with a computed ``ttl``
property used by the cache layer.
"""

from pydantic import BaseModel, Field


class ResponseHeaders(BaseModel):
    """Parsed HTTP response headers used for ETag caching and pagination.

    Attributes:
        etag: ``ETag`` header value for conditional requests.
        cache_control: ``Cache-Control`` header value.
        age: ``Age`` header value in seconds.
        paginate_pages: Total number of pages (from ``paginate-pages``).
    """

    etag: str | None = None
    cache_control: str | None = Field(default=None, alias="cache-control")
    age: int = 0
    paginate_pages: int | None = Field(default=None, alias="paginate-pages")

    @property
    def ttl(self) -> int | None:
        """Remaining TTL in seconds from ``Cache-Control: max-age``.

        Returns ``None`` when there is no ``max-age`` directive, or when
        ``max-age - age`` is not positive.
        """
        if not self.cache_control:
            return None
        for part in self.cache_control.split(","):
            part = part.strip()
            if part.startswith("max-age="):
                try:
                    ttl = int(part[len("max-age=") :]) - self.age
                except ValueError:
                    return None
                return ttl if ttl > 0 else None
        return None
