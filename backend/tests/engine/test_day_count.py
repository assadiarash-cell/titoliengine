"""
Test per il modulo day_count.py.

Verifica le tre convenzioni di calcolo giorni con casi reali:
- ACT/ACT (ICMA) — BTP semestrale
- ACT/360 — BOT/CTZ
- 30/360 European — Corporate bond

Tutti i valori attesi sono calcolati manualmente e verificati.
"""
from datetime import date
from decimal import Decimal

import pytest

from app.engine.day_count import DayCountConvention
from app.engine.constants import DayCountConventionType


class TestActActICMA:
    """Test ACT/ACT (ICMA) — usata per BTP, CCT."""

    def test_btp_half_period(self) -> None:
        """BTP semestrale: 01/03 → 01/09. Metà periodo = 92/184."""
        fraction = DayCountConvention.act_act_icma(
            start=date(2025, 3, 1),
            end=date(2025, 6, 1),
            period_start=date(2025, 3, 1),
            period_end=date(2025, 9, 1),
        )
        # Dal 1 marzo al 1 giugno = 92 giorni
        # Periodo completo 1 marzo - 1 settembre = 184 giorni
        expected = Decimal("92") / Decimal("184")
        assert fraction == expected

    def test_btp_full_period(self) -> None:
        """Periodo cedolare completo = 1."""
        fraction = DayCountConvention.act_act_icma(
            start=date(2025, 3, 1),
            end=date(2025, 9, 1),
            period_start=date(2025, 3, 1),
            period_end=date(2025, 9, 1),
        )
        assert fraction == Decimal("1")

    def test_btp_rateo_acquisto(self) -> None:
        """Rateo acquisto BTP: dal 01/03 al 15/05 = 75 giorni su 184."""
        fraction = DayCountConvention.act_act_icma(
            start=date(2025, 3, 1),
            end=date(2025, 5, 15),
            period_start=date(2025, 3, 1),
            period_end=date(2025, 9, 1),
        )
        expected = Decimal("75") / Decimal("184")
        assert fraction == expected

    def test_zero_period_returns_zero(self) -> None:
        """Periodo cedolare di durata zero."""
        fraction = DayCountConvention.act_act_icma(
            start=date(2025, 3, 1),
            end=date(2025, 3, 1),
            period_start=date(2025, 3, 1),
            period_end=date(2025, 3, 1),
        )
        assert fraction == Decimal("0")

    def test_same_start_end_zero_fraction(self) -> None:
        """Se start == end, la fraction è 0."""
        fraction = DayCountConvention.act_act_icma(
            start=date(2025, 6, 15),
            end=date(2025, 6, 15),
            period_start=date(2025, 3, 1),
            period_end=date(2025, 9, 1),
        )
        assert fraction == Decimal("0")

    def test_btp_annual_coupon(self) -> None:
        """BTP con cedola annuale: 01/01 → 01/01."""
        fraction = DayCountConvention.act_act_icma(
            start=date(2025, 1, 1),
            end=date(2025, 7, 1),
            period_start=date(2025, 1, 1),
            period_end=date(2026, 1, 1),
        )
        # 181 giorni su 365
        expected = Decimal("181") / Decimal("365")
        assert fraction == expected

    def test_result_is_decimal(self) -> None:
        """Il risultato deve essere Decimal, MAI float."""
        fraction = DayCountConvention.act_act_icma(
            start=date(2025, 3, 1),
            end=date(2025, 6, 1),
            period_start=date(2025, 3, 1),
            period_end=date(2025, 9, 1),
        )
        assert isinstance(fraction, Decimal)


class TestAct360:
    """Test ACT/360 — usata per BOT, CTZ, money market."""

    def test_bot_90_days(self) -> None:
        """BOT a 90 giorni: 90/360 = 0.25."""
        fraction = DayCountConvention.act_360(
            start=date(2025, 1, 15),
            end=date(2025, 4, 15),
        )
        expected = Decimal("90") / Decimal("360")
        assert fraction == expected

    def test_bot_365_days(self) -> None:
        """BOT annuale: 365/360 > 1."""
        fraction = DayCountConvention.act_360(
            start=date(2025, 1, 15),
            end=date(2026, 1, 15),
        )
        expected = Decimal("365") / Decimal("360")
        assert fraction == expected

    def test_bot_180_days(self) -> None:
        """BOT 6 mesi: 181/360."""
        fraction = DayCountConvention.act_360(
            start=date(2025, 1, 1),
            end=date(2025, 7, 1),
        )
        # 1 gen → 1 lug = 181 giorni
        expected = Decimal("181") / Decimal("360")
        assert fraction == expected

    def test_same_date_returns_zero(self) -> None:
        """Stessa data = 0."""
        fraction = DayCountConvention.act_360(
            start=date(2025, 6, 15),
            end=date(2025, 6, 15),
        )
        assert fraction == Decimal("0")

    def test_result_is_decimal(self) -> None:
        fraction = DayCountConvention.act_360(
            start=date(2025, 1, 1),
            end=date(2025, 4, 1),
        )
        assert isinstance(fraction, Decimal)


