"""
Test per il validatore di quadratura contabile.

Scenari testati:
1. Scrittura quadrata → OK
2. Scrittura non quadrata → BalanceValidationError
3. Riga con dare E avere → ValueError
4. Riga con dare = avere = 0 → ValueError
5. Importo negativo → ValueError
6. Scrittura vuota → ValueError
7. Validazione batch

Riferimento: Art. 2423 c.c.
"""
from datetime import date
from decimal import Decimal

import pytest

from app.engine.journal.base import JournalEntry, JournalLine
from app.engine.validators.balance import (
    BalanceValidationError,
    BalanceValidator,
)


class TestBalanceValidator:
    """Test validazione quadratura."""

    def test_balanced_entry_passes(self) -> None:
        """Scrittura quadrata: nessun errore."""
        entry = JournalEntry(
            entry_date=date(2025, 5, 15),
            description="Test quadratura",
            lines=[
                JournalLine("A", "Conto A", debit=Decimal("1000.00")),
                JournalLine("B", "Conto B", credit=Decimal("1000.00")),
            ],
        )
        BalanceValidator.validate(entry)  # Non deve lanciare

    def test_unbalanced_raises(self) -> None:
        """Scrittura non quadrata: BalanceValidationError."""
        entry = JournalEntry(
            entry_date=date(2025, 5, 15),
            description="Test non quadra",
            lines=[
                JournalLine("A", "Conto A", debit=Decimal("1000.00")),
                JournalLine("B", "Conto B", credit=Decimal("999.99")),
            ],
        )
        with pytest.raises(BalanceValidationError) as exc_info:
            BalanceValidator.validate(entry)
        assert exc_info.value.total_debit == Decimal("1000.00")
        assert exc_info.value.total_credit == Decimal("999.99")
        assert exc_info.value.difference == Decimal("0.01")

    def test_both_debit_and_credit_raises(self) -> None:
        """Riga con dare E avere entrambi > 0 → errore."""
        entry = JournalEntry(
            entry_date=date(2025, 5, 15),
            description="Test",
            lines=[
                JournalLine("A", "Conto A", debit=Decimal("100"), credit=Decimal("50")),
            ],
        )
        with pytest.raises(ValueError, match="XOR"):
            BalanceValidator.validate(entry)

    def test_zero_both_raises(self) -> None:
        """Riga con dare = avere = 0 → errore."""
        entry = JournalEntry(
            entry_date=date(2025, 5, 15),
            description="Test",
            lines=[
                JournalLine("A", "Conto A", debit=Decimal("0"), credit=Decimal("0")),
            ],
        )
        with pytest.raises(ValueError, match="almeno un importo"):
            BalanceValidator.validate(entry)

    def test_negative_debit_raises(self) -> None:
        """Importo dare negativo → errore."""
        entry = JournalEntry(
            entry_date=date(2025, 5, 15),
            description="Test",
            lines=[
                JournalLine("A", "Conto A", debit=Decimal("-100")),
            ],
        )
        with pytest.raises(ValueError, match="negativo"):
            BalanceValidator.validate(entry)

    def test_negative_credit_raises(self) -> None:
        """Importo avere negativo → errore."""
        entry = JournalEntry(
            entry_date=date(2025, 5, 15),
            description="Test",
            lines=[
                JournalLine("A", "Conto A", credit=Decimal("-100")),
            ],
        )
        with pytest.raises(ValueError, match="negativo"):
            BalanceValidator.validate(entry)

    def test_empty_entry_raises(self) -> None:
        """Scrittura senza righe → errore."""
        entry = JournalEntry(
            entry_date=date(2025, 5, 15),
            description="Test vuota",
        )
        with pytest.raises(ValueError, match="non ha righe"):
            BalanceValidator.validate(entry)

    def test_multi_line_balanced(self) -> None:
        """Scrittura multi-riga quadrata."""
        entry = JournalEntry(
            entry_date=date(2025, 5, 15),
            description="Multi",
            lines=[
                JournalLine("A", "Dare 1", debit=Decimal("500.00")),
                JournalLine("B", "Dare 2", debit=Decimal("300.00")),
                JournalLine("C", "Avere 1", credit=Decimal("800.00")),
            ],
        )
        BalanceValidator.validate(entry)

    def test_zero_tolerance(self) -> None:
        """Anche 0.01 di differenza deve fallire (ZERO tolleranza)."""
        entry = JournalEntry(
            entry_date=date(2025, 5, 15),
            description="Test tolleranza",
            lines=[
                JournalLine("A", "Conto", debit=Decimal("1000.00")),
                JournalLine("B", "Conto", credit=Decimal("1000.01")),
            ],
        )
        with pytest.raises(BalanceValidationError):
            BalanceValidator.validate(entry)


