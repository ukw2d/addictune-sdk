"""Network model and built-in registry for AudioAddict radio networks."""

from pydantic import BaseModel, model_validator

STREAM_QUALITIES: dict[str, str] = {
    "high": "premium_high",
    "medium": "premium",
    "low": "premium_medium",
}


class Network(BaseModel):
    """A single AudioAddict radio network.

    Attributes:
        slug: URL path segment used in API calls (e.g. ``"di"``, ``"rockradio"``).
        name: Human-readable display name (e.g. ``"DI.FM"``, ``"Rock Radio"``).
        listen_domain: Domain used to construct stream URLs (e.g. ``"di.fm"``).
        listen_host: Full streaming host.  If not provided, derived from
            ``listen_domain`` as ``https://listen.{listen_domain}``.
    """

    slug: str
    name: str
    listen_domain: str
    listen_host: str = ""

    model_config = {"frozen": True}

    @model_validator(mode="before")
    @classmethod
    def _derive_listen_host(cls, data: dict) -> dict:
        if not data.get("listen_host"):
            return {**data, "listen_host": f"https://listen.{data['listen_domain']}"}
        return data


# ── Built-in networks ────────────────────────────────────────────

BUILTIN_NETWORKS: list[Network] = [
    Network(slug="di", name="DI.FM", listen_domain="di.fm"),
    Network(slug="radiotunes", name="RadioTunes", listen_domain="radiotunes.com"),
    Network(slug="rockradio", name="Rock Radio", listen_domain="rockradio.com"),
    Network(slug="jazzradio", name="Jazz Radio", listen_domain="jazzradio.com"),
    Network(
        slug="classicalradio",
        name="Classical Radio",
        listen_domain="classicalradio.com",
    ),
    Network(slug="zenradio", name="Zen Radio", listen_domain="zenradio.com"),
]
