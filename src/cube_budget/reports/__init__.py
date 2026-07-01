"""Report generator facade."""

from __future__ import annotations

from pathlib import Path

from loguru import logger

from cube_budget.config.schema import OutputConfig
from cube_budget.core.models import OptimizationResult
from cube_budget.reports.csv_report import CSVReporter
from cube_budget.reports.excel import ExcelReporter
from cube_budget.reports.markdown import MarkdownReporter


class ReportGenerator:
    """Generates reports in configured formats."""

    def __init__(self, config: OutputConfig):
        self._config = config
        self._excel = ExcelReporter()
        self._csv = CSVReporter()
        self._markdown = MarkdownReporter()

    def generate_all(
        self,
        result: OptimizationResult,
        output_dir: str | Path | None = None,
        recent_runs: list[dict] | None = None,
    ) -> dict[str, Path | list[Path]]:
        out_dir = Path(output_dir or self._config.reports_dir)
        generated: dict[str, Path | list[Path]] = {}

        formats = self._config.formats

        if "excel" in formats:
            path = self._excel.generate(result, out_dir, recent_runs)
            generated["excel"] = path
            logger.info(f"Excel report: {path}")

        if "csv" in formats:
            paths = self._csv.generate(result, out_dir)
            generated["csv"] = paths
            logger.info(f"CSV reports: {len(paths)} files")

        if "markdown" in formats:
            path = self._markdown.generate(result, out_dir)
            generated["markdown"] = path
            logger.info(f"Markdown report: {path}")

        return generated
