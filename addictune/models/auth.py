from pydantic import BaseModel, SecretStr, model_validator


class AuthResponse(BaseModel):
    user_id: int
    api_key: SecretStr  # X-Session-Key header
    listen_key: SecretStr  # stream URL query param

    model_config = {"extra": "ignore"}

    @model_validator(mode="before")
    @classmethod
    def _normalize(cls, data: dict) -> dict:
        if not isinstance(data, dict):
            return data
        # member_sessions: {key, member_id, member: {listen_key, ...}}
        if "key" in data and "member" in data:
            return {
                "api_key": data["key"],
                "listen_key": data["member"].get("listen_key", ""),
                "user_id": data["member_id"],
            }
        # members/authenticate: {id, api_key, listen_key}
        if "id" in data and "user_id" not in data:
            data = dict(data)
            data["user_id"] = data.pop("id")
        return data
