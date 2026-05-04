import httpx

from .api import AuthAPI, ChannelsAPI, TracksAPI
from .models.network import Network


class NetworkClient:
    """Scoped client for a single radio network (e.g. ``"di"``, ``"rockradio"``).

    Created by :meth:`Client.network`.  Holds the API namespaces
    (``auth``, ``channels``, ``tracks``) scoped to a single network slug
    so that URL paths are automatically prefixed (e.g. ``/di/channels``).
    """

    def __init__(self, http_client: httpx.AsyncClient, network: Network):
        self._client = http_client
        self._network = network
        self.auth = AuthAPI(http_client, network.slug)
        self.channels = ChannelsAPI(http_client, network.slug, network.listen_base)
        self.tracks = TracksAPI(http_client, network.slug)

    @property
    def network(self) -> Network:
        """The resolved :class:`Network` this client is scoped to."""
        return self._network
