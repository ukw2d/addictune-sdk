from functools import wraps

import httpx
from aiolimiter import AsyncLimiter
from circuitbreaker import CircuitBreakerError, circuit
from loguru import logger
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)


def retry_request():  # Simple retry decorator
    return retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((httpx.ConnectError, httpx.ReadTimeout)),
        reraise=True
    )


def circuit_from_config():
    def decorator(method):
        @wraps(method)
        async def wrapper(self, *args, **kwargs):
            circuit_config = self.transport_config.get("circuit", {})
            circuit_decorator = circuit(**circuit_config
                                        if circuit_config else None) # type: ignore
            try:
                return await circuit_decorator(method)(self, *args, **kwargs)
            except CircuitBreakerError as e:
                logger.error(f"Circuit breaker triggered for {method.__name__}: {str(e)}")
                raise
        return wrapper
    return decorator


def limiter_from_config():
    def decorator(method):
        @wraps(method)
        async def wrapper(self, *args, **kwargs):
            limiter_config = self.transport_config.get("limiter", {})
            limiter = AsyncLimiter(**limiter_config
                                    if limiter_config else None) # type: ignore
            try:
                async with limiter:
                    return await method(self, *args, **kwargs)
            except Exception as e:
                logger.error(f"Rate limit error in {method.__name__}: {str(e)}")
                raise
        return wrapper
    return decorator


class APITransport(httpx.AsyncHTTPTransport):
    def __init__(self, transport_config: dict):
        super().__init__(**self._get_core_settings(transport_config))
        self.transport_config = transport_config
        logger.debug(f"Initialized APITransport with config: {transport_config}")

    def _get_core_settings(self, transport_config: dict) -> dict:
        core_config = transport_config.get("core", {})
        logger.debug(f"Core settings: {core_config}")
        return core_config

    @retry_request()
    @limiter_from_config()
    @circuit_from_config()
    async def handle_async_request(self, request):
        logger.debug(f"Handling request: {request.method} {request.url}")
        try:
            response = await super().handle_async_request(request)
            logger.debug(f"Response: {response.status_code}")
            return response
        except httpx.ConnectError as ce:
            logger.error("Connection failed: {}", ce)
            raise

        except httpx.ReadTimeout as te:
            logger.warning("Read timeout: {}", te)
            raise

        except Exception as e:
            logger.exception("Unexpected error during request: {}", e)
            raise
