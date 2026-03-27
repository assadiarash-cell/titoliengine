"""
SCENARIO 1: Acquisto BTP sopra la pari — Costo storico.

Dati dello scenario (dal blueprint sezione 5):
- Titolo: BTP 3.50% 01/03/2030
- Nominale: EUR 100.000
- Data acquisto: 15/05/2025
- Corso secco: 101.20 → 101.200 EUR su 100.000 nominale
- Ultimo godimento: 01/03/2025
- Prossimo godimento: 01/09/2025
- Rateo maturato: 75 giorni (01/03 → 15/05) su 184 (01/03 → 01/09)
  Rateo = 100.000 × 3.5%/2 × 75/184 = 713.32 EUR (arrotondato)
- Commissioni: 166.00 EUR
- Bollo: 0

Scrittura attesa (costo storico):
  Dare: Titoli immobilizzati    101.366,00  (101.200 + 166)
  Dare: Rateo attivo                713,32
  Avere: Banca c/c              102.079,32

Verifica: dare 102.079,32 = avere 102.079,32 ✓

Riferimento: OIC 20, par. 14-30, par. 50.
"""
from datetime import date
from decimal import Decimal

from app.engine.accruals import AccruedInterestCalculator
from app.engine.constants import (
    Classification,
    DayCountConventionType,
    QUANTIZE_CENTS,
)
from app.engine.journal.purchase import PurchaseEntryGenerator
from app.engine.journal.templates import DEFAULT_CHART


class TestScenario1AboveParPurchase:
    """Scenario 1: Acquisto BTP sopra la pari a costo storico."""

    # Dati dello scenario
    NOMINAL = Decimal("100000")
    CLEAN_PRICE = Decimal("101200.00")
    COMMISSION = Decimal("166.00")
    COUPON_RATE = Decimal("0.035")
    COUPON_FREQUENCY = 2
    PURCHASE_DATE = date(2025, 5, 15)
    LAST_COUPON = date(2025, 3, 1)
    NEXT_COUPON = date(2025, 9, 1)

    def test_accrued_interest_calculation(self) -> None:
        """Rateo maturato: 1750 × 75/184 = 713.3152..."""
        accrued = AccruedInterestCalculator.calculate_for_purchase(
            nominal_value=self.NOMINAL,
            coupon_rate=self.COUPON_RATE,
            coupon_frequency=self.COUPON_FREQUENCY,
            purchase_date=self.PURCHASE_DATE,
            last_coupon_date=self.LAST_COUPON,
            next_coupon_date=self.NEXT_COUPON,
            day_count_convention=DayCountConventionType.ACT_ACT,
        )
        # 1750 × 75/184 = 713.31521739...
        expected = self.NOMINAL * self.COUPON_RATE / Decimal("2") * Decimal("75") / Decimal("184")
        assert accrued == expected.quantize(Decimal("1E-10"))

    def test_purchase_entry_balanced(self) -> None:
        """La scrittura di acquisto deve essere perfettamente quadrata."""
        accrued = (
            self.NOMINAL * self.COUPON_RATE / Decimal("2")
            * Decimal("75") / Decimal("184")
        ).quantize(QUANTIZE_CENTS)

        entry = PurchaseEntryGenerator.generate_historical_cost(
            entry_date=self.PURCHASE_DATE,
            security_description="BTP 3.5% 01/03/2030",
            purchase_price_clean=self.CLEAN_PRICE,
            transaction_costs=self.COMMISSION,
            accrued_interest=accrued,
            classification=Classification.IMMOBILIZED,
        )

        assert entry.is_balanced
        assert entry.total_debit == entry.total_credit

    def test_purchase_entry_amounts(self) -> None:
        """Verifica importi esatti delle righe."""
        accrued = Decimal("713.32")  # Arrotondato ai centesimi

        entry = PurchaseEntryGenerator.generate_historical_cost(
            entry_date=self.PURCHASE_DATE,
            security_description="BTP 3.5% 01/03/2030",
            purchase_price_clean=self.CLEAN_PRICE,
            transaction_costs=self.COMMISSION,
            accrued_interest=accrued,
        )

        # Dare: Titoli = 101200 + 166 = 101366
        titoli = [
            l for l in entry.lines
            if l.account_code == DEFAULT_CHART.securities_immobilized.code
        ]
        assert titoli[0].debit == Decimal("101366.00")

        # Dare: Rateo = 713.32
        rateo = [
            l for l in entry.lines
            if l.account_code == DEFAULT_CHART.accrued_interest_asset.code
        ]
        assert rateo[0].debit == Decimal("713.32")

        # Avere: Banca = 101366 + 713.32 = 102079.32
        banca = [
            l for l in entry.lines
            if l.account_code == DEFAULT_CHART.bank_account.code
        ]
        assert banca[0].credit == Decimal("102079.32")

    def test_rateo_is_separate_from_cost(self) -> None:
        """OIC 20 par. 50: il rateo è SEMPRE separato dal costo del titolo."""
        entry = PurchaseEntryGenerator.generate_historical_cost(
            entry_date=self.PURCHASE_DATE,
            security_description="BTP 3.5%",
            purchase_price_clean=self.CLEAN_PRICE,
            transaction_costs=self.COMMISSION,
            accrued_interest=Decimal("713.32"),
        )

        # Il conto titoli NON include il rateo
        titoli = [
            l for l in entry.lines
            if l.account_code == DEFAULT_CHART.securities_immobilized.code
        ]
        assert titoli[0].debit == Decimal("101366.00")  # Solo corso secco + oneri

        # Il rateo è su un conto diverso
        rateo = [
            l for l in entry.lines
            if l.account_code == DEFAULT_CHART.accrued_interest_asset.code
        ]
        assert len(rateo) == 1
        assert rateo[0].account_code != titoli[0].account_code
