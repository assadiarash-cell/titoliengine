"""
Test per il modulo spread.py — Ammortamento scarto negoziazione/emissione.

Scenari testati:
1. Calcolo scarto sopra/sotto la pari
2. Ammortamento con metodo costo ammortizzato (TIR)
3. Ammortamento lineare pro-rata temporis
4. Piano di ammortamento completo
5. Coerenza: valore contabile finale converge al nominale

Riferimento: OIC 20, par. 37-55 (costo ammortizzato), par. 14-30 (costo storico).
"""
from datetime import date
from decimal import Decimal

import pytest

from app.engine.spread import AmortizationPeriod, SpreadAmortizationEngine
from app.engine.constants import DayCountConventionType


class TestComputeSpread:
    """Test calcolo scarto."""

    def test_above_par_negative_spread(self) -> None:
        """
        Acquisto sopra la pari: scarto negativo.
        Costo 101200, Nominale 100000, Rimborso 100.
        Scarto = 100000 - 101200 = -1200.

        Riferimento: OIC 20, par. 14.
        """
        spread = SpreadAmortizationEngine.compute_spread(
            acquisition_cost=Decimal("101200"),
            nominal_value=Decimal("100000"),
            redemption_price=Decimal("100"),
        )
        assert spread == Decimal("-1200")

    def test_below_par_positive_spread(self) -> None:
        """
        Acquisto sotto la pari: scarto positivo.
        Costo 96500, Nominale 100000, Rimborso 100.
        Scarto = 100000 - 96500 = 3500.
        """
        spread = SpreadAmortizationEngine.compute_spread(
            acquisition_cost=Decimal("96500"),
            nominal_value=Decimal("100000"),
            redemption_price=Decimal("100"),
        )
        assert spread == Decimal("3500")

    def test_at_par_zero_spread(self) -> None:
        """Acquisto alla pari: scarto = 0."""
        spread = SpreadAmortizationEngine.compute_spread(
            acquisition_cost=Decimal("100000"),
            nominal_value=Decimal("100000"),
            redemption_price=Decimal("100"),
        )
        assert spread == Decimal("0")

    def test_custom_redemption_price(self) -> None:
        """Rimborso diverso da 100 (es. 102)."""
        spread = SpreadAmortizationEngine.compute_spread(
            acquisition_cost=Decimal("100000"),
            nominal_value=Decimal("100000"),
            redemption_price=Decimal("102"),
        )
        # Rimborso = 100000 × 102/100 = 102000
        # Scarto = 102000 - 100000 = 2000
        assert spread == Decimal("2000")

    def test_result_is_decimal(self) -> None:
        spread = SpreadAmortizationEngine.compute_spread(
            acquisition_cost=Decimal("98000"),
            nominal_value=Decimal("100000"),
        )
        assert isinstance(spread, Decimal)


