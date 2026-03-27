"""
Test per il generatore scritture rateo fine esercizio.

Riferimento: OIC 20, par. 50; Art. 2424-bis c.c.
"""
from datetime import date
from decimal import Decimal

import pytest

from app.engine.journal.accrual import AccrualEntryGenerator
from app.engine.journal.templates import DEFAULT_CHART


class TestYearEndAccrual:
    """Test rateo di fine esercizio."""

    def test_accrual_balanced(self) -> None:
        """Rateo: dare rateo attivo = avere interessi."""
        entry = AccrualEntryGenerator.generate_year_end_accrual(
            entry_date=date(2025, 12, 31),
            security_description="BTP 3.5%",
            accrued_interest=Decimal("1169.61"),
        )
        assert entry.is_balanced
        assert entry.total_debit == Decimal("1169.61")

    def test_accrual_accounts(self) -> None:
        """Verifica conti corretti."""
        entry = AccrualEntryGenerator.generate_year_end_accrual(
            entry_date=date(2025, 12, 31),
            security_description="BTP",
            accrued_interest=Decimal("500.00"),
        )
        dare = [l for l in entry.lines if l.debit > 0]
        avere = [l for l in entry.lines if l.credit > 0]
        assert dare[0].account_code == DEFAULT_CHART.accrued_interest_asset.code
        assert avere[0].account_code == DEFAULT_CHART.interest_income.code

    def test_zero_raises(self) -> None:
        with pytest.raises(ValueError, match="positivo"):
            AccrualEntryGenerator.generate_year_end_accrual(
                entry_date=date(2025, 12, 31),
                security_description="BTP",
                accrued_interest=Decimal("0"),
            )

    def test_negative_raises(self) -> None:
        with pytest.raises(ValueError, match="positivo"):
            AccrualEntryGenerator.generate_year_end_accrual(
                entry_date=date(2025, 12, 31),
                security_description="BTP",
                accrued_interest=Decimal("-100"),
            )


class TestAccrualReversal:
    """Test storno rateo."""

    def test_reversal_balanced(self) -> None:
        """Storno: dare interessi = avere rateo."""
        entry = AccrualEntryGenerator.generate_reversal(
            entry_date=date(2026, 1, 1),
            security_description="BTP 3.5%",
            accrued_interest=Decimal("1169.61"),
        )
        assert entry.is_balanced
        assert entry.entry_type == "accrual_reversal"

    def test_reversal_accounts_inverted(self) -> None:
        """Storno ha conti invertiti rispetto a rilevazione."""
        entry = AccrualEntryGenerator.generate_reversal(
            entry_date=date(2026, 1, 1),
            security_description="BTP",
            accrued_interest=Decimal("500.00"),
        )
        dare = [l for l in entry.lines if l.debit > 0]
        avere = [l for l in entry.lines if l.credit > 0]
        # Storno: dare interessi, avere rateo (opposto della rilevazione)
        assert dare[0].account_code == DEFAULT_CHART.interest_income.code
        assert avere[0].account_code == DEFAULT_CHART.accrued_interest_asset.code
