"""Doctor command - system health check."""

from __future__ import annotations

import shutil
import sqlite3
import sys
from pathlib import Path
from typing import Optional

import typer

from cube_budget.cli.display import print_doctor_results
from cube_budget.config.loader import load_config
from cube_budget.database.migrations import run_migrations
from cube_budget.utils.logger import setup_logging


def doctor(
    config_path: Optional[Path] = typer.Option(None, "--config", help="Config YAML path"),
) -> None:
    """Verify system health: database, Playwright, connectivity."""
    config = load_config(config_path)
    setup_logging(config.logging)

    results: list[tuple[str, bool, str]] = []

    # Python version
    py_ok = sys.version_info >= (3, 10)
    results.append(("Python >= 3.10", py_ok, sys.version.split()[0]))

    # Database
    try:
        run_migrations(config.database.path)
        conn = sqlite3.connect(config.database.path)
        conn.execute("SELECT 1")
        conn.close()
        results.append(("Database", True, config.database.path))
    except Exception as e:
        results.append(("Database", False, str(e)))

    # Playwright
    try:
        from playwright.sync_api import sync_playwright

        pw = sync_playwright().start()
        browser = pw.chromium.launch(headless=True)
        browser.close()
        pw.stop()
        results.append(("Playwright/Chromium", True, "Browser available"))
    except Exception as e:
        results.append(("Playwright/Chromium", False, str(e)))

    # Disk space
    try:
        db_path = Path(config.database.path).parent
        usage = shutil.disk_usage(db_path)
        free_gb = usage.free / (1024**3)
        ok = free_gb > 0.5
        results.append(("Disk space", ok, f"{free_gb:.1f} GB free"))
    except Exception as e:
        results.append(("Disk space", False, str(e)))

    # Config
    results.append(("Config loaded", True, str(config_path or "default")))

    # Directories
    for name, path in [
        ("Reports dir", config.output.reports_dir),
        ("Logs dir", Path(config.logging.file).parent),
        ("DB dir", Path(config.database.path).parent),
    ]:
        p = Path(path)
        p.mkdir(parents=True, exist_ok=True)
        results.append((f"{name} writable", p.exists(), str(p)))

    print_doctor_results(results)

    if not all(r[1] for r in results):
        raise typer.Exit(code=1)
