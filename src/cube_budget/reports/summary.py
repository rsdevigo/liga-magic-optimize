"""Executive summary statistics."""

from __future__ import annotations

from collections import defaultdict

from cube_budget.core.models import OptimizationResult


class SummaryStats:
    """Compute aggregate statistics from optimization result."""

    @staticmethod
    def compute(result: OptimizationResult) -> dict:
        store_totals: dict[str, float] = defaultdict(float)
        store_counts: dict[str, int] = defaultdict(int)

        for a in result.assignments:
            store_totals[a.store.name] += a.price
            store_counts[a.store.name] += 1

        prices = [a.price for a in result.assignments]
        avg_price = sum(prices) / len(prices) if prices else 0.0
        max_price = max(prices) if prices else 0.0
        min_price = min(prices) if prices else 0.0

        top_expensive = sorted(result.assignments, key=lambda a: a.price, reverse=True)[:10]

        savings = 0.0
        if result.greedy_price and result.total_price:
            savings = result.greedy_price - result.total_price

        max_stores_label = (
            str(result.max_stores_limit)
            if result.max_stores_limit is not None
            else "sem limite"
        )

        return {
            "total_cards": result.total_cards,
            "found_cards": result.found_cards,
            "missing_cards": len(result.missing),
            "found_pct": (result.found_cards / result.total_cards * 100) if result.total_cards else 0,
            "stores_used": result.stores_used,
            "total_price": result.total_price,
            "avg_price": avg_price,
            "max_price": max_price,
            "min_price": min_price,
            "objective": result.objective,
            "max_stores_limit": max_stores_label,
            "solver": result.solver,
            "duration_ms": result.duration_ms,
            "greedy_stores": result.greedy_stores,
            "greedy_price": result.greedy_price,
            "savings": savings,
            "store_totals": dict(store_totals),
            "store_counts": dict(store_counts),
            "top_expensive": top_expensive,
        }
