"""Optimize command."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer

from cube_budget.cli.display import print_summary
from cube_budget.config.loader import load_config
from cube_budget.core.models import SolverType
from cube_budget.services.orchestrator import Orchestrator
from cube_budget.utils.logger import setup_logging


def optimize(
    file: Path = typer.Argument(..., help="Card list file (one card per line)"),
    fresh: bool = typer.Option(False, "--fresh", help="Ignore cache, re-scrape all"),
    resume: bool = typer.Option(False, "--resume", help="Resume interrupted run"),
    max_stores: Optional[int] = typer.Option(None, "--max-stores", help="Max stores limit"),
    solver: Optional[SolverType] = typer.Option(None, "--solver", help="Solver to use"),
    output_dir: Optional[Path] = typer.Option(None, "--output-dir", help="Output directory"),
    config_path: Optional[Path] = typer.Option(None, "--config", help="Config YAML path"),
) -> None:
    """Optimize card purchases across LigaMagic stores."""
    config = load_config(config_path)
    setup_logging(config.logging)

    orchestrator = Orchestrator(config)
    try:
        result = orchestrator.run_optimize(
            file,
            fresh=fresh,
            resume=resume,
            max_stores=max_stores,
            solver=solver,
            output_dir=output_dir,
        )
        print_summary(result)
    finally:
        orchestrator.close()
