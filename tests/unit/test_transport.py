import httpx
import pytest

from addictune_sdk.config import AddictuneConfig, CircuitConfig, RetryConfig
from addictune_sdk.transport import RetryTransport


@pytest.fixture
def transport(mocker):
    mocker.patch("addictune_sdk.transport.asyncio.sleep")
    config = AddictuneConfig(
        retry=RetryConfig(max_attempts=3, wait_jitter=0.0),
        circuit=CircuitConfig(failure_threshold=2),
    )
    return RetryTransport(config)


@pytest.mark.asyncio
async def test_retries_connect_error_then_succeeds(mocker, transport):
    inner = mocker.patch(
        "addictune_sdk.transport.AsyncHTTPTransport.handle_async_request",
        side_effect=[httpx.ConnectError("boom"), httpx.Response(200)],
    )
    request = httpx.Request("POST", "https://api.example/v1/x", json={"a": 1})

    response = await transport.handle_async_request(request)

    assert response.status_code == 200
    assert inner.call_count == 2
    assert inner.call_args[0][0] is request


@pytest.mark.asyncio
async def test_circuit_opens_after_threshold(mocker, transport):
    inner = mocker.patch(
        "addictune_sdk.transport.AsyncHTTPTransport.handle_async_request",
        side_effect=httpx.ReadTimeout("slow"),
    )
    request = httpx.Request("GET", "https://api.example/v1/x")

    with pytest.raises(httpx.ConnectError, match="Circuit breaker is open"):
        await transport.handle_async_request(request)

    assert inner.call_count == 2
