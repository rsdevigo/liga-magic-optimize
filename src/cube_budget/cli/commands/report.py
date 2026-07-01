"""Report command."""

from __future__ import annotations

from pathlib import Path
from typing import Literal, Optional

import typer

from cube_budget.cli.display import print_summary
from cube_budget.config.loader import load_config
from cube_budget.services.orchestrator import Orchestrator
from cube_budget.utils.logger import setup_logging


def report(
    run_id: Optional[str] = typer.Option(None, "--run-id", help="Run UUID"),
    output_dir: Optional[Path] = typer.Option(None, "--output-dir", help="Output directory"),
    fmt: Optional[Literal["excel", "csv", "markdown", "all"]] = typer.Option(
        "all", "--format", help="Report format"
    ),
    config_path: Optional[Path] = typer.Option(None, "--config", help="Config YAML path"),
) -> None:
    """Generate report for an optimization run."""
    config = load_config(config_path)
    setup_logging(config.logging)

    if fmt != "all":
        config.output.formats = [fmt]

    orchestrator = Orchestrator(config)
    try:
        result = orchestrator.run_report(run_id, output_dir)
        if result:
            print_summary(result)
    finally:
        orchestrator.close()
