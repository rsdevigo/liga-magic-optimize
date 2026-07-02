"""Tests for configuration loader."""

from pathlib import Path

import pytest

from cube_budget.config.loader import load_config
from cube_budget.core.exceptions import ConfigError


class TestConfigLoader:
    def test_load_default_config(self):
        config = load_config(Path("config/default.yaml"))
        assert config.scraper.headless is True
        assert config.scraper.concurrency == 2
        assert config.cache.ttl_hours == 24
        assert config.optimizer.objective == "stores"

    def test_load_missing_returns_defaults(self, tmp_path: Path):
        config = load_config(tmp_path / "nonexistent.yaml")
        assert config.optimizer.solver == "auto"

    def test_invalid_yaml(self, tmp_path: Path):
        bad = tmp_path / "bad.yaml"
        bad.write_text("invalid: [yaml:", encoding="utf-8")
        with pytest.raises(ConfigError):
            load_config(bad)
