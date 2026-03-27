"""
Test per il modulo tir.py — Calcolo Tasso Interno di Rendimento.

Scenari testati:
1. BTP con cedola semestrale acquistato sopra la pari
2. BOT zero coupon (sconto puro)
3. Titolo acquistato alla pari (TIR = tasso cedolare)
4. Titolo acquistato sotto la pari (TIR > tasso cedolare)
5. Validazione errori input
6. Contro-verifica NPV ≈ 0

Riferimento: OIC 20, par. 37-45.
"""
from datetime import date
from decimal import Decimal

import pytest

from app.engine.tir import CashFlow, TIRCalculator


class TestTIRBasic:
    """Test TIR su casi semplici."""

    def test_zero_coupon_bot(self) -> None:
        """
        BOT zero coupon 12 mesi.
        Investimento: -96.50, Rimborso: +100.00 dopo 1 anno.
        TIR atteso ≈ 3.63% (100/96.50 - 1).
        """
        flows = [
            CashFlow(flow_date=date(2025, 1, 15), amount=Decimal("-96.50")),
            CashFlow(flow_date=date(2026, 1, 15), amount=Decimal("100.00")),
        ]
        tir = TIRCalculator.calculate(flows)

        assert isinstance(tir, Decimal)
        # Il TIR deve essere positivo e ragionevole
        assert tir > Decimal("0.03")
        assert tir < Decimal("0.04")

    def test_at_par_tir_equals_coupon_rate(self) -> None:
        """
        Titolo acquistato alla pari con cedola annuale.
        Se acquisto a 100 e cedola è 5%, TIR ≈ 5%.
        """
        flows = [
            CashFlow(flow_date=date(2025, 1, 1), amount=Decimal("-100")),
            CashFlow(flow_date=date(2026, 1, 1), amount=Decimal("5")),     # Cedola anno 1
            CashFlow(flow_date=date(2027, 1, 1), amount=Decimal("5")),     # Cedola anno 2
            CashFlow(flow_date=date(2028, 1, 1), amount=Decimal("105")),   # Cedola + rimborso
        ]
        tir = TIRCalculator.calculate(flows)

        # TIR deve essere molto vicino a 0.05 (5%)
        assert abs(tir - Decimal("0.05")) < Decimal("0.001")

    def test_above_par_tir_less_than_coupon(self) -> None:
        """
        Acquisto sopra la pari: TIR < tasso cedolare.
        Compro a 105, cedola 5%, TIR < 5%.

        Riferimento: OIC 20, par. 42.
        """
        flows = [
            CashFlow(flow_date=date(2025, 1, 1), amount=Decimal("-105")),
            CashFlow(flow_date=date(2026, 1, 1), amount=Decimal("5")),
            CashFlow(flow_date=date(2027, 1, 1), amount=Decimal("5")),
            CashFlow(flow_date=date(2028, 1, 1), amount=Decimal("105")),
        ]
        tir = TIRCalculator.calculate(flows)

        assert tir < Decimal("0.05")
        assert tir > Decimal("0")

    def test_below_par_tir_more_than_coupon(self) -> None:
        """
        Acquisto sotto la pari: TIR > tasso cedolare.
        Compro a 95, cedola 5%, TIR > 5%.

        Riferimento: OIC 20, par. 42.
        """
        flows = [
            CashFlow(flow_date=date(2025, 1, 1), amount=Decimal("-95")),
            CashFlow(flow_date=date(2026, 1, 1), amount=Decimal("5")),
            CashFlow(flow_date=date(2027, 1, 1), amount=Decimal("5")),
            CashFlow(flow_date=date(2028, 1, 1), amount=Decimal("105")),
        ]
        tir = TIRCalculator.calculate(flows)

        assert tir > Decimal("0.05")

    def test_result_is_decimal(self) -> None:
        """Il TIR deve essere Decimal, MAI float."""
        flows = [
            CashFlow(flow_date=date(2025, 1, 1), amount=Decimal("-100")),
            CashFlow(flow_date=date(2026, 1, 1), amount=Decimal("105")),
        ]
        tir = TIRCalculator.calculate(flows)
        assert isinstance(tir, Decimal)


class TestTIRBTPScenario:
    """Test TIR su scenario BTP realistico dal blueprint."""

    def test_btp_semestrale_sopra_pari(self) -> None:
        """
        Scenario 5 del blueprint: BTP 3.50% 01/03/2030 acquistato a 101.20.
        TIR atteso ≈ 3.13% (< 3.5% perché sopra la pari).

        Riferimento: OIC 20, par. 37-55.
        """
        # Simulazione semplificata: nominale 100, cedola semestrale 1.75
        settlement = date(2025, 5, 15)
        # Investimento iniziale: prezzo tel quel + costi
        # 101.20 (corso secco) + 0.7133 (rateo) + 0.166 (costi) = 102.0793
        initial_outflow = Decimal("-102.0793")

        flows = [CashFlow(flow_date=settlement, amount=initial_outflow)]

        # Cedole semestrali future (1.75 ciascuna per 100 nominale)
        coupon = Decimal("1.75")
        coupon_dates = [
            date(2025, 9, 1), date(2026, 3, 1), date(2026, 9, 1),
            date(2027, 3, 1), date(2027, 9, 1), date(2028, 3, 1),
            date(2028, 9, 1), date(2029, 3, 1), date(2029, 9, 1),
        ]
        for cd in coupon_dates:
            flows.append(CashFlow(flow_date=cd, amount=coupon))

        # Ultima cedola + rimborso
        flows.append(
            CashFlow(flow_date=date(2030, 3, 1), amount=coupon + Decimal("100"))
        )

        tir = TIRCalculator.calculate(flows)

        # TIR deve essere < tasso cedolare (3.5%) perché acquistato sopra pari
        assert tir < Decimal("0.035")
        assert tir > Decimal("0.02")  # Ma comunque positivo