class TestThirty360:
    """Test 30/360 European — usata per corporate bond EUR."""

    def test_full_year(self) -> None:
        """Anno completo: 360/360 = 1."""
        fraction = DayCountConvention.thirty_360(
            start=date(2025, 1, 1),
            end=date(2026, 1, 1),
        )
        assert fraction == Decimal("1")

    def test_half_year(self) -> None:
        """Sei mesi: 180/360 = 0.5."""
        fraction = DayCountConvention.thirty_360(
            start=date(2025, 1, 1),
            end=date(2025, 7, 1),
        )
        assert fraction == Decimal("0.5")

    def test_one_month(self) -> None:
        """Un mese: 30/360."""
        fraction = DayCountConvention.thirty_360(
            start=date(2025, 3, 1),
            end=date(2025, 4, 1),
        )
        expected = Decimal("30") / Decimal("360")
        assert fraction == expected

    def test_february_30_day_rule(self) -> None:
        """Febbraio: 28 giorni diventa 28 (non 30), D1=min(28,30)=28."""
        fraction = DayCountConvention.thirty_360(
            start=date(2025, 2, 28),
            end=date(2025, 3, 31),
        )
        # D1 = min(28, 30) = 28, D2 = min(31, 30) = 30
        # days = 0*360 + 1*30 + (30-28) = 32
        expected = Decimal("32") / Decimal("360")
        assert fraction == expected

    def test_31st_day_capped(self) -> None:
        """Giorno 31 viene limitato a 30."""
        fraction = DayCountConvention.thirty_360(
            start=date(2025, 1, 31),
            end=date(2025, 3, 31),
        )
        # D1 = min(31, 30) = 30, D2 = min(31, 30) = 30
        # days = 0*360 + 2*30 + (30-30) = 60
        expected = Decimal("60") / Decimal("360")
        assert fraction == expected

    def test_same_date_returns_zero(self) -> None:
        fraction = DayCountConvention.thirty_360(
            start=date(2025, 6, 15),
            end=date(2025, 6, 15),
        )
        assert fraction == Decimal("0")

    def test_result_is_decimal(self) -> None:
        fraction = DayCountConvention.thirty_360(
            start=date(2025, 1, 1),
            end=date(2025, 7, 1),
        )
        assert isinstance(fraction, Decimal)


class TestDispatcher:
    """Test del metodo calculate() dispatcher."""

    def test_act_act_via_dispatcher(self) -> None:
        fraction = DayCountConvention.calculate(
            convention=DayCountConventionType.ACT_ACT,
            start=date(2025, 3, 1),
            end=date(2025, 6, 1),
            period_start=date(2025, 3, 1),
            period_end=date(2025, 9, 1),
        )
        expected = Decimal("92") / Decimal("184")
        assert fraction == expected

    def test_act_360_via_dispatcher(self) -> None:
        fraction = DayCountConvention.calculate(
            convention=DayCountConventionType.ACT_360,
            start=date(2025, 1, 15),
            end=date(2025, 4, 15),
        )
        expected = Decimal("90") / Decimal("360")
        assert fraction == expected

    def test_thirty_360_via_dispatcher(self) -> None:
        fraction = DayCountConvention.calculate(
            convention=DayCountConventionType.THIRTY_360,
            start=date(2025, 1, 1),
            end=date(2025, 7, 1),
        )
        assert fraction == Decimal("0.5")

    def test_act_act_requires_period_dates(self) -> None:
        """ACT/ACT senza period_start/end deve dare errore."""
        with pytest.raises(ValueError, match="period_start"):
            DayCountConvention.calculate(
                convention=DayCountConventionType.ACT_ACT,
                start=date(2025, 3, 1),
                end=date(2025, 6, 1),
            )