class TestAmortizeEffectiveRate:
    """Test ammortamento con metodo costo ammortizzato (TIR)."""

    def test_single_period_above_par(self) -> None:
        """
        Titolo acquistato sopra la pari: interessi effettivi < nominali.
        L'ammortamento è negativo (riduce il valore contabile).

        Riferimento: OIC 20, par. 42.
        """
        period = SpreadAmortizationEngine.amortize_effective_rate(
            nominal_value=Decimal("100000"),
            initial_book_value=Decimal("101366"),  # Sopra la pari
            effective_rate=Decimal("0.0313"),       # TIR < tasso cedolare
            coupon_rate=Decimal("0.035"),
            coupon_frequency=2,
            period_start=date(2025, 3, 1),
            period_end=date(2025, 9, 1),
            day_count_convention=DayCountConventionType.ACT_ACT,
            coupon_start=date(2025, 3, 1),
            coupon_end=date(2025, 9, 1),
            coupon_received=Decimal("1750"),
        )

        assert isinstance(period, AmortizationPeriod)
        # Interessi effettivi < interessi nominali → ammortamento negativo
        assert period.effective_interest < period.nominal_interest
        assert period.amortization < Decimal("0")
        # Valore contabile diminuisce (converge verso nominale)
        assert period.closing_book_value < period.opening_book_value

    def test_single_period_below_par(self) -> None:
        """
        Titolo acquistato sotto la pari: interessi effettivi > nominali.
        L'ammortamento è positivo (aumenta il valore contabile).
        """
        period = SpreadAmortizationEngine.amortize_effective_rate(
            nominal_value=Decimal("100000"),
            initial_book_value=Decimal("96500"),    # Sotto la pari
            effective_rate=Decimal("0.055"),         # TIR > tasso cedolare
            coupon_rate=Decimal("0.035"),
            coupon_frequency=2,
            period_start=date(2025, 3, 1),
            period_end=date(2025, 9, 1),
            day_count_convention=DayCountConventionType.ACT_ACT,
            coupon_start=date(2025, 3, 1),
            coupon_end=date(2025, 9, 1),
            coupon_received=Decimal("1750"),
        )

        assert period.effective_interest > period.nominal_interest
        assert period.amortization > Decimal("0")

    def test_year_fraction_is_correct(self) -> None:
        """Verifica che la year fraction sia calcolata correttamente."""
        period = SpreadAmortizationEngine.amortize_effective_rate(
            nominal_value=Decimal("100000"),
            initial_book_value=Decimal("100000"),
            effective_rate=Decimal("0.05"),
            coupon_rate=Decimal("0.05"),
            coupon_frequency=2,
            period_start=date(2025, 3, 1),
            period_end=date(2025, 9, 1),
            day_count_convention=DayCountConventionType.ACT_ACT,
            coupon_start=date(2025, 3, 1),
            coupon_end=date(2025, 9, 1),
        )

        # ACT/ACT: 184/184 = 1
        assert period.year_fraction == Decimal("1").quantize(Decimal("1E-10"))


class TestAmortizationScheduleEffective:
    """Test piano di ammortamento completo con costo ammortizzato."""

    def test_schedule_length(self) -> None:
        """Il piano deve avere una riga per ogni data cedola."""
        schedule = SpreadAmortizationEngine.generate_amortization_schedule_effective(
            nominal_value=Decimal("100000"),
            initial_book_value=Decimal("101366"),
            effective_rate=Decimal("0.0313"),
            coupon_rate=Decimal("0.035"),
            coupon_frequency=2,
            acquisition_date=date(2025, 5, 15),
            coupon_dates=[
                date(2025, 9, 1),
                date(2026, 3, 1),
                date(2026, 9, 1),
            ],
            day_count_convention=DayCountConventionType.ACT_ACT,
        )

        assert len(schedule) == 3

    def test_schedule_continuity(self) -> None:
        """Il closing di un periodo = opening del successivo."""
        schedule = SpreadAmortizationEngine.generate_amortization_schedule_effective(
            nominal_value=Decimal("100000"),
            initial_book_value=Decimal("101366"),
            effective_rate=Decimal("0.0313"),
            coupon_rate=Decimal("0.035"),
            coupon_frequency=2,
            acquisition_date=date(2025, 5, 15),
            coupon_dates=[
                date(2025, 9, 1),
                date(2026, 3, 1),
            ],
            day_count_convention=DayCountConventionType.ACT_ACT,
        )

        assert schedule[0].closing_book_value == schedule[1].opening_book_value

    def test_book_value_converges_above_par(self) -> None:
        """Sopra la pari: valore contabile diminuisce verso il nominale."""
        schedule = SpreadAmortizationEngine.generate_amortization_schedule_effective(
            nominal_value=Decimal("100000"),
            initial_book_value=Decimal("101366"),
            effective_rate=Decimal("0.0313"),
            coupon_rate=Decimal("0.035"),
            coupon_frequency=2,
            acquisition_date=date(2025, 5, 15),
            coupon_dates=[
                date(2025, 9, 1),
                date(2026, 3, 1),
            ],
            day_count_convention=DayCountConventionType.ACT_ACT,
        )

        # Ogni periodo il valore contabile scende
        assert schedule[0].closing_book_value < schedule[0].opening_book_value
        assert schedule[1].closing_book_value < schedule[1].opening_book_value


