import httpx

from ..exceptions import raise_for_status
from ..models.search import SearchResults


class SearchAPI:
    """Search endpoints scoped to a single network."""

    def __init__(self, client: httpx.AsyncClient, network: str = "di"):
        self._client = client
        self._network = network

    async def query(self, query: str) -> SearchResults:
        """Search across channels, shows, playlists, and tracks."""
        query = query.strip()
        if not query:
            raise ValueError("query must not be empty")

        response = await self._client.get(
            f"/{self._network}/search", params={"q": query}
        )
        await raise_for_status(response)
        return SearchResults.model_validate(response.json())

