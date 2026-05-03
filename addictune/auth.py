from pydantic import BaseModel, SecretStr


class AuthResponse(BaseModel):
    api_key: SecretStr  # used as X-Session-Key for authenticated API calls
    listen_key: SecretStr  # appended as query param to stream/playlist URLs


async def login(client, network: str, email: str, password: str) -> AuthResponse:
    response = await client.post(
        f"/{network}/members/authenticate",
        data={"username": email, "password": password},
    )
    response.raise_for_status()
    return AuthResponse.model_validate(response.json())