class TestAmortizeLinear:
    """Test ammortamento lineare pro-rata temporis."""

    def test_full_period_equals_total_spread(self) -> None:
        """Ammortamento su tutta la vita = spread totale."""
        amort = SpreadAmortizationEngine.amortize_linear(
            total_spread=Decimal("1200"),
            acquisition_date=date(2025, 1, 1),
            maturity_date=date(2026, 1, 1),
            period_start=date(2025, 1, 1),
            period_end=date(2026, 1, 1),
        )
        assert amort == Decimal("1200").quantize(Decimal("1E-10"))

    def test_half_period(self) -> None:
        """Ammortamento su metà vita ≈ metà spread."""
        acq = date(2025, 1, 1)
        mat = date(2027, 1, 1)
        total_days = (mat - acq).days  # 730
        period_days = (date(2026, 1, 1) - acq).days  # 365
        amort = SpreadAmortizationEngine.amortize_linear(
            total_spread=Decimal("1000"),
            acquisition_date=acq,
            maturity_date=mat,
            period_start=acq,
            period_end=date(2026, 1, 1),
        )
        expected = Decimal("1000") * Decimal(str(period_days)) / Decimal(str(total_days))
        assert amort == expected.quantize(Decimal("1E-10"))

    def test_zero_life_raises(self) -> None:
        """Vita residua zero deve dare errore."""
        with pytest.raises(ValueError, match="zero"):
            SpreadAmortizationEngine.amortize_linear(
                total_spread=Decimal("1000"),
                acquisition_date=date(2025, 1, 1),
                maturity_date=date(2025, 1, 1),
                period_start=date(2025, 1, 1),
                period_end=date(2025, 6, 1),
            )

    def test_negative_spread_linear(self) -> None:
        """Scarto negativo (sopra la pari): ammortamento negativo."""
        amort = SpreadAmortizationEngine.amortize_linear(
            total_spread=Decimal("-1200"),
            acquisition_date=date(2025, 1, 1),
            maturity_date=date(2026, 1, 1),
            period_start=date(2025, 1, 1),
            period_end=date(2025, 7, 1),
        )
        assert amort < Decimal("0")


class TestLinearSchedule:
    """Test piano di ammortamento lineare completo."""

    def test_schedule_sums_to_spread(self) -> None:
        """La somma degli ammortamenti deve essere il totale dello scarto."""
        schedule = SpreadAmortizationEngine.generate_linear_schedule(
            total_spread=Decimal("3650"),
            acquisition_date=date(2025, 1, 1),
            maturity_date=date(2026, 1, 1),
            period_end_dates=[
                date(2025, 4, 1),
                date(2025, 7, 1),
                date(2025, 10, 1),
                date(2026, 1, 1),
            ],
        )

        total_amort = sum(p["amortization"] for p in schedule)
        assert abs(total_amort - Decimal("3650")) < Decimal("0.01")

    def test_remaining_spread_decreases(self) -> None:
        """Lo spread residuo diminuisce ad ogni periodo."""
        schedule = SpreadAmortizationEngine.generate_linear_schedule(
            total_spread=Decimal("1000"),
            acquisition_date=date(2025, 1, 1),
            maturity_date=date(2026, 1, 1),
            period_end_dates=[
                date(2025, 6, 1),
                date(2026, 1, 1),
            ],
        )

        assert schedule[0]["remaining_spread"] > schedule[1]["remaining_spread"]

    def test_result_is_decimal(self) -> None:
        schedule = SpreadAmortizationEngine.generate_linear_schedule(
            total_spread=Decimal("500"),
            acquisition_date=date(2025, 1, 1),
            maturity_date=date(2025, 7, 1),
            period_end_dates=[date(2025, 7, 1)],
        )
        assert isinstance(schedule[0]["amortization"], Decimal)
