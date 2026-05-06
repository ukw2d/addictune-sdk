import logging

import httpx
from circuitbreaker import circuit
from httpx import AsyncHTTPTransport
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from tenacity import (
    RetryCallState,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
    wait_random,
)

logger = logging.getLogger(__name__)


def _log_retry(retry_state: RetryCallState) -> None:
    error = retry_state.outcome.exception() if retry_state.outcome else None
    sleep = getattr(retry_state.next_action, "sleep", None)
    logger.warning(
        "Retry attempt %d failed with %s: %s%s",
        retry_state.attempt_number,
        type(error).__name__ if error else "Unknown",
        error,
        f", next in {sleep:.2f}s" if sleep is not None else "",
    )


class RetryConfig(BaseModel):
    max_attempts: int = 3
    wait_multiplier: float = 1.0
    wait_min: float = 2.0
    wait_max: float = 10.0
    wait_jitter: float = 1.0


class CircuitConfig(BaseModel):
    failure_threshold: int = 5
    recovery_timeout: float = 60.0
    name: str | None = None


class TransportConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="ADDICTUNE_",
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        extra="ignore",
    )

    retry: RetryConfig = Field(default_factory=RetryConfig)
    circuit: CircuitConfig = Field(default_factory=CircuitConfig)


class RetryTransport(AsyncHTTPTransport):
    """HTTP transport with retry (outer) -> circuit breaker (inner)."""

    def __init__(self, config: TransportConfig | None = None):
        super().__init__()
        config = config or TransportConfig()
        rc = config.retry
        cc = config.circuit

        self._protected_send = retry(
            stop=stop_after_attempt(rc.max_attempts),
            wait=wait_exponential(
                multiplier=rc.wait_multiplier,
                min=rc.wait_min,
                max=rc.wait_max,
            )
            + wait_random(0, rc.wait_jitter),
            retry=retry_if_exception_type((httpx.ConnectError, httpx.ReadTimeout)),
            reraise=True,
            before_sleep=_log_retry,
        )(
            circuit(
                failure_threshold=cc.failure_threshold,
                recovery_timeout=cc.recovery_timeout,
                name=cc.name,
            )(self._send_attempt)
        )

    async def _send_attempt(
        self, request: httpx.Request, body: bytes
    ) -> httpx.Response:
        return await AsyncHTTPTransport.handle_async_request(
            self,
            httpx.Request(
                method=request.method,
                url=request.url,
                headers=request.headers,
                extensions=request.extensions,
                content=body,
            ),
        )

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        return await self._protected_send(request, await request.aread())
