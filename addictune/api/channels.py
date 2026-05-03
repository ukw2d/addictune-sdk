import time

import httpx

from ..exceptions import raise_for_status
from ..models.channel import (
    Channel,
    LikedChannelID,
    NowPlaying,
    TrackHistoryEntry,
)
from ._helpers import cached_get_list, cached_get_object


class ChannelsAPI:
    def __init__(self, client: httpx.AsyncClient, network: str = "di"):
        self._client = client
        self._network = network

    async def get_all(self) -> list[Channel]:
        return await cached_get_list(
            self._client, f"/{self._network}/channels", Channel
        )

    async def get_by_id(self, channel_id: int) -> Channel:
        return await cached_get_object(
            self._client, f"/{self._network}/channels/{channel_id}", Channel
        )

    async def get_track_history(self, channel_id: int) -> list[TrackHistoryEntry]:
        return await cached_get_list(
            self._client,
            f"/{self._network}/track_history/channel/{channel_id}",
            TrackHistoryEntry,
        )

    async def get_currently_playing(self) -> list[NowPlaying]:
        return await cached_get_list(
            self._client, f"/{self._network}/currently_playing", NowPlaying
        )

    async def get_routine(
        self,
        channel_id: int,
        audio_token: str,
        tune_in: bool = True,
    ) -> dict:
        """Return the raw routine tracklist response as a dict.

        The response shape is ``{"routine_id", "channel_id", "expires_on", "tracks"}``.
        Tracks contain streaming URLs that expire, so this endpoint is never ETag-cached.
        """
        url = f"/{self._network}/routines/channel/{channel_id}"
        params = {
            "tune_in": str(tune_in).lower(),
            "audio_token": audio_token,
            "_": int(time.time() * 1000),
        }
        response = await self._client.get(url, params=params)
        await raise_for_status(response)
        return response.json()

    async def add_listen_history(self, channel_id: int, track_id: int) -> None:
        url = f"/{self._network}/listen_history"
        response = await self._client.post(
            url, json={"channel_id": channel_id, "track_id": track_id}
        )
        await raise_for_status(response)

    async def get_listen_history(self, channel_id: int) -> list[dict]:
        """Get listen history for a channel. Returns raw dicts."""
        url = f"/{self._network}/listen_history/{channel_id}"
        response = await self._client.get(url)
        await raise_for_status(response)
        return response.json()

    async def get_favorites(self, user_id: int) -> list[LikedChannelID]:
        return await cached_get_list(
            self._client,
            f"/{self._network}/members/{user_id}/favorites/channels",
            LikedChannelID,
        )

    async def add_favorite(self, user_id: int, channel_id: int) -> None:
        url = f"/{self._network}/members/{user_id}/favorites/channel/{channel_id}"
        response = await self._client.post(url, json={"id": channel_id})
        await raise_for_status(response)

    async def remove_favorite(self, user_id: int, channel_id: int) -> None:
        url = f"/{self._network}/members/{user_id}/favorites/channel/{channel_id}"
        response = await self._client.delete(url)
        await raise_for_status(response)
