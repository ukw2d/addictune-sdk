import httpx

from .. import cache
from ..headers import ResponseHeaders


class ChannelsAPI:
    def __init__(self, client: httpx.AsyncClient, network: str = "di"):
        self._client = client
        self._network = network

    async def get_all(self) -> list:
        url = f"/{self._network}/channels"
        etag, cached_data = cache.get_etag(url)

        headers = {"If-None-Match": etag} if etag else {}
        response = await self._client.get(url, headers=headers)

        if response.status_code == 304 and cached_data is not None:
            return cached_data

        response.raise_for_status()
        data = response.json()
        rh = ResponseHeaders.model_validate(dict(response.headers))

        if rh.etag:
            cache.set_etag(url, rh.etag, data, ttl=rh.ttl)

        return data
