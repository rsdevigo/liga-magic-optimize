"""Integration tests for report generation."""

import uuid
from pathlib import Path

from cube_budget.core.models import AssignedCard, Card, Offer, OptimizationResult, Store
from cube_budget.reports import ReportGenerator
from cube_budget.config.schema import OutputConfig


class TestReports:
    def _make_result(self) -> OptimizationResult:
        card = Card(id=1, raw_name="Lightning Bolt", normalized_name="lightning bolt")
        store = Store(id=1, ligamagic_id="101", name="CardShop", slug="cardshop")
        offer = Offer(card_id=1, store_id=1, price=12.50, quantity=1, condition="NM")
        return OptimizationResult(
            run_uuid=str(uuid.uuid4()),
            assignments=[AssignedCard(card=card, store=store, offer=offer, price=12.50)],
            missing=[],
            stores_used=1,
            total_price=12.50,
            solver="greedy",
            duration_ms=50,
            total_cards=1,
            found_cards=1,
            greedy_stores=1,
            greedy_price=12.50,
        )

    def test_excel_report(self, tmp_path: Path):
        config = OutputConfig(reports_dir=str(tmp_path), formats=["excel"])
        gen = ReportGenerator(config)
        result = self._make_result()
        paths = gen.generate_all(result, tmp_path)
        assert "excel" in paths
        assert Path(paths["excel"]).exists()

    def test_csv_report(self, tmp_path: Path):
        config = OutputConfig(reports_dir=str(tmp_path), formats=["csv"])
        gen = ReportGenerator(config)
        result = self._make_result()
        paths = gen.generate_all(result, tmp_path)
        assert "csv" in paths
        assert len(paths["csv"]) == 3

    def test_markdown_report(self, tmp_path: Path):
        config = OutputConfig(reports_dir=str(tmp_path), formats=["markdown"])
        gen = ReportGenerator(config)
        result = self._make_result()
        paths = gen.generate_all(result, tmp_path)
        assert "markdown" in paths
        content = Path(paths["markdown"]).read_text(encoding="utf-8")
        assert "Lightning Bolt" in content

    def test_all_formats(self, tmp_path: Path):
        config = OutputConfig(
            reports_dir=str(tmp_path), formats=["excel", "csv", "markdown"]
        )
        gen = ReportGenerator(config)
        result = self._make_result()
        paths = gen.generate_all(result, tmp_path)
        assert len(paths) == 3
