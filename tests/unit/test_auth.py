import httpx
import pytest

from addictune.auth import login
from addictune.exceptions import AddictuneAuthError
from addictune.models.auth import AuthResponse
from tests.conftest import make_response


@pytest.mark.asyncio
async def test_login_success(mocker, auth_payload, auth_response):
    mock_client = mocker.AsyncMock(spec=httpx.AsyncClient)
    mock_client.post.return_value = auth_response

    result = await login(mock_client, "di", "user@example.com", "password123")

    mock_client.post.assert_called_once_with(
        "/di/members/authenticate",
        data={"username": "user@example.com", "password": "password123"},
    )
    assert isinstance(result, AuthResponse)
    assert result.api_key.get_secret_value() == auth_payload["api_key"]
    assert result.listen_key.get_secret_value() == auth_payload["listen_key"]


@pytest.mark.asyncio
async def test_login_uses_network_in_url(mocker, auth_response):
    mock_client = mocker.AsyncMock(spec=httpx.AsyncClient)
    mock_client.post.return_value = auth_response

    await login(mock_client, "rockradio", "user@example.com", "pass")

    call_url = mock_client.post.call_args[0][0]
    assert call_url == "/rockradio/members/authenticate"


@pytest.mark.asyncio
async def test_login_invalid_credentials_raises_auth_error(mocker):
    mock_client = mocker.AsyncMock(spec=httpx.AsyncClient)
    mock_client.post.return_value = make_response(401, text="Invalid credentials")

    with pytest.raises(AddictuneAuthError, match="Invalid credentials"):
        await login(mock_client, "di", "bad@example.com", "wrongpass")


@pytest.mark.asyncio
async def test_login_forbidden_raises_auth_error(mocker):
    mock_client = mocker.AsyncMock(spec=httpx.AsyncClient)
    mock_client.post.return_value = make_response(403, text="Forbidden")

    with pytest.raises(AddictuneAuthError):
        await login(mock_client, "di", "user@example.com", "pass")
