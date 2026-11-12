import base64
import json

import httpx
import pytest

from addictune_sdk.api.auth import AuthAPI, _APP_AUTH
from addictune_sdk.exceptions import AddictuneAuthError
from addictune_sdk.models.auth import AuthResponse
from tests.conftest import make_response


@pytest.mark.asyncio
async def test_login_posts_member_session(mocker, auth_payload, auth_response):
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
@pytest.mark.parametrize(
    "network", ["di", "radiotunes", "rockradio", "jazzradio", "classicalradio", "zenradio"]
)
async def test_login_sends_accepted_application_identity(network, auth_payload):
    def respond(request):
        assert request.method == "POST"
        assert request.url.path == f"/v1/{network}/member_sessions"
        expected = base64.b64encode(b"ephemeron:dayeiph0ne@pp").decode()
        assert request.headers["Authorization"] == f"Basic {expected}"
        assert json.loads(request.content) == {
            "member_session": {"username": "member@example.test", "password": "test-password"}
        }
        return httpx.Response(201, json=auth_payload)

    async with httpx.AsyncClient(
        base_url="https://api.audioaddict.com/v1",
        transport=httpx.MockTransport(respond),
    ) as client:
        result = await AuthAPI(client, network).login("member@example.test", "test-password")

    assert result.user_id == auth_payload["member_id"]
    assert result.api_key.get_secret_value() == auth_payload["key"]


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
        await api.login("[EMAIL_REDACTED]", "pass")


@pytest.mark.asyncio
async def test_login_unprocessable_raises_auth_error(mocker):
    """The API answers 422 for a wrong username/password."""
    mock_client = mocker.AsyncMock(spec=httpx.AsyncClient)
    mock_client.post.return_value = make_response(422, text="Invalid login")

    api = AuthAPI(mock_client, network="di")
    with pytest.raises(AddictuneAuthError, match="Invalid login"):
        await api.login("[EMAIL_REDACTED]", "pass")
        await api.login("user@example.com", "pass")
