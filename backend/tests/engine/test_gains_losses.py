"""
Test per il modulo gains_losses.py — Calcolo plus/minusvalenze.

Scenari testati:
1. Plusvalenza a costo storico (vendita sopra il costo)
2. Minusvalenza a costo storico (vendita sotto il costo)
3. Plus/minus a costo ammortizzato
4. Effetto commissioni di vendita
5. Rateo cedolare venduto separato dalla plus/minus
6. Classificazione capital_gain vs capital_loss vs zero
7. Metodo generico (dispatcher)

Riferimento: OIC 20, par. 56-62.
"""
from decimal import Decimal

import pytest

from app.engine.constants import ValuationMethod
from app.engine.gains_losses import (
    GainLossCalculator,
    GainLossResult,
    GainLossType,
)


class TestHistoricalCostGainLoss:
    """Test plus/minusvalenza a costo storico."""

    def test_capital_gain(self) -> None:
        """
        Acquisto a 96500 + oneri 166 = 96666.
        Vendita a 99000. Plus = 99000 - 96666 = 2334.

        Riferimento: OIC 20, par. 56-62.
        """
        result = GainLossCalculator.calculate_historical_cost(
            sale_price_clean=Decimal("99000"),
            acquisition_cost=Decimal("96500"),
            transaction_costs_buy=Decimal("166"),
        )
        assert isinstance(result, GainLossResult)
        assert result.gain_loss == Decimal("2334.00")
        assert result.gain_loss_type == GainLossType.CAPITAL_GAIN
        assert result.valuation_method == ValuationMethod.COSTO_STORICO

    def test_capital_loss(self) -> None:
        """
        Acquisto a 101200 + oneri 166 = 101366.
        Vendita a 99000. Minus = 99000 - 101366 = -2366.
        """
        result = GainLossCalculator.calculate_historical_cost(
            sale_price_clean=Decimal("99000"),
            acquisition_cost=Decimal("101200"),
            transaction_costs_buy=Decimal("166"),
        )
        assert result.gain_loss == Decimal("-2366.00")
        assert result.gain_loss_type == GainLossType.CAPITAL_LOSS

    def test_zero_gain_loss(self) -> None:
        """Vendita = costo → nessuna plus/minus."""
        result = GainLossCalculator.calculate_historical_cost(
            sale_price_clean=Decimal("100166"),
            acquisition_cost=Decimal("100000"),
            transaction_costs_buy=Decimal("166"),
        )
        assert result.gain_loss == Decimal("0.00")
        assert result.gain_loss_type == GainLossType.ZERO

    def test_sale_costs_reduce_gain(self) -> None:
        """Le commissioni di vendita riducono la plusvalenza."""
        result = GainLossCalculator.calculate_historical_cost(
            sale_price_clean=Decimal("105000"),
            acquisition_cost=Decimal("100000"),
            transaction_costs_buy=Decimal("0"),
            sale_costs=Decimal("200"),
        )
        # Net sale = 105000 - 200 = 104800
        # Gain = 104800 - 100000 = 4800
        assert result.gain_loss == Decimal("4800.00")
        assert result.sale_costs == Decimal("200.00")

    def test_accrued_interest_not_in_gain_loss(self) -> None:
        """
        Il rateo cedolare venduto NON fa parte della plus/minusvalenza.
        È classificato come interesse attivo (C.16.a).
        """
        result = GainLossCalculator.calculate_historical_cost(
            sale_price_clean=Decimal("100000"),
            acquisition_cost=Decimal("100000"),
            accrued_interest_sold=Decimal("713.32"),
        )
        # Gain/loss è zero (prezzo = costo)
        assert result.gain_loss == Decimal("0.00")
        # Ma net_proceeds include il rateo
        assert result.net_proceeds == Decimal("100713.32")
        assert result.accrued_interest_sold == Decimal("713.32")

    def test_result_types_are_decimal(self) -> None:
        """Tutti gli importi devono essere Decimal."""
        result = GainLossCalculator.calculate_historical_cost(
            sale_price_clean=Decimal("100000"),
            acquisition_cost=Decimal("98000"),
        )
        assert isinstance(result.sale_price, Decimal)
        assert isinstance(result.book_value, Decimal)
        assert isinstance(result.gain_loss, Decimal)
        assert isinstance(result.net_proceeds, Decimal)


