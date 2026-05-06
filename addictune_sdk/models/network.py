"""Network model and built-in registry for AudioAddict radio networks."""

from __future__ import annotations

from pydantic import BaseModel, model_validator


class Network(BaseModel):
    """A single AudioAddict radio network.

    Attributes:
        slug: URL path segment used in API calls (e.g. ``"di"``, ``"rockradio"``).
        name: Human-readable display name (e.g. ``"DI.FM"``, ``"RockRadio"``).
        listen_domain: Domain used to construct stream URLs (e.g. ``"di.fm"``).
        listen_base: Full streaming base URL.  If not provided, derived from
            ``listen_domain`` as ``https://prem2.{listen_domain}``.
        stream_suffixes: Mapping of quality key → channel key suffix for stream
            URLs.  For example ``{"hi": "_hi", "aac": ""}`` means the ``hi``
            quality appends ``_hi`` to the channel key while ``aac`` appends
            nothing.  Defaults to ``{"hi": "_hi", "aac": ""}`` (DI.FM-style).
    """

    slug: str
    name: str
    listen_domain: str
    listen_base: str = ""
    stream_suffixes: dict[str, str] = {"hi": "_hi", "aac": ""}

    model_config = {"frozen": True}

    @model_validator(mode="after")
    def _derive_listen_base(self) -> Network:
        if not self.listen_base:
            object.__setattr__(
                self, "listen_base", f"https://prem2.{self.listen_domain}"
            )
        return self


# ── Built-in networks ────────────────────────────────────────────

BUILTIN_NETWORKS: list[Network] = [
    Network(slug="di", name="DI.FM", listen_domain="di.fm"),
    Network(slug="radiotunes", name="RadioTunes", listen_domain="radiotunes.com"),
    Network(
        slug="rockradio",
        name="RockRadio",
        listen_domain="rockradio.com",
        stream_suffixes={"hi": "", "aac": "_aac"},
    ),
    Network(slug="jazzradio", name="JazzRadio", listen_domain="jazzradio.com"),
    Network(
        slug="classicalradio",
        name="ClassicalRadio",
        listen_domain="classicalradio.com",
    ),
    Network(slug="zenradio", name="ZenRadio", listen_domain="zenradio.com"),
]
