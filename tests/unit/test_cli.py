"""Tests for CLI commands."""

from pathlib import Path
from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from cube_budget.main import app

runner = CliRunner()


class TestCLI:
    def test_help(self):
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "optimize" in result.stdout

    @patch("cube_budget.cli.commands.stats.Orchestrator")
    @patch("cube_budget.cli.commands.stats.load_config")
    @patch("cube_budget.cli.commands.stats.setup_logging")
    def test_stats(self, mock_log, mock_config, mock_orch):
        mock_config.return_value = MagicMock()
        instance = MagicMock()
        instance.get_stats.return_value = {"cards": 10, "stores": 5}
        mock_orch.return_value = instance

        result = runner.invoke(app, ["stats"])
        assert result.exit_code == 0

    @patch("cube_budget.cli.commands.optimize.Orchestrator")
    @patch("cube_budget.cli.commands.optimize.load_config")
    @patch("cube_budget.cli.commands.optimize.setup_logging")
    def test_optimize(self, mock_log, mock_config, mock_orch, tmp_path: Path):
        from cube_budget.core.models import OptimizationResult

        mock_config.return_value = MagicMock()
        instance = MagicMock()
        instance.run_optimize.return_value = OptimizationResult(
            run_uuid="test",
            total_cards=1,
            found_cards=1,
            stores_used=1,
            total_price=10.0,
            solver="greedy",
        )
        mock_orch.return_value = instance

        f = tmp_path / "cube.txt"
        f.write_text("Lightning Bolt\n", encoding="utf-8")

        result = runner.invoke(app, ["optimize", str(f)])
        assert result.exit_code == 0

    @patch("cube_budget.cli.commands.clean.Orchestrator")
    @patch("cube_budget.cli.commands.clean.load_config")
    @patch("cube_budget.cli.commands.clean.setup_logging")
    def test_clean(self, mock_log, mock_config, mock_orch):
        mock_config.return_value = MagicMock()
        mock_config.return_value.logging.file = "/tmp/test.log"
        mock_config.return_value.output.reports_dir = "/tmp/reports"
        instance = MagicMock()
        mock_orch.return_value = instance

        result = runner.invoke(app, ["clean", "--cache"])
        assert result.exit_code == 0

    @patch("cube_budget.cli.commands.report.Orchestrator")
    @patch("cube_budget.cli.commands.report.load_config")
    @patch("cube_budget.cli.commands.report.setup_logging")
    def test_report(self, mock_log, mock_config, mock_orch):
        from cube_budget.core.models import OptimizationResult

        mock_config.return_value = MagicMock()
        instance = MagicMock()
        instance.run_report.return_value = OptimizationResult(
            run_uuid="test",
            total_cards=1,
            found_cards=1,
            stores_used=1,
            total_price=10.0,
            solver="greedy",
        )
        mock_orch.return_value = instance

        result = runner.invoke(app, ["report"])
        assert result.exit_code == 0
