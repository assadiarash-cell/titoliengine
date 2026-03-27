"""
Test per il modulo amortized_cost.py — Motore costo ammortizzato OIC 20.

Scenari testati:
1. Calcolo valore iniziale di iscrizione
2. Calcolo TIR (tasso effettivo) via compute_effective_rate
3. Calcolo valori singolo periodo (compute_period_values)
4. Piano di ammortamento completo con convergenza a scadenza
5. Snapshot valore contabile a data intermedia (get_book_value_at_date)
6. Validazione errori

Riferimento: OIC 20, par. 37-55.
"""
from datetime import date
from decimal import Decimal

import pytest

from app.engine.amortized_cost import (
    AmortizedCostEngine,
    AmortizedCostSnapshot,
)
from app.engine.constants import DayCountConventionType
from app.engine.spread import AmortizationPeriod


class TestComputeInitialBookValue:
    """Test calcolo valore iniziale di iscrizione."""

    def test_basic_initial_value(self) -> None:
        """
        Prezzo 101200 + costi 166 = 101366.

        Riferimento: OIC 20, par. 37-38.
        """
        bv = AmortizedCostEngine.compute_initial_book_value(
            purchase_price_clean=Decimal("101200"),
            transaction_costs=Decimal("166"),
        )
        assert bv == Decimal("101366").quantize(Decimal("1E-10"))

    def test_zero_costs(self) -> None:
        """Senza costi, valore = prezzo."""
        bv = AmortizedCostEngine.compute_initial_book_value(
            purchase_price_clean=Decimal("98000"),
            transaction_costs=Decimal("0"),
        )
        assert bv == Decimal("98000").quantize(Decimal("1E-10"))

    def test_result_is_decimal(self) -> None:
        bv = AmortizedCostEngine.compute_initial_book_value(
            purchase_price_clean=Decimal("100000"),
            transaction_costs=Decimal("100"),
        )
        assert isinstance(bv, Decimal)


class TestComputeEffectiveRate:
    """Test calcolo TIR per costo ammortizzato."""

    def test_at_par_tir_near_coupon(self) -> None:
        """
        Titolo alla pari: TIR ≈ tasso cedolare.

        Riferimento: OIC 20, par. 42.
        """
        tir = AmortizedCostEngine.compute_effective_rate(
            settlement_date=date(2025, 1, 1),
            maturity_date=date(2027, 1, 1),
            nominal_value=Decimal("100"),
            purchase_price_tel_quel=Decimal("100"),
            transaction_costs=Decimal("0"),
            coupon_rate=Decimal("0.05"),
            coupon_frequency=1,
            coupon_dates=[date(2026, 1, 1), date(2027, 1, 1)],
        )
        assert isinstance(tir, Decimal)
        assert abs(tir - Decimal("0.05")) < Decimal("0.001")

    def test_above_par_tir_less_than_coupon(self) -> None:
        """
        Sopra la pari: TIR < tasso cedolare.

        Riferimento: OIC 20, par. 42.
        """
        tir = AmortizedCostEngine.compute_effective_rate(
            settlement_date=date(2025, 1, 1),
            maturity_date=date(2028, 1, 1),
            nominal_value=Decimal("100"),
            purchase_price_tel_quel=Decimal("105"),
            transaction_costs=Decimal("0"),
            coupon_rate=Decimal("0.05"),
            coupon_frequency=1,
            coupon_dates=[
                date(2026, 1, 1),
                date(2027, 1, 1),
                date(2028, 1, 1),
            ],
        )
        assert tir < Decimal("0.05")
        assert tir > Decimal("0")

    def test_below_par_tir_more_than_coupon(self) -> None:
        """
        Sotto la pari: TIR > tasso cedolare.

        Riferimento: OIC 20, par. 42.
        """
        tir = AmortizedCostEngine.compute_effective_rate(
            settlement_date=date(2025, 1, 1),
            maturity_date=date(2028, 1, 1),
            nominal_value=Decimal("100"),
            purchase_price_tel_quel=Decimal("95"),
            transaction_costs=Decimal("0"),
            coupon_rate=Decimal("0.05"),
            coupon_frequency=1,
            coupon_dates=[
                date(2026, 1, 1),
                date(2027, 1, 1),
                date(2028, 1, 1),
            ],
        )
        assert tir > Decimal("0.05")


