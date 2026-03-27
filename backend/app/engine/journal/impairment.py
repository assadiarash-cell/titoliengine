"""
Generatore scritture contabili per svalutazione e ripristino valore titoli.

Riferimento:
- OIC 20, par. 63-75: Svalutazione titoli immobilizzati
- Art. 2426 c.c.: Svalutazione per perdite durevoli di valore
- OIC 20, par. 76-80: Ripristino di valore

SVALUTAZIONE (impairment):
Quando il valore di mercato scende durevolmente sotto il valore contabile,
si deve svalutare il titolo.

  Dare: Svalutazione titoli (D.19.b)
  Avere: Fondo svalutazione titoli (B.III.3.a.bis)

RIPRISTINO (reversal):
Se vengono meno le cause della svalutazione, il valore va ripristinato
fino al massimo del valore contabile originale.

  Dare: Fondo svalutazione titoli (B.III.3.a.bis)
  Avere: Ripristino di valore (D.18.b)

Tutti gli importi in Decimal, MAI float.
"""
from datetime import date
from decimal import Decimal

from ..constants import QUANTIZE_CENTS
from .base import JournalEntry
from .templates import ChartOfAccounts, DEFAULT_CHART


class ImpairmentEntryGenerator:
    """
    Genera scritture contabili per svalutazione e ripristino valore.

    Riferimento: OIC 20, par. 63-80; Art. 2426 c.c.
    """

    @classmethod
    def generate_impairment(
        cls,
        entry_date: date,
        security_description: str,
        impairment_amount: Decimal,
        chart: ChartOfAccounts = DEFAULT_CHART,
    ) -> JournalEntry:
        """
        Genera la scrittura di svalutazione per perdita durevole.

        Riferimento: OIC 20, par. 63-75; Art. 2426 c.c.

        Dare: Svalutazione titoli (D.19.b)
        Avere: Fondo svalutazione (B.III.3.a.bis)

        Args:
            entry_date: data della svalutazione (tipicamente 31/12)
            security_description: descrizione del titolo
            impairment_amount: importo della svalutazione

        Returns:
            JournalEntry validata e quadrata.

        Raises:
            ValueError: se l'importo è negativo o zero.
        """
        if impairment_amount <= Decimal("0"):
            raise ValueError(
                f"L'importo della svalutazione deve essere positivo. "
                f"Ricevuto: {impairment_amount}"
            )

        entry = JournalEntry(
            entry_date=entry_date,
            description=f"Svalutazione {security_description}",
            entry_type="impairment",
        )

        # Dare: Svalutazione (conto economico)
        entry.add_line(
            account_code=chart.impairment_cost.code,
            account_name=chart.impairment_cost.name,
            debit=impairment_amount.quantize(QUANTIZE_CENTS),
            description=f"Svalutazione per perdita durevole {security_description}",
        )

        # Avere: Fondo svalutazione (stato patrimoniale)
        entry.add_line(
            account_code=chart.securities_impairment_fund.code,
            account_name=chart.securities_impairment_fund.name,
            credit=impairment_amount.quantize(QUANTIZE_CENTS),
            description=f"Accantonamento fondo svalutazione {security_description}",
        )

        entry.validate_balance()
        return entry

    @classmethod
    def generate_reversal(
        cls,
        entry_date: date,
        security_description: str,
        reversal_amount: Decimal,
        chart: ChartOfAccounts = DEFAULT_CHART,
    ) -> JournalEntry:
        """
        Genera la scrittura di ripristino di valore.

        Riferimento: OIC 20, par. 76-80.

        Il ripristino non può eccedere il valore contabile originale
        (pre-svalutazione). Questa verifica è responsabilità del chiamante.

        Dare: Fondo svalutazione (B.III.3.a.bis)
        Avere: Ripristino di valore (D.18.b)

        Args:
            entry_date: data del ripristino
            security_description: descrizione del titolo
            reversal_amount: importo del ripristino

        Returns:
            JournalEntry validata e quadrata.

        Raises:
            ValueError: se l'importo è negativo o zero.
        """
        if reversal_amount <= Decimal("0"):
            raise ValueError(
                f"L'importo del ripristino deve essere positivo. "
                f"Ricevuto: {reversal_amount}"
            )

        entry = JournalEntry(
            entry_date=entry_date,
            description=f"Ripristino valore {security_description}",
            entry_type="reversal",
        )

        # Dare: Fondo svalutazione (riduzione fondo)
        entry.add_line(
            account_code=chart.securities_impairment_fund.code,
            account_name=chart.securities_impairment_fund.name,
            debit=reversal_amount.quantize(QUANTIZE_CENTS),
            description=f"Utilizzo fondo svalutazione {security_description}",
        )

        # Avere: Ripristino di valore (ricavo)
        entry.add_line(
            account_code=chart.reversal_income.code,
            account_name=chart.reversal_income.name,
            credit=reversal_amount.quantize(QUANTIZE_CENTS),
            description=f"Ripristino di valore {security_description}",
        )

        entry.validate_balance()
        return entry
