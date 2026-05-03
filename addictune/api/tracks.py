import httpx

from ..exceptions import raise_for_status
from ..models.track import (
    AudioQuality,
    CurrentAudioQuality,
    LikedTrack,
    SkipEvent,
    Track,
)
from ._helpers import cached_get_list, cached_get_object


class TracksAPI:
    def __init__(self, client: httpx.AsyncClient, network: str = "di"):
        self._client = client
        self._network = network

    # ── Qualities ────────────────────────────────────────────────

    async def get_qualities(self) -> list[AudioQuality]:
        return await cached_get_list(
            self._client, f"/{self._network}/qualities", AudioQuality
        )

    async def get_preferred_quality(self, user_id: int) -> CurrentAudioQuality:
        return await cached_get_object(
            self._client,
            f"/{self._network}/members/{user_id}/preferred_quality",
            CurrentAudioQuality,
        )

    async def set_preferred_quality(self, user_id: int, quality_id: int) -> None:
        url = f"/{self._network}/members/{user_id}/preferred_quality"
        data = f"quality_id={quality_id}"
        response = await self._client.post(url, content=data)
        await raise_for_status(response)

    # ── Tracks ───────────────────────────────────────────────────

    async def get_by_id(self, track_id: int) -> Track:
        return await cached_get_object(
            self._client, f"/{self._network}/tracks/{track_id}", Track
        )

    async def get_liked_track(self, user_id: int, track_id: int) -> Track | None:
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
    ) -> list[Track]:
        url = f"/{self._network}/members/{user_id}/track_votes"
        params = {"vote_type": vote_type, "per_page": per_page}
        response = await self._client.get(url, params=params)
        await raise_for_status(response)
        return [LikedTrack.model_validate(item) for item in response.json()]

    # ── Voting ───────────────────────────────────────────────────

    async def vote(self, track_id: int, direction: str = "up") -> None:
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
