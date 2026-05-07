import httpx
from pydantic import SecretStr

from .api import AuthAPI, ChannelsAPI, MixShowsAPI, PlaylistsAPI, TracksAPI, UserAPI
from .config import AddictuneSettings
from .models.auth import AuthResponse
from .models.network import BUILTIN_NETWORKS, Network
from .network_client import NetworkClient
from .transport import RetryTransport, TransportConfig


class Client:
    """Async entry point for the Addictune SDK.

    Wraps an ``httpx.AsyncClient`` and provides namespaced access to every
    AudioAddict API endpoint.  Use it as an async context manager to ensure
    the underlying HTTP connection is properly closed::

        async with Client() as client:
            ...

    Or call :meth:`close` manually when you're done.

    After instantiation, call :meth:`login` to authenticate, then scope
    operations to a specific radio network via :meth:`network`.

    Args:
        session_key: Pre-existing session key (``X-Session-Key`` header).
            If provided, you can skip :meth:`login`.
        listen_key: Pre-existing listen key for stream URLs.
        settings: Override default SDK settings (API base URL, timeout,
            default network, etc.).  Falls back to environment variables
            prefixed with ``ADDICTUNE_``.
        transport_config: Retry and circuit-breaker configuration.
        custom_networks: Additional :class:`Network` instances to
            register alongside the built-in ones.
    """

    def __init__(
        self,
        session_key: str | None = None,
        listen_key: str | None = None,
        settings: AddictuneSettings | None = None,
        transport_config: TransportConfig | None = None,
        custom_networks: list[Network] | None = None,
    ):
        self._settings = settings or AddictuneSettings()
        self._http_client = httpx.AsyncClient(
            base_url=self._settings.api_base,
            timeout=self._settings.timeout,
            transport=RetryTransport(transport_config),
        )
        self._listen_key: SecretStr | None = (
            SecretStr(listen_key) if listen_key else None
        )
        self._session_key: SecretStr | None = (
            SecretStr(session_key) if session_key else None
        )

        if session_key:
            self._http_client.headers.update({"X-Session-Key": session_key})

        # Build lookup of available networks: built-ins + custom
        self._networks: dict[str, Network] = {
            n.slug: n for n in BUILTIN_NETWORKS + (custom_networks or [])
        }

        # Cache for NetworkClient instances — same slug always returns same object
        self._network_clients: dict[str, NetworkClient] = {}

        # Client-level APIs (no network scope needed)
        self.user = UserAPI(self._http_client)

    def network(self, slug: str) -> NetworkClient:
        """Return a scoped client for the given network slug.

        The same slug always returns the same :class:`NetworkClient` instance.

        Args:
            slug: Network identifier, e.g. ``"di"``, ``"rockradio"``,
                ``"radiotunes"``.  See
                :data:`~addictune_sdk.models.network.BUILTIN_NETWORKS`
                for the full list.

        Returns:
            A :class:`NetworkClient` with ``.auth``, ``.channels``,
            ``.mixshows``, ``.playlists``, and ``.tracks`` namespaces.

        Raises:
            ValueError: If *slug* is not a registered network.
        """
        if slug not in self._networks:
            valid = ", ".join(sorted(self._networks))
            raise ValueError(
                f"Unknown network {slug!r}. "
                f"Valid networks: {valid}. "
                f"Add custom networks via AddictuneSettings.custom_networks."
            )
        if slug not in self._network_clients:
            self._network_clients[slug] = NetworkClient(
                self._http_client, self._networks[slug]
            )
        return self._network_clients[slug]

    @property
    def listen_key(self) -> str | None:
        """The authenticated user's listen key (for stream URLs), or ``None``."""
        return self._listen_key.get_secret_value() if self._listen_key else None

    @property
    def session_key(self) -> str | None:
        """The current session key, or ``None`` if not authenticated."""
        return self._session_key.get_secret_value() if self._session_key else None

    async def login(self, email: str, password: str) -> AuthResponse:
        """Authenticate with email and password.

        Stores the returned session key and listen key on this client
        so that subsequent requests are automatically authenticated.

        Args:
            email: Account email address.
            password: Account password.

        Returns:
            :class:`AuthResponse` containing ``user_id``, ``api_key``,
            and ``listen_key``.
        """
        default = self.network(self._settings.network)
        auth = await default.auth.login(email, password)
        raw_key = auth.api_key.get_secret_value()
        self._http_client.headers.update({"X-Session-Key": raw_key})
        self._session_key = SecretStr(raw_key)
        self._listen_key = SecretStr(auth.listen_key.get_secret_value())
        return auth

    async def close(self) -> None:
        """Close the underlying HTTP connection pool."""
        await self._http_client.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_) -> None:
        await self.close()


# Backward-compatible alias
AddictuneClient = Client
