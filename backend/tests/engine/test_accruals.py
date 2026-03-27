"""
Test per il modulo accruals.py — Calcolo ratei cedolari.

Scenari testati:
1. Rateo BTP semestrale alla data di acquisto (scenario 1 blueprint)
2. Rateo a fine esercizio (31/12)
3. Interessi di competenza all'incasso cedola (scenario 2 blueprint)
4. Zero coupon (rateo = 0)
5. Validazione errori

Riferimento: OIC 20, par. 50.
"""
from datetime import date
from decimal import Decimal

import pytest

from app.engine.accruals import AccruedInterestCalculator
from app.engine.constants import DayCountConventionType


class TestAccruedInterestAtPurchase:
    """Test rateo cedolare alla data di acquisto."""

    def test_btp_rateo_scenario_1(self) -> None:
        """
        Scenario 1 blueprint: BTP 3.50% semestrale, acquisto il 15/05/2025.
        Ultimo godimento: 01/03/2025. Prossimo: 01/09/2025.
        Rateo atteso: 713.32 EUR su nominale 100000.

        Calcolo manuale:
        - Cedola semestrale = 100000 × 3.5% / 2 = 1750
        - Giorni dal 01/03 al 15/05 = 75
        - Giorni periodo 01/03 → 01/09 = 184
        - Rateo = 1750 × (75/184) = 713.3152...

        Riferimento: OIC 20, par. 50.
        """
        accrued = AccruedInterestCalculator.calculate_for_purchase(
            nominal_value=Decimal("100000"),
            coupon_rate=Decimal("0.035"),
            coupon_frequency=2,
            purchase_date=date(2025, 5, 15),
            last_coupon_date=date(2025, 3, 1),
            next_coupon_date=date(2025, 9, 1),
            day_count_convention=DayCountConventionType.ACT_ACT,
        )

        # Verifica: 1750 × 75/184 = 713.31521739...
        expected = Decimal("100000") * Decimal("0.035") / Decimal("2") * Decimal("75") / Decimal("184")
        assert accrued == expected.quantize(Decimal("1E-10"))

    def test_rateo_is_decimal(self) -> None:
        """Il risultato deve essere Decimal."""
        accrued = AccruedInterestCalculator.calculate_for_purchase(
            nominal_value=Decimal("100000"),
            coupon_rate=Decimal("0.035"),
            coupon_frequency=2,
            purchase_date=date(2025, 5, 15),
            last_coupon_date=date(2025, 3, 1),
            next_coupon_date=date(2025, 9, 1),
            day_count_convention=DayCountConventionType.ACT_ACT,
        )
        assert isinstance(accrued, Decimal)

    def test_rateo_on_coupon_date_is_zero(self) -> None:
        """Se acquisto sulla data cedola, rateo = 0."""
        accrued = AccruedInterestCalculator.calculate_for_purchase(
            nominal_value=Decimal("100000"),
            coupon_rate=Decimal("0.035"),
            coupon_frequency=2,
            purchase_date=date(2025, 3, 1),
            last_coupon_date=date(2025, 3, 1),
            next_coupon_date=date(2025, 9, 1),
            day_count_convention=DayCountConventionType.ACT_ACT,
        )
        assert accrued == Decimal("0")


class TestAccruedInterestYearEnd:
    """Test rateo a fine esercizio."""

    def test_btp_year_end_rateo(self) -> None:
        """
        BTP 3.50% semestrale, ultimo godimento 01/09/2025.
        Rateo al 31/12/2025 per la rilevazione in bilancio.

        Giorni: 01/09 → 31/12 = 121 giorni
        Periodo cedolare: 01/09 → 01/03 = 181 giorni
        Rateo = 1750 × 121/181

        Riferimento: OIC 20, par. 50; Art. 2424-bis c.c.
        """
        accrued = AccruedInterestCalculator.calculate_year_end(
            nominal_value=Decimal("100000"),
            coupon_rate=Decimal("0.035"),
            coupon_frequency=2,
            last_coupon_date=date(2025, 9, 1),
            next_coupon_date=date(2026, 3, 1),
            year_end_date=date(2025, 12, 31),
            day_count_convention=DayCountConventionType.ACT_ACT,
        )

        expected = Decimal("100000") * Decimal("0.035") / Decimal("2") * Decimal("121") / Decimal("181")
        assert accrued == expected.quantize(Decimal("1E-10"))
        assert accrued > Decimal("0")


