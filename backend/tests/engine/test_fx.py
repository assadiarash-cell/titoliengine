"""
Test per il modulo fx.py — Conversione cambi per titoli in valuta estera.

Scenari testati:
1. Conversione da valuta estera a EUR
2. Conversione da EUR a valuta estera
3. Calcolo differenza cambio (utile/perdita)
4. Rivalutazione di fine esercizio
5. Validazione errori (tasso zero/negativo)

Riferimento: OIC 26, OIC 20 par. 65-70.
"""
from datetime import date
from decimal import Decimal

import pytest

from app.engine.constants import Classification
from app.engine.fx import (
    FxConversionResult,
    FxDifferenceResult,
    FxDifferenceType,
    FxEngine,
)


class TestConvertToEur:
    """Test conversione valuta estera → EUR."""

    def test_usd_to_eur(self) -> None:
        """
        1000 USD con cambio EUR/USD = 1.08.
        EUR = 1000 / 1.08 = 925.93.

        Riferimento: OIC 26, par. 10-15.
        """
        result = FxEngine.convert_to_eur(
            amount_foreign=Decimal("1000.00"),
            exchange_rate=Decimal("1.08"),
            conversion_date=date(2025, 5, 15),
            currency="USD",
        )
        assert isinstance(result, FxConversionResult)
        assert result.amount_eur == Decimal("925.93")
        assert result.currency == "USD"

    def test_gbp_to_eur(self) -> None:
        """
        5000 GBP con cambio EUR/GBP = 0.85.
        EUR = 5000 / 0.85 = 5882.35.
        """
        result = FxEngine.convert_to_eur(
            amount_foreign=Decimal("5000.00"),
            exchange_rate=Decimal("0.85"),
            conversion_date=date(2025, 6, 1),
            currency="GBP",
        )
        assert result.amount_eur == Decimal("5882.35")

    def test_exact_conversion(self) -> None:
        """Cambio 1:1 → importo uguale."""
        result = FxEngine.convert_to_eur(
            amount_foreign=Decimal("10000.00"),
            exchange_rate=Decimal("1.00"),
            conversion_date=date(2025, 1, 1),
        )
        assert result.amount_eur == Decimal("10000.00")

    def test_currency_uppercase(self) -> None:
        """Il codice valuta viene normalizzato a uppercase."""
        result = FxEngine.convert_to_eur(
            amount_foreign=Decimal("100"),
            exchange_rate=Decimal("1.10"),
            conversion_date=date(2025, 1, 1),
            currency="usd",
        )
        assert result.currency == "USD"

    def test_zero_rate_raises(self) -> None:
        """Tasso di cambio zero → errore."""
        with pytest.raises(ValueError, match="positivo"):
            FxEngine.convert_to_eur(
                amount_foreign=Decimal("1000"),
                exchange_rate=Decimal("0"),
                conversion_date=date(2025, 1, 1),
            )

    def test_negative_rate_raises(self) -> None:
        """Tasso di cambio negativo → errore."""
        with pytest.raises(ValueError, match="positivo"):
            FxEngine.convert_to_eur(
                amount_foreign=Decimal("1000"),
                exchange_rate=Decimal("-1.08"),
                conversion_date=date(2025, 1, 1),
            )

    def test_result_is_decimal(self) -> None:
        result = FxEngine.convert_to_eur(
            amount_foreign=Decimal("1000"),
            exchange_rate=Decimal("1.08"),
            conversion_date=date(2025, 1, 1),
        )
        assert isinstance(result.amount_eur, Decimal)
        assert isinstance(result.amount_foreign, Decimal)


class TestConvertFromEur:
    """Test conversione EUR → valuta estera."""

    def test_eur_to_usd(self) -> None:
        """
        925.93 EUR con cambio EUR/USD = 1.08.
        USD = 925.93 × 1.08 = 1000.00 (arrotondato).
        """
        result = FxEngine.convert_from_eur(
            amount_eur=Decimal("925.93"),
            exchange_rate=Decimal("1.08"),
            conversion_date=date(2025, 5, 15),
            currency="USD",
        )
        assert isinstance(result, FxConversionResult)
        assert result.amount_foreign == Decimal("1000.00")

    def test_zero_rate_raises(self) -> None:
        with pytest.raises(ValueError, match="positivo"):
            FxEngine.convert_from_eur(
                amount_eur=Decimal("1000"),
                exchange_rate=Decimal("0"),
                conversion_date=date(2025, 1, 1),
            )


