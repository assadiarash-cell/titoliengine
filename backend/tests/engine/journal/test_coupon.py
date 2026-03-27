"""
Test per il generatore scritture incasso cedola.

Riferimento: OIC 20, par. 50.
"""
from datetime import date
from decimal import Decimal

from app.engine.journal.coupon import CouponEntryGenerator
from app.engine.journal.templates import DEFAULT_CHART


class TestCouponEntry:
    """Test incasso cedola."""

    def test_coupon_without_accrued(self) -> None:
        """Cedola senza rateo da acquisto da chiudere."""
        entry = CouponEntryGenerator.generate(
            entry_date=date(2025, 9, 1),
            security_description="BTP 3.5%",
            coupon_gross=Decimal("1750.00"),
            withholding_tax=Decimal("218.75"),
        )
        assert entry.is_balanced
        # Dare: banca 1531.25 + ritenute 218.75 = 1750
        # Avere: interessi attivi 1750
        assert entry.total_debit == Decimal("1750.00")

    def test_coupon_with_accrued_at_purchase(self) -> None:
        """Cedola con chiusura rateo da acquisto."""
        entry = CouponEntryGenerator.generate(
            entry_date=date(2025, 9, 1),
            security_description="BTP 3.5%",
            coupon_gross=Decimal("1750.00"),
            withholding_tax=Decimal("218.75"),
            accrued_at_purchase=Decimal("713.32"),
        )
        assert entry.is_balanced
        # Dare: banca 1531.25 + ritenute 218.75 = 1750.00
        # Avere: rateo 713.32 + interessi competenza 1036.68 = 1750.00
        rateo_lines = [
            l for l in entry.lines
            if l.account_code == DEFAULT_CHART.accrued_interest_asset.code
        ]
        assert rateo_lines[0].credit == Decimal("713.32")

        interest_lines = [
            l for l in entry.lines
            if l.account_code == DEFAULT_CHART.interest_income.code
        ]
        assert interest_lines[0].credit == Decimal("1036.68")

    def test_coupon_no_withholding(self) -> None:
        """Cedola esente da ritenuta."""
        entry = CouponEntryGenerator.generate(
            entry_date=date(2025, 9, 1),
            security_description="Bond",
            coupon_gross=Decimal("2000.00"),
            withholding_tax=Decimal("0"),
        )
        assert entry.is_balanced
        # Solo banca in dare, niente ritenute
        withholding_lines = [
            l for l in entry.lines
            if l.account_code == DEFAULT_CHART.withholding_tax.code
        ]
        assert len(withholding_lines) == 0

    def test_entry_type(self) -> None:
        entry = CouponEntryGenerator.generate(
            entry_date=date(2025, 9, 1),
            security_description="BTP",
            coupon_gross=Decimal("1000.00"),
            withholding_tax=Decimal("125.00"),
        )
        assert entry.entry_type == "coupon"
