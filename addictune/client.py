import httpx
from pydantic import SecretStr

from .api import AuthAPI, ChannelsAPI, TracksAPI
from .config import AddictuneSettings
from .models.auth import AuthResponse
from .transport import RetryTransport, TransportConfig


class AddictuneClient:
    def __init__(
        self,
        session_key: str | None = None,
        listen_key: str | None = None,
        settings: AddictuneSettings | None = None,
        transport_config: TransportConfig | None = None,
    ):
        self._settings = settings or AddictuneSettings()
        self._client = httpx.AsyncClient(
            base_url=self._settings.api_base,
            timeout=self._settings.timeout,
            transport=RetryTransport(transport_config),
        )
        self.auth = AuthAPI(self._client, self._settings.network)
        self.channels = ChannelsAPI(
            self._client,
            self._settings.network,
            self._settings.resolved_listen_base,
        )
        self.tracks = TracksAPI(self._client, self._settings.network)

        self._listen_key: str | None = listen_key

        if session_key:
            self._client.headers.update({"X-Session-Key": session_key})

    @property
    def listen_key(self) -> str | None:
        return self._listen_key

    async def login(self, email: str, password: SecretStr) -> AuthResponse:
        auth = await self.auth.login(email, password.get_secret_value())
        self._client.headers.update({"X-Session-Key": auth.api_key.get_secret_value()})
        self._listen_key = auth.listen_key.get_secret_value()
        return auth

    async def close(self) -> None:
        await self._client.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_) -> None:
        await self.close()
