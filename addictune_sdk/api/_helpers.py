"""Shared request helpers used across API namespace classes."""

from collections.abc import AsyncIterator
from typing import Any, TypeVar

import httpx
from pydantic import BaseModel

from .. import cache
from ..exceptions import raise_for_status
from ..headers import ResponseHeaders

T = TypeVar("T", bound=BaseModel)


async def _conditional_get(
    client: httpx.AsyncClient, url: str, params: dict | None = None
) -> tuple[Any, int | None]:
    """ETag-cached GET returning ``(json_data, total_pages)``.

    Sends ``If-None-Match`` when an ETag is cached and serves the cached body
    on 304.  ``total_pages`` comes from the ``paginate-pages`` header and is
    ``None`` on a 304 because headers are not cached.
    """
    key = str(client.build_request("GET", url, params=params).url) if params else url
    etag, cached_data = cache.get_etag(key)
    headers = {"If-None-Match": etag} if etag else {}
    response = await client.get(url, params=params, headers=headers)

    if response.status_code == 304 and cached_data is not None:
        return cached_data, None

    await raise_for_status(response)
    data = response.json()
    rh = ResponseHeaders.model_validate(dict(response.headers))
    if rh.etag:
        cache.set_etag(key, rh.etag, data, ttl=rh.ttl)
    return data, rh.paginate_pages


async def cached_get_list(
    client: httpx.AsyncClient,
    url: str,
    model: type[T],
    params: dict | None = None,
    use_cache: bool = True,
) -> list[T]:
    """ETag-cached GET returning a list of validated models.

    Set *use_cache* to ``False`` for volatile endpoints whose data changes
    faster than the server's ETag/Cache-Control lifetime reflects (e.g.
    ``/events/upcoming``, ``/currently_playing``).  When disabled, no
    ``If-None-Match`` is sent and no cache read/write occurs.
    """
    if use_cache:
        data, _ = await _conditional_get(client, url, params)
    else:
        response = await client.get(url, params=params)
        await raise_for_status(response)
        data = response.json()
    return [model.model_validate(item) for item in data]


async def cached_get_object(
    client: httpx.AsyncClient, url: str, model: type[T]
) -> T:
    """ETag-cached GET returning a single validated model."""
    data, _ = await _conditional_get(client, url)
    return model.model_validate(data)


# ── Pagination ───────────────────────────────────────────────────


async def _fetch_page(
    client: httpx.AsyncClient,
    url: str,
    *,
    params: dict | None = None,
    unwrap_key: str | None = None,
) -> tuple[list, int | None]:
    """ETag-cached GET returning ``(raw_items, total_pages)``.

    If *unwrap_key* is set and the response is a dict, the item list is
    extracted from that key (e.g. ``"results"`` for envelope responses).
    """
    data, total_pages = await _conditional_get(client, url, params)
    if unwrap_key and isinstance(data, dict):
        data = data.get(unwrap_key, data)
    return data, total_pages


async def paginate(
    client: httpx.AsyncClient,
    url: str,
    model: type[T],
    *,
    params: dict | None = None,
    per_page: int = 20,
    start_page: int = 1,
    end_page: int | None = None,
    unwrap_key: str | None = None,
) -> AsyncIterator[T]:
    """Yield validated items across pages automatically.

    Each page is ETag-cached independently.  Reads the
    ``paginate-pages`` response header to detect the last page.

    If *unwrap_key* is given, extracts the item list from that key
    in the response dict (e.g. ``"results"`` for envelope responses).

    Models with an ``id`` field are yielded once per iteration.  This
    prevents an endpoint that repeats a page from returning duplicate
    entities indefinitely.
    """
    base_params = dict(params or {})
    base_params["per_page"] = per_page
    page = start_page
    seen_ids: set[object] = set()

    while True:
        base_params["page"] = page
        items, total_pages = await _fetch_page(
            client,
            url,
            params=base_params,
            unwrap_key=unwrap_key,
        )

        new_items = 0
        for item in items:
            validated = model.model_validate(item)
            item_id = getattr(validated, "id", None)
            if item_id is not None:
                if item_id in seen_ids:
                    continue
                seen_ids.add(item_id)
            new_items += 1
            yield validated

        if end_page is not None and page >= end_page:
            break
        if total_pages is not None and page >= total_pages:
            break
        if len(items) < per_page:
            break
        if items and new_items == 0:
            break

        page += 1
