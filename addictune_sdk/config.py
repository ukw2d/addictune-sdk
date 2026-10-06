from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field, replace
from pathlib import Path
from typing import Any


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
        name: Optional label for logging / metrics.  ``None`` by default.
    """

    failure_threshold: int = 5
    recovery_timeout: float = 60.0
    name: str | None = None


@dataclass(frozen=True)
class AddictuneConfig:
    """SDK configuration with sensible defaults.

    Pass an instance to :class:`Client` or let it auto-discover a JSON
    config file via :func:`load_config`.

    All fields have defaults so you can instantiate a blank
    ``AddictuneConfig()`` for production-ready settings, then override
    only the fields you need — either via the constructor, via
    :func:`dataclasses.replace`, from a JSON file, or through
    :func:`load_config` auto-discovery.

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

    @classmethod
    def from_json(cls, path: str | Path) -> AddictuneConfig:
        """Load config from a JSON file, merging over defaults.

        Missing keys in the JSON file fall back to their default values,
        so you only need to specify the fields you want to override.

        Args:
            path: Path to a JSON file.  ``~`` is expanded automatically.

        Returns:
            A fully-resolved :class:`AddictuneConfig` instance.
        """
        raw = json.loads(Path(path).expanduser().read_text(encoding="utf-8"))
        return cls._from_dict(raw)

    def to_dict(self) -> dict[str, Any]:
        """Serialise the config to a plain dict (suitable for JSON)."""
        return asdict(self)

    def to_json(self, path: str | Path) -> None:
        """Write the config to a JSON file.

        Creates parent directories if they don't exist.

        Args:
            path: Destination file path.  ``~`` is expanded automatically.
        """
        p = Path(path).expanduser()
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(
            json.dumps(self.to_dict(), indent=2),
            encoding="utf-8",
        )

    @classmethod
    def _from_dict(cls, data: dict[str, Any]) -> AddictuneConfig:
        data = dict(data)
        retry = RetryConfig(**data.pop("retry", {}))
        circuit = CircuitConfig(**data.pop("circuit", {}))
        return cls(**data, retry=retry, circuit=circuit)


def _default_config_paths() -> list[Path]:
    """XDG / platform-compatible config search paths."""
    paths: list[Path] = []

    xdg = os.environ.get("XDG_CONFIG_HOME")
    base = Path(xdg) if xdg else Path.home() / ".config"
    paths.append(base / "addictune" / "config.json")
    paths.append(Path.home() / ".addictune" / "config.json")

    appdata = os.environ.get("APPDATA")
    if appdata:
        paths.append(Path(appdata) / "addictune" / "config.json")

    return paths


def load_config(path: str | Path | None = None) -> AddictuneConfig:
    """Load config from *path*, auto-discover, or fall back to defaults.

    Resolution order:

    1. If *path* is given, load that file directly.
    2. Otherwise search standard OS config locations (see below).
    3. If no file is found, return ``AddictuneConfig()`` (all defaults).

    Auto-discovery search paths:

    ====================  ===============================================
    Platform              Paths (in order)
    ====================  ===============================================
    Linux / macOS         ``$XDG_CONFIG_HOME/addictune/config.json``,
                           ``~/.addictune/config.json``
    Windows               ``%APPDATA%\\addictune\\config.json``
    ====================  ===============================================

    Args:
        path: Explicit path to a JSON config file, or ``None`` to
            trigger auto-discovery.

    Returns:
        A resolved :class:`AddictuneConfig` instance.
    """
    if path is not None:
        return AddictuneConfig.from_json(path)

    for p in _default_config_paths():
        if p.exists():
            return AddictuneConfig.from_json(p)

    return AddictuneConfig()
