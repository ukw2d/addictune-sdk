from httpx import AsyncClient
from loguru import logger
from pydantic import SecretStr
from typing import Optional
from functools import cached_property
from pathlib import PurePosixPath
from src.data_models.profile_model import Profile, SecretProfile
from src.data_models.auth_data import AuthData
from src.utils.keyring import KeyringManager

class Auth:
    def __init__(self, config: dict, api_client: AsyncClient, keyring_manager: KeyringManager):
        self.config = config
        logger.debug(f"Auth initialized with config: {config}")
        self.api_client = api_client
        self.keyring_manager = keyring_manager

    @cached_property
    def default_network(self) -> str:
        return self.config["default_network"].strip("/")

    @cached_property
    def auth_path(self) -> str:
        return self.config["auth_path"].strip("/")

    def _build_auth_url(self, network: Optional[str] = None) -> str:
        """Build a clean, normalized auth URL path."""
        network = (network or self.default_network).strip("/")
        full_path = PurePosixPath('/') / network / self.auth_path
        logger.debug(f"Built auth URL path: {full_path}")
        return str(full_path)

    async def login(self, auth_data: AuthData, network: Optional[str] = None) -> dict:
        auth_url = self._build_auth_url(network)
        logger.info(f"Logging in via {auth_url}")
        response = await self.api_client.post(
            auth_url,
            data=auth_data.model_dump(),
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        response.raise_for_status()
        profile = SecretProfile(**response.json())
        logger.success(f"Login successful for {profile.email}")
        self.save_keys(profile)
        return Profile(**profile.model_dump()).model_dump()
    
    def save_keys(self, profile: SecretProfile) -> bool:
        api_key_saved = self.keyring_manager.save_secret(
            "api_key",
            profile.api_key.get_secret_value(),
            profile.email
        )
        listen_key_saved = self.keyring_manager.save_secret(
            "listen_key",
            profile.listen_key.get_secret_value(),
            profile.email
        )

        return api_key_saved and listen_key_saved