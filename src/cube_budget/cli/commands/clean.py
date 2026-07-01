"""Clean command."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

from cube_budget.config.loader import load_config
from cube_budget.services.orchestrator import Orchestrator
from cube_budget.utils.logger import setup_logging

console = Console()


def clean(
    cache: bool = typer.Option(False, "--cache", help="Clear cache"),
    logs: bool = typer.Option(False, "--logs", help="Clear logs"),
    reports: bool = typer.Option(False, "--reports", help="Clear reports"),
    all_data: bool = typer.Option(False, "--all", help="Clear everything"),
    config_path: Optional[Path] = typer.Option(None, "--config", help="Config YAML path"),
) -> None:
    """Clean cache, logs, and reports."""
    config = load_config(config_path)
    setup_logging(config.logging)

    orchestrator = Orchestrator(config)
    try:
        orchestrator.clean(cache=cache or all_data, all_data=all_data)

        if logs or all_data:
            log_dir = Path(config.logging.file).parent
            for f in log_dir.glob("*.log*"):
                f.unlink(missing_ok=True)
            console.print("[green]Logs cleared[/green]")

        if reports or all_data:
            report_dir = Path(config.output.reports_dir)
            for f in report_dir.glob("*"):
                if f.is_file():
                    f.unlink()
            console.print("[green]Reports cleared[/green]")

        console.print("[green]Cleanup complete[/green]")
    finally:
        orchestrator.close()
