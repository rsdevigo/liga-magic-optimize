"""Stats command."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer

from cube_budget.cli.display import print_stats_table
from cube_budget.config.loader import load_config
from cube_budget.services.orchestrator import Orchestrator
from cube_budget.utils.logger import setup_logging


def stats(
    config_path: Optional[Path] = typer.Option(None, "--config", help="Config YAML path"),
) -> None:
    """Show database statistics."""
    config = load_config(config_path)
    setup_logging(config.logging)

    orchestrator = Orchestrator(config)
    try:
        data = orchestrator.get_stats()
        print_stats_table(data)
    finally:
        orchestrator.close()
