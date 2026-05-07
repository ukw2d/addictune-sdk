import httpx


class AddictuneError(Exception):
    """Base exception for all SDK errors."""


class AddictuneAuthError(AddictuneError):
    """Raised on 401 / 403 responses (invalid or expired credentials)."""


class AddictuneNotFoundError(AddictuneError):
    """Raised on 404 responses (resource not found)."""


class AddictuneAPIError(AddictuneError):
    """Raised on unexpected HTTP errors (non-2xx / non-304).

    Attributes:
        status_code: The HTTP status code returned by the server.
    """

    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        super().__init__(f"HTTP {status_code}: {message}")


async def raise_for_status(response: httpx.Response) -> None:
    """Raise a typed SDK exception for non-success responses."""
    if response.is_success or response.status_code == 304:
        return
    message = response.text.strip() or response.reason_phrase
    match response.status_code:
        case 401 | 403:
            raise AddictuneAuthError(message)
        case 404:
            raise AddictuneNotFoundError(message)
        case _:
            raise AddictuneAPIError(response.status_code, message)
