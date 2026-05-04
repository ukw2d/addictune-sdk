"""Shared request helpers used across API namespace classes."""

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
) -> list[T]:
    """ETag-cached GET that returns a list of validated models.

    1. Checks the ETag cache for *url*.
    2. Sends ``If-None-Match`` if a cached ETag exists.
    3. On 304, returns models validated from cached data.
    4. On success, stores the new ETag, indexes items (if *id_field*
       is given), and returns validated models.
    """
    etag, cached_data = cache.get_etag(url)

    headers = {"If-None-Match": etag} if etag else {}
    response = await client.get(url, headers=headers)

    if response.status_code == 304 and cached_data is not None:
        return [model.model_validate(item) for item in cached_data]

    await raise_for_status(response)
    data = response.json()
    rh = ResponseHeaders.model_validate(dict(response.headers))

    if rh.etag:
        cache.set_etag(url, rh.etag, data, ttl=rh.ttl)
        if id_field:
            cache.index_list(url, data, id_field=id_field, ttl=rh.ttl)

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
        cache.set_etag(url, rh.etag, data, ttl=rh.ttl)

    return model.model_validate(data)
