from unittest.mock import AsyncMock

import pytest
from pydantic import SecretStr

from addictune.api.auth import AuthAPI
from addictune.api.channels import ChannelsAPI
from addictune.client import AddictuneClient, Client
from addictune.config import AddictuneSettings
from addictune.exceptions import AddictuneAuthError
from addictune.models.auth import AuthResponse
from addictune.models.network import Network
from addictune.network_client import NetworkClient


@pytest.fixture
def settings():
    return AddictuneSettings(api_base="https://api.example.com/v1", network="di")


@pytest.fixture
def patch_transport(mocker):
    """Patch RetryTransport so httpx.AsyncClient can close without real I/O."""
    mock_transport = AsyncMock()
    mocker.patch("addictune.client.RetryTransport", return_value=mock_transport)
    return mock_transport


@pytest.mark.asyncio
async def test_login_returns_auth_response(
    mocker, settings, patch_transport, auth_payload
):
    mocker.patch.object(
        AuthAPI,
        "login",
        return_value=AuthResponse.model_validate(auth_payload),
    )

    async with Client(settings=settings) as client:
        result = await client.login("user@example.com", SecretStr("pass"))

    assert isinstance(result, AuthResponse)
    assert result.api_key.get_secret_value() == auth_payload["key"]


@pytest.mark.asyncio
async def test_login_sets_session_key_header(
    mocker, settings, patch_transport, auth_payload
):
    auth = AuthResponse.model_validate(auth_payload)
    mocker.patch.object(AuthAPI, "login", return_value=auth)

    async with Client(settings=settings) as client:
        await client.login("user@example.com", SecretStr("pass"))
        assert client._http_client.headers.get("x-session-key") == auth_payload["key"]


@pytest.mark.asyncio
async def test_login_sets_listen_key(mocker, settings, patch_transport, auth_payload):
    auth = AuthResponse.model_validate(auth_payload)
    mocker.patch.object(AuthAPI, "login", return_value=auth)

    async with Client(settings=settings) as client:
        await client.login("user@example.com", SecretStr("pass"))
        assert client.listen_key == auth_payload["member"]["listen_key"]


@pytest.mark.asyncio
async def test_login_sets_session_key_property(
    mocker, settings, patch_transport, auth_payload
):
    auth = AuthResponse.model_validate(auth_payload)
    mocker.patch.object(AuthAPI, "login", return_value=auth)

    async with Client(settings=settings) as client:
        await client.login("user@example.com", SecretStr("pass"))
        assert client.session_key == auth_payload["key"]


@pytest.mark.asyncio
async def test_session_key_constructor_sets_header(settings, patch_transport):
    async with Client(session_key="preloaded-key", settings=settings) as client:
        assert client._http_client.headers.get("x-session-key") == "preloaded-key"


@pytest.mark.asyncio
async def test_listen_key_constructor(settings, patch_transport):
    async with Client(listen_key="preloaded-listen-key", settings=settings) as client:
        assert client.listen_key == "preloaded-listen-key"


@pytest.mark.asyncio
async def test_login_failure_raises_auth_error(mocker, settings, patch_transport):
    mocker.patch.object(
        AuthAPI,
        "login",
        side_effect=AddictuneAuthError("bad credentials"),
    )

    async with Client(settings=settings) as client:
        with pytest.raises(AddictuneAuthError, match="bad credentials"):
            await client.login("bad@example.com", SecretStr("wrong"))


@pytest.mark.asyncio
async def test_context_manager_closes_http_client(mocker, settings, patch_transport):
    mock_aclose = mocker.AsyncMock()

    async with Client(settings=settings) as client:
        client._http_client.aclose = mock_aclose

    mock_aclose.assert_called_once()


@pytest.mark.asyncio
async def test_network_returns_network_client(settings, patch_transport):
    async with Client(settings=settings) as client:
        di = client.network("di")
        assert isinstance(di, NetworkClient)


@pytest.mark.asyncio
async def test_network_client_has_channels_api(settings, patch_transport):
    async with Client(settings=settings) as client:
        di = client.network("di")
        assert isinstance(di.channels, ChannelsAPI)


@pytest.mark.asyncio
async def test_network_client_has_auth_api(settings, patch_transport):
    async with Client(settings=settings) as client:
        di = client.network("di")
        assert isinstance(di.auth, AuthAPI)


@pytest.mark.asyncio
async def test_network_client_network_property(settings, patch_transport):
    async with Client(settings=settings) as client:
        di = client.network("di")
        assert di.network.slug == "di"
        assert di.network.name == "DI.FM"


@pytest.mark.asyncio
async def test_network_caches_same_instance(settings, patch_transport):
    async with Client(settings=settings) as client:
        di1 = client.network("di")
        di2 = client.network("di")
        assert di1 is di2


@pytest.mark.asyncio
async def test_network_different_slugs_return_different_instances(
    settings, patch_transport
):
    async with Client(settings=settings) as client:
        di = client.network("di")
        rock = client.network("rockradio")
        assert di is not rock
        assert di.network.slug == "di"
        assert rock.network.slug == "rockradio"


@pytest.mark.asyncio
async def test_network_unknown_slug_raises(settings, patch_transport):
    async with Client(settings=settings) as client:
        with pytest.raises(ValueError, match="Unknown network 'unknown'"):
            client.network("unknown")


def test_default_settings_used_when_none_provided(mocker):
    mocker.patch("addictune.client.RetryTransport", return_value=AsyncMock())
    client = Client()
    assert isinstance(client._settings, AddictuneSettings)


def test_addictune_client_is_alias_for_client():
    assert AddictuneClient is Client


@pytest.mark.asyncio
async def test_custom_networks(settings, patch_transport):
    custom = Network(slug="custom", name="Custom", listen_domain="custom.fm")
    async with Client(settings=settings, custom_networks=[custom]) as client:
        nc = client.network("custom")
        assert nc.network.name == "Custom"
        assert nc.network.listen_base == "http://prem2.custom.fm:80"
