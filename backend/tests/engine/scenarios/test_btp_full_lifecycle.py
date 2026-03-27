"""
SCENARIO 5: BTP con costo ammortizzato e TIR.

Dati dello scenario:
- Titolo: BTP 3.50% 01/03/2030
- Nominale: EUR 100.000
- Data acquisto: 15/05/2025
- Corso secco: 101.200,00
- Commissioni: 166,00
- Rateo pagato: 713,32
- Valore iniziale iscrizione: 101.200 + 166 = 101.366,00
- TIR atteso: < 3.50% (acquisto sopra la pari)

Test:
1. La scrittura di acquisto a costo ammortizzato è quadrata
2. Il TIR calcolato è < 3.50%
3. Il piano di ammortamento converge al nominale a scadenza
4. Gli interessi effettivi < interessi nominali (sopra la pari)
5. Il valore contabile di fine esercizio (31/12/2025) è calcolabile
6. La scrittura di rateo a fine esercizio è quadrata

Riferimento: OIC 20, par. 37-55.
"""
from datetime import date
from decimal import Decimal

from app.engine.amortized_cost import AmortizedCostEngine
from app.engine.constants import DayCountConventionType, Classification
from app.engine.journal.purchase import PurchaseEntryGenerator
from app.engine.journal.accrual import AccrualEntryGenerator
from app.engine.journal.templates import DEFAULT_CHART
from app.engine.tir import CashFlow, TIRCalculator


