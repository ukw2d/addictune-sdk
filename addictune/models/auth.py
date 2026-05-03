from pydantic import BaseModel, SecretStr


class AuthResponse(BaseModel):
    api_key: SecretStr  # used as X-Session-Key for authenticated API calls
    listen_key: SecretStr  # appended as query param to stream/playlist URLs