class TestAmortizedCostGainLoss:
    """Test plus/minusvalenza a costo ammortizzato."""

    def test_gain_on_amortized(self) -> None:
        """
        Valore ammortizzato 100500, vendita a 101000.
        Plus = 101000 - 100500 = 500.

        Riferimento: OIC 20, par. 56-62.
        """
        result = GainLossCalculator.calculate_amortized_cost(
            sale_price_clean=Decimal("101000"),
            amortized_book_value=Decimal("100500"),
        )
        assert result.gain_loss == Decimal("500.00")
        assert result.gain_loss_type == GainLossType.CAPITAL_GAIN
        assert result.valuation_method == ValuationMethod.COSTO_AMMORTIZZATO

    def test_loss_on_amortized(self) -> None:
        """
        Valore ammortizzato 101000, vendita a 99500.
        Minus = 99500 - 101000 = -1500.
        """
        result = GainLossCalculator.calculate_amortized_cost(
            sale_price_clean=Decimal("99500"),
            amortized_book_value=Decimal("101000"),
        )
        assert result.gain_loss == Decimal("-1500.00")
        assert result.gain_loss_type == GainLossType.CAPITAL_LOSS

    def test_sale_costs_on_amortized(self) -> None:
        """Commissioni vendita riducono il ricavo netto."""
        result = GainLossCalculator.calculate_amortized_cost(
            sale_price_clean=Decimal("101000"),
            amortized_book_value=Decimal("100500"),
            sale_costs=Decimal("100"),
        )
        # Net sale = 101000 - 100 = 100900
        # Gain = 100900 - 100500 = 400
        assert result.gain_loss == Decimal("400.00")

    def test_accrued_in_net_proceeds(self) -> None:
        """Net proceeds = prezzo netto + rateo venduto."""
        result = GainLossCalculator.calculate_amortized_cost(
            sale_price_clean=Decimal("100000"),
            amortized_book_value=Decimal("100000"),
            accrued_interest_sold=Decimal("500"),
        )
        assert result.net_proceeds == Decimal("100500.00")


class TestGenericCalculate:
    """Test metodo generico (dispatcher)."""

    def test_historical_via_dispatcher(self) -> None:
        """Calcolo via dispatcher con costo storico."""
        result = GainLossCalculator.calculate(
            sale_price_clean=Decimal("105000"),
            book_value=Decimal("100000"),
            valuation_method=ValuationMethod.COSTO_STORICO,
        )
        assert result.gain_loss == Decimal("5000.00")
        assert result.valuation_method == ValuationMethod.COSTO_STORICO

    def test_amortized_via_dispatcher(self) -> None:
        """Calcolo via dispatcher con costo ammortizzato."""
        result = GainLossCalculator.calculate(
            sale_price_clean=Decimal("98000"),
            book_value=Decimal("100000"),
            valuation_method=ValuationMethod.COSTO_AMMORTIZZATO,
        )
        assert result.gain_loss == Decimal("-2000.00")
        assert result.valuation_method == ValuationMethod.COSTO_AMMORTIZZATO

    def test_dispatcher_with_costs(self) -> None:
        """Dispatcher con commissioni e rateo."""
        result = GainLossCalculator.calculate(
            sale_price_clean=Decimal("100000"),
            book_value=Decimal("98000"),
            valuation_method=ValuationMethod.COSTO_STORICO,
            sale_costs=Decimal("50"),
            accrued_interest_sold=Decimal("300"),
        )
        # Net sale = 100000 - 50 = 99950
        # Gain = 99950 - 98000 = 1950
        assert result.gain_loss == Decimal("1950.00")
        assert result.net_proceeds == Decimal("100250.00")  # 99950 + 300


class TestClassify:
    """Test classificazione gain/loss."""

    def test_positive_is_gain(self) -> None:
        assert GainLossCalculator._classify(Decimal("100")) == GainLossType.CAPITAL_GAIN

    def test_negative_is_loss(self) -> None:
        assert GainLossCalculator._classify(Decimal("-50")) == GainLossType.CAPITAL_LOSS

    def test_zero_is_zero(self) -> None:
        assert GainLossCalculator._classify(Decimal("0")) == GainLossType.ZERO
