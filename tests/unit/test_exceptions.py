import pytest

from addictune.exceptions import (
    AddictuneAPIError,
    AddictuneAuthError,
    AddictuneError,
    AddictuneNotFoundError,
    raise_for_status,
)
from tests.conftest import make_response


@pytest.mark.asyncio
async def test_success_response_does_not_raise():
    response = make_response(200, {"ok": True})
    await raise_for_status(response)  # no exception


@pytest.mark.asyncio
async def test_304_does_not_raise():
    response = make_response(304)
    await raise_for_status(response)


@pytest.mark.asyncio
@pytest.mark.parametrize("status_code", [401, 403])
async def test_auth_error(status_code):
    response = make_response(status_code, text="Unauthorized")
    with pytest.raises(AddictuneAuthError, match="Unauthorized"):
        await raise_for_status(response)


@pytest.mark.asyncio
async def test_not_found_error():
    response = make_response(404, text="Not Found")
    with pytest.raises(AddictuneNotFoundError, match="Not Found"):
        await raise_for_status(response)


@pytest.mark.asyncio
async def test_generic_api_error():
    response = make_response(500, text="Internal Server Error")
    with pytest.raises(AddictuneAPIError) as exc_info:
        await raise_for_status(response)
    assert exc_info.value.status_code == 500
    assert "500" in str(exc_info.value)


@pytest.mark.asyncio
async def test_api_error_empty_body_uses_reason_phrase():
    # httpx populates reason_phrase from status code when body is empty
    response = make_response(503, text="")
    with pytest.raises(AddictuneAPIError) as exc_info:
        await raise_for_status(response)
    assert exc_info.value.status_code == 503


def test_exception_hierarchy():
    assert issubclass(AddictuneAuthError, AddictuneError)
    assert issubclass(AddictuneNotFoundError, AddictuneError)
    assert issubclass(AddictuneAPIError, AddictuneError)