class TestComputePeriodValues:
    """Test calcolo valori singolo periodo."""

    def test_above_par_amortization_negative(self) -> None:
        """
        Sopra la pari: ammortamento negativo (riduce valore contabile).

        Riferimento: OIC 20, par. 42.
        """
        period = AmortizedCostEngine.compute_period_values(
            nominal_value=Decimal("100000"),
            opening_book_value=Decimal("101366"),
            effective_rate=Decimal("0.0313"),
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
        assert period.amortization < Decimal("0")
        assert period.closing_book_value < period.opening_book_value

    def test_below_par_amortization_positive(self) -> None:
        """
        Sotto la pari: ammortamento positivo (aumenta valore contabile).
        """
        period = AmortizedCostEngine.compute_period_values(
            nominal_value=Decimal("100000"),
            opening_book_value=Decimal("96500"),
            effective_rate=Decimal("0.055"),
            coupon_rate=Decimal("0.035"),
            coupon_frequency=2,
            period_start=date(2025, 3, 1),
            period_end=date(2025, 9, 1),
            day_count_convention=DayCountConventionType.ACT_ACT,
            coupon_start=date(2025, 3, 1),
            coupon_end=date(2025, 9, 1),
            coupon_received=Decimal("1750"),
        )
        assert period.amortization > Decimal("0")

    def test_returns_amortization_period(self) -> None:
        """Il risultato deve essere AmortizationPeriod."""
        period = AmortizedCostEngine.compute_period_values(
            nominal_value=Decimal("100000"),
            opening_book_value=Decimal("100000"),
            effective_rate=Decimal("0.05"),
            coupon_rate=Decimal("0.05"),
            coupon_frequency=2,
            period_start=date(2025, 3, 1),
            period_end=date(2025, 9, 1),
            day_count_convention=DayCountConventionType.ACT_ACT,
            coupon_start=date(2025, 3, 1),
            coupon_end=date(2025, 9, 1),
        )
        assert isinstance(period, AmortizationPeriod)
        assert isinstance(period.effective_interest, Decimal)
        assert isinstance(period.nominal_interest, Decimal)


class TestGenerateAmortizationSchedule:
    """Test piano di ammortamento completo."""

    def test_schedule_length(self) -> None:
        """Il piano deve avere una riga per ogni data cedola."""
        schedule = AmortizedCostEngine.generate_amortization_schedule(
            nominal_value=Decimal("100000"),
            initial_book_value=Decimal("101366"),
            effective_rate=Decimal("0.0313"),
            coupon_rate=Decimal("0.035"),
            coupon_frequency=2,
            acquisition_date=date(2025, 5, 15),
            maturity_date=date(2026, 9, 1),
            coupon_dates=[
                date(2025, 9, 1),
                date(2026, 3, 1),
                date(2026, 9, 1),
            ],
            day_count_convention=DayCountConventionType.ACT_ACT,
        )
        assert len(schedule) == 3

    def test_schedule_continuity(self) -> None:
        """Closing di un periodo = opening del successivo."""
        schedule = AmortizedCostEngine.generate_amortization_schedule(
            nominal_value=Decimal("100000"),
            initial_book_value=Decimal("101366"),
            effective_rate=Decimal("0.0313"),
            coupon_rate=Decimal("0.035"),
            coupon_frequency=2,
            acquisition_date=date(2025, 5, 15),
            maturity_date=date(2026, 9, 1),
            coupon_dates=[
                date(2025, 9, 1),
                date(2026, 3, 1),
                date(2026, 9, 1),
            ],
            day_count_convention=DayCountConventionType.ACT_ACT,
        )
        assert schedule[0].closing_book_value == schedule[1].opening_book_value
        assert schedule[1].closing_book_value == schedule[2].opening_book_value

    def test_converges_to_nominal_at_maturity(self) -> None:
        """
        A scadenza il valore contabile converge al nominale.

        Riferimento: OIC 20, par. 42. Il costo ammortizzato converge
        al valore di rimborso alla scadenza.
        """
        schedule = AmortizedCostEngine.generate_amortization_schedule(
            nominal_value=Decimal("100000"),
            initial_book_value=Decimal("101366"),
            effective_rate=Decimal("0.0313"),
            coupon_rate=Decimal("0.035"),
            coupon_frequency=2,
            acquisition_date=date(2025, 5, 15),
            maturity_date=date(2026, 9, 1),
            coupon_dates=[
                date(2025, 9, 1),
                date(2026, 3, 1),
                date(2026, 9, 1),
            ],
            day_count_convention=DayCountConventionType.ACT_ACT,
        )
        # Ultimo periodo: valore contabile = nominale (rimborso a 100)
        last = schedule[-1]
        assert last.closing_book_value == Decimal("100000").quantize(Decimal("1E-10"))

    def test_above_par_book_value_decreases(self) -> None:
        """Sopra la pari: il valore contabile diminuisce nel tempo."""
        schedule = AmortizedCostEngine.generate_amortization_schedule(
            nominal_value=Decimal("100000"),
            initial_book_value=Decimal("101366"),
            effective_rate=Decimal("0.0313"),
            coupon_rate=Decimal("0.035"),
            coupon_frequency=2,
            acquisition_date=date(2025, 5, 15),
            maturity_date=date(2026, 9, 1),
            coupon_dates=[
                date(2025, 9, 1),
                date(2026, 3, 1),
                date(2026, 9, 1),
            ],
            day_count_convention=DayCountConventionType.ACT_ACT,
        )
        # Il valore contabile diminuisce ad ogni periodo (sopra la pari)
        assert schedule[0].closing_book_value < schedule[0].opening_book_value

    def test_custom_redemption_price(self) -> None:
        """Con rimborso a 102, il valore contabile converge a 102000."""
        schedule = AmortizedCostEngine.generate_amortization_schedule(
            nominal_value=Decimal("100000"),
            initial_book_value=Decimal("100000"),
            effective_rate=Decimal("0.05"),
            coupon_rate=Decimal("0.035"),
            coupon_frequency=1,
            acquisition_date=date(2025, 1, 1),
            maturity_date=date(2026, 1, 1),
            coupon_dates=[date(2026, 1, 1)],
            day_count_convention=DayCountConventionType.ACT_ACT,
            redemption_price=Decimal("102"),
        )
        last = schedule[-1]
        assert last.closing_book_value == Decimal("102000").quantize(Decimal("1E-10"))


class TestGetBookValueAtDate:
    """Test snapshot valore contabile a data intermedia."""

    def _make_schedule(self) -> tuple:
        """Helper: genera un piano di ammortamento per i test."""
        initial_bv = Decimal("101366")
        schedule = AmortizedCostEngine.generate_amortization_schedule(
            nominal_value=Decimal("100000"),
            initial_book_value=initial_bv,
            effective_rate=Decimal("0.0313"),
            coupon_rate=Decimal("0.035"),
            coupon_frequency=2,
            acquisition_date=date(2025, 5, 15),
            maturity_date=date(2026, 9, 1),
            coupon_dates=[
                date(2025, 9, 1),
                date(2026, 3, 1),
                date(2026, 9, 1),
            ],
            day_count_convention=DayCountConventionType.ACT_ACT,
        )
        return schedule, initial_bv

    def test_at_period_end(self) -> None:
        """Alla fine di un periodo = closing_book_value di quel periodo."""
        schedule, initial_bv = self._make_schedule()
        snap = AmortizedCostEngine.get_book_value_at_date(
            schedule=schedule,
            target_date=date(2025, 9, 1),
            initial_book_value=initial_bv,
        )
        assert isinstance(snap, AmortizedCostSnapshot)
        assert snap.book_value == schedule[0].closing_book_value

    def test_at_start_date(self) -> None:
        """Alla data di acquisto, nessun ammortamento ancora."""
        schedule, initial_bv = self._make_schedule()
        snap = AmortizedCostEngine.get_book_value_at_date(
            schedule=schedule,
            target_date=date(2025, 5, 15),
            initial_book_value=initial_bv,
        )
        assert snap.book_value == initial_bv.quantize(Decimal("1E-10"))

    def test_mid_period_interpolation(self) -> None:
        """A metà periodo: il valore è interpolato pro-rata."""
        schedule, initial_bv = self._make_schedule()
        # Data a metà del primo periodo (15/5 → 1/9)
        snap = AmortizedCostEngine.get_book_value_at_date(
            schedule=schedule,
            target_date=date(2025, 7, 15),
            initial_book_value=initial_bv,
        )
        # Il valore deve essere tra opening e closing del primo periodo
        assert snap.book_value < schedule[0].opening_book_value
        assert snap.book_value > schedule[0].closing_book_value

    def test_before_start_raises(self) -> None:
        """Data anteriore all'inizio del piano → errore."""
        schedule, initial_bv = self._make_schedule()
        with pytest.raises(ValueError, match="anteriore"):
            AmortizedCostEngine.get_book_value_at_date(
                schedule=schedule,
                target_date=date(2025, 1, 1),
                initial_book_value=initial_bv,
            )

    def test_empty_schedule_raises(self) -> None:
        """Piano vuoto → errore."""
        with pytest.raises(ValueError, match="vuoto"):
            AmortizedCostEngine.get_book_value_at_date(
                schedule=[],
                target_date=date(2025, 12, 31),
                initial_book_value=Decimal("100000"),
            )

    def test_result_types_are_decimal(self) -> None:
        """Tutti i valori nello snapshot devono essere Decimal."""
        schedule, initial_bv = self._make_schedule()
        snap = AmortizedCostEngine.get_book_value_at_date(
            schedule=schedule,
            target_date=date(2025, 12, 31),
            initial_book_value=initial_bv,
        )
        assert isinstance(snap.book_value, Decimal)
        assert isinstance(snap.cumulative_amortization, Decimal)
        assert isinstance(snap.initial_book_value, Decimal)
