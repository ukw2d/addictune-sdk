from pickletools import string1
from httpx import AsyncClient
from loguru import logger
from typing import Optional, Dict, Any
from functools import cached_property
from pathlib import PurePosixPath


class APIBase:
    def __init__(self, config: Dict[str, Any], api_client: AsyncClient):
        """
        Initialize the mixin with configuration and API client.
        
        Args:
            config: Configuration dictionary
            api_client: Async HTTP client for making requests
        """
        self.config = config
        self.api_client = api_client
        logger.debug(f"{self.__class__.__name__} initialized with config: {config}")

    @cached_property
    def default_network(self) -> str:
        """Get the default network from config with trailing slashes removed."""
        return self.config["default_network"].strip("/")
    
    def _build_request_path(self, endpoint: str, network: Optional[str] = None) -> str:
        """Build a clean, normalized URL path."""
        network = (network or self.default_network).strip("/")
        endpoint = endpoint.strip("/")
        return str(PurePosixPath(network, endpoint))