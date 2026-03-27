"""
Test per il modulo tax.py — Ritenute fiscali e test società di comodo.

Scenari testati:
1. Determinazione regime fiscale per tipo titolo
2. Calcolo ritenuta su interessi e capital gain
3. Regime PEX per partecipazioni
4. White list paesi esteri
5. Test società di comodo art. 30 L. 724/1994
6. Validazione errori

Riferimento: TUIR, D.P.R. 600/1973, D.Lgs. 239/1996, L. 724/1994.
"""
from decimal import Decimal

import pytest

from app.engine.constants import SecurityType, TaxRegime, TAX_RATES
from app.engine.tax import (
    IncomeType,
    SocietaComodoResult,
    TaxEngine,
    WithholdingResult,
)


class TestDetermineRegime:
    """Test determinazione regime fiscale."""

    def test_btp_is_government(self) -> None:
        """BTP → regime 12,5%."""
        regime = TaxEngine.determine_regime(SecurityType.BTP)
        assert regime == TaxRegime.GOVERNMENT_12_5

    def test_bot_is_government(self) -> None:
        """BOT → regime 12,5%."""
        regime = TaxEngine.determine_regime(SecurityType.BOT)
        assert regime == TaxRegime.GOVERNMENT_12_5

    def test_cct_is_government(self) -> None:
        """CCT → regime 12,5%."""
        regime = TaxEngine.determine_regime(SecurityType.CCT)
        assert regime == TaxRegime.GOVERNMENT_12_5

    def test_ctz_is_government(self) -> None:
        """CTZ → regime 12,5%."""
        regime = TaxEngine.determine_regime(SecurityType.CTZ)
        assert regime == TaxRegime.GOVERNMENT_12_5

    def test_corporate_bond_is_standard(self) -> None:
        """Corporate bond → regime 26%."""
        regime = TaxEngine.determine_regime(SecurityType.CORPORATE_BOND)
        assert regime == TaxRegime.STANDARD_26

    def test_equity_is_standard(self) -> None:
        """Azioni → regime 26%."""
        regime = TaxEngine.determine_regime(SecurityType.EQUITY)
        assert regime == TaxRegime.STANDARD_26

    def test_etf_is_standard(self) -> None:
        """ETF → regime 26%."""
        regime = TaxEngine.determine_regime(SecurityType.ETF)
        assert regime == TaxRegime.STANDARD_26

    def test_fund_is_standard(self) -> None:
        """Fondo comune → regime 26%."""
        regime = TaxEngine.determine_regime(SecurityType.FUND)
        assert regime == TaxRegime.STANDARD_26

    def test_foreign_gov_white_list(self) -> None:
        """Titolo di Stato tedesco (white list) → 12,5%."""
        regime = TaxEngine.determine_regime(
            SecurityType.GOVERNMENT_BOND, issuer_country="DE"
        )
        assert regime == TaxRegime.GOVERNMENT_12_5

    def test_foreign_gov_non_white_list(self) -> None:
        """Titolo di Stato di paese non white list → 26%."""
        regime = TaxEngine.determine_regime(
            SecurityType.GOVERNMENT_BOND, issuer_country="VE"
        )
        assert regime == TaxRegime.STANDARD_26

    def test_pex_equity(self) -> None:
        """Azioni con PEX → regime PEX (1,3% effettivo)."""
        regime = TaxEngine.determine_regime(
            SecurityType.EQUITY, is_pex=True
        )
        assert regime == TaxRegime.PEX

    def test_pex_ignored_for_bonds(self) -> None:
        """PEX non si applica alle obbligazioni."""
        regime = TaxEngine.determine_regime(
            SecurityType.CORPORATE_BOND, is_pex=True
        )
        assert regime == TaxRegime.STANDARD_26

    def test_country_case_insensitive(self) -> None:
        """Il codice paese deve funzionare case insensitive."""
        regime = TaxEngine.determine_regime(
            SecurityType.GOVERNMENT_BOND, issuer_country="de"
        )
        assert regime == TaxRegime.GOVERNMENT_12_5


