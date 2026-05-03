import httpx

from .config import AddictuneSettings
from .transport import RetryTransport, TransportConfig


def create_client(
    settings: AddictuneSettings | None = None,
    transport_config: TransportConfig | None = None,
) -> httpx.AsyncClient:
    settings = settings or AddictuneSettings()
    return httpx.AsyncClient(
        base_url=settings.api_base,
        timeout=settings.timeout,
        transport=RetryTransport(transport_config),
    )
