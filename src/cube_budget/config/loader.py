"""Load configuration from YAML and environment variables."""

from __future__ import annotations

import os
from pathlib import Path

import yaml

from cube_budget.config.schema import AppConfig
from cube_budget.core.exceptions import ConfigError


def _deep_merge(base: dict, override: dict) -> dict:
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def _apply_env_overrides(config_dict: dict) -> dict:
    """Apply environment variable overrides to config dict."""
    env_map = {
        "CUBE_DB_PATH": ("database", "path"),
        "CUBE_REPORTS_DIR": ("output", "reports_dir"),
        "CUBE_LOG_LEVEL": ("logging", "level"),
        "CUBE_HEADLESS": ("scraper", "headless"),
        "CUBE_SCRAPER_CONCURRENCY": ("scraper", "concurrency"),
        "CUBE_CACHE_TTL_HOURS": ("cache", "ttl_hours"),
    }
    for env_key, path in env_map.items():
        value = os.environ.get(env_key)
        if value is None:
            continue
        section, field = path
        if section not in config_dict:
            config_dict[section] = {}
        if field == "headless":
            config_dict[section][field] = value.lower() in ("1", "true", "yes")
        elif field in ("ttl_hours", "concurrency"):
            config_dict[section][field] = int(value)
        else:
            config_dict[section][field] = value
    return config_dict


def load_config(config_path: str | Path | None = None) -> AppConfig:
    """Load and validate application configuration."""
    path = Path(config_path or os.environ.get("CUBE_CONFIG", "/app/config/default.yaml"))

    if not path.exists():
        # Fallback for local development outside Docker
        local_fallback = Path("config/default.yaml")
        if local_fallback.exists():
            path = local_fallback
        else:
            return AppConfig()

    try:
        with path.open(encoding="utf-8") as f:
            raw = yaml.safe_load(f) or {}
    except yaml.YAMLError as e:
        raise ConfigError(f"Invalid YAML in config file {path}: {e}") from e

    raw = _apply_env_overrides(raw)

    try:
        return AppConfig.model_validate(raw)
    except Exception as e:
        raise ConfigError(f"Config validation failed: {e}") from e
