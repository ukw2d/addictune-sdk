"""ETag-aware response header parser.

Normalises HTTP response headers (ETag, Cache-Control, pagination)
into a typed :class:`ResponseHeaders` model with a computed ``ttl``
property used by the cache layer.
"""

from pydantic import BaseModel, model_validator


class ResponseHeaders(BaseModel):
    """Parsed HTTP response headers used for ETag caching and pagination.

    Attributes:
        etag: The ``ETag`` header value for conditional requests.
        cache_control: The ``Cache-Control`` header value.
        age: The ``Age`` header value in seconds.
        paginate_page: Current page number (from ``paginate-page``).
        paginate_pages: Total number of pages (from ``paginate-pages``).
        paginate_records: Total number of records (from ``paginate-records``).
        paginate_per_page: Items per page (from ``paginate-perpage``).
    """

    etag: str | None = None
    cache_control: str | None = None
    age: int = 0

    # Pagination headers returned by list endpoints
    paginate_page: int | None = None
    paginate_pages: int | None = None
    paginate_records: int | None = None
    paginate_per_page: int | None = None

    model_config = {"populate_by_name": True}

    @model_validator(mode="before")
    @classmethod
    def normalize_keys(cls, data):
        if hasattr(data, "get"):
            return {
                "etag": data.get("etag"),
                "cache_control": data.get("cache-control"),
                "age": data.get("age", 0),
                "paginate_page": data.get("paginate-page"),
                "paginate_pages": data.get("paginate-pages"),
                "paginate_records": data.get("paginate-records"),
                "paginate_per_page": data.get("paginate-perpage"),
            }
        return data

    @property
    def ttl(self) -> int | None:
        """Remaining TTL in seconds derived from ``Cache-Control: max-age``.

        Computed as ``max-age - age``.  Returns ``None`` if no
        ``max-age`` directive is present or if the remaining TTL
        would be zero or negative.
        """
        if not self.cache_control:
            return None
        for part in self.cache_control.split(","):
            part = part.strip()
            if part.startswith("max-age="):
                try:
                    remaining = int(part[len("max-age=") :]) - self.age
                    return remaining if remaining > 0 else None
                except ValueError:
                    pass
        return None
