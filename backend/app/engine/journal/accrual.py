"""
Generatore scritture contabili per ratei di fine esercizio.

Riferimento: OIC 20, par. 50; Art. 2424-bis c.c.

Al 31/12 (o altra data di chiusura) si rileva il rateo attivo per
gli interessi maturati ma non ancora incassati sul titolo.

Scrittura di rilevazione rateo:
  Dare: Rateo attivo (D.18.d)
  Avere: Interessi attivi (C.16.a)

Scrittura di storno rateo (apertura esercizio successivo):
  Dare: Interessi attivi (C.16.a)
  Avere: Rateo attivo (D.18.d)

Tutti gli importi in Decimal, MAI float.
"""
from datetime import date
from decimal import Decimal

from ..constants import QUANTIZE_CENTS
from .base import JournalEntry
from .templates import ChartOfAccounts, DEFAULT_CHART


class AccrualEntryGenerator:
    """
    Genera scritture contabili per ratei di fine esercizio.

    Riferimento: OIC 20, par. 50; Art. 2424-bis c.c.
    """

    @classmethod
    def generate_year_end_accrual(
        cls,
        entry_date: date,
        security_description: str,
        accrued_interest: Decimal,
        chart: ChartOfAccounts = DEFAULT_CHART,
    ) -> JournalEntry:
        """
        Genera la scrittura di rateo attivo di fine esercizio.

        Riferimento: OIC 20, par. 50.

        Dare: Rateo attivo
        Avere: Interessi attivi

        Args:
            entry_date: data di chiusura esercizio (es. 31/12/2025)
            security_description: descrizione del titolo
            accrued_interest: rateo maturato calcolato pro-rata

        Returns:
            JournalEntry validata e quadrata.

        Raises:
            ValueError: se l'importo è negativo o zero.
        """
        if accrued_interest <= Decimal("0"):
            raise ValueError(
                f"Il rateo di fine esercizio deve essere positivo. "
                f"Ricevuto: {accrued_interest}"
            )

        entry = JournalEntry(
            entry_date=entry_date,
            description=f"Rateo attivo {security_description}",
            entry_type="accrual",
        )

        # Dare: Rateo attivo
        entry.add_line(
            account_code=chart.accrued_interest_asset.code,
            account_name=chart.accrued_interest_asset.name,
            debit=accrued_interest.quantize(QUANTIZE_CENTS),
            description=f"Rateo interessi maturati al {entry_date}",
        )

        # Avere: Interessi attivi
        entry.add_line(
            account_code=chart.interest_income.code,
            account_name=chart.interest_income.name,
            credit=accrued_interest.quantize(QUANTIZE_CENTS),
            description="Interessi di competenza esercizio",
        )

        entry.validate_balance()
        return entry

    @classmethod
    def generate_reversal(
        cls,
        entry_date: date,
        security_description: str,
        accrued_interest: Decimal,
        chart: ChartOfAccounts = DEFAULT_CHART,
    ) -> JournalEntry:
        """
        Genera la scrittura di storno rateo (apertura esercizio successivo).

        Riferimento: OIC 20, par. 50.

        Dare: Interessi attivi (storno)
        Avere: Rateo attivo (storno)

        Args:
            entry_date: data di apertura esercizio (es. 01/01/2026)
            security_description: descrizione del titolo
            accrued_interest: importo rateo da stornare

        Returns:
            JournalEntry validata e quadrata.
        """
        if accrued_interest <= Decimal("0"):
            raise ValueError(
                f"L'importo dello storno deve essere positivo. "
                f"Ricevuto: {accrued_interest}"
            )

        entry = JournalEntry(
            entry_date=entry_date,
            description=f"Storno rateo {security_description}",
            entry_type="accrual_reversal",
        )

        # Dare: Interessi attivi (storno)
        entry.add_line(
            account_code=chart.interest_income.code,
            account_name=chart.interest_income.name,
            debit=accrued_interest.quantize(QUANTIZE_CENTS),
            description="Storno interessi attivi esercizio precedente",
        )

        # Avere: Rateo attivo (storno)
        entry.add_line(
            account_code=chart.accrued_interest_asset.code,
            account_name=chart.accrued_interest_asset.name,
            credit=accrued_interest.quantize(QUANTIZE_CENTS),
            description="Storno rateo attivo esercizio precedente",
        )

        entry.validate_balance()
        return entry
