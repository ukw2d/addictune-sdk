import httpx

from .api import AuthAPI, ChannelsAPI, MixShowsAPI, PlaylistsAPI, TracksAPI
from .models.network import Network


class NetworkClient:
    """Scoped client for a single radio network (e.g. ``"di"``, ``"rockradio"``).

    Created by :meth:`Client.network`.  Holds the API namespaces
    (``auth``, ``channels``, ``mixshows``, ``playlists``, ``tracks``)
    scoped to a single network slug so that URL paths are automatically
    prefixed (e.g. ``/di/channels``).

    Attributes:
        auth: :class:`~addictune_sdk.api.auth.AuthAPI` — login and authentication.
        channels: :class:`~addictune_sdk.api.channels.ChannelsAPI` — browse
            channels, get now-playing info, manage favorites, and build
            stream URLs.
        mixshows: :class:`~addictune_sdk.api.mixshows.MixShowsAPI` — browse
            mix shows, episodes, and upcoming events.
        playlists: :class:`~addictune_sdk.api.playlists.PlaylistsAPI` — browse
            playlists, get playlist content, and manage followed playlists.
        tracks: :class:`~addictune_sdk.api.tracks.TracksAPI` — get track
            details, manage liked tracks, vote, and report skips.
    """

    def __init__(self, http_client: httpx.AsyncClient, network: Network):
        self._client = http_client
        self._network = network
        self.auth = AuthAPI(http_client, network.slug)
        self.channels = ChannelsAPI(http_client, network.slug, network.listen_host)
        self.mixshows = MixShowsAPI(http_client, network.slug)
        self.playlists = PlaylistsAPI(http_client, network.slug)
        self.tracks = TracksAPI(http_client, network.slug)

    @property
    def network(self) -> Network:
        """The resolved :class:`Network` this client is scoped to."""
        return self._network
