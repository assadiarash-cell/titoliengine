"""
Generatore scritture contabili per incasso cedola.

Riferimento: OIC 20, par. 50.

Scrittura all'incasso cedola:
  Dare: Banca c/c (netto cedola dopo ritenuta)
  Dare: Erario c/ritenute (ritenuta fiscale)
  Avere: Rateo attivo da acquisto (chiusura rateo, se presente)
  Avere: Interessi attivi (interessi di competenza)

Se esiste un rateo da acquisto (pagato al venditore), quel rateo
viene chiuso alla prima cedola. La quota di competenza è:
  competenza = cedola_lorda - rateo_acquisto

Tutti gli importi in Decimal, MAI float.
"""
from datetime import date
from decimal import Decimal

from ..constants import QUANTIZE_CENTS
from .base import JournalEntry
from .templates import ChartOfAccounts, DEFAULT_CHART


class CouponEntryGenerator:
    """
    Genera scritture contabili per l'incasso di cedole.

    Riferimento: OIC 20, par. 50.
    """

    @classmethod
    def generate(
        cls,
        entry_date: date,
        security_description: str,
        coupon_gross: Decimal,
        withholding_tax: Decimal,
        accrued_at_purchase: Decimal = Decimal("0"),
        chart: ChartOfAccounts = DEFAULT_CHART,
    ) -> JournalEntry:
        """
        Genera la scrittura di incasso cedola.

        Riferimento: OIC 20, par. 50.

        Dare: Banca (netto)
        Dare: Erario c/ritenute (ritenuta)
        Avere: Rateo attivo (chiusura rateo acquisto, se presente)
        Avere: Interessi attivi (interessi di competenza)

        Args:
            entry_date: data incasso cedola
            security_description: descrizione del titolo
            coupon_gross: cedola lorda
            withholding_tax: ritenuta fiscale
            accrued_at_purchase: rateo pagato all'acquisto (da chiudere)
            chart: piano dei conti

        Returns:
            JournalEntry validata e quadrata.
        """
        entry = JournalEntry(
            entry_date=entry_date,
            description=f"Incasso cedola {security_description}",
            entry_type="coupon",
        )

        # Dare: Banca (netto)
        coupon_net: Decimal = (
            coupon_gross - withholding_tax
        ).quantize(QUANTIZE_CENTS)

        entry.add_line(
            account_code=chart.bank_account.code,
            account_name=chart.bank_account.name,
            debit=coupon_net,
            description=f"Incasso cedola netta {security_description}",
        )

        # Dare: Erario c/ritenute (se la ritenuta è > 0)
        if withholding_tax > Decimal("0"):
            entry.add_line(
                account_code=chart.withholding_tax.code,
                account_name=chart.withholding_tax.name,
                debit=withholding_tax.quantize(QUANTIZE_CENTS),
                description="Ritenuta fiscale su cedola",
            )

        # Avere: Chiusura rateo attivo da acquisto (se presente)
        if accrued_at_purchase > Decimal("0"):
            entry.add_line(
                account_code=chart.accrued_interest_asset.code,
                account_name=chart.accrued_interest_asset.name,
                credit=accrued_at_purchase.quantize(QUANTIZE_CENTS),
                description="Chiusura rateo cedolare pagato all'acquisto",
            )

        # Avere: Interessi attivi di competenza
        # competenza = cedola_lorda - rateo_acquisto
        competence_interest: Decimal = (
            coupon_gross - accrued_at_purchase
        ).quantize(QUANTIZE_CENTS)

        entry.add_line(
            account_code=chart.interest_income.code,
            account_name=chart.interest_income.name,
            credit=competence_interest,
            description="Interessi attivi di competenza",
        )

        entry.validate_balance()
        return entry
