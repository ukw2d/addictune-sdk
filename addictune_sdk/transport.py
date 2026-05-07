"""HTTP transport with retry and circuit breaker.

Retry uses exponential backoff with jitter.  The circuit breaker tracks
consecutive failures and short-circuits requests when open, recovering
after a configurable timeout.
"""

from __future__ import annotations

import asyncio
import logging
import random
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
        was_open = self._open
        self._failure_count = 0
        self._open = False
        if was_open:
            logger.info("Circuit breaker closed after recovery")

    def record_failure(self) -> None:
        self._failure_count += 1
        self._last_failure_time = time.monotonic()
        if self._failure_count >= self._failure_threshold:
            if not self._open:
                logger.warning(
                    "Circuit breaker tripped open after %d consecutive failures (recovery_timeout=%.1fs)",
                    self._failure_count,
                    self._recovery_timeout,
                )
            self._open = True

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
        url = str(request.url)

        for attempt in range(1, self._rc.max_attempts + 1):
            if self._breaker.is_open:
                logger.warning("Request rejected — circuit breaker is open (%s)", url)
                raise httpx.ConnectError("Circuit breaker is open")

            try:
                response = await self._send(request, body)
                self._breaker.record_success()
                if attempt > 1:
                    logger.info(
                        "Request succeeded on attempt %d (%s %s)",
                        attempt,
                        request.method,
                        url,
                    )
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
                    wait += random.uniform(0, self._rc.wait_jitter)
                    logger.warning(
                        "Attempt %d/%d failed (%s: %s) for %s %s — retrying in %.2fs",
                        attempt,
                        self._rc.max_attempts,
                        type(exc).__name__,
                        exc,
                        request.method,
                        url,
                        wait,
                    )
                    await asyncio.sleep(wait)

        logger.error(
            "All %d attempts exhausted for %s %s (last error: %s: %s)",
            self._rc.max_attempts,
            request.method,
            url,
            type(last_error).__name__,
            last_error,
        )
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
