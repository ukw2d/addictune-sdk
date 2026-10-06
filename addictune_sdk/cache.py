"""SQLite-backed ETag cache for conditional HTTP requests.

The cache stores ETags and response bodies so subsequent requests to the
same URL include an ``If-None-Match`` header, allowing the server to
respond ``304 Not Modified`` and save bandwidth.

By default the cache is enabled and stored at
``~/.cache/addictune_sdk/cache.db``.  Use :func:`configure` to change the
directory or disable caching entirely.
"""

from __future__ import annotations

import json
import logging
import sqlite3
import time
from pathlib import Path
from typing import Any

from platformdirs import user_cache_path

DEFAULT_TTL = 300
"""Fallback TTL (seconds) when the server sends no usable ``max-age``."""

_conn: sqlite3.Connection | None = None
_cache_dir: Path = user_cache_path("addictune_sdk")
_enabled: bool = True

logger = logging.getLogger(__name__)

_CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS etag_cache (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    exp REAL
)
"""

_SET = "INSERT OR REPLACE INTO etag_cache (key, value, exp) VALUES (?, ?, ?)"
_GET = "SELECT value, exp FROM etag_cache WHERE key = ?"
_DELETE_EXPIRED = "DELETE FROM etag_cache WHERE exp IS NOT NULL AND exp < ?"


def configure(*, enabled: bool = True, cache_dir: str | Path | None = None) -> None:
    """Configure the ETag cache.

    Args:
        enabled: Set to ``False`` to disable caching entirely.
        cache_dir: Directory for the SQLite file.  Defaults to
            ``~/.cache/addictune_sdk``.
    """
    global _conn, _cache_dir, _enabled
    _enabled = enabled
    if cache_dir is not None:
        _cache_dir = Path(cache_dir)
    if _conn is not None:
        _conn.close()
        _conn = None
    logger.debug("Cache %s (%s)", "enabled" if enabled else "disabled", _cache_dir)


def _get_conn() -> sqlite3.Connection | None:
    global _conn
    if not _enabled:
        return None
    if _conn is None:
        _cache_dir.mkdir(parents=True, exist_ok=True)
        _conn = sqlite3.connect(str(_cache_dir / "cache.db"))
        _conn.execute("PRAGMA journal_mode=WAL")
        _conn.execute(_CREATE_TABLE)
        _conn.commit()
    return _conn


def clear() -> None:
    """Remove all cached entries."""
    if (conn := _get_conn()) is not None:
        conn.execute("DELETE FROM etag_cache")
        conn.commit()
        logger.debug("Cache cleared")


def get_etag(url: str) -> tuple[str, Any] | tuple[None, None]:
    """Return cached ``(etag, data)`` for *url*, or ``(None, None)``."""
    conn = _get_conn()
    if conn is None:
        return None, None
    row = conn.execute(_GET, (url,)).fetchone()
    if row is None:
        return None, None
    value_json, exp = row
    now = time.time()
    if exp is not None and exp < now:
        conn.execute(_DELETE_EXPIRED, (now,))
        conn.commit()
        logger.debug("Cache expired: %s", url)
        return None, None
    logger.debug("Cache hit: %s", url)
    value = json.loads(value_json)
    return value["etag"], value["data"]


def set_etag(url: str, etag: str, data: Any, ttl: int | None = None) -> None:
    """Store an ETag and response data for *url*.

    Args:
        url: Request URL used as the cache key.
        etag: ETag header value from the response.
        data: Parsed response body.
        ttl: Time-to-live in seconds; ``None`` uses :data:`DEFAULT_TTL`.
    """
    conn = _get_conn()
    if conn is None:
        return
    exp = time.time() + (ttl if ttl is not None else DEFAULT_TTL)
    conn.execute(_SET, (url, json.dumps({"etag": etag, "data": data}), exp))
    conn.commit()
    logger.debug("Cache stored: %s (ttl=%s)", url, ttl)
