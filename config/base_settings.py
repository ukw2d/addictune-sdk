# base_settings.py
from pathlib import Path
import sys
from pydantic_settings import BaseSettings, YamlConfigSettingsSource
from abc import ABCMeta, abstractmethod

class BaseSettingsWithYAML(BaseSettings, metaclass=ABCMeta):
    @classmethod
    @abstractmethod
    def get_yaml_filename(cls) -> str:
        """Subclasses must override this to return their YAML filename."""
        pass

    @classmethod
    def settings_customise_sources(cls, settings_cls, **_):
        # Determine config path
        if getattr(sys, 'frozen', False):  # Running as compiled executable
            yaml_path = Path.home() / ".myapp" / cls.get_yaml_filename()
        else:  # Running in development
            yaml_path = Path(cls.get_yaml_filename())

        yaml_path.parent.mkdir(exist_ok=True)

        return (
            YamlConfigSettingsSource(settings_cls, yaml_file=yaml_path),
        )