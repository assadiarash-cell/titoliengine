"""
Validatore di quadratura contabile (dare = avere).

Riferimento: Art. 2423 c.c. — Il bilancio deve essere redatto con chiarezza
e deve rappresentare in modo veritiero e corretto la situazione patrimoniale.

La partita doppia richiede che per ogni scrittura contabile la somma
degli importi in DARE sia ESATTAMENTE uguale alla somma degli importi in AVERE.

ZERO tolleranza: nessun arrotondamento accettato.

Tutti i calcoli usano decimal.Decimal, MAI float.
"""
from decimal import Decimal
from typing import List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ..journal.base import JournalEntry, JournalLine


class BalanceValidationError(Exception):
    """
    Errore di quadratura contabile.

    Riferimento: Art. 2423 c.c.

    Lanciata quando la somma dare ≠ somma avere in una scrittura contabile.

    Attributes:
        total_debit: totale dare
        total_credit: totale avere
        difference: differenza (dare - avere)
        message: messaggio di dettaglio
    """

    def __init__(
        self,
        total_debit: Decimal,
        total_credit: Decimal,
        message: str = "",
    ) -> None:
        self.total_debit: Decimal = total_debit
        self.total_credit: Decimal = total_credit
        self.difference: Decimal = total_debit - total_credit
        detail: str = (
            f"Quadratura fallita: "
            f"Dare={total_debit}, Avere={total_credit}, "
            f"Differenza={self.difference}"
        )
        if message:
            detail = f"{message} — {detail}"
        super().__init__(detail)


class BalanceValidator:
    """
    Validatore di quadratura per scritture contabili.

    Verifica tre condizioni:
    1. Somma dare == somma avere (ZERO tolleranza)
    2. Ogni riga ha dare XOR avere (mai entrambi, mai nessuno dei due)
    3. Nessun importo negativo

    Riferimento: Art. 2423 c.c., principi generali partita doppia.
    """

    @classmethod
    def validate(cls, entry: "JournalEntry") -> None:
        """
        Valida una singola scrittura contabile.

        Riferimento: Art. 2423 c.c.

        Args:
            entry: scrittura contabile da validare

        Raises:
            BalanceValidationError: se la quadratura fallisce
            ValueError: se una riga viola le regole dare/avere
        """
        if not entry.lines:
            raise ValueError("La scrittura contabile non ha righe.")

        total_debit: Decimal = Decimal("0")
        total_credit: Decimal = Decimal("0")

        for i, line in enumerate(entry.lines):
            cls._validate_line(line, line_index=i)
            total_debit += line.debit
            total_credit += line.credit

        if total_debit != total_credit:
            raise BalanceValidationError(
                total_debit=total_debit,
                total_credit=total_credit,
                message=f"Scrittura '{entry.description}'",
            )

    @classmethod
    def _validate_line(cls, line: "JournalLine", line_index: int = 0) -> None:
        """
        Valida una singola riga contabile.

        Regole:
        - Dare XOR avere (mai entrambi > 0, mai entrambi = 0)
        - Nessun importo negativo

        Args:
            line: riga contabile da validare
            line_index: indice della riga (per messaggi di errore)

        Raises:
            ValueError: se la riga viola le regole.
        """
        if line.debit < Decimal("0"):
            raise ValueError(
                f"Riga {line_index} ({line.account_code}): "
                f"importo dare negativo ({line.debit}). "
                "Gli importi devono essere >= 0."
            )

        if line.credit < Decimal("0"):
            raise ValueError(
                f"Riga {line_index} ({line.account_code}): "
                f"importo avere negativo ({line.credit}). "
                "Gli importi devono essere >= 0."
            )

        has_debit: bool = line.debit > Decimal("0")
        has_credit: bool = line.credit > Decimal("0")

        if has_debit and has_credit:
            raise ValueError(
                f"Riga {line_index} ({line.account_code}): "
                f"dare={line.debit} e avere={line.credit} entrambi > 0. "
                "Ogni riga deve avere dare XOR avere."
            )

        if not has_debit and not has_credit:
            raise ValueError(
                f"Riga {line_index} ({line.account_code}): "
                "dare e avere sono entrambi 0. "
                "Ogni riga deve avere almeno un importo > 0."
            )

    @classmethod
    def validate_batch(cls, entries: List["JournalEntry"]) -> List[str]:
        """
        Valida un batch di scritture contabili.

        Riferimento: Art. 2423 c.c.

        Args:
            entries: lista di scritture da validare

        Returns:
            Lista di messaggi di errore (vuota se tutto valido).

        Raises:
            ValueError: se la lista è vuota.
        """
        if not entries:
            raise ValueError("Nessuna scrittura da validare.")

        errors: List[str] = []
        for i, entry in enumerate(entries):
            try:
                cls.validate(entry)
            except (BalanceValidationError, ValueError) as e:
                errors.append(f"Scrittura {i}: {e}")

        return errors
