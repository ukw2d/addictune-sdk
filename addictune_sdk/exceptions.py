import httpx


class AddictuneError(Exception):
    pass


class AddictuneAuthError(AddictuneError):
    pass


class AddictuneNotFoundError(AddictuneError):
    pass


class AddictuneAPIError(AddictuneError):
    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        super().__init__(f"HTTP {status_code}: {message}")


async def raise_for_status(response: httpx.Response) -> None:
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
