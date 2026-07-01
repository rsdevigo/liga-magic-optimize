"""Loguru configuration."""

from __future__ import annotations

import sys
from pathlib import Path

from loguru import logger

from cube_budget.config.schema import LoggingConfig

_configured = False


def setup_logging(config: LoggingConfig) -> None:
    """Configure Loguru with file and console sinks."""
    global _configured
    if _configured:
        return

    logger.remove()

    log_path = Path(config.file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    logger.add(
        config.file,
        level=config.level,
        rotation=config.rotation,
        retention=config.retention,
        format=config.format,
        encoding="utf-8",
        backtrace=True,
        diagnose=True,
    )

    logger.add(
        sys.stderr,
        level=config.level,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | "
        "<cyan>{module}</cyan>:<cyan>{function}</cyan> | <level>{message}</level>",
        colorize=config.colorize,
    )

    _configured = True


def get_logger():
    return logger
