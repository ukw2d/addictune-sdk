from unittest.mock import AsyncMock

import pytest

from addictune_sdk.api.auth import AuthAPI
from addictune_sdk.api.assets import AssetsAPI
from addictune_sdk.api.channels import ChannelsAPI
from addictune_sdk.api.search import SearchAPI
from addictune_sdk.client import AddictuneClient, Client
from addictune_sdk.config import AddictuneConfig
from addictune_sdk.exceptions import AddictuneAuthError
from addictune_sdk.models.auth import AuthResponse
from addictune_sdk.models.network import Network
from addictune_sdk.network_client import NetworkClient


@pytest.fixture
def config():
    return AddictuneConfig(api_base="https://api.example.com/v1", network="di")


@pytest.fixture
def patch_transport(mocker):
    """Patch RetryTransport so httpx.AsyncClient can close without real I/O."""
    mock_transport = AsyncMock()
    mocker.patch("addictune_sdk.client.RetryTransport", return_value=mock_transport)
    return mock_transport


@pytest.mark.asyncio
async def test_login_returns_auth_response(
    mocker, config, patch_transport, auth_payload
):
    mocker.patch.object(
        AuthAPI,
        "login",
        return_value=AuthResponse.model_validate(auth_payload),
    )

    async with Client(config=config) as client:
        result = await client.login("user@example.com", "pass")

    assert isinstance(result, AuthResponse)
    assert result.api_key.get_secret_value() == auth_payload["key"]


@pytest.mark.asyncio
async def test_login_sets_session_key_header(
    mocker, config, patch_transport, auth_payload
):
    auth = AuthResponse.model_validate(auth_payload)
    mocker.patch.object(AuthAPI, "login", return_value=auth)

    async with Client(config=config) as client:
        await client.login("user@example.com", "pass")
        assert client._session_keys.get(config.network) == auth_payload["key"]


@pytest.mark.asyncio
async def test_login_sets_listen_key(mocker, config, patch_transport, auth_payload):
    auth = AuthResponse.model_validate(auth_payload)
    mocker.patch.object(AuthAPI, "login", return_value=auth)

    async with Client(config=config) as client:
        await client.login("user@example.com", "pass")
        assert client.listen_key == auth_payload["member"]["listen_key"]


@pytest.mark.asyncio
async def test_login_sets_session_key_property(
    mocker, config, patch_transport, auth_payload
):
    auth = AuthResponse.model_validate(auth_payload)
    mocker.patch.object(AuthAPI, "login", return_value=auth)

    async with Client(config=config) as client:
        await client.login("user@example.com", "pass")
        assert client.session_key == auth_payload["key"]


@pytest.mark.asyncio
async def test_session_key_constructor_sets_header(config, patch_transport):
    async with Client(session_key="preloaded-key", config=config) as client:
        assert client._session_keys.get(config.network) == "preloaded-key"


@pytest.mark.asyncio
async def test_listen_key_constructor(config, patch_transport):
    async with Client(listen_key="preloaded-listen-key", config=config) as client:
        assert client.listen_key == "preloaded-listen-key"


@pytest.mark.asyncio
async def test_login_failure_raises_auth_error(mocker, config, patch_transport):
    mocker.patch.object(
        AuthAPI,
        "login",
        side_effect=AddictuneAuthError("bad credentials"),
    )

    async with Client(config=config) as client:
        with pytest.raises(AddictuneAuthError, match="bad credentials"):
            await client.login("bad@example.com", "wrong")


@pytest.mark.asyncio
async def test_context_manager_closes_http_client(mocker, config, patch_transport):
    mock_aclose = mocker.AsyncMock()

    async with Client(config=config) as client:
        client._http_client.aclose = mock_aclose

    mock_aclose.assert_called_once()


@pytest.mark.asyncio
async def test_network_returns_network_client(config, patch_transport):
    async with Client(config=config) as client:
        di = client.network("di")
        assert isinstance(di, NetworkClient)


@pytest.mark.asyncio
async def test_network_client_has_channels_api(config, patch_transport):
    async with Client(config=config) as client:
        di = client.network("di")
        assert isinstance(di.channels, ChannelsAPI)


@pytest.mark.asyncio
async def test_client_has_assets_api(config, patch_transport):
    async with Client(config=config) as client:
        assert isinstance(client.assets, AssetsAPI)


@pytest.mark.asyncio
async def test_network_client_has_search_api(config, patch_transport):
    async with Client(config=config) as client:
        di = client.network("di")
        assert isinstance(di.search, SearchAPI)


@pytest.mark.asyncio
async def test_network_client_has_auth_api(config, patch_transport):
    async with Client(config=config) as client:
        di = client.network("di")
        assert isinstance(di.auth, AuthAPI)


@pytest.mark.asyncio
async def test_network_client_network_property(config, patch_transport):
    async with Client(config=config) as client:
        di = client.network("di")
        assert di.network.slug == "di"
        assert di.network.name == "DI.FM"


@pytest.mark.asyncio
async def test_network_caches_same_instance(config, patch_transport):
    async with Client(config=config) as client:
        di1 = client.network("di")
        di2 = client.network("di")
        assert di1 is di2


@pytest.mark.asyncio
async def test_network_different_slugs_return_different_instances(
    config, patch_transport
):
    async with Client(config=config) as client:
        di = client.network("di")
        rock = client.network("rockradio")
        assert di is not rock
        assert di.network.slug == "di"
        assert rock.network.slug == "rockradio"


@pytest.mark.asyncio
async def test_network_unknown_slug_raises(config, patch_transport):
    async with Client(config=config) as client:
        with pytest.raises(ValueError, match="Unknown network 'unknown'"):
            client.network("unknown")


def test_default_config_used_when_none_provided(mocker):
    mocker.patch("addictune_sdk.client.RetryTransport", return_value=AsyncMock())
    client = Client()
    assert isinstance(client._config, AddictuneConfig)


def test_addictune_client_is_alias_for_client():
    assert AddictuneClient is Client


@pytest.mark.asyncio
async def test_custom_networks(config, patch_transport):
    custom = Network(slug="custom", name="Custom", listen_domain="custom.fm")
    async with Client(config=config, custom_networks=[custom]) as client:
        nc = client.network("custom")
        assert nc.network.name == "Custom"
        assert nc.network.listen_host == "https://listen.custom.fm"
