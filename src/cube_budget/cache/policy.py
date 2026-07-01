"""Cache TTL policy."""

from __future__ import annotations

from cube_budget.config.schema import CacheConfig
from cube_budget.core.constants import (
    CACHE_STATUS_ERROR,
    CACHE_STATUS_NOT_FOUND,
    CACHE_STATUS_OK,
)


def get_ttl_hours(status: str, config: CacheConfig) -> int:
    """Return TTL hours based on cache entry status."""
    if status == CACHE_STATUS_NOT_FOUND:
        return config.ttl_not_found_hours
    if status == CACHE_STATUS_ERROR:
        return config.ttl_error_hours
    return config.ttl_hours
