"""Configuration schema (Pydantic models)."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class ScraperConfig(BaseModel):
    headless: bool = True
    browser: Literal["chromium", "firefox", "webkit"] = "chromium"
    concurrency: int = Field(default=2, ge=1, le=8)
    timeout_ms: int = 30000
    retry_attempts: int = 3
    retry_base_delay_s: float = 2.0
    retry_jitter: bool = True
    page_load_delay_ms: list[int] = Field(default_factory=lambda: [800, 2000])
    max_pages_per_card: int = 10
    user_agent: str = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
    base_url: str = "https://www.ligamagic.com.br"


class CacheConfig(BaseModel):
    ttl_hours: int = 24
    ttl_not_found_hours: int = 6
    ttl_error_hours: int = 1


class FiltersConfig(BaseModel):
    min_condition: str = "NM"
    preferred_language: str = "PT"
    ignore_foil: bool = True
    min_stock: int = 1


class OptimizerConfig(BaseModel):
    solver: Literal["auto", "greedy", "ilp", "ortools"] = "auto"
    objective: Literal["stores", "price"] = "stores"
    ilp_timeout_s: int = 120
    ortools_timeout_s: int = 300
    ilp_ortools_threshold: int = 15000
    max_stores: int | None = None


class OutputConfig(BaseModel):
    reports_dir: str = "/app/reports"
    formats: list[str] = Field(default_factory=lambda: ["excel", "csv", "markdown"])
    excel_open_after: bool = False


class LoggingConfig(BaseModel):
    level: str = "INFO"
    file: str = "/app/logs/cube-budget.log"
    rotation: str = "10 MB"
    retention: str = "7 days"
    format: str = "{time:YYYY-MM-DD HH:mm:ss} | {level} | {module}:{function}:{line} | {message}"
    colorize: bool = True


class DatabaseConfig(BaseModel):
    path: str = "/app/data/db/cube_budget.sqlite"
    wal_mode: bool = True
    busy_timeout_ms: int = 5000


class AppConfig(BaseModel):
    scraper: ScraperConfig = Field(default_factory=ScraperConfig)
    cache: CacheConfig = Field(default_factory=CacheConfig)
    filters: FiltersConfig = Field(default_factory=FiltersConfig)
    optimizer: OptimizerConfig = Field(default_factory=OptimizerConfig)
    output: OutputConfig = Field(default_factory=OutputConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
