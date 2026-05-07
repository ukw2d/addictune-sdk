"""Network model and built-in registry for AudioAddict radio networks."""

from __future__ import annotations

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
        name: Human-readable display name (e.g. ``"DI.FM"``, ``"RockRadio"``).
        listen_domain: Domain used to construct stream URLs (e.g. ``"di.fm"``).
        listen_host: Full streaming host.  If not provided, derived from
            ``listen_domain`` as ``https://listen.{listen_domain}``.
    """

    slug: str
    name: str
    listen_domain: str
    listen_host: str = ""

    model_config = {"frozen": True}

    @model_validator(mode="after")
    def _derive_listen_host(self) -> Network:
        if not self.listen_host:
            object.__setattr__(
                self, "listen_host", f"https://listen.{self.listen_domain}"
            )
        return self


# ── Built-in networks ────────────────────────────────────────────

BUILTIN_NETWORKS: list[Network] = [
    Network(slug="di", name="DI.FM", listen_domain="di.fm"),
    Network(slug="radiotunes", name="RadioTunes", listen_domain="radiotunes.com"),
    Network(slug="rockradio", name="RockRadio", listen_domain="rockradio.com"),
    Network(slug="jazzradio", name="JazzRadio", listen_domain="jazzradio.com"),
    Network(
        slug="classicalradio",
        name="ClassicalRadio",
        listen_domain="classicalradio.com",
    ),
    Network(slug="zenradio", name="ZenRadio", listen_domain="zenradio.com"),
]
