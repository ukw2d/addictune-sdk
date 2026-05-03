import httpx

from .. import cache
from ..exceptions import raise_for_status
from ..headers import ResponseHeaders
from ..models.channel import Channel


class ChannelsAPI:
    def __init__(self, client: httpx.AsyncClient, network: str = "di"):
        self._client = client
        self._network = network

    async def get_all(self) -> list[Channel]:
        url = f"/{self._network}/channels"
        etag, cached_data = cache.get_etag(url)

        headers = {"If-None-Match": etag} if etag else {}
        response = await self._client.get(url, headers=headers)

        if response.status_code == 304 and cached_data is not None:
            return [Channel.model_validate(ch) for ch in cached_data]

        await raise_for_status(response)
        data = response.json()
        rh = ResponseHeaders.model_validate(dict(response.headers))

        if rh.etag:
            cache.set_etag(url, rh.etag, data, ttl=rh.ttl)

        return [Channel.model_validate(ch) for ch in data]
