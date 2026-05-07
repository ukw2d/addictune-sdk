from typing import Literal

import httpx

from ..exceptions import raise_for_status
from ..models.auth import AuthResponse

_APP_AUTH = httpx.BasicAuth("streams", "diradio")


class AuthAPI:
    """Authentication endpoints scoped to a single network.

    Accessed via ``client.network("di").auth``.
    """

    def __init__(self, client: httpx.AsyncClient, network: str = "di"):
        self._client = client
        self._network = network

    async def login(
        self,
        email: str,
        password: str,
        mode: Literal["session", "direct"] = "session",
    ) -> AuthResponse:
        """Authenticate and return normalised credentials.

        Args:
            email: Account email address.
            password: Account password.
            mode: ``"session"`` creates a full-privilege session via
                ``/member_sessions`` (default).  ``"direct"`` performs
                a lighter ``/members/authenticate`` call that returns a
                read-only API key.

        Returns:
            :class:`~addictune_sdk.models.auth.AuthResponse` with
            ``user_id``, ``api_key``, and ``listen_key``.
        """
        if mode == "session":
            response = await self._client.post(
                f"/{self._network}/member_sessions",
                json={"member_session": {"username": email, "password": password}},
                auth=_APP_AUTH,
            )
        else:
            response = await self._client.post(
                f"/{self._network}/members/authenticate",
                data={"username": email, "password": password},
            )
        await raise_for_status(response)
        return AuthResponse.model_validate(response.json())
