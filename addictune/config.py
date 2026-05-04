from pydantic_settings import BaseSettings, SettingsConfigDict


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
