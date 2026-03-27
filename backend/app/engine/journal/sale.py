"""
Generatore scritture contabili per vendita titoli.

Riferimento: OIC 20, par. 56-62.

Scrittura di vendita:
  Dare: Banca c/c (incasso netto)
  Dare: Commissioni vendita (se presenti)
  Dare: Minusvalenza (se prezzo < valore contabile)
  Avere: Titoli (scarico valore contabile)
  Avere: Rateo cedolare maturato e venduto (se presente)
  Avere: Plusvalenza (se prezzo > valore contabile)

La plus/minusvalenza è calcolata come:
  gain_loss = (prezzo_vendita_clean - commissioni_vendita) - valore_contabile

Il rateo cedolare maturato e venduto è rilevato come interesse attivo,
separato dalla plus/minusvalenza.

Tutti gli importi in Decimal, MAI float.
"""
from datetime import date
from decimal import Decimal

from ..constants import Classification, QUANTIZE_CENTS
from .base import JournalEntry
from .templates import ChartOfAccounts, DEFAULT_CHART


class SaleEntryGenerator:
    """
    Genera scritture contabili per la vendita di titoli.

    Riferimento: OIC 20, par. 56-62.
    """

    @classmethod
    def generate(
        cls,
        entry_date: date,
        security_description: str,
        sale_price_clean: Decimal,
        book_value: Decimal,
        sale_costs: Decimal = Decimal("0"),
        accrued_interest_sold: Decimal = Decimal("0"),
        withholding_tax_on_gain: Decimal = Decimal("0"),
        classification: Classification = Classification.IMMOBILIZED,
        chart: ChartOfAccounts = DEFAULT_CHART,
    ) -> JournalEntry:
        """
        Genera la scrittura di vendita titoli.

        Riferimento: OIC 20, par. 56-62.

        Args:
            entry_date: data vendita
            security_description: descrizione titolo
            sale_price_clean: prezzo di vendita corso secco
            book_value: valore contabile del titolo (storico o ammortizzato)
            sale_costs: commissioni e spese di vendita
            accrued_interest_sold: rateo cedolare maturato e venduto
            withholding_tax_on_gain: ritenuta su plusvalenza (se applicabile)
            classification: classificazione contabile
            chart: piano dei conti

        Returns:
            JournalEntry validata e quadrata.
        """
        entry = JournalEntry(
            entry_date=entry_date,
            description=f"Vendita {security_description}",
            entry_type="sale",
        )

        securities_account = (
            chart.securities_immobilized
            if classification == Classification.IMMOBILIZED
            else chart.securities_current
        )

        # Plus/minusvalenza (prezzo lordo vs valore contabile)
        # Le commissioni di vendita sono un costo separato (B.14),
        # NON riducono la plus/minusvalenza.
        gain_loss: Decimal = (
            sale_price_clean - book_value
        ).quantize(QUANTIZE_CENTS)

        # Banca riceve: prezzo - commissioni + rateo - ritenuta
        bank_inflow: Decimal = (
            sale_price_clean - sale_costs
            + accrued_interest_sold - withholding_tax_on_gain
        ).quantize(QUANTIZE_CENTS)

        # Dare: Banca (incasso netto)
        entry.add_line(
            account_code=chart.bank_account.code,
            account_name=chart.bank_account.name,
            debit=bank_inflow,
            description=f"Incasso vendita {security_description}",
        )

        # Dare: Commissioni vendita (se presenti)
        if sale_costs > Decimal("0"):
            entry.add_line(
                account_code=chart.transaction_costs.code,
                account_name=chart.transaction_costs.name,
                debit=sale_costs.quantize(QUANTIZE_CENTS),
                description="Commissioni vendita titoli",
            )

        # Dare: Ritenuta su plusvalenza (se presente)
        if withholding_tax_on_gain > Decimal("0"):
            entry.add_line(
                account_code=chart.withholding_tax.code,
                account_name=chart.withholding_tax.name,
                debit=withholding_tax_on_gain.quantize(QUANTIZE_CENTS),
                description="Ritenuta fiscale su plusvalenza",
            )

        # Dare: Minusvalenza (se prezzo < valore contabile)
        if gain_loss < Decimal("0"):
            entry.add_line(
                account_code=chart.capital_loss.code,
                account_name=chart.capital_loss.name,
                debit=abs(gain_loss),
                description="Minusvalenza da cessione titoli",
            )

        # Avere: Titoli (scarico valore contabile)
        entry.add_line(
            account_code=securities_account.code,
            account_name=securities_account.name,
            credit=book_value.quantize(QUANTIZE_CENTS),
            description=f"Scarico {security_description} dal portafoglio",
        )

        # Avere: Rateo cedolare maturato e venduto
        if accrued_interest_sold > Decimal("0"):
            entry.add_line(
                account_code=chart.interest_income.code,
                account_name=chart.interest_income.name,
                credit=accrued_interest_sold.quantize(QUANTIZE_CENTS),
                description="Rateo cedolare maturato e venduto",
            )

        # Avere: Plusvalenza (se prezzo > valore contabile)
        if gain_loss > Decimal("0"):
            entry.add_line(
                account_code=chart.capital_gain.code,
                account_name=chart.capital_gain.name,
                credit=gain_loss,
                description="Plusvalenza da cessione titoli",
            )

        entry.validate_balance()
        return entry
