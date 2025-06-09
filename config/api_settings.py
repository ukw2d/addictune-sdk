# transport_settings.py
from pydantic import Field, model_serializer, field_serializer, AnyHttpUrl
from pydantic_settings import BaseSettings
from typing import Optional, Callable
from httpx import Limits, URL
from src.config.base_settings import BaseSettingsWithYAML

class APITransportLimitSettings(BaseSettings):
    max_connections: int = Field(default=100)
    max_keepalive_connections: int = Field(default=20)
    keepalive_expiry: float = Field(default=5.0)

    @model_serializer(mode="wrap")
    def return_limits(self, nxt):
        return Limits(**nxt(self))

class APITransportSettings(BaseSettings):
    verify: bool = Field(default=False)
    cert: Optional[str] = None
    limits: APITransportLimitSettings = Field(default_factory=APITransportLimitSettings)
    proxy: Optional[str] = None
    uds: Optional[str] = None
    local_address: Optional[str] = None
    retries: int = Field(default=0)


class TransportCircuitSettings(BaseSettings):
    failure_threshold: int = Field(default=5)
    recovery_timeout: float = Field(default=60.0)
    name: Optional[str] = None
    expected_exception: Optional[type[Exception]] = Field(default=None)
    fallback_function: Optional[Callable] = None


class TransportLimiterSettings(BaseSettings):
    max_rate: float = Field(default=10.0)
    time_period: float = Field(default=1.0)


class TransportSettings(BaseSettings):
    core: APITransportSettings = Field(default_factory=APITransportSettings)
    circuit: TransportCircuitSettings = Field(default_factory=TransportCircuitSettings)
    limiter: TransportLimiterSettings = Field(default_factory=TransportLimiterSettings)

class APIClientSettings(BaseSettings):
    base_url: AnyHttpUrl
    headers: dict = {}
    verify: bool = False
    timeout: float = 30.0

    @field_serializer("base_url")
    def serialize_base_url(self, v):
        if v:
            return URL(str(v))

class APISettings(BaseSettingsWithYAML):
    @classmethod
    def get_yaml_filename(cls) -> str:
        return "api_settings.yaml"

    transport: TransportSettings
    api_client: APIClientSettings
