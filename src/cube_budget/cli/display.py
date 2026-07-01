"""Rich terminal display helpers."""

from __future__ import annotations

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from cube_budget.core.models import OptimizationResult
from cube_budget.reports.summary import SummaryStats

console = Console()


def print_summary(result: OptimizationResult) -> None:
    """Print executive summary panel."""
    stats = SummaryStats.compute(result)

    content = (
        f"[bold]Total cartas processadas:[/bold] {result.total_cards}\n"
        f"[bold]Cartas encontradas:[/bold] {result.found_cards} ({stats['found_pct']:.1f}%)\n"
        f"[bold]Cartas não encontradas:[/bold] {len(result.missing)}\n"
        f"[bold]Lojas necessárias:[/bold] {result.stores_used}\n"
        f"[bold]Preço total estimado:[/bold] R$ {result.total_price:,.2f}\n"
        f"[bold]Solver utilizado:[/bold] {result.solver}\n"
        f"[bold]Tempo de otimização:[/bold] {result.duration_ms / 1000:.1f}s"
    )

    console.print(Panel(content, title="Cube Budget Optimizer", border_style="green"))


def print_stats_table(stats: dict) -> None:
    """Print statistics table."""
    table = Table(title="Database Statistics")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")

    for key, value in stats.items():
        table.add_row(str(key), str(value))

    console.print(table)


def print_doctor_results(results: list[tuple[str, bool, str]]) -> None:
    """Print doctor check results."""
    table = Table(title="System Health Check")
    table.add_column("Check", style="cyan")
    table.add_column("Status")
    table.add_column("Details")

    for name, ok, detail in results:
        status = "[green]OK[/green]" if ok else "[red]FAIL[/red]"
        table.add_row(name, status, detail)

    console.print(table)