class TestTIRVerification:
    """Test della contro-verifica del TIR."""

    def test_npv_is_zero_after_tir(self) -> None:
        """
        Dopo il calcolo del TIR, il NPV calcolato col TIR
        deve essere prossimo a zero.
        """
        flows = [
            CashFlow(flow_date=date(2025, 1, 1), amount=Decimal("-100")),
            CashFlow(flow_date=date(2026, 1, 1), amount=Decimal("5")),
            CashFlow(flow_date=date(2027, 1, 1), amount=Decimal("105")),
        ]
        tir = TIRCalculator.calculate(flows)

        # Verifica NPV ≈ 0
        npv = TIRCalculator.compute_npv(flows, tir)
        assert abs(npv) < Decimal("0.01")

    def test_compute_npv_empty_flows(self) -> None:
        """NPV di lista vuota = 0."""
        assert TIRCalculator.compute_npv([], Decimal("0.05")) == Decimal("0")


class TestTIRErrors:
    """Test gestione errori."""

    def test_empty_flows_raises(self) -> None:
        with pytest.raises(ValueError, match="Nessun flusso"):
            TIRCalculator.calculate([])

    def test_positive_first_flow_raises(self) -> None:
        flows = [
            CashFlow(flow_date=date(2025, 1, 1), amount=Decimal("100")),
            CashFlow(flow_date=date(2026, 1, 1), amount=Decimal("-100")),
        ]
        with pytest.raises(ValueError, match="negativo"):
            TIRCalculator.calculate(flows)

    def test_zero_first_flow_raises(self) -> None:
        flows = [
            CashFlow(flow_date=date(2025, 1, 1), amount=Decimal("0")),
            CashFlow(flow_date=date(2026, 1, 1), amount=Decimal("100")),
        ]
        with pytest.raises(ValueError, match="negativo"):
            TIRCalculator.calculate(flows)


class TestBuildBondCashFlows:
    """Test costruzione flussi di cassa per obbligazioni."""

    def test_bond_cash_flows_structure(self) -> None:
        """Verifica struttura base dei flussi generati."""
        flows = TIRCalculator.build_bond_cash_flows(
            settlement_date=date(2025, 5, 15),
            maturity_date=date(2027, 3, 1),
            nominal_value=Decimal("100000"),
            purchase_price_tel_quel=Decimal("101913.32"),
            transaction_costs=Decimal("166"),
            coupon_rate=Decimal("0.035"),
            coupon_frequency=2,
            coupon_dates=[
                date(2025, 9, 1),
                date(2026, 3, 1),
                date(2026, 9, 1),
                date(2027, 3, 1),
            ],
        )

        # Primo flusso è negativo (investimento)
        assert flows[0].amount < Decimal("0")

        # Flussi intermedi sono positivi (cedole)
        for f in flows[1:-1]:
            assert f.amount > Decimal("0")

        # Ultimo flusso è cedola + rimborso (molto grande)
        assert flows[-1].amount > Decimal("90000")

    def test_first_flow_is_investment(self) -> None:
        """Il primo flusso deve essere -(prezzo + costi)."""
        flows = TIRCalculator.build_bond_cash_flows(
            settlement_date=date(2025, 1, 1),
            maturity_date=date(2026, 1, 1),
            nominal_value=Decimal("100"),
            purchase_price_tel_quel=Decimal("98"),
            transaction_costs=Decimal("2"),
            coupon_rate=Decimal("0.05"),
            coupon_frequency=1,
            coupon_dates=[date(2026, 1, 1)],
        )

        assert flows[0].amount == Decimal("-100")  # -(98 + 2)

    def test_maturity_without_coupon_date(self) -> None:
        """Se scadenza non coincide con data cedola, aggiunge rimborso separato."""
        flows = TIRCalculator.build_bond_cash_flows(
            settlement_date=date(2025, 1, 1),
            maturity_date=date(2025, 12, 15),
            nominal_value=Decimal("100"),
            purchase_price_tel_quel=Decimal("96.50"),
            transaction_costs=Decimal("0.50"),
            coupon_rate=Decimal("0"),
            coupon_frequency=1,
            coupon_dates=[],  # Zero coupon
        )

        # Deve avere: investimento + rimborso a scadenza
        assert len(flows) == 2
        assert flows[-1].amount == Decimal("100")
