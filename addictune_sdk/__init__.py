"""Addictune SDK — async Python client for the AudioAddict Radio API.

Quick start::

    from addictune_sdk import Client

    async with Client() as client:
        await client.login("user@example.com", "password")

        di = client.network("di")
        channels = await di.channels.get_all()

The SDK targets AudioAddict-powered networks including DI.FM, RadioTunes,
RockRadio, JazzRadio, ClassicalRadio, and ZenRadio.  Each network is
accessed through a :class:`NetworkClient` obtained via
:meth:`Client.network`.

Supported networks are registered as built-ins (see
:data:`~addictune_sdk.models.network.BUILTIN_NETWORKS`) and can be
extended with custom :class:`Network` instances passed to the
:class:`Client` constructor.
"""

from .client import AddictuneClient, Client
from .config import AddictuneSettings
from .exceptions import (
    AddictuneAPIError,
    AddictuneAuthError,
    AddictuneError,
    AddictuneNotFoundError,
)
from .models import (
    BUILTIN_NETWORKS,
    Artist,
    AudioFormat,
    AudioQuality,
    AudioQualityDetail,
    AuthResponse,
    Channel,
    ChannelArtist,
    ChannelTracklist,
    ContentAsset,
    CurrentAudioQuality,
    ImageSet,
    LikedChannelID,
    LikedTrack,
    ListenHistoryEntry,
    MixShow,
    Network,
    NowPlaying,
    PaymentMethod,
    PaymentType,
    Ping,
    Playlist,
    PlaylistListenHistoryEntry,
    PlaylistProgress,
    PlaylistTag,
    PlaylistTracks,
    PremiumStatus,
    ShowChannel,
    ShowEpisode,
    SimilarChannel,
    SkipEvent,
    Track,
    TrackHistoryEntry,
    UpcomingEvent,
    Votes,
)
from .network_client import NetworkClient

__all__ = [
    "Client",
    "AddictuneClient",
    "AddictuneSettings",
    "AddictuneError",
    "AddictuneAuthError",
    "AddictuneNotFoundError",
    "AddictuneAPIError",
    "Artist",
    "AudioFormat",
    "AudioQuality",
    "AudioQualityDetail",
    "AuthResponse",
    "BUILTIN_NETWORKS",
    "Channel",
    "ChannelArtist",
    "ChannelTracklist",
    "ContentAsset",
    "CurrentAudioQuality",
    "ImageSet",
    "LikedChannelID",
    "LikedTrack",
    "ListenHistoryEntry",
    "MixShow",
    "Network",
    "NetworkClient",
    "NowPlaying",
    "PaymentMethod",
    "PaymentType",
    "Playlist",
    "PlaylistListenHistoryEntry",
    "PlaylistProgress",
    "PlaylistTag",
    "PlaylistTracks",
    "Ping",
    "PremiumStatus",
    "ShowChannel",
    "ShowEpisode",
    "SimilarChannel",
    "SkipEvent",
    "Track",
    "TrackHistoryEntry",
    "UpcomingEvent",
    "Votes",
]
