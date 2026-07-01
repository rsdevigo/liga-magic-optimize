"""Configuration module."""

from cube_budget.config.loader import load_config
from cube_budget.config.schema import AppConfig

__all__ = ["AppConfig", "load_config"]
