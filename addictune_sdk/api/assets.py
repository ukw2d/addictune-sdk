import httpx

from ..exceptions import raise_for_status


class AssetsAPI:
    """Public artwork and other unauthenticated asset downloads."""

    def __init__(self, client: httpx.AsyncClient):
        self._client = client

    async def get_bytes(self, url: str) -> bytes:
        """Download a public asset URL and return its raw bytes."""
        response = await self._client.get(url)
        await raise_for_status(response)
        return response.content