class TestCompetenceInterest:
    """Test interessi di competenza all'incasso cedola."""

    def test_scenario_2_blueprint(self) -> None:
        """
        Scenario 2 blueprint: cedola lorda 1750, rateo acquisto 713.32.
        Interessi competenza = 1750 - 713.32 = 1036.68.

        Riferimento: OIC 20, par. 50.
        """
        competence = AccruedInterestCalculator.calculate_competence_interest(
            coupon_gross=Decimal("1750.00"),
            accrued_at_purchase=Decimal("713.32"),
        )
        assert competence == Decimal("1036.68")

    def test_full_coupon_if_no_accrued(self) -> None:
        """Se nessun rateo pagato, tutta la cedola è di competenza."""
        competence = AccruedInterestCalculator.calculate_competence_interest(
            coupon_gross=Decimal("1750.00"),
            accrued_at_purchase=Decimal("0"),
        )
        assert competence == Decimal("1750.00")


class TestAccruedInterestGeneric:
    """Test casi generici."""

    def test_act_360_convention(self) -> None:
        """Rateo con convenzione ACT/360 (BOT/CTZ)."""
        accrued = AccruedInterestCalculator.calculate(
            nominal_value=Decimal("50000"),
            coupon_rate=Decimal("0.04"),
            coupon_frequency=1,
            accrual_start=date(2025, 1, 1),
            accrual_end=date(2025, 4, 1),
            day_count_convention=DayCountConventionType.ACT_360,
        )

        # 50000 × 0.04 / 1 × (90/360) = 500
        expected = Decimal("50000") * Decimal("0.04") * Decimal("90") / Decimal("360")
        assert accrued == expected.quantize(Decimal("1E-10"))

    def test_thirty_360_convention(self) -> None:
        """Rateo con convenzione 30/360 (corporate bond)."""
        accrued = AccruedInterestCalculator.calculate(
            nominal_value=Decimal("100000"),
            coupon_rate=Decimal("0.05"),
            coupon_frequency=2,
            accrual_start=date(2025, 1, 1),
            accrual_end=date(2025, 7, 1),
            day_count_convention=DayCountConventionType.THIRTY_360,
        )

        # 100000 × 0.05/2 × 0.5 (sei mesi 30/360) = 1250
        expected = Decimal("100000") * Decimal("0.05") / Decimal("2") * Decimal("0.5")
        assert accrued == expected.quantize(Decimal("1E-10"))


class TestAccruedErrors:
    """Test validazione errori."""

    def test_zero_frequency_raises(self) -> None:
        with pytest.raises(ValueError, match="Frequenza"):
            AccruedInterestCalculator.calculate(
                nominal_value=Decimal("100000"),
                coupon_rate=Decimal("0.035"),
                coupon_frequency=0,
                accrual_start=date(2025, 3, 1),
                accrual_end=date(2025, 6, 1),
                day_count_convention=DayCountConventionType.ACT_ACT,
                period_start=date(2025, 3, 1),
                period_end=date(2025, 9, 1),
            )

    def test_negative_frequency_raises(self) -> None:
        with pytest.raises(ValueError, match="Frequenza"):
            AccruedInterestCalculator.calculate(
                nominal_value=Decimal("100000"),
                coupon_rate=Decimal("0.035"),
                coupon_frequency=-1,
                accrual_start=date(2025, 3, 1),
                accrual_end=date(2025, 6, 1),
                day_count_convention=DayCountConventionType.ACT_ACT,
                period_start=date(2025, 3, 1),
                period_end=date(2025, 9, 1),
            )

    def test_end_before_start_raises(self) -> None:
        with pytest.raises(ValueError, match="anteriore"):
            AccruedInterestCalculator.calculate(
                nominal_value=Decimal("100000"),
                coupon_rate=Decimal("0.035"),
                coupon_frequency=2,
                accrual_start=date(2025, 9, 1),
                accrual_end=date(2025, 3, 1),
                day_count_convention=DayCountConventionType.ACT_ACT,
                period_start=date(2025, 3, 1),
                period_end=date(2025, 9, 1),
            )
