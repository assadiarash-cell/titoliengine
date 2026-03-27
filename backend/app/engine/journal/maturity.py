"""
Generatore scritture contabili per scadenza/rimborso titoli.

Riferimento: OIC 20, par. 56-62.

Alla scadenza il titolo viene rimborsato al valore nominale (o al prezzo
di rimborso pattuito). La differenza tra valore di rimborso e valore
contabile genera una plus/minusvalenza.

Scrittura per titoli a cedola:
  Dare: Banca (valore di rimborso)
  Avere: Titoli (scarico valore contabile)
  Avere: Plusvalenza / Dare: Minusvalenza (se presente)

Scrittura per zero coupon (BOT/CTZ):
  Dare: Banca (netto dopo ritenuta)
  Dare: Erario c/ritenute (ritenuta sullo scarto)
  Avere: Titoli (scarico costo acquisto)
  Avere: Interessi attivi (scarto di emissione)

Tutti gli importi in Decimal, MAI float.
"""
from datetime import date
from decimal import Decimal

from ..constants import Classification, QUANTIZE_CENTS
from .base import JournalEntry
from .templates import ChartOfAccounts, DEFAULT_CHART


class MaturityEntryGenerator:
    """
    Genera scritture contabili per scadenza/rimborso titoli.

    Riferimento: OIC 20, par. 56-62.
    """

    @classmethod
    def generate_bond_maturity(
        cls,
        entry_date: date,
        security_description: str,
        redemption_value: Decimal,
        book_value: Decimal,
        last_coupon_gross: Decimal = Decimal("0"),
        withholding_tax_coupon: Decimal = Decimal("0"),
        classification: Classification = Classification.IMMOBILIZED,
        chart: ChartOfAccounts = DEFAULT_CHART,
    ) -> JournalEntry:
        """
        Genera la scrittura di rimborso a scadenza per titoli a cedola.

        Riferimento: OIC 20, par. 56-62.

        Args:
            entry_date: data scadenza
            security_description: descrizione titolo
            redemption_value: valore di rimborso (nominale × prezzo rimborso/100)
            book_value: valore contabile alla data di scadenza
            last_coupon_gross: ultima cedola lorda (se pagata insieme al rimborso)
            withholding_tax_coupon: ritenuta sull'ultima cedola
            classification: classificazione contabile
            chart: piano dei conti

        Returns:
            JournalEntry validata e quadrata.
        """
        entry = JournalEntry(
            entry_date=entry_date,
            description=f"Rimborso a scadenza {security_description}",
            entry_type="maturity",
        )

        securities_account = (
            chart.securities_immobilized
            if classification == Classification.IMMOBILIZED
            else chart.securities_current
        )

        gain_loss: Decimal = (
            redemption_value - book_value
        ).quantize(QUANTIZE_CENTS)

        # Totale incasso: rimborso + eventuale ultima cedola netta
        coupon_net: Decimal = (
            last_coupon_gross - withholding_tax_coupon
        ).quantize(QUANTIZE_CENTS)
        bank_inflow: Decimal = (
            redemption_value + coupon_net
        ).quantize(QUANTIZE_CENTS)

        # Dare: Banca
        entry.add_line(
            account_code=chart.bank_account.code,
            account_name=chart.bank_account.name,
            debit=bank_inflow,
            description=f"Rimborso {security_description}",
        )

        # Dare: Ritenuta su ultima cedola (se presente)
        if withholding_tax_coupon > Decimal("0"):
            entry.add_line(
                account_code=chart.withholding_tax.code,
                account_name=chart.withholding_tax.name,
                debit=withholding_tax_coupon.quantize(QUANTIZE_CENTS),
                description="Ritenuta fiscale su ultima cedola",
            )

        # Dare: Minusvalenza (se rimborso < valore contabile)
        if gain_loss < Decimal("0"):
            entry.add_line(
                account_code=chart.capital_loss.code,
                account_name=chart.capital_loss.name,
                debit=abs(gain_loss),
                description="Minusvalenza da rimborso",
            )

        # Avere: Titoli (scarico valore contabile)
        entry.add_line(
            account_code=securities_account.code,
            account_name=securities_account.name,
            credit=book_value.quantize(QUANTIZE_CENTS),
            description=f"Scarico {security_description}",
        )

        # Avere: Interessi attivi (ultima cedola, se presente)
        if last_coupon_gross > Decimal("0"):
            entry.add_line(
                account_code=chart.interest_income.code,
                account_name=chart.interest_income.name,
                credit=last_coupon_gross.quantize(QUANTIZE_CENTS),
                description="Ultima cedola a scadenza",
            )

        # Avere: Plusvalenza (se rimborso > valore contabile)
        if gain_loss > Decimal("0"):
            entry.add_line(
                account_code=chart.capital_gain.code,
                account_name=chart.capital_gain.name,
                credit=gain_loss,
                description="Plusvalenza da rimborso",
            )

        entry.validate_balance()
        return entry

    @classmethod
    def generate_zero_coupon_maturity(
        cls,
        entry_date: date,
        security_description: str,
        redemption_value: Decimal,
        purchase_cost: Decimal,
        withholding_tax: Decimal = Decimal("0"),
        classification: Classification = Classification.CURRENT,
        chart: ChartOfAccounts = DEFAULT_CHART,
    ) -> JournalEntry:
        """
        Genera la scrittura di rimborso per titoli zero coupon (BOT/CTZ).

        Riferimento: OIC 20, par. 14-30.

        Per gli zero coupon, lo scarto tra prezzo di acquisto e valore
        di rimborso è trattato come interesse (reddito di capitale),
        non come plusvalenza.

        Dare: Banca (netto dopo ritenuta)
        Dare: Erario c/ritenute (ritenuta sullo scarto)
        Avere: Titoli (scarico costo acquisto)
        Avere: Interessi attivi (scarto di emissione)

        Args:
            entry_date: data scadenza
            security_description: descrizione titolo
            redemption_value: valore di rimborso (nominale)
            purchase_cost: costo di acquisto originale
            withholding_tax: ritenuta sullo scarto di emissione
            classification: classificazione contabile
            chart: piano dei conti

        Returns:
            JournalEntry validata e quadrata.
        """
        entry = JournalEntry(
            entry_date=entry_date,
            description=f"Rimborso {security_description}",
            entry_type="maturity_zc",
        )

        securities_account = (
            chart.securities_immobilized
            if classification == Classification.IMMOBILIZED
            else chart.securities_current
        )

        # Scarto di emissione (interesse)
        spread: Decimal = (
            redemption_value - purchase_cost
        ).quantize(QUANTIZE_CENTS)

        # Incasso netto
        bank_inflow: Decimal = (
            redemption_value - withholding_tax
        ).quantize(QUANTIZE_CENTS)

        # Dare: Banca (netto)
        entry.add_line(
            account_code=chart.bank_account.code,
            account_name=chart.bank_account.name,
            debit=bank_inflow,
            description=f"Rimborso {security_description} (netto ritenuta)",
        )

        # Dare: Erario c/ritenute
        if withholding_tax > Decimal("0"):
            entry.add_line(
                account_code=chart.withholding_tax.code,
                account_name=chart.withholding_tax.name,
                debit=withholding_tax.quantize(QUANTIZE_CENTS),
                description="Ritenuta su scarto di emissione",
            )

        # Avere: Titoli (scarico costo acquisto)
        entry.add_line(
            account_code=securities_account.code,
            account_name=securities_account.name,
            credit=purchase_cost.quantize(QUANTIZE_CENTS),
            description=f"Scarico {security_description}",
        )

        # Avere: Interessi attivi (scarto di emissione)
        if spread > Decimal("0"):
            entry.add_line(
                account_code=chart.interest_income.code,
                account_name=chart.interest_income.name,
                credit=spread,
                description="Scarto di emissione (interessi)",
            )

        entry.validate_balance()
        return entry
