from typing import Literal

import httpx

from ..exceptions import raise_for_status
from ..models.auth import AuthResponse

_APP_AUTH = httpx.BasicAuth("streams", "diradio")


class AuthAPI:
    def __init__(self, client: httpx.AsyncClient, network: str = "di"):
        self._client = client
        self._network = network

    async def login(
        self,
        email: str,
        password: str,
        mode: Literal["session", "direct"] = "session",
    ) -> AuthResponse:
        """Login and return normalised credentials.

        mode="session"  — POST /member_sessions with app Basic Auth.
                          Returns a full-privilege session key (default).
        mode="direct"   — POST /members/authenticate, no Basic Auth.
                          Returns a read-only API key.
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
