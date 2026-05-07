from pydantic_settings import BaseSettings, SettingsConfigDict


class AddictuneSettings(BaseSettings):
    """SDK configuration loaded from environment variables or a ``.env`` file.

    All variables are prefixed with ``ADDICTUNE_``.  For example,
    ``ADDICTUNE_API_BASE`` overrides the default API URL.

    Attributes:
        api_base: Base URL of the AudioAddict API.
        network: Default network slug used by :meth:`Client.login`.
        timeout: HTTP request timeout in seconds.
    """

    model_config = SettingsConfigDict(
        env_prefix="ADDICTUNE_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    api_base: str = "https://api.audioaddict.com/v1"
    network: str = "di"
    timeout: float = 30.0
