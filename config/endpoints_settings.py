from typing import List
from pydantic import BaseModel, model_validator, field_serializer
from pathlib import PurePosixPath
from src.config.base_settings import BaseSettingsWithYAML

class NetworkEntry(BaseModel):
    slug: str
    domain: str

class AudioAddictConfig(BaseSettingsWithYAML):
    default_network: str
    networks: List[NetworkEntry]
    auth_path: PurePosixPath

    @model_validator(mode="after")
    def validate_default_network(self):
        network_slugs = [network.slug for network in self.networks]
        if self.default_network not in network_slugs:
            raise ValueError(f"default_network '{self.default_network}' not found in networks")
        return self
    
    @field_serializer("auth_path")
    def serialize_auth_path(self, auth_path: PurePosixPath):
        return str(auth_path)
    
    @classmethod
    def get_yaml_filename(cls) -> str:
        return "audioaddict_settings.yaml"

