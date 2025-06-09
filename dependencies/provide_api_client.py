from httpx import AsyncClient
from src.api_client.api_client import get_httpx_client, get_httpx_transport

def provide_http_client(api_config: dict, transport_config: dict) -> AsyncClient:
    transport = get_httpx_transport(transport_config)
    return get_httpx_client(api_config, transport=transport)