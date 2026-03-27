"""
Test per il generatore scritture vendita titoli.

Riferimento: OIC 20, par. 56-62.
"""
from datetime import date
from decimal import Decimal

from app.engine.journal.sale import SaleEntryGenerator
from app.engine.journal.templates import DEFAULT_CHART


class TestSaleEntry:
    """Test vendita titoli."""

    def test_sale_with_gain(self) -> None:
        """Vendita con plusvalenza."""
        entry = SaleEntryGenerator.generate(
            entry_date=date(2025, 11, 15),
            security_description="BTP 3.5%",
            sale_price_clean=Decimal("103000.00"),
            book_value=Decimal("101366.00"),
        )
        assert entry.is_balanced
        # Plusvalenza = 103000 - 101366 = 1634
        gain_lines = [
            l for l in entry.lines
            if l.account_code == DEFAULT_CHART.capital_gain.code
        ]
        assert len(gain_lines) == 1
        assert gain_lines[0].credit == Decimal("1634.00")

    def test_sale_with_loss(self) -> None:
        """Vendita con minusvalenza."""
        entry = SaleEntryGenerator.generate(
            entry_date=date(2025, 11, 15),
            security_description="BTP 3.5%",
            sale_price_clean=Decimal("99000.00"),
            book_value=Decimal("101366.00"),
        )
        assert entry.is_balanced
        # Minusvalenza = 99000 - 101366 = -2366
        loss_lines = [
            l for l in entry.lines
            if l.account_code == DEFAULT_CHART.capital_loss.code
        ]
        assert len(loss_lines) == 1
        assert loss_lines[0].debit == Decimal("2366.00")

    def test_sale_with_costs(self) -> None:
        """Vendita con commissioni: costi separati dalla plus/minus."""
        entry = SaleEntryGenerator.generate(
            entry_date=date(2025, 11, 15),
            security_description="BTP",
            sale_price_clean=Decimal("102000.00"),
            book_value=Decimal("100000.00"),
            sale_costs=Decimal("150.00"),
        )
        assert entry.is_balanced
        # Gain = 102000 - 100000 = 2000 (costi separati)
        gain_lines = [
            l for l in entry.lines
            if l.account_code == DEFAULT_CHART.capital_gain.code
        ]
        assert gain_lines[0].credit == Decimal("2000.00")
        # Commissioni come costo separato
        cost_lines = [
            l for l in entry.lines
            if l.account_code == DEFAULT_CHART.transaction_costs.code
        ]
        assert cost_lines[0].debit == Decimal("150.00")

    def test_sale_with_accrued_interest(self) -> None:
        """Vendita con rateo cedolare."""
        entry = SaleEntryGenerator.generate(
            entry_date=date(2025, 11, 15),
            security_description="BTP",
            sale_price_clean=Decimal("100000.00"),
            book_value=Decimal("100000.00"),
            accrued_interest_sold=Decimal("500.00"),
        )
        assert entry.is_balanced
        # Rateo su conto interessi attivi
        interest_lines = [
            l for l in entry.lines
            if l.account_code == DEFAULT_CHART.interest_income.code
        ]
        assert interest_lines[0].credit == Decimal("500.00")

    def test_sale_at_par(self) -> None:
        """Vendita alla pari: nessuna plus/minus."""
        entry = SaleEntryGenerator.generate(
            entry_date=date(2025, 11, 15),
            security_description="BTP",
            sale_price_clean=Decimal("100000.00"),
            book_value=Decimal("100000.00"),
        )
        assert entry.is_balanced
        # Nessuna riga plus/minus
        gain_lines = [
            l for l in entry.lines
            if l.account_code == DEFAULT_CHART.capital_gain.code
        ]
        loss_lines = [
            l for l in entry.lines
            if l.account_code == DEFAULT_CHART.capital_loss.code
        ]
        assert len(gain_lines) == 0
        assert len(loss_lines) == 0

    def test_entry_type(self) -> None:
        entry = SaleEntryGenerator.generate(
            entry_date=date(2025, 11, 15),
            security_description="BTP",
            sale_price_clean=Decimal("100000.00"),
            book_value=Decimal("100000.00"),
        )
        assert entry.entry_type == "sale"
