import httpx
import pytest

from addictune.api.auth import AuthAPI, _APP_AUTH
from addictune.exceptions import AddictuneAuthError
from addictune.models.auth import AuthResponse
from tests.conftest import make_response


@pytest.mark.asyncio
async def test_login_session_mode(mocker, auth_payload, auth_response):
    mock_client = mocker.AsyncMock(spec=httpx.AsyncClient)
    mock_client.post.return_value = auth_response

    api = AuthAPI(mock_client, network="di")
    result = await api.login("user@example.com", "password123")

    mock_client.post.assert_called_once_with(
        "/di/member_sessions",
        json={"member_session": {"username": "user@example.com", "password": "password123"}},
        auth=_APP_AUTH,
    )
    assert isinstance(result, AuthResponse)
    assert result.api_key.get_secret_value() == auth_payload["key"]
    assert result.listen_key.get_secret_value() == auth_payload["member"]["listen_key"]
    assert result.user_id == auth_payload["member_id"]


@pytest.mark.asyncio
async def test_login_direct_mode(mocker):
    mock_client = mocker.AsyncMock(spec=httpx.AsyncClient)
    mock_client.post.return_value = make_response(
        200, {"id": 42, "api_key": "direct-key", "listen_key": "direct-listen"}
    )

    api = AuthAPI(mock_client, network="di")
    result = await api.login("user@example.com", "pass", mode="direct")

    mock_client.post.assert_called_once_with(
        "/di/members/authenticate",
        data={"username": "user@example.com", "password": "pass"},
    )
    assert isinstance(result, AuthResponse)
    assert result.api_key.get_secret_value() == "direct-key"
    assert result.listen_key.get_secret_value() == "direct-listen"
    assert result.user_id == 42


@pytest.mark.asyncio
async def test_login_uses_network_in_url(mocker, auth_response):
    mock_client = mocker.AsyncMock(spec=httpx.AsyncClient)
    mock_client.post.return_value = auth_response

    api = AuthAPI(mock_client, network="rockradio")
    await api.login("user@example.com", "pass")

    assert mock_client.post.call_args[0][0] == "/rockradio/member_sessions"


@pytest.mark.asyncio
async def test_login_invalid_credentials_raises_auth_error(mocker):
    mock_client = mocker.AsyncMock(spec=httpx.AsyncClient)
    mock_client.post.return_value = make_response(401, text="Invalid credentials")

    api = AuthAPI(mock_client, network="di")
    with pytest.raises(AddictuneAuthError, match="Invalid credentials"):
        await api.login("bad@example.com", "wrongpass")


@pytest.mark.asyncio
async def test_login_forbidden_raises_auth_error(mocker):
    mock_client = mocker.AsyncMock(spec=httpx.AsyncClient)
    mock_client.post.return_value = make_response(403, text="Forbidden")

    api = AuthAPI(mock_client, network="di")
    with pytest.raises(AddictuneAuthError):
        await api.login("user@example.com", "pass")
