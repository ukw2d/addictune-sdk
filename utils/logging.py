import sys
from pathlib import Path
from typing import IO, TypeVar

from loguru import logger

from src.config.logging_settings import LoggingSettings

SinkType = TypeVar('SinkType', Path, str, IO[str])

def _get_logger_config(settings: LoggingSettings, sink: SinkType | None = None) -> dict:
    """Helper to generate consistent logger config"""
    config = settings.model_dump(exclude={"sink"})
    if isinstance(sink, sys.stderr.__class__):
        config.pop("rotation", None)
        config.pop("retention", None)
        config.pop("format", None)
    return {"sink": sink, **config} if sink else config


def configure_logging(settings: LoggingSettings):
    logger.remove()
    if settings.sink:
        settings.sink.parent.mkdir(parents=True, exist_ok=True)
        logger.add(**_get_logger_config(settings, settings.sink))

    logger.add(**_get_logger_config(settings, sys.stderr))
