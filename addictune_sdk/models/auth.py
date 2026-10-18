from pydantic import BaseModel, SecretStr, model_validator


class AuthResponse(BaseModel):
    """Credentials returned after a successful login.

    Attributes:
        user_id: The authenticated user's numeric ID.
        api_key: Session key used in the ``X-Session-Key`` header.
        listen_key: Key appended to stream URLs for authentication.
        premium: Whether the account holds an active subscription, which the
            ``premium_*`` streams require. ``None`` when the payload carried
            no ``subscriptions`` list.
    """

    user_id: int
    api_key: SecretStr  # X-Session-Key header
    listen_key: SecretStr  # stream URL query param
    premium: bool | None = None

    model_config = {"extra": "ignore"}

    @model_validator(mode="before")
    @classmethod
    def _normalize(cls, data: dict) -> dict:
        if not isinstance(data, dict):
            return data
        # member_sessions: {key, member_id, member: {listen_key, subscriptions, ...}}
        if "key" in data and "member" in data:
            member = data["member"]
            return {
                "api_key": data["key"],
                "listen_key": member.get("listen_key", ""),
                "user_id": data["member_id"],
                "premium": _premium(member),
            }
        # members/authenticate: {id, api_key, listen_key, subscriptions}
        if "id" in data and "user_id" not in data:
            data = {**data, "user_id": data["id"], "premium": _premium(data)}
        return data


def _premium(member: dict) -> bool | None:
    if (subscriptions := member.get("subscriptions")) is None:
        return None
    return any(s.get("status") == "active" for s in subscriptions)
