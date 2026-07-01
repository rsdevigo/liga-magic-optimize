"""Markdown report generation."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from cube_budget.core.models import OptimizationResult
from cube_budget.reports.summary import SummaryStats


class MarkdownReporter:
    """Generate Markdown reports."""

    def generate(self, result: OptimizationResult, output_dir: str | Path) -> Path:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        filepath = output_dir / f"cube_budget_report_{timestamp}.md"

        stats = SummaryStats.compute(result)
        lines = [
            "# Cube Budget Optimizer - Relatório",
            "",
            f"**Gerado em:** {datetime.now().strftime('%d/%m/%Y %H:%M')}",
            f"**Run UUID:** `{result.run_uuid}`",
            "",
            "## Resumo Executivo",
            "",
            "| Métrica | Valor |",
            "|---------|-------|",
            f"| Total de cartas | {result.total_cards} |",
            f"| Cartas encontradas | {result.found_cards} ({stats['found_pct']:.1f}%) |",
            f"| Cartas não encontradas | {len(result.missing)} |",
            f"| Lojas necessárias | {result.stores_used} |",
            f"| Preço total | R$ {result.total_price:,.2f} |",
            f"| Preço médio | R$ {stats['avg_price']:,.2f} |",
            f"| Solver | {result.solver} |",
            f"| Tempo | {result.duration_ms / 1000:.1f}s |",
            "",
        ]

        lines.extend(["## Compras por Loja", ""])
        for store_name in sorted(stats["store_totals"].keys()):
            lines.append(f"### {store_name}")
            lines.append("")
            lines.append(f"**Subtotal:** R$ {stats['store_totals'][store_name]:,.2f} "
                         f"({stats['store_counts'][store_name]} cartas)")
            lines.append("")
            for a in result.assignments:
                if a.store.name == store_name:
                    lines.append(f"- {a.card.raw_name} — R$ {a.price:,.2f} ({a.offer.condition})")
            lines.append("")

        if result.missing:
            lines.extend(["## Cartas Não Encontradas", ""])
            for m in result.missing:
                lines.append(f"- {m.raw_name} ({m.reason})")
            lines.append("")

        lines.extend([
            "## Notas",
            "",
            f"- Algoritmo: {result.solver}",
            f"- Greedy benchmark: {result.greedy_stores} lojas, "
            f"R$ {result.greedy_price or 0:,.2f}",
            f"- Economia vs Greedy: R$ {stats['savings']:,.2f}",
        ])

        filepath.write_text("\n".join(lines), encoding="utf-8")
        return filepath
