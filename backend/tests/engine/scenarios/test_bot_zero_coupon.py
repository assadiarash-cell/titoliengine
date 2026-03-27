"""
SCENARIO 4: BOT zero coupon — Acquisto + Scadenza.

Dati dello scenario:
- Titolo: BOT 12 mesi
- Nominale: EUR 100.000
- Data acquisto: 15/01/2025
- Prezzo acquisto: 96.50 (96.500 EUR su 100.000 nominale)
- Commissioni: 50,00 EUR
- Data scadenza: 15/01/2026
- Rimborso: 100.000,00 EUR
- Scarto di emissione: 100.000 - 96.500 = 3.500,00 EUR
- Ritenuta su scarto: 12,5% × 3.500 = 437,50 EUR

Scrittura acquisto:
  Dare: Titoli circolanti         96.550,00  (96.500 + 50)
  Avere: Banca c/c                96.550,00

Scrittura scadenza:
  Dare: Banca c/c                99.562,50  (100.000 - 437,50)
  Dare: Erario c/ritenute           437,50
  Avere: Titoli circolanti       96.550,00  (scarico costo)
  Avere: Interessi attivi         3.450,00  (scarto: 100.000 - 96.550)

Verifica acquisto: 96.550 = 96.550 ✓
Verifica scadenza: 100.000 = 100.000 ✓

Riferimento: OIC 20, par. 14-30.
"""
from datetime import date
from decimal import Decimal

from app.engine.constants import Classification
from app.engine.journal.purchase import PurchaseEntryGenerator
from app.engine.journal.maturity import MaturityEntryGenerator
from app.engine.journal.templates import DEFAULT_CHART


class TestScenario4BotZeroCoupon:
    """Scenario 4: BOT zero coupon — ciclo completo."""

    NOMINAL = Decimal("100000.00")
    PURCHASE_PRICE = Decimal("96500.00")
    COMMISSION = Decimal("50.00")
    PURCHASE_COST = Decimal("96550.00")  # 96500 + 50
    REDEMPTION = Decimal("100000.00")
    SPREAD = Decimal("3450.00")  # 100000 - 96550
    WITHHOLDING = Decimal("437.50")  # 3500 × 12.5%

    def test_purchase_balanced(self) -> None:
        """Scrittura acquisto BOT quadrata."""
        entry = PurchaseEntryGenerator.generate_historical_cost(
            entry_date=date(2025, 1, 15),
            security_description="BOT 12M",
            purchase_price_clean=self.PURCHASE_PRICE,
            transaction_costs=self.COMMISSION,
            classification=Classification.CURRENT,
        )
        assert entry.is_balanced
        assert entry.total_debit == self.PURCHASE_COST

    def test_purchase_on_current_account(self) -> None:
        """BOT va su attivo circolante (C.III.6)."""
        entry = PurchaseEntryGenerator.generate_historical_cost(
            entry_date=date(2025, 1, 15),
            security_description="BOT 12M",
            purchase_price_clean=self.PURCHASE_PRICE,
            transaction_costs=self.COMMISSION,
            classification=Classification.CURRENT,
        )
        sec = [l for l in entry.lines if l.account_code == DEFAULT_CHART.securities_current.code]
        assert len(sec) == 1
        assert sec[0].debit == self.PURCHASE_COST

    def test_maturity_balanced(self) -> None:
        """Scrittura scadenza BOT quadrata."""
        entry = MaturityEntryGenerator.generate_zero_coupon_maturity(
            entry_date=date(2026, 1, 15),
            security_description="BOT 12M",
            redemption_value=self.REDEMPTION,
            purchase_cost=self.PURCHASE_COST,
            withholding_tax=self.WITHHOLDING,
            classification=Classification.CURRENT,
        )
        assert entry.is_balanced

    def test_maturity_amounts(self) -> None:
        """Verifica importi esatti della scadenza."""
        entry = MaturityEntryGenerator.generate_zero_coupon_maturity(
            entry_date=date(2026, 1, 15),
            security_description="BOT 12M",
            redemption_value=self.REDEMPTION,
            purchase_cost=self.PURCHASE_COST,
            withholding_tax=self.WITHHOLDING,
            classification=Classification.CURRENT,
        )

        # Dare: Banca = 100000 - 437.50 = 99562.50
        banca = [l for l in entry.lines if l.account_code == DEFAULT_CHART.bank_account.code]
        assert banca[0].debit == Decimal("99562.50")

        # Dare: Ritenute = 437.50
        rit = [l for l in entry.lines if l.account_code == DEFAULT_CHART.withholding_tax.code]
        assert rit[0].debit == Decimal("437.50")

        # Avere: Titoli = 96550 (scarico costo acquisto)
        sec = [l for l in entry.lines if l.account_code == DEFAULT_CHART.securities_current.code]
        assert sec[0].credit == self.PURCHASE_COST

        # Avere: Interessi = 100000 - 96550 = 3450
        int_lines = [l for l in entry.lines if l.account_code == DEFAULT_CHART.interest_income.code]
        assert int_lines[0].credit == self.SPREAD

    def test_full_lifecycle_balanced(self) -> None:
        """Ciclo completo acquisto + scadenza entrambi quadrati."""
        purchase = PurchaseEntryGenerator.generate_historical_cost(
            entry_date=date(2025, 1, 15),
            security_description="BOT 12M",
            purchase_price_clean=self.PURCHASE_PRICE,
            transaction_costs=self.COMMISSION,
            classification=Classification.CURRENT,
        )
        maturity = MaturityEntryGenerator.generate_zero_coupon_maturity(
            entry_date=date(2026, 1, 15),
            security_description="BOT 12M",
            redemption_value=self.REDEMPTION,
            purchase_cost=self.PURCHASE_COST,
            withholding_tax=self.WITHHOLDING,
            classification=Classification.CURRENT,
        )
        assert purchase.is_balanced
        assert maturity.is_balanced
