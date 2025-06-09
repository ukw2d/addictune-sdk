from typing import Optional

from httpx import AsyncClient, AsyncHTTPTransport
from loguru import logger

from src.api_client.api_transport import APITransport



def get_httpx_transport(transport_settings: dict) -> AsyncHTTPTransport:
    transport = APITransport(transport_settings)
    logger.debug(f"HTTPX transport created with settings: {transport_settings}")
    return transport


def get_httpx_client(client_settings: dict, transport: Optional[AsyncHTTPTransport] = None) -> AsyncClient:
    client = AsyncClient(**client_settings, transport=transport)
    logger.debug(f"HTTPX client created with settings: {client_settings} and transport: {transport}")
    return client
