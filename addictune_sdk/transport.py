"""HTTP transport with retry and circuit breaker.

Retry uses exponential backoff with jitter.  The circuit breaker tracks
consecutive failures and short-circuits requests when open, recovering
after a configurable timeout.
"""

from __future__ import annotations

import asyncio
import logging
import time

import httpx
from httpx import AsyncHTTPTransport

from .config import AddictuneConfig

logger = logging.getLogger(__name__)

_RETRYABLE = (httpx.ConnectError, httpx.ReadTimeout)


class _CircuitBreaker:
    """Simple circuit breaker: track failures, trip open, recover after timeout."""

    def __init__(
        self, failure_threshold: int = 5, recovery_timeout: float = 60.0
    ) -> None:
        self._failure_threshold = failure_threshold
        self._recovery_timeout = recovery_timeout
        self._failure_count = 0
        self._last_failure_time: float = 0.0
        self._open = False

    def record_success(self) -> None:
        self._failure_count = 0
        self._open = False

    def record_failure(self) -> None:
        self._failure_count += 1
        self._last_failure_time = time.monotonic()
        if self._failure_count >= self._failure_threshold:
            self._open = True
            logger.warning(
                "Circuit breaker tripped after %d failures", self._failure_count
            )

    @property
    def is_open(self) -> bool:
        if not self._open:
            return False
        if time.monotonic() - self._last_failure_time >= self._recovery_timeout:
            self._open = False
            self._failure_count = 0
            return False
        return True


class RetryTransport(AsyncHTTPTransport):
    """HTTP transport with retry (outer) -> circuit breaker (inner)."""

    def __init__(self, config: AddictuneConfig | None = None):
        super().__init__()
        config = config or AddictuneConfig()
        self._rc = config.retry
        self._cc = config.circuit
        self._breaker = _CircuitBreaker(
            failure_threshold=self._cc.failure_threshold,
            recovery_timeout=self._cc.recovery_timeout,
        )

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        body = await request.aread()
        last_error: Exception | None = None

        for attempt in range(1, self._rc.max_attempts + 1):
            if self._breaker.is_open:
                raise httpx.ConnectError("Circuit breaker is open")

            try:
                response = await self._send(request, body)
                self._breaker.record_success()
                return response
            except _RETRYABLE as exc:
                last_error = exc
                self._breaker.record_failure()

                if attempt < self._rc.max_attempts:
                    wait = min(
                        self._rc.wait_multiplier * (2 ** (attempt - 1)),
                        self._rc.wait_max,
                    )
                    wait = max(wait, self._rc.wait_min)
                    import random

                    wait += random.uniform(0, self._rc.wait_jitter)
                    logger.warning(
                        "Retry attempt %d failed with %s: %s, next in %.2fs",
                        attempt,
                        type(exc).__name__,
                        exc,
                        wait,
                    )
                    await asyncio.sleep(wait)

        raise last_error  # type: ignore[misc]

    async def _send(self, request: httpx.Request, body: bytes) -> httpx.Response:
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
