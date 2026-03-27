"""
Test per il modulo constants.py.

Verifica che tutte le costanti siano definite correttamente
e che i tipi siano Decimal (MAI float).
"""
from decimal import Decimal

from app.engine.constants import (
    TAX_RATES,
    TaxRegime,
    SecurityType,
    DayCountConventionType,
    DEFAULT_DAY_COUNT,
    WHITE_LIST_COUNTRIES,
    GOVERNMENT_SECURITY_TYPES,
    SOCIETA_COMODO_RATES,
    QUANTIZE_CENTS,
    QUANTIZE_CALC,
    TIR_TOLERANCE,
    TIR_MAX_ITERATIONS,
    DefaultAccounts,
    Classification,
    ValuationMethod,
    CostMethod,
    CouponFrequency,
)


class TestTaxRates:
    """Test aliquote fiscali."""

    def test_government_rate_is_decimal(self) -> None:
        rate = TAX_RATES[TaxRegime.GOVERNMENT_12_5]
        assert isinstance(rate, Decimal)
        assert rate == Decimal("0.1250")

    def test_standard_rate_is_decimal(self) -> None:
        rate = TAX_RATES[TaxRegime.STANDARD_26]
        assert isinstance(rate, Decimal)
        assert rate == Decimal("0.2600")

    def test_pex_effective_rate(self) -> None:
        """PEX: 26% sul 5% = 1,3% effettivo."""
        rate = TAX_RATES[TaxRegime.PEX]
        assert rate == Decimal("0.0130")

    def test_exempt_rate_is_zero(self) -> None:
        assert TAX_RATES[TaxRegime.EXEMPT] == Decimal("0")

    def test_all_rates_are_decimal(self) -> None:
        for regime, rate in TAX_RATES.items():
            assert isinstance(rate, Decimal), f"{regime}: rate is {type(rate)}"


class TestSecurityTypes:
    """Test tipi di titoli."""

    def test_government_types_include_btp(self) -> None:
        assert "btp" in GOVERNMENT_SECURITY_TYPES

    def test_government_types_include_bot(self) -> None:
        assert "bot" in GOVERNMENT_SECURITY_TYPES

    def test_government_types_include_cct(self) -> None:
        assert "cct" in GOVERNMENT_SECURITY_TYPES

    def test_government_types_include_ctz(self) -> None:
        assert "ctz" in GOVERNMENT_SECURITY_TYPES

    def test_corporate_not_in_government(self) -> None:
        assert "corporate_bond" not in GOVERNMENT_SECURITY_TYPES


class TestDayCountDefaults:
    """Test convenzioni giorni di default per tipo titolo."""

    def test_btp_uses_act_act(self) -> None:
        assert DEFAULT_DAY_COUNT["btp"] == DayCountConventionType.ACT_ACT

    def test_bot_uses_act_360(self) -> None:
        assert DEFAULT_DAY_COUNT["bot"] == DayCountConventionType.ACT_360

    def test_corporate_uses_30_360(self) -> None:
        assert DEFAULT_DAY_COUNT["corporate_bond"] == DayCountConventionType.THIRTY_360


class TestWhiteList:
    """Test white list paesi."""

    def test_italy_in_white_list(self) -> None:
        assert "IT" in WHITE_LIST_COUNTRIES

    def test_germany_in_white_list(self) -> None:
        assert "DE" in WHITE_LIST_COUNTRIES

    def test_us_in_white_list(self) -> None:
        assert "US" in WHITE_LIST_COUNTRIES


class TestSocietaComodoRates:
    """Test coefficienti società di comodo."""

    def test_titoli_rate_is_2_percent(self) -> None:
        assert SOCIETA_COMODO_RATES["titoli_e_crediti"] == Decimal("0.02")

    def test_immobili_rate_is_6_percent(self) -> None:
        assert SOCIETA_COMODO_RATES["immobili"] == Decimal("0.06")

    def test_all_rates_are_decimal(self) -> None:
        for key, rate in SOCIETA_COMODO_RATES.items():
            assert isinstance(rate, Decimal), f"{key}: rate is {type(rate)}"


class TestPrecisionConstants:
    """Test costanti di precisione."""

    def test_quantize_cents(self) -> None:
        assert QUANTIZE_CENTS == Decimal("0.01")

    def test_quantize_calc(self) -> None:
        assert QUANTIZE_CALC == Decimal("1E-10")

    def test_tir_tolerance(self) -> None:
        assert TIR_TOLERANCE == Decimal("1E-12")

    def test_tir_max_iterations(self) -> None:
        assert TIR_MAX_ITERATIONS == 1000
