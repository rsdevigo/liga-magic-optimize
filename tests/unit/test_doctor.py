"""Tests for doctor CLI command."""

from pathlib import Path
from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from cube_budget.main import app

runner = CliRunner()


class TestDoctor:
    @patch("playwright.sync_api.sync_playwright")
    @patch("cube_budget.cli.commands.doctor.shutil.disk_usage")
    @patch("cube_budget.cli.commands.doctor.setup_logging")
    @patch("cube_budget.cli.commands.doctor.load_config")
    @patch("cube_budget.cli.commands.doctor.run_migrations")
    def test_doctor_success(
        self, mock_migrate, mock_config, mock_log, mock_disk, mock_pw, tmp_path: Path
    ):
        from cube_budget.config.schema import AppConfig, DatabaseConfig, LoggingConfig, OutputConfig

        db_path = tmp_path / "db" / "test.sqlite"
        db_path.parent.mkdir(parents=True)
        mock_config.return_value = AppConfig(
            database=DatabaseConfig(path=str(db_path)),
            logging=LoggingConfig(file=str(tmp_path / "logs" / "test.log")),
            output=OutputConfig(reports_dir=str(tmp_path / "reports")),
        )
        mock_disk.return_value = MagicMock(free=10 * 1024**3)

        pw_instance = MagicMock()
        mock_pw.return_value.start.return_value = pw_instance
        browser = MagicMock()
        pw_instance.chromium.launch.return_value = browser

        result = runner.invoke(app, ["doctor"])
        assert result.exit_code == 0
