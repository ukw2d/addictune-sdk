from collections.abc import AsyncIterator

import httpx

from ..exceptions import raise_for_status
from ..models.playlist import Playlist, PlaylistListenHistoryEntry, PlaylistTracks
from ._helpers import cached_get_list, cached_get_object, paginate


class PlaylistsAPI:
    """Playlist endpoints scoped to a single network.

    Accessed via ``client.network("di").playlists``.

    Provides methods to browse featured/all playlists, get playlist
    content, manage followed playlists, and record listen history.
    """

    def __init__(self, client: httpx.AsyncClient, network: str = "di"):
        self._client = client
        self._network = network

    # ── Browse ───────────────────────────────────────────────────

    async def get_featured(self) -> list[Playlist]:
        """Return featured playlists from the homepage collection.

        Results are ETag-cached.
        """
        return await cached_get_list(
            self._client,
            f"/{self._network}/playlist_collections/name/homepage-featured",
            Playlist,
            id_field="id",
        )

    def iter_playlists(
        self,
        *,
        order_by: str = "popularity",
        per_page: int = 25,
        start_page: int = 1,
        end_page: int | None = None,
    ) -> AsyncIterator[Playlist]:
        """Yield playlists across pages.

        Args:
            order_by: Sort order — ``"popularity"`` or ``"newest"``.
            per_page: Items per page (max 25).
            start_page: First page to request (1-based).
            end_page: Last page to request.  ``None`` fetches all pages.

        Yields:
            :class:`~addictune_sdk.models.playlist.Playlist` instances.

        Raises:
            ValueError: If *order_by* is invalid or *per_page* is out
                of range.
        """
        if order_by not in ("popularity", "newest"):
            raise ValueError(f"Invalid order_by: {order_by!r}")
        if per_page < 1 or per_page > 25:
            raise ValueError("per_page must be between 1 and 25")
        return paginate(
            self._client,
            f"/{self._network}/playlists",
            Playlist,
            params={"order_by": order_by, "legacy_result": "false"},
            per_page=per_page,
            start_page=start_page,
            end_page=end_page,
        )

    # ── Single playlist ──────────────────────────────────────────

    async def get_by_id(self, playlist_id: int) -> Playlist:
        """Return a single playlist by its ID.

        Args:
            playlist_id: The numeric playlist identifier.
        """
        return await cached_get_object(
            self._client,
            f"/{self._network}/playlists/{playlist_id}",
            Playlist,
            index_key=f"/{self._network}/playlists/id={playlist_id}",
        )

    async def get_content(self, playlist_id: int) -> PlaylistTracks:
        """Fetch the playable track list for a playlist.

        Args:
            playlist_id: The numeric playlist identifier.

        Returns:
            A :class:`~addictune_sdk.models.playlist.PlaylistTracks`
            containing the tracks and playback progress.
        """
        url = f"/{self._network}/playlists/{playlist_id}/play"
        response = await self._client.post(url)
        await raise_for_status(response)
        return PlaylistTracks.model_validate(response.json())

    # ── Followed ─────────────────────────────────────────────────

    def iter_followed(
        self,
        user_id: int,
        *,
        limit: int = 13,
        start_page: int = 1,
        end_page: int | None = None,
    ) -> AsyncIterator[Playlist]:
        """Yield the user's followed playlists across pages.

        Args:
            user_id: The authenticated user's ID.
            limit: Items per page (max 13).
            start_page: First page to request (1-based).
            end_page: Last page to request.  ``None`` fetches all pages.

        Yields:
            :class:`~addictune_sdk.models.playlist.Playlist` instances.

        Raises:
            ValueError: If *limit* is out of range.
        """
        if limit < 1 or limit > 13:
            raise ValueError("limit must be between 1 and 13")
        return paginate(
            self._client,
            f"/{self._network}/members/{user_id}/followed_items/playlist",
            Playlist,
            params={"order_by": "follow_date", "limit": str(limit)},
            per_page=limit,
            start_page=start_page,
            end_page=end_page,
        )

    # ── Listen history ───────────────────────────────────────────

    async def get_listen_history(
        self, playlist_id: int
    ) -> list[PlaylistListenHistoryEntry]:
        """Return the listen history for a playlist.

        Args:
            playlist_id: The numeric playlist identifier.
        """
        url = f"/{self._network}/listen_history"
        response = await self._client.get(url, params={"playlist_id": playlist_id})
        await raise_for_status(response)
        data = response.json()
        if not data:
            return []
        return [PlaylistListenHistoryEntry.model_validate(item) for item in data]

    async def add_listen_history(self, playlist_id: int, track_id: int) -> None:
        """Record that a track was listened to in a playlist.

        Args:
            playlist_id: The playlist the track belongs to.
            track_id: The track that was listened to.
        """
        url = f"/{self._network}/listen_history"
        response = await self._client.post(
            url, json={"playlist_id": playlist_id, "track_id": track_id}
        )
        if response.status_code not in (201, 204):
            await raise_for_status(response)
