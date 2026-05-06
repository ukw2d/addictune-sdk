import httpx
import pytest

from addictune.api.user import UserAPI
from addictune.exceptions import AddictuneAPIError, AddictuneNotFoundError
from addictune.models.user import PaymentMethod, Ping, PremiumStatus
from tests.conftest import make_response

# ── ping ─────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_ping_returns_ping(mocker, ping_payload):
    mock_client = mocker.AsyncMock(spec=httpx.AsyncClient)
    mock_client.get.return_value = make_response(200, ping_payload)

    api = UserAPI(mock_client)
    result = await api.ping()

    assert isinstance(result, Ping)
    assert result.api_version == 1.0
    assert result.ip == "2a01:4f8:1c1a:9009::1"
    assert result.country == "Germany"
    assert result.country_code == "DE"
    assert result.time is not None
    mock_client.get.assert_called_once_with("/ping")


@pytest.mark.asyncio
async def test_ping_raises_on_error(mocker):
    mock_client = mocker.AsyncMock(spec=httpx.AsyncClient)
    mock_client.get.return_value = make_response(500, text="Internal Server Error")

    api = UserAPI(mock_client)
    with pytest.raises(AddictuneAPIError):
        await api.ping()


# ── get_payment_method ───────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_payment_method_returns_method(mocker, payment_method_payload):
    mock_client = mocker.AsyncMock(spec=httpx.AsyncClient)
    mock_client.get.return_value = make_response(200, payment_method_payload)

    api = UserAPI(mock_client)
    result = await api.get_payment_method(user_id=13716939, network="di")

    assert isinstance(result, PaymentMethod)
    assert result.id == 544029
    assert result.active is True
    assert result.description == "visa 6077"
    assert result.country == "BY"
    assert result.archived_at is None
    assert result.first_name == "Uladzislau"
    assert result.last_name == "Andreyeu"
    assert result.member_id == 13716939
    assert result.payment_type is not None
    assert result.payment_type.id == 13
    assert result.payment_type.billable is True
    assert result.payment_type.key == "stripe"
    assert result.payment_type.label == "Credit Card"
    assert result.payment_type.indirect_billing is False
    assert result.payment_type.require_address is True
    mock_client.get.assert_called_once_with("/di/members/13716939/payment_method")


@pytest.mark.asyncio
async def test_get_payment_method_uses_network(mocker, payment_method_payload):
    mock_client = mocker.AsyncMock(spec=httpx.AsyncClient)
    mock_client.get.return_value = make_response(200, payment_method_payload)

    api = UserAPI(mock_client)
    await api.get_payment_method(user_id=99999, network="rockradio")

    call_url = mock_client.get.call_args[0][0]
    assert call_url == "/rockradio/members/99999/payment_method"


@pytest.mark.asyncio
async def test_get_payment_method_raises_on_not_found(mocker):
    mock_client = mocker.AsyncMock(spec=httpx.AsyncClient)
    mock_client.get.return_value = make_response(404, text="Not Found")

    api = UserAPI(mock_client)
    with pytest.raises(AddictuneNotFoundError):
        await api.get_payment_method(user_id=1, network="di")


@pytest.mark.asyncio
async def test_get_payment_method_raises_on_server_error(mocker):
    mock_client = mocker.AsyncMock(spec=httpx.AsyncClient)
    mock_client.get.return_value = make_response(500, text="Internal Server Error")

    api = UserAPI(mock_client)
    with pytest.raises(AddictuneAPIError):
        await api.get_payment_method(user_id=1, network="di")


# ── check_premium_status ─────────────────────────────────────────────


@pytest.mark.asyncio
async def test_check_premium_status_returns_status(mocker, premium_status_payload):
    mock_client = mocker.AsyncMock(spec=httpx.AsyncClient)
    mock_client.get.return_value = make_response(200, premium_status_payload)

    api = UserAPI(mock_client)
    result = await api.check_premium_status(network="di")

    assert isinstance(result, PremiumStatus)
    assert result.listener_type == "premium"
    assert result.territories == []
    assert result.window_unit == "hours"
    assert result.window_duration == 1
    assert result.limit == 15
    assert result.skips_remaining is None
    assert result.expires_at is None
    mock_client.get.assert_called_once_with("/di/skip_rulesets/active")


@pytest.mark.asyncio
async def test_check_premium_status_uses_network(mocker, premium_status_payload):
    mock_client = mocker.AsyncMock(spec=httpx.AsyncClient)
    mock_client.get.return_value = make_response(200, premium_status_payload)

    api = UserAPI(mock_client)
    await api.check_premium_status(network="jazzradio")

    call_url = mock_client.get.call_args[0][0]
    assert call_url == "/jazzradio/skip_rulesets/active"


@pytest.mark.asyncio
async def test_check_premium_status_raises_on_error(mocker):
    mock_client = mocker.AsyncMock(spec=httpx.AsyncClient)
    mock_client.get.return_value = make_response(500, text="Internal Server Error")

    api = UserAPI(mock_client)
    with pytest.raises(AddictuneAPIError):
        await api.check_premium_status(network="di")
