"""
Classi base per le scritture contabili (journal entries).

Riferimento: Art. 2214-2220 c.c. — Tenuta dei libri contabili.

Ogni JournalEntry rappresenta una scrittura in partita doppia.
Ogni JournalLine rappresenta una riga (dare o avere) della scrittura.

La quadratura dare = avere è verificata con ZERO tolleranza.

Tutti gli importi in Decimal, MAI float.
"""
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from typing import List, Optional

from ..validators.balance import BalanceValidationError, BalanceValidator


@dataclass
class JournalLine:
    """
    Singola riga di una scrittura contabile.

    Riferimento: Art. 2214 c.c.

    Attributes:
        account_code: codice conto (es. "B.III.3.a")
        account_name: nome descrittivo del conto
        debit: importo in dare (0 se avere)
        credit: importo in avere (0 se dare)
        description: descrizione della riga
    """
    account_code: str
    account_name: str
    debit: Decimal = Decimal("0")
    credit: Decimal = Decimal("0")
    description: str = ""


@dataclass
class JournalEntry:
    """
    Scrittura contabile in partita doppia.

    Riferimento: Art. 2214 c.c.

    Attributes:
        entry_date: data della scrittura
        description: causale della scrittura
        lines: lista di righe contabili
        reference: riferimento documento (facoltativo)
        entry_type: tipo di operazione (acquisto, cedola, vendita, ecc.)
    """
    entry_date: date
    description: str
    lines: List[JournalLine] = field(default_factory=list)
    reference: str = ""
    entry_type: str = ""

    def add_line(
        self,
        account_code: str,
        account_name: str,
        debit: Decimal = Decimal("0"),
        credit: Decimal = Decimal("0"),
        description: str = "",
    ) -> None:
        """
        Aggiunge una riga alla scrittura.

        Args:
            account_code: codice conto
            account_name: nome conto
            debit: importo dare
            credit: importo avere
            description: descrizione riga
        """
        self.lines.append(JournalLine(
            account_code=account_code,
            account_name=account_name,
            debit=debit,
            credit=credit,
            description=description,
        ))

    def validate_balance(self) -> None:
        """
        Verifica la quadratura dare = avere con ZERO tolleranza.

        Riferimento: Art. 2423 c.c.

        Raises:
            BalanceValidationError: se dare ≠ avere
            ValueError: se una riga viola regole dare/avere
        """
        BalanceValidator.validate(self)

    @property
    def total_debit(self) -> Decimal:
        """Totale dare della scrittura."""
        return sum((line.debit for line in self.lines), Decimal("0"))

    @property
    def total_credit(self) -> Decimal:
        """Totale avere della scrittura."""
        return sum((line.credit for line in self.lines), Decimal("0"))

    @property
    def is_balanced(self) -> bool:
        """True se la scrittura è quadrata (dare == avere)."""
        return self.total_debit == self.total_credit