class TestCalculateFxDifference:
    """Test calcolo differenza cambio."""

    def test_fx_gain_eur_strengthens(self) -> None:
        """
        EUR si rafforza: storico 1.10, corrente 1.05.
        Stesso importo in USD vale di più in EUR → utile.

        10000 USD / 1.10 = 9090.91 (storico)
        10000 USD / 1.05 = 9523.81 (corrente)
        Diff = +432.90 → utile.
        """
        result = FxEngine.calculate_fx_difference(
            amount_foreign=Decimal("10000"),
            historical_rate=Decimal("1.10"),
            current_rate=Decimal("1.05"),
        )
        assert isinstance(result, FxDifferenceResult)
        assert result.difference_type == FxDifferenceType.GAIN
        assert result.fx_difference > Decimal("0")
        assert result.original_eur == Decimal("9090.91")
        assert result.current_eur == Decimal("9523.81")

    def test_fx_loss_eur_weakens(self) -> None:
        """
        EUR si indebolisce: storico 1.05, corrente 1.10.
        Stesso importo in USD vale di meno in EUR → perdita.
        """
        result = FxEngine.calculate_fx_difference(
            amount_foreign=Decimal("10000"),
            historical_rate=Decimal("1.05"),
            current_rate=Decimal("1.10"),
        )
        assert result.difference_type == FxDifferenceType.LOSS
        assert result.fx_difference < Decimal("0")

    def test_no_difference(self) -> None:
        """Cambio invariato → nessuna differenza."""
        result = FxEngine.calculate_fx_difference(
            amount_foreign=Decimal("10000"),
            historical_rate=Decimal("1.08"),
            current_rate=Decimal("1.08"),
        )
        assert result.difference_type == FxDifferenceType.ZERO
        assert result.fx_difference == Decimal("0.00")

    def test_realized_flag(self) -> None:
        """Il flag is_realized viene passato correttamente."""
        result = FxEngine.calculate_fx_difference(
            amount_foreign=Decimal("10000"),
            historical_rate=Decimal("1.10"),
            current_rate=Decimal("1.05"),
            is_realized=True,
        )
        assert result.is_realized is True

    def test_unrealized_by_default(self) -> None:
        """Di default la differenza è non realizzata."""
        result = FxEngine.calculate_fx_difference(
            amount_foreign=Decimal("10000"),
            historical_rate=Decimal("1.10"),
            current_rate=Decimal("1.05"),
        )
        assert result.is_realized is False

    def test_zero_historical_rate_raises(self) -> None:
        with pytest.raises(ValueError, match="positivi"):
            FxEngine.calculate_fx_difference(
                amount_foreign=Decimal("10000"),
                historical_rate=Decimal("0"),
                current_rate=Decimal("1.08"),
            )

    def test_result_types_are_decimal(self) -> None:
        result = FxEngine.calculate_fx_difference(
            amount_foreign=Decimal("10000"),
            historical_rate=Decimal("1.10"),
            current_rate=Decimal("1.05"),
        )
        assert isinstance(result.original_eur, Decimal)
        assert isinstance(result.current_eur, Decimal)
        assert isinstance(result.fx_difference, Decimal)


class TestYearEndRevaluation:
    """Test rivalutazione di fine esercizio."""

    def test_current_asset_revaluation(self) -> None:
        """
        Attivo circolante: sempre rivalutato al cambio di chiusura.

        Riferimento: OIC 26, par. 30-42.
        """
        result = FxEngine.year_end_revaluation(
            amount_foreign=Decimal("50000"),
            historical_rate=Decimal("1.10"),
            closing_rate=Decimal("1.05"),
            classification=Classification.CURRENT,
        )
        assert isinstance(result, FxDifferenceResult)
        assert result.is_realized is False
        # EUR si rafforza → utile su cambi
        assert result.difference_type == FxDifferenceType.GAIN

    def test_immobilized_asset_revaluation(self) -> None:
        """
        Immobilizzazione: differenza calcolata ma rilevazione
        dipende da valutazione durevolezza.

        Riferimento: OIC 26, par. 35.
        """
        result = FxEngine.year_end_revaluation(
            amount_foreign=Decimal("100000"),
            historical_rate=Decimal("1.05"),
            closing_rate=Decimal("1.10"),
            classification=Classification.IMMOBILIZED,
        )
        assert result.is_realized is False
        # EUR si indebolisce → perdita
        assert result.difference_type == FxDifferenceType.LOSS

    def test_no_change(self) -> None:
        """Cambio invariato a fine anno → nessuna differenza."""
        result = FxEngine.year_end_revaluation(
            amount_foreign=Decimal("50000"),
            historical_rate=Decimal("1.08"),
            closing_rate=Decimal("1.08"),
            classification=Classification.CURRENT,
        )
        assert result.difference_type == FxDifferenceType.ZERO
