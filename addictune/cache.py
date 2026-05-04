from pathlib import Path

import diskcache

_cache = diskcache.Cache(Path.home() / ".cache" / "addictune")


def get_etag(url: str) -> tuple[str, object] | tuple[None, None]:
    entry = _cache.get(url)
    if entry:
        return entry["etag"], entry["data"]
    return None, None


def set_etag(url: str, etag: str, data: object, ttl: int | None = None) -> None:
    _cache.set(url, {"etag": etag, "data": data}, expire=ttl)


def index_list(
    url: str, items: list[dict], id_field: str = "id", ttl: int | None = None
) -> None:
    """Index items from a list response for individual lookups.

    Stores each item under ``{url}/{id_field}={value}`` so that
    :func:`get_indexed` can find them without a network request.
    All writes happen inside a single transaction.
    """
    if not items:
        return
    prefix = f"{url}/{id_field}"
    with _cache.transact():
        for item in items:
            if id_field in item:
                _cache.set(f"{prefix}={item[id_field]}", item, expire=ttl)


def get_indexed(key: str) -> dict | None:
    """Return a single indexed item, or ``None`` if not found."""
    return _cache.get(key)
