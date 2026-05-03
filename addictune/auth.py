import httpx

from .exceptions import raise_for_status
from .models.auth import AuthResponse


async def login(
    client: httpx.AsyncClient, network: str, email: str, password: str
) -> AuthResponse:
    response = await client.post(
        f"/{network}/members/authenticate",
        data={"username": email, "password": password},
    )
    await raise_for_status(response)
    return AuthResponse.model_validate(response.json())
