"""
SCENARIO 2: Incasso cedola semestrale BTP con chiusura rateo acquisto.

Dati dello scenario:
- Titolo: BTP 3.50% 01/03/2030 (acquistato il 15/05/2025)
- Nominale: EUR 100.000
- Cedola semestrale: 100.000 × 3.5%/2 = 1.750,00 EUR
- Data incasso: 01/09/2025
- Rateo pagato all'acquisto: 713,32 EUR
- Ritenuta: 12,5% su 1.750 = 218,75 EUR
- Netto cedola: 1.750 - 218,75 = 1.531,25 EUR
- Interessi di competenza: 1.750 - 713,32 = 1.036,68 EUR

Scrittura attesa:
  Dare: Banca c/c                1.531,25
  Dare: Erario c/ritenute          218,75
  Avere: Rateo attivo               713,32
  Avere: Interessi attivi         1.036,68

Verifica: dare 1.750,00 = avere 1.750,00 ✓

Riferimento: OIC 20, par. 50.
"""
from datetime import date
from decimal import Decimal

from app.engine.journal.coupon import CouponEntryGenerator
from app.engine.journal.templates import DEFAULT_CHART


class TestScenario2CouponCollection:
    """Scenario 2: Incasso cedola semestrale BTP."""

    COUPON_GROSS = Decimal("1750.00")
    WITHHOLDING = Decimal("218.75")
    ACCRUED_AT_PURCHASE = Decimal("713.32")
    COUPON_NET = Decimal("1531.25")
    COMPETENCE = Decimal("1036.68")

    def test_coupon_entry_balanced(self) -> None:
        """La scrittura di incasso cedola deve essere quadrata."""
        entry = CouponEntryGenerator.generate(
            entry_date=date(2025, 9, 1),
            security_description="BTP 3.5% 01/03/2030",
            coupon_gross=self.COUPON_GROSS,
            withholding_tax=self.WITHHOLDING,
            accrued_at_purchase=self.ACCRUED_AT_PURCHASE,
        )
        assert entry.is_balanced

    def test_coupon_entry_amounts(self) -> None:
        """Verifica importi esatti delle righe."""
        entry = CouponEntryGenerator.generate(
            entry_date=date(2025, 9, 1),
            security_description="BTP 3.5% 01/03/2030",
            coupon_gross=self.COUPON_GROSS,
            withholding_tax=self.WITHHOLDING,
            accrued_at_purchase=self.ACCRUED_AT_PURCHASE,
        )

        banca = [l for l in entry.lines if l.account_code == DEFAULT_CHART.bank_account.code]
        assert banca[0].debit == self.COUPON_NET

        ritenute = [l for l in entry.lines if l.account_code == DEFAULT_CHART.withholding_tax.code]
        assert ritenute[0].debit == self.WITHHOLDING

        rateo = [l for l in entry.lines if l.account_code == DEFAULT_CHART.accrued_interest_asset.code]
        assert rateo[0].credit == self.ACCRUED_AT_PURCHASE

        interessi = [l for l in entry.lines if l.account_code == DEFAULT_CHART.interest_income.code]
        assert interessi[0].credit == self.COMPETENCE

    def test_totals_equal_coupon_gross(self) -> None:
        """Dare = avere = cedola lorda."""
        entry = CouponEntryGenerator.generate(
            entry_date=date(2025, 9, 1),
            security_description="BTP 3.5%",
            coupon_gross=self.COUPON_GROSS,
            withholding_tax=self.WITHHOLDING,
            accrued_at_purchase=self.ACCRUED_AT_PURCHASE,
        )
        assert entry.total_debit == self.COUPON_GROSS
        assert entry.total_credit == self.COUPON_GROSS
