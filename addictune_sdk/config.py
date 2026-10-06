from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class RetryConfig:
    """Controls automatic retry behaviour for failed HTTP requests.

    Retry uses exponential backoff with jitter.  On each attempt the base
    delay is ``wait_multiplier * 2^(attempt-1)``, clamped to
    ``[wait_min, wait_max]``, then a random jitter in ``[0, wait_jitter]``
    is added.

    Attributes:
        max_attempts: Maximum number of attempts per request (including
            the initial try).  Set to ``1`` to disable retries.
        wait_multiplier: Multiplier applied to the exponential backoff.
        wait_min: Minimum delay between retries (seconds).
        wait_max: Maximum delay between retries (seconds).
        wait_jitter: Upper bound of random jitter added to each delay
            (seconds).  Helps avoid thundering-herd retries.
    """

    max_attempts: int = 3
    wait_multiplier: float = 1.0
    wait_min: float = 2.0
    wait_max: float = 10.0
    wait_jitter: float = 1.0


@dataclass(frozen=True)
class CircuitConfig:
    """Controls the circuit-breaker that protects against cascading failures.

    When consecutive failures reach *failure_threshold* the circuit opens
    and all requests are short-circuited with an error.  After
    *recovery_timeout* seconds the circuit closes again and new requests
    are allowed through.

    Attributes:
        failure_threshold: Consecutive failures required to trip the
            circuit open.
        recovery_timeout: Seconds to wait before allowing a retry after
            the circuit has opened.
    """

    failure_threshold: int = 5
    recovery_timeout: float = 60.0


@dataclass(frozen=True)
class AddictuneConfig:
    """SDK configuration with sensible defaults.

    Pass an instance to :class:`Client`.  All fields have defaults, so a
    blank ``AddictuneConfig()`` gives production-ready settings; override
    only the fields you need via the constructor.

    Attributes:
        api_base: Base URL of the AudioAddict API.
        network: Default network slug used by :meth:`Client.login`.
        timeout: HTTP request timeout in seconds.
        retry: :class:`RetryConfig` for automatic retry behaviour.
        circuit: :class:`CircuitConfig` for circuit-breaker protection.
    """

    api_base: str = "https://api.audioaddict.com/v1"
    network: str = "di"
    timeout: float = 30.0
    retry: RetryConfig = field(default_factory=RetryConfig)
    circuit: CircuitConfig = field(default_factory=CircuitConfig)
