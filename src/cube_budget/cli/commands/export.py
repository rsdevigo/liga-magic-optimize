"""Export command."""

from __future__ import annotations

from pathlib import Path
from typing import Literal, Optional

import typer
from rich.console import Console

from cube_budget.config.loader import load_config
from cube_budget.services.orchestrator import Orchestrator
from cube_budget.utils.logger import setup_logging

console = Console()


def export_cmd(
    run_id: Optional[str] = typer.Option(None, "--run-id", help="Run UUID"),
    fmt: Literal["excel", "csv", "markdown"] = typer.Option("excel", "--format"),
    output: Path = typer.Option(Path("./reports"), "--output", help="Output directory"),
    config_path: Optional[Path] = typer.Option(None, "--config", help="Config YAML path"),
) -> None:
    """Export optimization results to file."""
    config = load_config(config_path)
    setup_logging(config.logging)
    config.output.formats = [fmt]

    orchestrator = Orchestrator(config)
    try:
        result = orchestrator.run_report(run_id, output)
        if result:
            console.print(f"[green]Exported to {output}[/green]")
    finally:
        orchestrator.close()
