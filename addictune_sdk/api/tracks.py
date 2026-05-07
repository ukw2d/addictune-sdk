from collections.abc import AsyncIterator

import httpx

from ..exceptions import raise_for_status
from ..models.track import (
    AudioQuality,
    CurrentAudioQuality,
    LikedTrack,
    SkipEvent,
    Track,
)
from ._helpers import cached_get_list, cached_get_object, paginate


class TracksAPI:
    """Track endpoints scoped to a single network.

    Accessed via ``client.network("di").tracks``.

    Provides methods to get track details, manage liked tracks,
    vote on tracks, report skips, and manage audio quality preferences.
    """

    def __init__(self, client: httpx.AsyncClient, network: str = "di"):
        self._client = client
        self._network = network

    # ── Qualities ────────────────────────────────────────────────

    async def get_qualities(self) -> list[AudioQuality]:
        """Return the available audio quality tiers for this network."""
        return await cached_get_list(
            self._client, f"/{self._network}/qualities", AudioQuality, id_field="id"
        )

    async def get_preferred_quality(self, user_id: int) -> CurrentAudioQuality:
        """Return the user's currently selected audio quality.

        Args:
            user_id: The authenticated user's ID.
        """
        return await cached_get_object(
            self._client,
            f"/{self._network}/members/{user_id}/preferred_quality",
            CurrentAudioQuality,
        )

    async def set_preferred_quality(self, user_id: int, quality_id: int) -> None:
        """Change the user's preferred audio quality.

        Args:
            user_id: The authenticated user's ID.
            quality_id: The quality tier ID (from :meth:`get_qualities`).
        """
        url = f"/{self._network}/members/{user_id}/preferred_quality"
        data = f"quality_id={quality_id}"
        response = await self._client.post(url, content=data)
        await raise_for_status(response)

    # ── Tracks ───────────────────────────────────────────────────

    async def get_by_id(self, track_id: int) -> Track:
        """Return a single track by its ID.

        Args:
            track_id: The numeric track identifier.
        """
        return await cached_get_object(
            self._client,
            f"/{self._network}/tracks/{track_id}",
            Track,
            index_key=f"/{self._network}/tracks/id={track_id}",
        )

    async def get_liked_track(self, user_id: int, track_id: int) -> Track | None:
        """Return a liked track, or ``None`` if the user hasn't liked it.

        Args:
            user_id: The authenticated user's ID.
            track_id: The track to look up.
        """
        url = f"/{self._network}/members/{user_id}/track_votes/{track_id}"
        response = await self._client.get(url)
        await raise_for_status(response)
        data = response.json()
        if not data:
            return None
        item = data[0] if isinstance(data, list) else data
        return LikedTrack.model_validate(item)

    async def get_liked_tracks(
        self,
        user_id: int,
        vote_type: str = "up",
        per_page: int = 20,
        page: int = 1,
    ) -> list[Track]:
        """Fetch a single page of liked tracks.

        For auto-advancing across all pages, use :meth:`iter_liked_tracks`.

        Args:
            user_id: The authenticated user's ID.
            vote_type: ``"up"`` or ``"down"``.
            per_page: Items per page.
            page: Page number (1-based).
        """
        url = f"/{self._network}/members/{user_id}/track_votes"
        params = {"vote_type": vote_type, "per_page": per_page, "page": page}
        response = await self._client.get(url, params=params)
        await raise_for_status(response)
        return [LikedTrack.model_validate(item) for item in response.json()]

    def iter_liked_tracks(
        self,
        user_id: int,
        vote_type: str = "up",
        per_page: int = 20,
        start_page: int = 1,
        end_page: int | None = None,
    ) -> AsyncIterator[Track]:
        """Yield liked tracks across all pages automatically.

        Each page is ETag-cached independently.

        Args:
            user_id: The authenticated user's ID.
            vote_type: ``"up"`` or ``"down"``.
            per_page: Items per page.
            start_page: First page to request (1-based).
            end_page: Last page to request.  ``None`` fetches all pages.

        Yields:
            :class:`~addictune_sdk.models.track.Track` instances.
        """
        url = f"/{self._network}/members/{user_id}/track_votes"
        params = {"vote_type": vote_type}
        return paginate(
            self._client,
            url,
            LikedTrack,
            params=params,
            per_page=per_page,
            start_page=start_page,
            end_page=end_page,
        )

    # ── Voting ───────────────────────────────────────────────────

    async def vote(self, track_id: int, direction: str = "up") -> None:
        """Vote on a track or remove an existing vote.

        Args:
            track_id: The track to vote on.
            direction: ``"up"``, ``"down"``, or ``"delete"`` to remove
                an existing vote.

        Raises:
            ValueError: If *direction* is not one of the allowed values.
        """
        if direction not in ("up", "down", "delete"):
            raise ValueError(f"Invalid vote direction: {direction}")
        if direction == "delete":
            url = f"/{self._network}/tracks/{track_id}/vote"
            response = await self._client.delete(url)
        else:
            url = f"/{self._network}/tracks/{track_id}/vote/{direction}"
            response = await self._client.post(url, json={"direction": direction})
        await raise_for_status(response)

    # ── Skip events ──────────────────────────────────────────────

    async def skip_track(
        self,
        track_id: int,
        channel_id: int | None = None,
        playlist_id: int | None = None,
        skipped_at: int | None = None,
        length: int | None = None,
    ) -> None:
        """Report that a track was skipped.

        Args:
            track_id: The track that was skipped.
            channel_id: The channel the track was playing on, if any.
            playlist_id: The playlist the track was playing from, if any.
            skipped_at: Unix timestamp of when the skip occurred.
            length: How many seconds into the track the skip happened.
        """
        event = SkipEvent(
            track_id=track_id,
            channel_id=channel_id,
            playlist_id=playlist_id,
            skipped_at=skipped_at,
            length=length,
        )
        url = f"/{self._network}/skip_events"
        response = await self._client.post(
            url, json=event.model_dump(exclude_none=True)
        )
        await raise_for_status(response)
