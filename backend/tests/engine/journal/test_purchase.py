"""
Test per il generatore scritture di acquisto titoli.

Riferimento: OIC 20, par. 14-30 (costo storico), par. 37-55 (costo ammortizzato).
"""
from datetime import date
from decimal import Decimal

import pytest

from app.engine.constants import Classification
from app.engine.journal.purchase import PurchaseEntryGenerator
from app.engine.journal.templates import DEFAULT_CHART


class TestHistoricalCostPurchase:
    """Test acquisto a costo storico."""

    def test_basic_purchase_balanced(self) -> None:
        """Acquisto base: dare = avere."""
        entry = PurchaseEntryGenerator.generate_historical_cost(
            entry_date=date(2025, 5, 15),
            security_description="BTP 3.5% 01/03/2030",
            purchase_price_clean=Decimal("101200.00"),
            transaction_costs=Decimal("166.00"),
        )
        assert entry.is_balanced
        assert entry.total_debit == Decimal("101366.00")

    def test_purchase_with_accrued_interest(self) -> None:
        """Acquisto con rateo: rateo separato dal costo."""
        entry = PurchaseEntryGenerator.generate_historical_cost(
            entry_date=date(2025, 5, 15),
            security_description="BTP 3.5% 01/03/2030",
            purchase_price_clean=Decimal("101200.00"),
            transaction_costs=Decimal("166.00"),
            accrued_interest=Decimal("713.32"),
        )
        assert entry.is_balanced
        # Totale = 101366 + 713.32 = 102079.32
        assert entry.total_debit == Decimal("102079.32")
        # Verifica che rateo sia su conto separato
        rateo_lines = [
            l for l in entry.lines
            if l.account_code == DEFAULT_CHART.accrued_interest_asset.code
        ]
        assert len(rateo_lines) == 1
        assert rateo_lines[0].debit == Decimal("713.32")

    def test_purchase_with_stamp_duty(self) -> None:
        """Acquisto con bollo."""
        entry = PurchaseEntryGenerator.generate_historical_cost(
            entry_date=date(2025, 5, 15),
            security_description="BTP",
            purchase_price_clean=Decimal("100000.00"),
            transaction_costs=Decimal("100.00"),
            stamp_duty=Decimal("50.00"),
        )
        assert entry.is_balanced
        assert entry.total_debit == Decimal("100150.00")

    def test_current_classification(self) -> None:
        """Titolo circolante usa conto C.III.6."""
        entry = PurchaseEntryGenerator.generate_historical_cost(
            entry_date=date(2025, 5, 15),
            security_description="BOT",
            purchase_price_clean=Decimal("96500.00"),
            transaction_costs=Decimal("0.00"),
            classification=Classification.CURRENT,
        )
        sec_lines = [
            l for l in entry.lines
            if l.account_code == DEFAULT_CHART.securities_current.code
        ]
        assert len(sec_lines) == 1

    def test_entry_type_is_purchase(self) -> None:
        entry = PurchaseEntryGenerator.generate_historical_cost(
            entry_date=date(2025, 5, 15),
            security_description="BTP",
            purchase_price_clean=Decimal("100000.00"),
            transaction_costs=Decimal("0.00"),
        )
        assert entry.entry_type == "purchase"


class TestAmortizedCostPurchase:
    """Test acquisto a costo ammortizzato."""

    def test_basic_amortized_purchase(self) -> None:
        """Acquisto costo ammortizzato: costi inclusi nel valore."""
        entry = PurchaseEntryGenerator.generate_amortized_cost(
            entry_date=date(2025, 5, 15),
            security_description="BTP 3.5% 01/03/2030",
            purchase_price_clean=Decimal("101200.00"),
            transaction_costs=Decimal("166.00"),
        )
        assert entry.is_balanced
        # Titoli = 101200 + 166 = 101366
        assert entry.total_debit == Decimal("101366.00")

    def test_amortized_with_accrued(self) -> None:
        """Costo ammortizzato con rateo separato."""
        entry = PurchaseEntryGenerator.generate_amortized_cost(
            entry_date=date(2025, 5, 15),
            security_description="BTP 3.5%",
            purchase_price_clean=Decimal("101200.00"),
            transaction_costs=Decimal("166.00"),
            accrued_interest=Decimal("713.32"),
        )
        assert entry.is_balanced
        assert entry.total_debit == Decimal("102079.32")
