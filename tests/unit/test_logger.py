"""Tests for logger setup."""

from cube_budget.config.schema import LoggingConfig
from cube_budget.utils.logger import setup_logging, get_logger


class TestLogger:
    def test_setup_logging(self, tmp_path):
        config = LoggingConfig(
            file=str(tmp_path / "test.log"),
            level="DEBUG",
        )
        setup_logging(config)
        logger = get_logger()
        logger.info("test message")
        assert (tmp_path / "test.log").exists()
