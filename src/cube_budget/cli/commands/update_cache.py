"""Update cache command."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

from cube_budget.config.loader import load_config
from cube_budget.services.orchestrator import Orchestrator
from cube_budget.utils.logger import setup_logging

console = Console()


def update_cache(
    file: Optional[Path] = typer.Argument(None, help="Card list file (optional)"),
    config_path: Optional[Path] = typer.Option(None, "--config", help="Config YAML path"),
) -> None:
    """Force re-scrape cards and update cache."""
    config = load_config(config_path)
    setup_logging(config.logging)

    orchestrator = Orchestrator(config)
    try:
        count = orchestrator.run_update_cache(file)
        console.print(f"[green]Updated cache for {count} cards[/green]")
    finally:
        orchestrator.close()
