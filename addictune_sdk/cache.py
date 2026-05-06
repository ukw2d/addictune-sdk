from __future__ import annotations

from pathlib import Path
from typing import Any, cast

import diskcache

_default_cache_dir = Path.home() / ".cache" / "addictune_sdk"

_cache: diskcache.Cache | None = None
_cache_dir: Path = _default_cache_dir
_enabled: bool = True


def configure(*, enabled: bool = True, cache_dir: str | Path | None = None) -> None:
    """Configure the ETag cache.

    Args:
        enabled: Set to ``False`` to disable caching entirely.
        cache_dir: Directory for the diskcache store.
            Defaults to ``~/.cache/addictune_sdk``.
    """
    global _cache, _cache_dir, _enabled

    _enabled = enabled
    _cache_dir = Path(cache_dir) if cache_dir else _default_cache_dir

    if enabled:
        _cache = diskcache.Cache(_cache_dir)
    else:
        if _cache is not None:
            _cache.close()
        _cache = None


def _get_cache() -> diskcache.Cache:
    global _cache
    if _cache is None and _enabled:
        _cache = diskcache.Cache(_cache_dir)
    return _cache  # type: ignore[return-value]


def clear() -> None:
    """Remove all cached entries."""
    c = _get_cache()
    if c is not None:
        c.clear()


def get_etag(url: str) -> tuple[str, Any] | tuple[None, None]:
    c = _get_cache()
    if c is None:
        return None, None
    entry = cast(_CacheEntry | None, c.get(url))
    if entry:
        return entry["etag"], entry["data"]
    return None, None


def set_etag(url: str, etag: str, data: Any, ttl: int | None = None) -> None:
    c = _get_cache()
    if c is None:
        return
    c.set(url, {"etag": etag, "data": data}, expire=ttl)


_CacheEntry = dict[str, Any]


def index_list(
    url: str, items: list[dict[str, Any]], id_field: str = "id", ttl: int | None = None
) -> None:
    """Index items from a list response for individual lookups.

    Stores each item under ``{url}/{id_field}={value}`` so that
    :func:`get_indexed` can find them without a network request.
    All writes happen inside a single transaction.
    """
    c = _get_cache()
    if c is None or not items:
        return
    prefix = f"{url}/{id_field}"
    with c.transact():
        for item in items:
            if id_field in item:
                c.set(f"{prefix}={item[id_field]}", item, expire=ttl)


def get_indexed(key: str) -> dict[str, Any] | None:
    """Return a single indexed item, or ``None`` if not found."""
    c = _get_cache()
    if c is None:
        return None
    return cast(dict[str, Any] | None, c.get(key))
