import httpx
from pydantic import SecretStr

from .config import AddictuneSettings
from .models.auth import AuthResponse
from .models.network import BUILTIN_NETWORKS, Network
from .network_client import NetworkClient
from .transport import RetryTransport, TransportConfig


class Client:
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
        self._listen_key: str | None = listen_key
        self._session_key: str | None = session_key

        if session_key:
            self._http_client.headers.update({"X-Session-Key": session_key})

        # Build lookup of available networks: built-ins + custom
        self._networks: dict[str, Network] = {
            n.slug: n for n in BUILTIN_NETWORKS + (custom_networks or [])
        }

        # Cache for NetworkClient instances — same slug always returns same object
        self._network_clients: dict[str, NetworkClient] = {}

    def network(self, slug: str) -> NetworkClient:
        """Return a scoped client for the given network slug.

        The same slug always returns the same NetworkClient instance.
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
        return self._listen_key

    @property
    def session_key(self) -> str | None:
        return self._session_key

    async def login(self, email: str, password: SecretStr) -> AuthResponse:
        # Login always goes through the default network from settings
        default = self.network(self._settings.network)
        auth = await default.auth.login(email, password.get_secret_value())
        self._http_client.headers.update(
            {"X-Session-Key": auth.api_key.get_secret_value()}
        )
        self._session_key = auth.api_key.get_secret_value()
        self._listen_key = auth.listen_key.get_secret_value()
        return auth

    async def close(self) -> None:
        await self._http_client.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_) -> None:
        await self.close()


# Backward-compatible alias
AddictuneClient = Client
