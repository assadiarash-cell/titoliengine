"""
Generatore scritture contabili per acquisto titoli.

Riferimento: OIC 20, par. 14-30 (costo storico), par. 37-55 (costo ammortizzato).

DUE METODI:

1. COSTO STORICO (bilancio abbreviato/micro):
   Dare: Titoli (corso secco + oneri accessori)
   Dare: Rateo cedolare maturato (se presente)
   Dare: Bollo/imposte (se presenti)
   Avere: Banca c/c (totale esborso)

2. COSTO AMMORTIZZATO (bilancio ordinario):
   Dare: Titoli (corso secco + costi di transazione)
   Dare: Rateo cedolare maturato (se presente)
   Avere: Banca c/c (totale esborso)

REGOLA FONDAMENTALE (OIC 20, par. 50):
Il rateo cedolare è SEMPRE rilevato separatamente dal costo del titolo.
Non fa parte del valore di iscrizione iniziale.

Tutti gli importi in Decimal, MAI float.
"""
from datetime import date
from decimal import Decimal
from typing import Optional

from ..constants import Classification, ValuationMethod, QUANTIZE_CENTS
from .base import JournalEntry, JournalLine
from .templates import ChartOfAccounts, DEFAULT_CHART


class PurchaseEntryGenerator:
    """
    Genera scritture contabili per l'acquisto di titoli.

    Riferimento: OIC 20, par. 14-55.
    """

    @classmethod
    def generate_historical_cost(
        cls,
        entry_date: date,
        security_description: str,
        purchase_price_clean: Decimal,
        transaction_costs: Decimal,
        accrued_interest: Decimal = Decimal("0"),
        stamp_duty: Decimal = Decimal("0"),
        classification: Classification = Classification.IMMOBILIZED,
        chart: ChartOfAccounts = DEFAULT_CHART,
    ) -> JournalEntry:
        """
        Genera la scrittura di acquisto a costo storico.

        Riferimento: OIC 20, par. 14-30.

        Dare: Titoli (corso secco + oneri)
        Dare: Rateo cedolare (se presente)
        Dare: Bollo (se presente)
        Avere: Banca (totale)

        Args:
            entry_date: data dell'operazione
            security_description: descrizione del titolo (es. "BTP 3.5% 01/03/2030")
            purchase_price_clean: prezzo corso secco
            transaction_costs: commissioni e oneri accessori
            accrued_interest: rateo cedolare maturato pagato
            stamp_duty: imposta di bollo
            classification: immobilizzato o circolante
            chart: piano dei conti

        Returns:
            JournalEntry validata e quadrata.
        """
        entry = JournalEntry(
            entry_date=entry_date,
            description=f"Acquisto {security_description}",
            entry_type="purchase",
        )

        # Conto titoli in base alla classificazione
        securities_account = (
            chart.securities_immobilized
            if classification == Classification.IMMOBILIZED
            else chart.securities_current
        )

        # Dare: Titoli (corso secco + commissioni + oneri)
        security_value: Decimal = (
            purchase_price_clean + transaction_costs
        ).quantize(QUANTIZE_CENTS)

        entry.add_line(
            account_code=securities_account.code,
            account_name=securities_account.name,
            debit=security_value,
            description=f"Acquisto {security_description} (corso secco + oneri)",
        )

        # Dare: Rateo cedolare (separato dal costo — OIC 20, par. 50)
        if accrued_interest > Decimal("0"):
            entry.add_line(
                account_code=chart.accrued_interest_asset.code,
                account_name=chart.accrued_interest_asset.name,
                debit=accrued_interest.quantize(QUANTIZE_CENTS),
                description="Rateo cedolare maturato pagato all'acquisto",
            )

        # Dare: Bollo (se presente)
        if stamp_duty > Decimal("0"):
            entry.add_line(
                account_code=chart.transaction_costs.code,
                account_name=chart.transaction_costs.name,
                debit=stamp_duty.quantize(QUANTIZE_CENTS),
                description="Imposta di bollo su acquisto titoli",
            )

        # Avere: Banca (totale esborso)
        total_outflow: Decimal = (
            security_value + accrued_interest + stamp_duty
        ).quantize(QUANTIZE_CENTS)

        entry.add_line(
            account_code=chart.bank_account.code,
            account_name=chart.bank_account.name,
            credit=total_outflow,
            description=f"Pagamento acquisto {security_description}",
        )

        # Validazione OBBLIGATORIA
        entry.validate_balance()
        return entry

    @classmethod
    def generate_amortized_cost(
        cls,
        entry_date: date,
        security_description: str,
        purchase_price_clean: Decimal,
        transaction_costs: Decimal,
        accrued_interest: Decimal = Decimal("0"),
        classification: Classification = Classification.IMMOBILIZED,
        chart: ChartOfAccounts = DEFAULT_CHART,
    ) -> JournalEntry:
        """
        Genera la scrittura di acquisto a costo ammortizzato.

        Riferimento: OIC 20, par. 37-55.

        A costo ammortizzato, i costi di transazione sono inclusi nel
        valore iniziale di iscrizione (fanno parte della base per il TIR).

        Dare: Titoli (corso secco + costi transazione)
        Dare: Rateo cedolare (se presente)
        Avere: Banca (totale)

        Args:
            entry_date: data dell'operazione
            security_description: descrizione del titolo
            purchase_price_clean: prezzo corso secco
            transaction_costs: costi transazione (inclusi nel valore iniziale)
            accrued_interest: rateo cedolare maturato pagato
            classification: immobilizzato o circolante
            chart: piano dei conti

        Returns:
            JournalEntry validata e quadrata.
        """
        entry = JournalEntry(
            entry_date=entry_date,
            description=f"Acquisto {security_description} (costo ammortizzato)",
            entry_type="purchase",
        )

        securities_account = (
            chart.securities_immobilized
            if classification == Classification.IMMOBILIZED
            else chart.securities_current
        )

        # Dare: Titoli (corso secco + costi di transazione)
        security_value: Decimal = (
            purchase_price_clean + transaction_costs
        ).quantize(QUANTIZE_CENTS)

        entry.add_line(
            account_code=securities_account.code,
            account_name=securities_account.name,
            debit=security_value,
            description=f"Acquisto {security_description} (costo ammortizzato)",
        )

        # Dare: Rateo cedolare (separato — OIC 20, par. 50)
        if accrued_interest > Decimal("0"):
            entry.add_line(
                account_code=chart.accrued_interest_asset.code,
                account_name=chart.accrued_interest_asset.name,
                debit=accrued_interest.quantize(QUANTIZE_CENTS),
                description="Rateo cedolare maturato pagato all'acquisto",
            )

        # Avere: Banca
        total_outflow: Decimal = (
            security_value + accrued_interest
        ).quantize(QUANTIZE_CENTS)

        entry.add_line(
            account_code=chart.bank_account.code,
            account_name=chart.bank_account.name,
            credit=total_outflow,
            description=f"Pagamento acquisto {security_description}",
        )

        entry.validate_balance()
        return entry
