from unittest.mock import AsyncMock

import pytest
from pydantic import SecretStr

from addictune.api.auth import AuthAPI
from addictune.api.channels import ChannelsAPI
from addictune.client import AddictuneClient
from addictune.config import AddictuneSettings
from addictune.exceptions import AddictuneAuthError
from addictune.models.auth import AuthResponse


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

    async with AddictuneClient(settings=settings) as client:
        result = await client.login("user@example.com", SecretStr("pass"))

    assert isinstance(result, AuthResponse)
    assert result.api_key.get_secret_value() == auth_payload["key"]


@pytest.mark.asyncio
async def test_login_sets_session_key_header(
    mocker, settings, patch_transport, auth_payload
):
    auth = AuthResponse.model_validate(auth_payload)
    mocker.patch.object(AuthAPI, "login", return_value=auth)

    async with AddictuneClient(settings=settings) as client:
        await client.login("user@example.com", SecretStr("pass"))
        assert client._client.headers.get("x-session-key") == auth_payload["key"]


@pytest.mark.asyncio
async def test_login_sets_listen_key(mocker, settings, patch_transport, auth_payload):
    auth = AuthResponse.model_validate(auth_payload)
    mocker.patch.object(AuthAPI, "login", return_value=auth)

    async with AddictuneClient(settings=settings) as client:
        await client.login("user@example.com", SecretStr("pass"))
        assert client.listen_key == auth_payload["member"]["listen_key"]


@pytest.mark.asyncio
async def test_session_key_constructor_sets_header(settings, patch_transport):
    async with AddictuneClient(
        session_key="preloaded-key", settings=settings
    ) as client:
        assert client._client.headers.get("x-session-key") == "preloaded-key"


@pytest.mark.asyncio
async def test_listen_key_constructor(settings, patch_transport):
    async with AddictuneClient(
        listen_key="preloaded-listen-key", settings=settings
    ) as client:
        assert client.listen_key == "preloaded-listen-key"


@pytest.mark.asyncio
async def test_login_failure_raises_auth_error(mocker, settings, patch_transport):
    mocker.patch.object(
        AuthAPI,
        "login",
        side_effect=AddictuneAuthError("bad credentials"),
    )

    async with AddictuneClient(settings=settings) as client:
        with pytest.raises(AddictuneAuthError, match="bad credentials"):
            await client.login("bad@example.com", SecretStr("wrong"))


@pytest.mark.asyncio
async def test_context_manager_closes_http_client(mocker, settings, patch_transport):
    mock_aclose = mocker.AsyncMock()

    async with AddictuneClient(settings=settings) as client:
        client._client.aclose = mock_aclose

    mock_aclose.assert_called_once()


@pytest.mark.asyncio
async def test_channels_api_attached(settings, patch_transport):
    async with AddictuneClient(settings=settings) as client:
        assert isinstance(client.channels, ChannelsAPI)


@pytest.mark.asyncio
async def test_auth_api_attached(settings, patch_transport):
    async with AddictuneClient(settings=settings) as client:
        assert isinstance(client.auth, AuthAPI)


def test_default_settings_used_when_none_provided(mocker):
    mocker.patch("addictune.client.RetryTransport", return_value=AsyncMock())
    client = AddictuneClient()
    assert isinstance(client._settings, AddictuneSettings)
