import time
from urllib.parse import urljoin, urlparse

import httpx

from ..exceptions import raise_for_status
from ..models.channel import (
    Channel,
    ChannelFilter,
    LikedChannelID,
    ListenHistoryEntry,
    NowPlaying,
    TrackHistoryEntry,
)
from ..models.network import STREAM_QUALITIES
from ..models.track import ChannelTracklist
from ._helpers import cached_get_list, cached_get_object


class ChannelsAPI:
    """Channel endpoints scoped to a single network.

    Accessed via ``client.network("di").channels``.

    Provides methods to browse channels, get now-playing information,
    manage channel favorites, retrieve track history, and build
    direct stream URLs.
    """

    def __init__(
        self,
        client: httpx.AsyncClient,
        network: str = "di",
        listen_host: str = "",
        stream_qualities: dict[str, str] | None = None,
        public_client: httpx.AsyncClient | None = None,
    ):
        self._client = client
        self._network = network
        self._listen_host = listen_host
        self._stream_qualities = stream_qualities or STREAM_QUALITIES
        self._public_client = public_client or client

    async def get_all(self) -> list[Channel]:
        """Return all channels on the network.

        Results are ETag-cached; subsequent calls may not hit the
        network if data hasn't changed.
        """
        return await cached_get_list(
            self._client, f"/{self._network}/channels", Channel, id_field="id"
        )

    async def get_by_id(self, channel_id: int) -> Channel:
        """Return a single channel by its ID.

        Args:
            channel_id: The numeric channel identifier.
        """
        return await cached_get_object(
            self._client,
            f"/{self._network}/channels/{channel_id}",
            Channel,
            index_key=f"/{self._network}/channels/id={channel_id}",
        )

    async def get_filter(self, key: str) -> ChannelFilter:
        """Return a channel filter by key.

        Args:
            key: Channel filter key, e.g. ``"popular"``.
        """
        return await cached_get_object(
            self._client,
            f"/{self._network}/channel_filters/key/{key}",
            ChannelFilter,
        )

    async def get_track_history(self, channel_id: int) -> list[TrackHistoryEntry]:
        """Return the recent track history for a channel.

        Args:
            channel_id: The numeric channel identifier.
        """
        return await cached_get_list(
            self._client,
            f"/{self._network}/track_history/channel/{channel_id}",
            TrackHistoryEntry,
        )

    async def get_currently_playing(self) -> list[NowPlaying]:
        """Return now-playing information for all channels.

        Each entry includes the channel ID/key and the currently
        playing track.
        """
        return await cached_get_list(
            self._client, f"/{self._network}/currently_playing", NowPlaying
        )

    async def get_routine(
        self,
        channel_id: int,
        audio_token: str,
        tune_in: bool = True,
    ) -> ChannelTracklist:
        """Return the current routine/tracklist for a live channel.

        Args:
            channel_id: The numeric channel identifier.
            audio_token: Audio token (typically from the channel data).
            tune_in: Whether to register a tune-in event (default ``True``).

        Returns:
            A :class:`~addictune_sdk.models.track.ChannelTracklist`
            containing the routine's tracks.
        """
        url = f"/{self._network}/routines/channel/{channel_id}"
        params = {
            "tune_in": str(tune_in).lower(),
            "audio_token": audio_token,
            "_": int(time.time() * 1000),
        }
        response = await self._client.get(url, params=params)
        await raise_for_status(response)
        return ChannelTracklist.model_validate(response.json())

    async def add_listen_history(self, channel_id: int, track_id: int) -> None:
        """Record that a track was listened to on a channel.

        Args:
            channel_id: The channel the track played on.
            track_id: The track that was listened to.
        """
        url = f"/{self._network}/listen_history"
        response = await self._client.post(
            url, json={"channel_id": channel_id, "track_id": track_id}
        )
        await raise_for_status(response)

    async def get_listen_history(self, channel_id: int) -> list[ListenHistoryEntry]:
        """Return the listen history for a channel.

        Args:
            channel_id: The numeric channel identifier.
        """
        url = f"/{self._network}/listen_history/{channel_id}"
        response = await self._client.get(url)
        await raise_for_status(response)
        return [ListenHistoryEntry.model_validate(e) for e in response.json()]

    async def get_favorites(self, user_id: int) -> list[LikedChannelID]:
        """Return the list of channel IDs favorited by a user.

        Args:
            user_id: The authenticated user's ID.
        """
        return await cached_get_list(
            self._client,
            f"/{self._network}/members/{user_id}/favorites/channels",
            LikedChannelID,
        )

    async def add_favorite(self, user_id: int, channel_id: int) -> None:
        """Add a channel to the user's favorites.

        Args:
            user_id: The authenticated user's ID.
            channel_id: The channel to favorite.
        """
        url = f"/{self._network}/members/{user_id}/favorites/channel/{channel_id}"
        response = await self._client.post(url, json={"id": channel_id})
        await raise_for_status(response)

    async def get_favorite(
        self, user_id: int, channel_id: int
    ) -> LikedChannelID | None:
        """Check if a channel is in the user's favorites.

        Args:
            user_id: The authenticated user's ID.
            channel_id: The channel to check.

        Returns:
            :class:`~addictune_sdk.models.channel.LikedChannelID` if the
            channel is a favorite, otherwise ``None``.
        """
        url = f"/{self._network}/members/{user_id}/favorites/channel/{channel_id}"
        response = await self._client.get(url)
        if response.status_code == 404:
            return None
        await raise_for_status(response)
        data = response.json()
        if not data:
            return None
        item = data[0] if isinstance(data, list) else data
        return LikedChannelID.model_validate(item)

    async def remove_favorite(self, user_id: int, channel_id: int) -> None:
        """Remove a channel from the user's favorites.

        Args:
            user_id: The authenticated user's ID.
            channel_id: The channel to unfavorite.
        """
        url = f"/{self._network}/members/{user_id}/favorites/channel/{channel_id}"
        response = await self._client.delete(url)
        await raise_for_status(response)

    def get_stream_url(
        self, channel_key: str, listen_key: str, quality: str = "high"
    ) -> str:
        """Return the direct stream URL for a channel.

        Format: ``https://listen.{domain}/{quality_path}/{channel_key}.pls?listen_key={key}``

        Args:
            channel_key: The channel's key (e.g. ``"trance"``).
            listen_key: The authenticated user's listen key.
            quality: Quality tier — ``"high"`` (320k MP3), ``"medium"``
                (128k AAC), or ``"low"`` (64k AAC).  Defaults to ``"high"``.

        Returns:
            A fully resolved streaming URL.
        """
        quality_path = self._stream_qualities.get(quality, STREAM_QUALITIES["high"])
        return f"{self._listen_host}/{quality_path}/{channel_key}.pls?listen_key={listen_key}"

    async def resolve_stream_url(self, url: str) -> str:
        """Resolve a PLS/M3U playlist URL to its first audio stream URL."""
        path = urlparse(url).path.lower()
        if not path.endswith((".pls", ".m3u", ".m3u8")):
            return url

        response = await self._public_client.get(url)
        await raise_for_status(response)

        lines = (line.strip() for line in response.text.splitlines())
        if path.endswith(".pls"):
            lines = (
                line.split("=", 1)[1].strip()
                for line in lines
                if "=" in line and line.split("=", 1)[0].lower().startswith("file")
            )
        else:
            lines = (line for line in lines if line and not line.startswith("#"))

        for stream_url in lines:
            if stream_url:
                return urljoin(url, stream_url)
        raise ValueError("No stream URL found in playlist")
