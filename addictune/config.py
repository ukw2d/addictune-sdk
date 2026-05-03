from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict

NETWORKS: dict[str, str] = {
    "di": "DI.FM",
    "radiotunes": "RadioTunes",
    "rockradio": "RockRadio",
    "jazzradio": "JazzRadio",
    "classicalradio": "ClassicalRadio",
    "zenradio": "ZenRadio",
}

LISTEN_DOMAINS: dict[str, str] = {
    "di": "di.fm",
    "radiotunes": "radiotunes.com",
    "rockradio": "rockradio.com",
    "jazzradio": "jazzradio.com",
    "classicalradio": "classicalradio.com",
    "zenradio": "zenradio.com",
}


class AddictuneSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="ADDICTUNE_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    api_base: str = "https://api.audioaddict.com/v1"
    network: str = "di"
    timeout: float = 30.0
    networks: dict[str, str] = Field(default_factory=lambda: dict(NETWORKS))
    listen_domains: dict[str, str] = Field(default_factory=lambda: dict(LISTEN_DOMAINS))

    @computed_field
    @property
    def network_name(self) -> str:
        return self.networks.get(self.network, self.network)

    @computed_field
    @property
    def resolved_listen_base(self) -> str:
        domain = self.listen_domains.get(self.network, f"{self.network}.com")
        return f"http://prem2.{domain}:80"