class TestBalanceValidatorBatch:
    """Test validazione batch."""

    def test_all_valid_returns_empty(self) -> None:
        """Tutte le scritture valide → lista errori vuota."""
        entries = [
            JournalEntry(
                entry_date=date(2025, 1, 1),
                description="OK 1",
                lines=[
                    JournalLine("A", "A", debit=Decimal("100")),
                    JournalLine("B", "B", credit=Decimal("100")),
                ],
            ),
            JournalEntry(
                entry_date=date(2025, 1, 2),
                description="OK 2",
                lines=[
                    JournalLine("C", "C", debit=Decimal("200")),
                    JournalLine("D", "D", credit=Decimal("200")),
                ],
            ),
        ]
        errors = BalanceValidator.validate_batch(entries)
        assert errors == []

    def test_mixed_returns_errors(self) -> None:
        """Batch con errori → lista non vuota."""
        entries = [
            JournalEntry(
                entry_date=date(2025, 1, 1),
                description="OK",
                lines=[
                    JournalLine("A", "A", debit=Decimal("100")),
                    JournalLine("B", "B", credit=Decimal("100")),
                ],
            ),
            JournalEntry(
                entry_date=date(2025, 1, 2),
                description="NON QUADRA",
                lines=[
                    JournalLine("C", "C", debit=Decimal("100")),
                    JournalLine("D", "D", credit=Decimal("99")),
                ],
            ),
        ]
        errors = BalanceValidator.validate_batch(entries)
        assert len(errors) == 1
        assert "Scrittura 1" in errors[0]

    def test_empty_batch_raises(self) -> None:
        """Batch vuoto → errore."""
        with pytest.raises(ValueError, match="Nessuna"):
            BalanceValidator.validate_batch([])


class TestJournalEntryBase:
    """Test classe JournalEntry."""

    def test_add_line(self) -> None:
        entry = JournalEntry(entry_date=date(2025, 1, 1), description="Test")
        entry.add_line("A", "Conto A", debit=Decimal("100"))
        entry.add_line("B", "Conto B", credit=Decimal("100"))
        assert len(entry.lines) == 2

    def test_total_debit(self) -> None:
        entry = JournalEntry(
            entry_date=date(2025, 1, 1),
            description="Test",
            lines=[
                JournalLine("A", "A", debit=Decimal("500")),
                JournalLine("B", "B", debit=Decimal("300")),
                JournalLine("C", "C", credit=Decimal("800")),
            ],
        )
        assert entry.total_debit == Decimal("800")
        assert entry.total_credit == Decimal("800")

    def test_is_balanced(self) -> None:
        entry = JournalEntry(
            entry_date=date(2025, 1, 1),
            description="Test",
            lines=[
                JournalLine("A", "A", debit=Decimal("100")),
                JournalLine("B", "B", credit=Decimal("100")),
            ],
        )
        assert entry.is_balanced is True

    def test_validate_balance_calls_validator(self) -> None:
        entry = JournalEntry(
            entry_date=date(2025, 1, 1),
            description="Test",
            lines=[
                JournalLine("A", "A", debit=Decimal("100")),
                JournalLine("B", "B", credit=Decimal("100")),
            ],
        )
        entry.validate_balance()  # Non deve lanciare
