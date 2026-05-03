import httpx

from .api import ChannelsAPI
from .auth import login
from .config import AddictuneSettings
from .models.auth import AuthResponse
from .transport import RetryTransport, TransportConfig


class AddictuneClient:
    def __init__(
        self,
        session_key: str | None = None,
        settings: AddictuneSettings | None = None,
        transport_config: TransportConfig | None = None,
    ):
        self._settings = settings or AddictuneSettings()
        self._client = httpx.AsyncClient(
            base_url=self._settings.api_base,
            timeout=self._settings.timeout,
            transport=RetryTransport(transport_config),
        )
        self.channels = ChannelsAPI(self._client, self._settings.network)

        if session_key:
            self._client.headers.update({"X-Session-Key": session_key})

    async def login(self, email: str, password: str) -> AuthResponse:
        auth = await login(self._client, self._settings.network, email, password)
        self._client.headers.update({"X-Session-Key": auth.api_key.get_secret_value()})
        return auth

    async def close(self) -> None:
        await self._client.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_) -> None:
        await self.close()
