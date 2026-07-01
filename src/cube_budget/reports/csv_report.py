"""CSV report generation."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pandas as pd

from cube_budget.core.models import OptimizationResult
from cube_budget.reports.summary import SummaryStats


class CSVReporter:
    """Generate CSV reports."""

    def generate(self, result: OptimizationResult, output_dir: str | Path) -> list[Path]:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        paths: list[Path] = []

        # Assignments
        assignments_data = [
            {
                "carta": a.card.raw_name,
                "loja": a.store.name,
                "condicao": a.offer.condition,
                "idioma": a.offer.language,
                "edicao": a.offer.edition or "",
                "preco": a.price,
            }
            for a in result.assignments
        ]
        p1 = output_dir / f"assignments_{timestamp}.csv"
        pd.DataFrame(assignments_data).to_csv(p1, index=False, encoding="utf-8-sig")
        paths.append(p1)

        # Missing cards
        missing_data = [{"carta": m.raw_name, "motivo": m.reason} for m in result.missing]
        p2 = output_dir / f"missing_cards_{timestamp}.csv"
        pd.DataFrame(missing_data).to_csv(p2, index=False, encoding="utf-8-sig")
        paths.append(p2)

        # Store summary
        stats = SummaryStats.compute(result)
        store_data = [
            {
                "loja": name,
                "cartas": stats["store_counts"][name],
                "subtotal": stats["store_totals"][name],
            }
            for name in sorted(stats["store_totals"].keys())
        ]
        p3 = output_dir / f"stores_summary_{timestamp}.csv"
        pd.DataFrame(store_data).to_csv(p3, index=False, encoding="utf-8-sig")
        paths.append(p3)

        return paths
