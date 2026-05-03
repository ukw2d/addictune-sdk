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