class TestCalculateWithholding:
    """Test calcolo ritenuta fiscale."""

    def test_btp_interest_withholding(self) -> None:
        """
        Ritenuta su interessi BTP: 1750 × 12,5% = 218.75.

        Riferimento: D.Lgs. 239/1996.
        """
        result = TaxEngine.calculate_withholding(
            gross_amount=Decimal("1750.00"),
            security_type=SecurityType.BTP,
        )
        assert isinstance(result, WithholdingResult)
        assert result.tax_regime == TaxRegime.GOVERNMENT_12_5
        assert result.tax_rate == Decimal("0.1250")
        assert result.withholding_tax == Decimal("218.75")
        assert result.net_amount == Decimal("1531.25")

    def test_corporate_bond_withholding(self) -> None:
        """
        Ritenuta su interessi corporate bond: 2000 × 26% = 520.

        Riferimento: Art. 26 D.P.R. 600/1973.
        """
        result = TaxEngine.calculate_withholding(
            gross_amount=Decimal("2000.00"),
            security_type=SecurityType.CORPORATE_BOND,
        )
        assert result.tax_regime == TaxRegime.STANDARD_26
        assert result.withholding_tax == Decimal("520.00")
        assert result.net_amount == Decimal("1480.00")

    def test_pex_withholding(self) -> None:
        """
        Ritenuta PEX su dividendo: 10000 × 1,3% = 130.

        Riferimento: Art. 87 TUIR.
        """
        result = TaxEngine.calculate_withholding(
            gross_amount=Decimal("10000.00"),
            security_type=SecurityType.EQUITY,
            income_type=IncomeType.DIVIDEND,
            is_pex=True,
        )
        assert result.tax_regime == TaxRegime.PEX
        assert result.tax_rate == Decimal("0.0130")
        assert result.withholding_tax == Decimal("130.00")
        assert result.net_amount == Decimal("9870.00")

    def test_regime_override(self) -> None:
        """Override del regime: forza EXEMPT su corporate bond."""
        result = TaxEngine.calculate_withholding(
            gross_amount=Decimal("5000.00"),
            security_type=SecurityType.CORPORATE_BOND,
            regime_override=TaxRegime.EXEMPT,
        )
        assert result.tax_regime == TaxRegime.EXEMPT
        assert result.withholding_tax == Decimal("0.00")
        assert result.net_amount == Decimal("5000.00")

    def test_zero_gross_amount(self) -> None:
        """Lordo zero → ritenuta zero."""
        result = TaxEngine.calculate_withholding(
            gross_amount=Decimal("0"),
            security_type=SecurityType.BTP,
        )
        assert result.withholding_tax == Decimal("0.00")
        assert result.net_amount == Decimal("0")

    def test_result_types_are_decimal(self) -> None:
        """Tutti gli importi devono essere Decimal."""
        result = TaxEngine.calculate_withholding(
            gross_amount=Decimal("1000.00"),
            security_type=SecurityType.BTP,
        )
        assert isinstance(result.gross_amount, Decimal)
        assert isinstance(result.tax_rate, Decimal)
        assert isinstance(result.withholding_tax, Decimal)
        assert isinstance(result.net_amount, Decimal)

    def test_rounding_to_cents(self) -> None:
        """La ritenuta è arrotondata ai centesimi."""
        result = TaxEngine.calculate_withholding(
            gross_amount=Decimal("1333.33"),
            security_type=SecurityType.BTP,
        )
        # 1333.33 × 0.125 = 166.66625 → 166.67
        assert result.withholding_tax == Decimal("166.67")

    def test_gross_equals_net_plus_withholding(self) -> None:
        """Invariante: lordo = netto + ritenuta."""
        result = TaxEngine.calculate_withholding(
            gross_amount=Decimal("7777.77"),
            security_type=SecurityType.CORPORATE_BOND,
        )
        assert result.gross_amount == result.net_amount + result.withholding_tax


