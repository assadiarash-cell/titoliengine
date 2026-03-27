"""
SCENARIO 3: Vendita anticipata con minusvalenza.

Dati dello scenario:
- Titolo: BTP 3.50% 01/03/2030
- Nominale: EUR 100.000
- Valore contabile (costo storico): 101.366,00 (101.200 + 166 oneri)
- Data vendita: 15/11/2025
- Prezzo vendita corso secco: 99.000,00
- Commissioni vendita: 150,00
- Rateo cedolare maturato: 01/09 → 15/11 = 75 giorni su 181 (01/09 → 01/03)
  Rateo = 1750 × 75/181 = 725,14 EUR
- Minusvalenza: 99.000 - 101.366 = -2.366,00

Scrittura attesa:
  Dare: Banca c/c                99.575,14  (99.000 - 150 + 725,14)
  Dare: Commissioni vendita          150,00
  Dare: Minusvalenza               2.366,00
  Avere: Titoli immobilizzati   101.366,00  (scarico valore contabile)
  Avere: Interessi attivi            725,14  (rateo maturato venduto)

Verifica: dare 102.091,14 = avere 102.091,14 ✓

Riferimento: OIC 20, par. 56-62.
"""
from datetime import date
from decimal import Decimal

from app.engine.journal.sale import SaleEntryGenerator
from app.engine.journal.templates import DEFAULT_CHART


class TestScenario3EarlySaleWithLoss:
    """Scenario 3: Vendita anticipata con minusvalenza."""

    BOOK_VALUE = Decimal("101366.00")
    SALE_PRICE = Decimal("99000.00")
    SALE_COSTS = Decimal("150.00")
    ACCRUED_SOLD = Decimal("725.14")
    LOSS = Decimal("2366.00")  # 99000 - 101366

    def test_sale_entry_balanced(self) -> None:
        """La scrittura di vendita deve essere quadrata."""
        entry = SaleEntryGenerator.generate(
            entry_date=date(2025, 11, 15),
            security_description="BTP 3.5% 01/03/2030",
            sale_price_clean=self.SALE_PRICE,
            book_value=self.BOOK_VALUE,
            sale_costs=self.SALE_COSTS,
            accrued_interest_sold=self.ACCRUED_SOLD,
        )
        assert entry.is_balanced

    def test_sale_entry_amounts(self) -> None:
        """Verifica importi esatti delle righe."""
        entry = SaleEntryGenerator.generate(
            entry_date=date(2025, 11, 15),
            security_description="BTP 3.5% 01/03/2030",
            sale_price_clean=self.SALE_PRICE,
            book_value=self.BOOK_VALUE,
            sale_costs=self.SALE_COSTS,
            accrued_interest_sold=self.ACCRUED_SOLD,
        )

        # Dare: Banca = 99000 - 150 + 725.14 = 99575.14
        banca = [l for l in entry.lines if l.account_code == DEFAULT_CHART.bank_account.code]
        assert banca[0].debit == Decimal("99575.14")

        # Dare: Commissioni = 150
        comm = [l for l in entry.lines if l.account_code == DEFAULT_CHART.transaction_costs.code]
        assert comm[0].debit == Decimal("150.00")

        # Dare: Minusvalenza = 2366 (prezzo lordo - book)
        # Nota: con la nuova logica, loss = sale_price - book = 99000 - 101366 = -2366
        minus = [l for l in entry.lines if l.account_code == DEFAULT_CHART.capital_loss.code]
        assert minus[0].debit == self.LOSS

        # Avere: Titoli = 101366
        titoli = [l for l in entry.lines if l.account_code == DEFAULT_CHART.securities_immobilized.code]
        assert titoli[0].credit == self.BOOK_VALUE

        # Avere: Interessi attivi (rateo venduto) = 725.14
        interessi = [l for l in entry.lines if l.account_code == DEFAULT_CHART.interest_income.code]
        assert interessi[0].credit == self.ACCRUED_SOLD

    def test_no_plusvalenza_present(self) -> None:
        """Nessuna plusvalenza nella vendita in perdita."""
        entry = SaleEntryGenerator.generate(
            entry_date=date(2025, 11, 15),
            security_description="BTP 3.5%",
            sale_price_clean=self.SALE_PRICE,
            book_value=self.BOOK_VALUE,
            sale_costs=self.SALE_COSTS,
            accrued_interest_sold=self.ACCRUED_SOLD,
        )
        gain = [l for l in entry.lines if l.account_code == DEFAULT_CHART.capital_gain.code]
        assert len(gain) == 0

    def test_minusvalenza_is_correct(self) -> None:
        """La minusvalenza è calcolata su prezzo lordo (non netto)."""
        entry = SaleEntryGenerator.generate(
            entry_date=date(2025, 11, 15),
            security_description="BTP",
            sale_price_clean=self.SALE_PRICE,
            book_value=self.BOOK_VALUE,
            sale_costs=self.SALE_COSTS,
        )
        minus = [l for l in entry.lines if l.account_code == DEFAULT_CHART.capital_loss.code]
        # Loss = 99000 - 101366 = -2366 (non deducendo commissioni)
        assert minus[0].debit == Decimal("2366.00")
