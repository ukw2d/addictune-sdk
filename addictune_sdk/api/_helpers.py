"""Shared request helpers used across API namespace classes."""

from collections.abc import AsyncIterator
from typing import TypeVar

import httpx
from pydantic import BaseModel

from .. import cache
from ..exceptions import raise_for_status
from ..headers import ResponseHeaders

T = TypeVar("T", bound=BaseModel)


async def cached_get_list(
    client: httpx.AsyncClient,
    url: str,
    model: type[T],
    id_field: str | None = None,
    params: dict | None = None,
    use_cache: bool = True,
) -> list[T]:
    """ETag-cached GET that returns a list of validated models.

    1. Checks the ETag cache for *url*.
    2. Sends ``If-None-Match`` if a cached ETag exists.
    3. On 304, returns models validated from cached data.
    4. On success, stores the new ETag, indexes items (if *id_field*
       is given), and returns validated models.

    Set *use_cache* to ``False`` for volatile endpoints whose data changes
    faster than the server's ETag/Cache-Control lifetime can reflect
    (e.g. ``/events/upcoming``, ``/currently_playing``).  When disabled,
    no ``If-None-Match`` is sent, no cache read/write occurs, and a fresh
    response is always returned.
    """
    if not use_cache:
        if params:
            response = await client.get(url, params=params)
        else:
            response = await client.get(url)
        await raise_for_status(response)
        return [model.model_validate(item) for item in response.json()]

    cache_key = (
        str(client.build_request("GET", url, params=params).url) if params else url
    )
    etag, cached_data = cache.get_etag(cache_key)

    headers = {"If-None-Match": etag} if etag else {}
    if params:
        response = await client.get(url, params=params, headers=headers)
    else:
        response = await client.get(url, headers=headers)

    if response.status_code == 304 and cached_data is not None:
        return [model.model_validate(item) for item in cached_data]

    await raise_for_status(response)
    data = response.json()
    rh = ResponseHeaders.model_validate(dict(response.headers))

    if rh.etag:
        ttl = cache.resolve_ttl(rh.ttl)
        cache.set_etag(cache_key, rh.etag, data, ttl=ttl)
        if id_field:
            cache.index_list(cache_key, data, id_field=id_field, ttl=ttl)

    return [model.model_validate(item) for item in data]


async def cached_get_object(
    client: httpx.AsyncClient,
    url: str,
    model: type[T],
    index_key: str | None = None,
) -> T:
    """ETag-cached GET that returns a single validated model.

    If *index_key* is given, checks the item index first (populated
    by :func:`cached_get_list` with ``id_field``).  Falls back to
    HTTP + ETag caching on miss.
    """
    # Try the item index first (populated from a previous list fetch)
    if index_key:
        indexed = cache.get_indexed(index_key)
        if indexed is not None:
            return model.model_validate(indexed)

    etag, cached_data = cache.get_etag(url)

    headers = {"If-None-Match": etag} if etag else {}
    response = await client.get(url, headers=headers)

    if response.status_code == 304 and cached_data is not None:
        return model.model_validate(cached_data)

    await raise_for_status(response)
    data = response.json()
    rh = ResponseHeaders.model_validate(dict(response.headers))

    if rh.etag:
        cache.set_etag(url, rh.etag, data, ttl=cache.resolve_ttl(rh.ttl))

    return model.model_validate(data)


# ── Pagination ───────────────────────────────────────────────────


async def _fetch_page(
    client: httpx.AsyncClient,
    url: str,
    *,
    params: dict | None = None,
    unwrap_key: str | None = None,
) -> tuple[list, int | None]:
    """ETag-cached GET returning (raw_items, total_pages).

    ``total_pages`` comes from the ``paginate-pages`` response header
    and is ``None`` on 304 (cache hit) since headers aren't available.

    If *unwrap_key* is given and the response is a dict, extracts the
    list under that key (e.g. ``"results"`` for envelope responses).
    """
    etag, cached_data = cache.get_etag(
        str(client.build_request("GET", url, params=params).url)
    )
    headers = {"If-None-Match": etag} if etag else {}
    response = await client.get(url, params=params, headers=headers)

    if response.status_code == 304 and cached_data is not None:
        if unwrap_key and isinstance(cached_data, dict):
            return cached_data.get(unwrap_key, cached_data), None
        return cached_data, None

    await raise_for_status(response)
    data = response.json()
    items = (
        data.get(unwrap_key, data) if unwrap_key and isinstance(data, dict) else data
    )
    rh = ResponseHeaders.model_validate(dict(response.headers))
    if rh.etag:
        cache.set_etag(str(response.url), rh.etag, data, ttl=cache.resolve_ttl(rh.ttl))
    return items, rh.paginate_pages


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
