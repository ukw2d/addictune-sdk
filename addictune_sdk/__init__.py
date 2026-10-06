"""Addictune SDK — async Python client for the AudioAddict Radio API.

Quick start::

    from addictune_sdk import Client

    async with Client() as client:
        await client.login("user@example.com", "password")

        di = client.network("di")
        channels = await di.channels.get_all()

The SDK targets AudioAddict-powered networks including DI.FM, RadioTunes,
Rock Radio, Jazz Radio, Classical Radio, and Zen Radio.  Each network is
accessed through a :class:`NetworkClient` obtained via
:meth:`Client.network`.

Supported networks are registered as built-ins (see
:data:`~addictune_sdk.models.network.BUILTIN_NETWORKS`) and can be
extended with custom :class:`Network` instances passed to the
:class:`Client` constructor.
"""

from . import models
from .client import Client
from .config import AddictuneConfig, CircuitConfig, RetryConfig
from .exceptions import (
    AddictuneAPIError,
    AddictuneAuthError,
    AddictuneError,
    AddictuneNotFoundError,
)
from .models import *
from .network_client import NetworkClient

__all__ = [
    "AddictuneAPIError",
    "AddictuneAuthError",
    "AddictuneConfig",
    "AddictuneError",
    "AddictuneNotFoundError",
    "CircuitConfig",
    "Client",
    "NetworkClient",
    "RetryConfig",
]
__all__ += models.__all__
