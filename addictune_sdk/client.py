import logging

import httpx
from pydantic import SecretStr

from .api import AssetsAPI, UserAPI
from . import cache
from .config import AddictuneConfig
from .exceptions import AddictuneAuthError
from .models.auth import AuthResponse
from .models.network import BUILTIN_NETWORKS, Network
from .network_client import NetworkClient
from .transport import RetryTransport

logger = logging.getLogger(__name__)


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
        session_key: Pre-existing session key for the default network.
            If provided alongside *credentials*, you can defer per-network
            sessions to :meth:`ensure_session` without calling :meth:`login`.
        listen_key: Pre-existing listen key for stream URLs.
        credentials: ``(email, password)`` tuple.  When supplied, allows
            :meth:`ensure_session` to mint sessions for any network on demand
            without an explicit :meth:`login` call first.  Useful when
            restoring a session from a keyring / cache.
        config: Override default SDK settings (API base URL, timeout,
            default network, retry, circuit breaker, etc.).
        custom_networks: Additional :class:`Network` instances to
            register alongside the built-in ones.
    """

    def __init__(
        self,
        session_key: str | None = None,
        listen_key: str | None = None,
        credentials: tuple[str, str] | None = None,
        config: AddictuneConfig | None = None,
        custom_networks: list[Network] | None = None,
    ):
        self._config = config or AddictuneConfig()
        self._session_keys: dict[str, str] = {}
        self._credentials: tuple[str, str] | None = credentials
        self._http_client = httpx.AsyncClient(
            base_url=self._config.api_base,
            timeout=self._config.timeout,
            transport=RetryTransport(self._config),
            event_hooks={"request": [self._inject_session_key]},
        )
        self._public_http_client = httpx.AsyncClient(
            timeout=self._config.timeout,
            follow_redirects=True,
            transport=RetryTransport(self._config),
        )
        self._listen_key: SecretStr | None = (
            SecretStr(listen_key) if listen_key else None
        )

        if session_key:
            self._session_keys[self._config.network] = session_key

        # Build lookup of available networks: built-ins + custom
        self._networks: dict[str, Network] = {
            n.slug: n for n in BUILTIN_NETWORKS + (custom_networks or [])
        }

        # Cache for NetworkClient instances — same slug always returns same object
        self._network_clients: dict[str, NetworkClient] = {}

        # Client-level APIs (no network scope needed)
        self.assets = AssetsAPI(self._public_http_client)
        self.user = UserAPI(self._http_client)

        # Propagate default cache TTL
        cache.set_default_ttl(self._config.default_cache_ttl)

        logger.debug(
            "Client initialised (api_base=%s, network=%s, timeout=%.1fs)",
            self._config.api_base,
            self._config.network,
            self._config.timeout,
        )

    async def _inject_session_key(self, request: httpx.Request) -> None:
        # path: /v1/<slug>/...
        parts = request.url.path.strip("/").split("/")
        slug = parts[1] if len(parts) > 1 else self._config.network
        if key := self._session_keys.get(slug):
            request.headers["X-Session-Key"] = key

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
                f"Add custom networks via custom_networks."
            )
        if slug not in self._network_clients:
            self._network_clients[slug] = NetworkClient(
                self._http_client, self._networks[slug], self._public_http_client
            )
        return self._network_clients[slug]

    @property
    def listen_key(self) -> str | None:
        """The authenticated user's listen key (for stream URLs), or ``None``."""
        return self._listen_key.get_secret_value() if self._listen_key else None

    @property
    def session_key(self) -> str | None:
        """The session key for the default network, or ``None`` if not authenticated."""
        return self._session_keys.get(self._config.network)

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
        self._credentials = (email, password)
        auth = await self.network(self._config.network).auth.login(email, password)
        self._session_keys[self._config.network] = auth.api_key.get_secret_value()
        self._listen_key = SecretStr(auth.listen_key.get_secret_value())
        logger.info(
            "Login successful (user_id=%s, network=%s)",
            auth.user_id,
            self._config.network,
        )
        return auth

    async def ensure_session(self, slug: str) -> None:
        """Sessions are per-network; mint one from stored credentials on demand.

        Args:
            slug: Network identifier to ensure a session for.

        Raises:
            AddictuneAuthError: If no session exists and no credentials are stored.
        """
        if slug in self._session_keys:
            return
        if self._credentials is None:
            raise AddictuneAuthError(
                f"No session for {slug!r} and no credentials to mint one"
            )
        auth = await self.network(slug).auth.login(*self._credentials)
        self._session_keys[slug] = auth.api_key.get_secret_value()

    async def close(self) -> None:
        """Close the underlying HTTP connection pool."""
        logger.debug("Closing HTTP connection pool")
        await self._http_client.aclose()
        await self._public_http_client.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_) -> None:
        await self.close()


# Backward-compatible alias
AddictuneClient = Client
