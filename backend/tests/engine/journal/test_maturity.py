"""
Test per il generatore scritture scadenza/rimborso.

Riferimento: OIC 20, par. 56-62.
"""
from datetime import date
from decimal import Decimal

from app.engine.journal.maturity import MaturityEntryGenerator
from app.engine.journal.templates import DEFAULT_CHART


class TestBondMaturity:
    """Test rimborso titoli a cedola."""

    def test_maturity_at_par(self) -> None:
        """Rimborso alla pari: book_value = redemption."""
        entry = MaturityEntryGenerator.generate_bond_maturity(
            entry_date=date(2030, 3, 1),
            security_description="BTP 3.5%",
            redemption_value=Decimal("100000.00"),
            book_value=Decimal("100000.00"),
        )
        assert entry.is_balanced

    def test_maturity_with_gain(self) -> None:
        """Rimborso con plusvalenza (book < redemption)."""
        entry = MaturityEntryGenerator.generate_bond_maturity(
            entry_date=date(2030, 3, 1),
            security_description="BTP",
            redemption_value=Decimal("100000.00"),
            book_value=Decimal("98000.00"),
        )
        assert entry.is_balanced
        gain_lines = [
            l for l in entry.lines
            if l.account_code == DEFAULT_CHART.capital_gain.code
        ]
        assert gain_lines[0].credit == Decimal("2000.00")

    def test_maturity_with_last_coupon(self) -> None:
        """Rimborso con ultima cedola."""
        entry = MaturityEntryGenerator.generate_bond_maturity(
            entry_date=date(2030, 3, 1),
            security_description="BTP 3.5%",
            redemption_value=Decimal("100000.00"),
            book_value=Decimal("100000.00"),
            last_coupon_gross=Decimal("1750.00"),
            withholding_tax_coupon=Decimal("218.75"),
        )
        assert entry.is_balanced
        # Banca = 100000 + 1750 - 218.75 = 101531.25
        bank_lines = [
            l for l in entry.lines
            if l.account_code == DEFAULT_CHART.bank_account.code
        ]
        assert bank_lines[0].debit == Decimal("101531.25")


class TestZeroCouponMaturity:
    """Test rimborso zero coupon (BOT/CTZ)."""

    def test_bot_maturity(self) -> None:
        """BOT: scarto = interesse, con ritenuta 12,5%."""
        entry = MaturityEntryGenerator.generate_zero_coupon_maturity(
            entry_date=date(2026, 1, 15),
            security_description="BOT 12M",
            redemption_value=Decimal("100000.00"),
            purchase_cost=Decimal("96500.00"),
            withholding_tax=Decimal("437.50"),  # 3500 × 12.5%
        )
        assert entry.is_balanced
        # Dare: banca 99562.50 + ritenute 437.50 = 100000
        # Avere: titoli 96500 + interessi 3500 = 100000
        interest_lines = [
            l for l in entry.lines
            if l.account_code == DEFAULT_CHART.interest_income.code
        ]
        assert interest_lines[0].credit == Decimal("3500.00")

    def test_bot_no_withholding(self) -> None:
        """BOT senza ritenuta."""
        entry = MaturityEntryGenerator.generate_zero_coupon_maturity(
            entry_date=date(2026, 1, 15),
            security_description="CTZ",
            redemption_value=Decimal("100000.00"),
            purchase_cost=Decimal("98000.00"),
        )
        assert entry.is_balanced

    def test_entry_type(self) -> None:
        entry = MaturityEntryGenerator.generate_zero_coupon_maturity(
            entry_date=date(2026, 1, 15),
            security_description="BOT",
            redemption_value=Decimal("100000.00"),
            purchase_cost=Decimal("97000.00"),
        )
        assert entry.entry_type == "maturity_zc"