class TestScenario5BTPAmortizedCost:
    """Scenario 5: BTP con costo ammortizzato e TIR."""

    NOMINAL = Decimal("100000")
    CLEAN_PRICE = Decimal("101200.00")
    COMMISSION = Decimal("166.00")
    ACCRUED = Decimal("713.32")
    INITIAL_BV = Decimal("101366.00")  # 101200 + 166
    COUPON_RATE = Decimal("0.035")
    COUPON_FREQ = 2
    ACQUISITION = date(2025, 5, 15)
    MATURITY = date(2030, 3, 1)
    TEL_QUEL = Decimal("101913.32")  # 101200 + 713.32

    COUPON_DATES = [
        date(2025, 9, 1), date(2026, 3, 1), date(2026, 9, 1),
        date(2027, 3, 1), date(2027, 9, 1), date(2028, 3, 1),
        date(2028, 9, 1), date(2029, 3, 1), date(2029, 9, 1),
        date(2030, 3, 1),
    ]

    def test_purchase_entry_amortized_cost_balanced(self) -> None:
        """Scrittura acquisto a costo ammortizzato è quadrata."""
        entry = PurchaseEntryGenerator.generate_amortized_cost(
            entry_date=self.ACQUISITION,
            security_description="BTP 3.5% 01/03/2030",
            purchase_price_clean=self.CLEAN_PRICE,
            transaction_costs=self.COMMISSION,
            accrued_interest=self.ACCRUED,
        )
        assert entry.is_balanced
        # Totale = 101366 + 713.32 = 102079.32
        assert entry.total_debit == Decimal("102079.32")

    def test_tir_less_than_coupon_rate(self) -> None:
        """Sopra la pari: TIR < tasso cedolare (3.5%)."""
        tir = AmortizedCostEngine.compute_effective_rate(
            settlement_date=self.ACQUISITION,
            maturity_date=self.MATURITY,
            nominal_value=self.NOMINAL,
            purchase_price_tel_quel=self.TEL_QUEL,
            transaction_costs=self.COMMISSION,
            coupon_rate=self.COUPON_RATE,
            coupon_frequency=self.COUPON_FREQ,
            coupon_dates=self.COUPON_DATES,
        )
        assert tir < Decimal("0.035")
        assert tir > Decimal("0.02")

    def test_amortization_schedule_converges(self) -> None:
        """Il piano di ammortamento converge al nominale a scadenza."""
        tir = AmortizedCostEngine.compute_effective_rate(
            settlement_date=self.ACQUISITION,
            maturity_date=self.MATURITY,
            nominal_value=self.NOMINAL,
            purchase_price_tel_quel=self.TEL_QUEL,
            transaction_costs=self.COMMISSION,
            coupon_rate=self.COUPON_RATE,
            coupon_frequency=self.COUPON_FREQ,
            coupon_dates=self.COUPON_DATES,
        )

        schedule = AmortizedCostEngine.generate_amortization_schedule(
            nominal_value=self.NOMINAL,
            initial_book_value=self.INITIAL_BV,
            effective_rate=tir,
            coupon_rate=self.COUPON_RATE,
            coupon_frequency=self.COUPON_FREQ,
            acquisition_date=self.ACQUISITION,
            maturity_date=self.MATURITY,
            coupon_dates=self.COUPON_DATES,
            day_count_convention=DayCountConventionType.ACT_ACT,
        )

        # Deve avere 10 periodi
        assert len(schedule) == 10

        # Ultimo periodo: closing = nominale (convergenza)
        last = schedule[-1]
        assert last.closing_book_value == Decimal("100000").quantize(Decimal("1E-10"))

    def test_effective_interest_less_than_nominal(self) -> None:
        """Sopra la pari: interessi effettivi < nominali per ogni periodo."""
        tir = AmortizedCostEngine.compute_effective_rate(
            settlement_date=self.ACQUISITION,
            maturity_date=self.MATURITY,
            nominal_value=self.NOMINAL,
            purchase_price_tel_quel=self.TEL_QUEL,
            transaction_costs=self.COMMISSION,
            coupon_rate=self.COUPON_RATE,
            coupon_frequency=self.COUPON_FREQ,
            coupon_dates=self.COUPON_DATES,
        )

        schedule = AmortizedCostEngine.generate_amortization_schedule(
            nominal_value=self.NOMINAL,
            initial_book_value=self.INITIAL_BV,
            effective_rate=tir,
            coupon_rate=self.COUPON_RATE,
            coupon_frequency=self.COUPON_FREQ,
            acquisition_date=self.ACQUISITION,
            maturity_date=self.MATURITY,
            coupon_dates=self.COUPON_DATES,
            day_count_convention=DayCountConventionType.ACT_ACT,
        )

        # Per tutti i periodi tranne l'ultimo (forzato), ammortamento negativo
        for period in schedule[:-1]:
            assert period.amortization < Decimal("0"), (
                f"Periodo {period.period_start}-{period.period_end}: "
                f"ammortamento = {period.amortization}, atteso negativo"
            )

    def test_book_value_at_year_end(self) -> None:
        """Valore contabile al 31/12/2025 è calcolabile e tra initial e nominal."""
        tir = AmortizedCostEngine.compute_effective_rate(
            settlement_date=self.ACQUISITION,
            maturity_date=self.MATURITY,
            nominal_value=self.NOMINAL,
            purchase_price_tel_quel=self.TEL_QUEL,
            transaction_costs=self.COMMISSION,
            coupon_rate=self.COUPON_RATE,
            coupon_frequency=self.COUPON_FREQ,
            coupon_dates=self.COUPON_DATES,
        )

        schedule = AmortizedCostEngine.generate_amortization_schedule(
            nominal_value=self.NOMINAL,
            initial_book_value=self.INITIAL_BV,
            effective_rate=tir,
            coupon_rate=self.COUPON_RATE,
            coupon_frequency=self.COUPON_FREQ,
            acquisition_date=self.ACQUISITION,
            maturity_date=self.MATURITY,
            coupon_dates=self.COUPON_DATES,
            day_count_convention=DayCountConventionType.ACT_ACT,
        )

        snap = AmortizedCostEngine.get_book_value_at_date(
            schedule=schedule,
            target_date=date(2025, 12, 31),
            initial_book_value=self.INITIAL_BV,
        )

        # Al 31/12/2025 il valore contabile deve essere tra initial e nominal
        assert snap.book_value < self.INITIAL_BV
        assert snap.book_value > self.NOMINAL

    def test_year_end_accrual_entry_balanced(self) -> None:
        """La scrittura di rateo al 31/12/2025 è quadrata."""
        # Rateo al 31/12/2025: calcolo semplificato
        # Dal 01/09/2025 al 31/12/2025 = 121 giorni su 181
        # Rateo = 1750 × 121/181 = 1169.61
        accrued = (
            Decimal("1750") * Decimal("121") / Decimal("181")
        ).quantize(Decimal("0.01"))

        entry = AccrualEntryGenerator.generate_year_end_accrual(
            entry_date=date(2025, 12, 31),
            security_description="BTP 3.5% 01/03/2030",
            accrued_interest=accrued,
        )
        assert entry.is_balanced
        assert entry.total_debit == accrued
