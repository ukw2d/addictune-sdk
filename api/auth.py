from loguru import logger
from typing import Optional
from functools import cached_property
from src.data_models.profile_model import Profile, SecretProfile
from src.data_models.auth_data import AuthData
from src.api.api_base import APIBase
from src.utils.keyring import KeyringManager

class Auth:
    def __init__(self, api_base: APIBase, keyring_manager: KeyringManager):
        self.api_base = api_base
        self.keyring_manager = keyring_manager

    @cached_property
    def auth_path(self) -> str:
        return self.api_base.config["auth_path"].strip("/")

    async def login(self, auth_data: AuthData, network: Optional[str] = None) -> dict:
        auth_url = self.api_base._build_request_path(self.auth_path, network)
        logger.info(f"Logging in via {auth_url}")
        response = await self.api_base.api_client.post(
            auth_url,
            data=auth_data.model_dump(),
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