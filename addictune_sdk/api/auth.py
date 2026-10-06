import httpx

from ..exceptions import AddictuneAuthError, raise_for_status
from ..models.auth import AuthResponse

_APP_AUTH = httpx.BasicAuth("streams", "diradio")


class AuthAPI:
    """Authentication endpoints scoped to a single network.

    Accessed via ``client.network("di").auth``.
    """

    def __init__(self, client: httpx.AsyncClient, network: str = "di"):
        self._client = client
        self._network = network

    async def login(self, email: str, password: str) -> AuthResponse:
        """Create a full-privilege session via ``/member_sessions``.

        Args:
            email: Account email address.
            password: Account password.

        Returns:
            :class:`~addictune_sdk.models.auth.AuthResponse` with
            ``user_id``, ``api_key``, and ``listen_key``.
        """
        response = await self._client.post(
            f"/{self._network}/member_sessions",
            json={"member_session": {"username": email, "password": password}},
            auth=_APP_AUTH,
        )
        if response.status_code == 422:  # API answers 422 for a bad username/password
            raise AddictuneAuthError(response.text.strip() or response.reason_phrase)
        await raise_for_status(response)
        return AuthResponse.model_validate(response.json())
