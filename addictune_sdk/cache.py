"""SQLite-backed ETag cache for conditional HTTP requests.

The cache stores ETags and response bodies so that subsequent requests
for the same URL include an ``If-None-Match`` header, allowing the
server to respond with ``304 Not Modified`` and save bandwidth.

By default the cache is enabled and stored at
``~/.cache/addictune_sdk/cache.db``.  Use :func:`configure` to change the
directory or disable caching entirely.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

_default_cache_dir = Path.home() / ".cache" / "addictune_sdk"

_conn: sqlite3.Connection | None = None
_cache_dir: Path = _default_cache_dir
_enabled: bool = True

_CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS etag_cache (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    exp   REAL
)
"""

_SET = """
INSERT OR REPLACE INTO etag_cache (key, value, exp)
VALUES (?, ?, ?)
"""

_GET = """
SELECT value, exp FROM etag_cache WHERE key = ?
"""

_DELETE_EXPIRED = """
DELETE FROM etag_cache WHERE exp IS NOT NULL AND exp < ?
"""


def _now() -> float:
    from time import monotonic

    return monotonic()


def _open_db() -> sqlite3.Connection:
    conn = sqlite3.connect(str(_cache_dir / "cache.db"))
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute(_CREATE_TABLE)
    conn.commit()
    return conn


def configure(*, enabled: bool = True, cache_dir: str | Path | None = None) -> None:
    """Configure the ETag cache.

    Args:
        enabled: Set to ``False`` to disable caching entirely.
        cache_dir: Directory for the SQLite database.
            Defaults to ``~/.cache/addictune_sdk``.
    """
    global _conn, _cache_dir, _enabled

    _enabled = enabled
    _cache_dir = Path(cache_dir) if cache_dir else _default_cache_dir

    if _conn is not None:
        _conn.close()
        _conn = None

    if enabled:
        _cache_dir.mkdir(parents=True, exist_ok=True)
        _conn = _open_db()


def _get_conn() -> sqlite3.Connection | None:
    global _conn
    if not _enabled:
        return None
    if _conn is None:
        _cache_dir.mkdir(parents=True, exist_ok=True)
        _conn = _open_db()
    return _conn


def clear() -> None:
    """Remove all cached entries."""
    conn = _get_conn()
    if conn is not None:
        conn.execute("DELETE FROM etag_cache")
        conn.commit()


def get_etag(url: str) -> tuple[str, Any] | tuple[None, None]:
    """Return the cached ``(etag, data)`` for *url*, or ``(None, None)``."""
    conn = _get_conn()
    if conn is None:
        return None, None

    now = _now()
    row = conn.execute(_GET, (url,)).fetchone()
    if row is None:
        return None, None
    value_json, exp = row
    if exp is not None and exp < now:
        conn.execute(_DELETE_EXPIRED, (now,))
        conn.commit()
        return None, None

    entry = json.loads(value_json)
    return entry["etag"], entry["data"]


def set_etag(url: str, etag: str, data: Any, ttl: int | None = None) -> None:
    """Store an ETag and its corresponding response data.

    Args:
        url: The request URL used as the cache key.
        etag: The ETag header value.
        data: The parsed response data to cache.
        ttl: Optional time-to-live in seconds.
    """
    conn = _get_conn()
    if conn is None:
        return
    value = json.dumps({"etag": etag, "data": data})
    exp = (_now() + ttl) if ttl is not None else None
    conn.execute(_SET, (url, value, exp))
    conn.commit()


def index_list(
    url: str, items: list[dict[str, Any]], id_field: str = "id", ttl: int | None = None
) -> None:
    """Index items from a list response for individual lookups.

    Stores each item under ``{url}/{id_field}={value}`` so that
    :func:`get_indexed` can find them without a network request.
    All writes happen inside a single transaction.
    """
    conn = _get_conn()
    if conn is None or not items:
        return
    prefix = f"{url}/{id_field}"
    exp = (_now() + ttl) if ttl is not None else None
    rows = [
        (f"{prefix}={item[id_field]}", json.dumps(item), exp)
        for item in items
        if id_field in item
    ]
    if not rows:
        return
    conn.executemany(_SET, rows)
    conn.commit()


def get_indexed(key: str) -> dict[str, Any] | None:
    """Return a single indexed item, or ``None`` if not found."""
    conn = _get_conn()
    if conn is None:
        return None

    now = _now()
    row = conn.execute(_GET, (key,)).fetchone()
    if row is None:
        return None
    value_json, exp = row
    if exp is not None and exp < now:
        return None
    return json.loads(value_json)