class TestSocietaComodo:
    """Test società di comodo (art. 30 L. 724/1994)."""

    def test_is_comodo_below_minimum(self) -> None:
        """
        Società con ricavi sotto il minimo → è di comodo.

        Attivo: titoli 500.000 (2% = 10.000), immobili 1.000.000 (6% = 60.000)
        Minimo = 70.000, Ricavi effettivi = 50.000 → di comodo.
        """
        result = TaxEngine.societa_comodo_test(
            titoli_e_crediti=Decimal("500000"),
            immobili=Decimal("1000000"),
            immobili_a10=Decimal("0"),
            altre_immobilizzazioni=Decimal("0"),
            actual_revenue=Decimal("50000"),
        )
        assert isinstance(result, SocietaComodoResult)
        assert result.is_comodo is True
        assert result.minimum_revenue == Decimal("70000.00")

    def test_not_comodo_above_minimum(self) -> None:
        """
        Società con ricavi sopra il minimo → NON è di comodo.

        Minimo = 70.000, Ricavi effettivi = 100.000.
        """
        result = TaxEngine.societa_comodo_test(
            titoli_e_crediti=Decimal("500000"),
            immobili=Decimal("1000000"),
            immobili_a10=Decimal("0"),
            altre_immobilizzazioni=Decimal("0"),
            actual_revenue=Decimal("100000"),
        )
        assert result.is_comodo is False

    def test_exact_minimum_not_comodo(self) -> None:
        """Ricavi esattamente = minimo → NON è di comodo."""
        result = TaxEngine.societa_comodo_test(
            titoli_e_crediti=Decimal("500000"),
            immobili=Decimal("1000000"),
            immobili_a10=Decimal("0"),
            altre_immobilizzazioni=Decimal("0"),
            actual_revenue=Decimal("70000.00"),
        )
        assert result.is_comodo is False

    def test_all_categories(self) -> None:
        """
        Test con tutte le categorie attive.

        titoli 200.000 × 2% = 4.000
        immobili 500.000 × 6% = 30.000
        A/10 300.000 × 5% = 15.000
        altre 100.000 × 15% = 15.000
        Minimo = 64.000
        """
        result = TaxEngine.societa_comodo_test(
            titoli_e_crediti=Decimal("200000"),
            immobili=Decimal("500000"),
            immobili_a10=Decimal("300000"),
            altre_immobilizzazioni=Decimal("100000"),
            actual_revenue=Decimal("50000"),
        )
        assert result.minimum_revenue == Decimal("64000.00")
        assert result.is_comodo is True
        assert result.total_assets == Decimal("1100000")

    def test_coefficients_in_details(self) -> None:
        """Il dettaglio contiene coefficienti corretti."""
        result = TaxEngine.societa_comodo_test(
            titoli_e_crediti=Decimal("100000"),
            immobili=Decimal("0"),
            immobili_a10=Decimal("0"),
            altre_immobilizzazioni=Decimal("0"),
            actual_revenue=Decimal("5000"),
        )
        assert result.details["titoli_e_crediti"]["coefficiente"] == Decimal("0.02")
        assert result.details["titoli_e_crediti"]["ricavo_minimo"] == Decimal("2000.00")

    def test_zero_assets_zero_minimum(self) -> None:
        """Nessun attivo → minimo = 0 → non è di comodo."""
        result = TaxEngine.societa_comodo_test(
            titoli_e_crediti=Decimal("0"),
            immobili=Decimal("0"),
            immobili_a10=Decimal("0"),
            altre_immobilizzazioni=Decimal("0"),
            actual_revenue=Decimal("0"),
        )
        assert result.is_comodo is False
        assert result.minimum_revenue == Decimal("0.00")

    def test_negative_amount_raises(self) -> None:
        """Importo negativo deve dare errore."""
        with pytest.raises(ValueError, match="negativi"):
            TaxEngine.societa_comodo_test(
                titoli_e_crediti=Decimal("-100"),
                immobili=Decimal("0"),
                immobili_a10=Decimal("0"),
                altre_immobilizzazioni=Decimal("0"),
                actual_revenue=Decimal("0"),
            )

    def test_result_types_are_decimal(self) -> None:
        """Tutti gli importi nel risultato devono essere Decimal."""
        result = TaxEngine.societa_comodo_test(
            titoli_e_crediti=Decimal("100000"),
            immobili=Decimal("200000"),
            immobili_a10=Decimal("0"),
            altre_immobilizzazioni=Decimal("50000"),
            actual_revenue=Decimal("30000"),
        )
        assert isinstance(result.total_assets, Decimal)
        assert isinstance(result.minimum_revenue, Decimal)
        assert isinstance(result.actual_revenue, Decimal)
