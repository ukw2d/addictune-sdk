from collections.abc import AsyncIterator

import httpx

from ..exceptions import raise_for_status
from ..models.mixshow import MixShow, ShowEpisode
from ._helpers import cached_get_object, paginate


class MixShowsAPI:
    def __init__(self, client: httpx.AsyncClient, network: str = "di"):
        self._client = client
        self._network = network

    # ── Shows ────────────────────────────────────────────────────

    async def get_by_id(self, show_id: int) -> MixShow:
        return await cached_get_object(
            self._client,
            f"/{self._network}/shows/{show_id}",
            MixShow,
        )

    def iter_shows(
        self,
        *,
        active: bool = True,
        per_page: int = 20,
        start_page: int = 1,
        end_page: int | None = None,
    ) -> AsyncIterator[MixShow]:
        """Yield mix shows across pages.

        The API wraps results in a ``{"results": [...]}`` envelope;
        the ``_unwrap_results`` validator on :class:`MixShow` handles
        this when items are validated individually.
        """
        return paginate(
            self._client,
            f"/{self._network}/shows",
            MixShow,
            params={"active": str(active).lower()},
            per_page=per_page,
            start_page=start_page,
            end_page=end_page,
            unwrap_key="results",
        )

    # ── Episodes ─────────────────────────────────────────────────

    def iter_episodes(
        self,
        show_id: int,
        *,
        per_page: int = 20,
        start_page: int = 1,
        end_page: int | None = None,
    ) -> AsyncIterator[ShowEpisode]:
        """Yield episodes for a show across pages."""
        return paginate(
            self._client,
            f"/{self._network}/shows/{show_id}/episodes",
            ShowEpisode,
            per_page=per_page,
            start_page=start_page,
            end_page=end_page,
        )

    async def get_upcoming(self, limit: int = 24) -> list[ShowEpisode]:
        """Fetch upcoming mix show events."""
        url = f"/{self._network}/events/upcoming"
        response = await self._client.get(url, params={"limit": limit})
        await raise_for_status(response)
        return [ShowEpisode.model_validate(item) for item in response.json()]

    # ── Followed ─────────────────────────────────────────────────

    def iter_followed(
        self,
        user_id: int,
        *,
        active: bool = True,
        per_page: int = 20,
        start_page: int = 1,
        end_page: int | None = None,
    ) -> AsyncIterator[MixShow]:
        """Yield the user's followed mix shows across pages."""
        return paginate(
            self._client,
            f"/{self._network}/members/{user_id}/followed_items/show",
            MixShow,
            params={"active": str(active).lower()},
            per_page=per_page,
            start_page=start_page,
            end_page=end_page,
        )
