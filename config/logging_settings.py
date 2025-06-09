from pathlib import Path
from typing import Optional
from pydantic import Field
from src.config.base_settings import BaseSettingsWithYAML

class LoggingSettings(BaseSettingsWithYAML):
    level: str = Field("INFO")
    format: str = Field(default="")
    sink: Optional[Path] = Field(default=None)
    rotation: str = Field(default="10 MB")
    retention: str = Field(default="30 days")
    serialize: bool = Field(default=False)
    enqueue: bool = Field(default=True)
    colorize: bool = Field(default=True)

    @classmethod
    def get_yaml_filename(cls) -> str:
        return "logging_settings.yaml"