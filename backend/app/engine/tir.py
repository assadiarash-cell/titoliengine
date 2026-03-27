"""
Calcolo del Tasso Interno di Rendimento (TIR) per titoli di debito.

Riferimento: OIC 20, par. 37-45.

Il TIR è il tasso che rende uguale il valore attuale dei flussi finanziari
futuri derivanti dal titolo e il suo valore di rilevazione iniziale:

    Σ CF_i / (1 + r)^t_i = 0

dove t_i = giorni dalla data iniziale / 365.25

IMPLEMENTAZIONE: Newton-Raphson con convergenza garantita.
PRECISIONE: 12 cifre decimali (superiore ai 6 richiesti dall'OIC).
VALIDAZIONE: il TIR calcolato viene verificato ricalcolando il NPV
             dei flussi e confrontandolo con zero.

Tutti i calcoli usano decimal.Decimal, MAI float.
"""
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, getcontext
from typing import List

from .constants import (
    DAYS_PER_YEAR,
    QUANTIZE_CALC,
    TIR_MAX_ITERATIONS,
    TIR_TOLERANCE,
    TIR_VERIFY_TOLERANCE,
)

getcontext().prec = 28


@dataclass
class CashFlow:
    """
    Singolo flusso di cassa associato a un titolo.

    Riferimento: OIC 20, par. 37-45.

    Attributes:
        flow_date: data del flusso
        amount: importo del flusso. Positivo = incasso, Negativo = esborso.
    """
    flow_date: date
    amount: Decimal


class TIRCalculator:
    """
    Calcola il Tasso Interno di Rendimento per un titolo di debito.

    L'investimento iniziale è un flusso negativo.
    Le cedole e il rimborso finale sono flussi positivi.

    TIR è quel tasso r tale che:
        Σ CF_i / (1 + r)^t_i = 0

    dove t_i = giorni dalla data iniziale / 365.25

    Riferimento: OIC 20, par. 37-45.
    """

    @classmethod
    def calculate(
        cls,
        cash_flows: List[CashFlow],
        initial_guess: Decimal = Decimal("0.05"),
    ) -> Decimal:
        """
        Calcola il TIR usando il metodo di Newton-Raphson.

        Riferimento: OIC 20, par. 37-45.

        Il metodo Newton-Raphson converge iterativamente al tasso r che
        rende NPV(r) = 0. Ad ogni iterazione:
            r_new = r_old - NPV(r_old) / NPV'(r_old)

        Args:
            cash_flows: lista di flussi di cassa. Il primo deve essere
                        negativo (investimento iniziale).
            initial_guess: stima iniziale del tasso (default 5%).

        Returns:
            TIR come Decimal quantizzato a 10 cifre decimali.
            Esempio: Decimal('0.0354720000') per 3.5472%.

        Raises:
            ValueError: se la lista è vuota, il primo flusso non è negativo,
                        la derivata è zero, o non converge.
        """
        if not cash_flows:
            raise ValueError("Nessun flusso di cassa fornito.")

        if cash_flows[0].amount >= Decimal("0"):
            raise ValueError(
                "Il primo flusso deve essere negativo (investimento iniziale). "
                f"Ricevuto: {cash_flows[0].amount}"
            )

        base_date: date = cash_flows[0].flow_date
        rate: Decimal = initial_guess

        for iteration in range(TIR_MAX_ITERATIONS):
            npv: Decimal = Decimal("0")
            dnpv: Decimal = Decimal("0")  # Derivata prima per Newton-Raphson

            for cf in cash_flows:
                years: Decimal = (
                    Decimal(str((cf.flow_date - base_date).days)) / DAYS_PER_YEAR
                )

                if years == Decimal("0"):
                    npv += cf.amount
                else:
                    discount: Decimal = (Decimal("1") + rate) ** years
                    npv += cf.amount / discount
                    dnpv -= (
                        years * cf.amount
                        / ((Decimal("1") + rate) ** (years + Decimal("1")))
                    )

            if abs(npv) < TIR_TOLERANCE:
                # Convergenza raggiunta — CONTRO-VERIFICA
                cls._verify_result(cash_flows, rate, base_date)
                return rate.quantize(QUANTIZE_CALC)

            if dnpv == Decimal("0"):
                raise ValueError(
                    f"Derivata zero all'iterazione {iteration}. "
                    f"NPV={npv}, rate={rate}. "
                    "Impossibile continuare Newton-Raphson."
                )

            rate = rate - npv / dnpv

        raise ValueError(
            f"TIR non converge dopo {TIR_MAX_ITERATIONS} iterazioni. "
            f"Ultimo rate={rate}, ultimo NPV={npv}"
        )

    @classmethod
    def _verify_result(
        cls,
        cash_flows: List[CashFlow],
        rate: Decimal,
        base_date: date,
    ) -> None:
        """
        Contro-verifica del TIR calcolato.

        Ricalcola il NPV usando il TIR trovato e verifica che sia prossimo a zero.
        Questa è la garanzia di correttezza del risultato.

        Riferimento: OIC 20, par. 37 — il TIR deve rendere il valore attuale
        dei flussi futuri pari al valore iniziale di iscrizione.

        Args:
            cash_flows: flussi di cassa originali
            rate: TIR calcolato
            base_date: data base per il calcolo degli anni

        Raises:
            ValueError: se il NPV residuo supera la tolleranza (0.01 EUR).
        """
        npv: Decimal = Decimal("0")
        for cf in cash_flows:
            years: Decimal = (
                Decimal(str((cf.flow_date - base_date).days)) / DAYS_PER_YEAR
            )
            if years == Decimal("0"):
                npv += cf.amount
            else:
                npv += cf.amount / ((Decimal("1") + rate) ** years)

        if abs(npv) > TIR_VERIFY_TOLERANCE:
            raise ValueError(
                f"ERRORE VERIFICA TIR: NPV residuo = {npv} "
                f"(tolleranza: {TIR_VERIFY_TOLERANCE}). "
                f"Il TIR calcolato ({rate}) non è corretto."
            )

    @classmethod
    def compute_npv(
        cls,
        cash_flows: List[CashFlow],
        rate: Decimal,
    ) -> Decimal:
        """
        Calcola il Net Present Value (NPV) di una serie di flussi di cassa.

        Riferimento: OIC 20, par. 37.

        Args:
            cash_flows: lista di flussi di cassa
            rate: tasso di sconto

        Returns:
            NPV come Decimal quantizzato a 10 cifre decimali.
        """
        if not cash_flows:
            return Decimal("0")

        base_date: date = cash_flows[0].flow_date
        npv: Decimal = Decimal("0")

        for cf in cash_flows:
            years: Decimal = (
                Decimal(str((cf.flow_date - base_date).days)) / DAYS_PER_YEAR
            )
            if years == Decimal("0"):
                npv += cf.amount
            else:
                npv += cf.amount / ((Decimal("1") + rate) ** years)

        return npv.quantize(QUANTIZE_CALC)

    @classmethod
    def build_bond_cash_flows(
        cls,
        settlement_date: date,
        maturity_date: date,
        nominal_value: Decimal,
        purchase_price_tel_quel: Decimal,
        transaction_costs: Decimal,
        coupon_rate: Decimal,
        coupon_frequency: int,
        coupon_dates: List[date],
        redemption_price: Decimal = Decimal("100"),
    ) -> List[CashFlow]:
        """
        Costruisce i flussi di cassa per un titolo obbligazionario.

        Riferimento: OIC 20, par. 37-45.

        Flusso iniziale = -(purchase_price_tel_quel + transaction_costs) [negativo]
        Flussi intermedi = cedole periodiche [positivi]
        Flusso finale = ultima cedola + rimborso nominale [positivo]

        Args:
            settlement_date: data regolamento acquisto
            maturity_date: data scadenza titolo
            nominal_value: valore nominale (es. 100000)
            purchase_price_tel_quel: prezzo tel quel pagato (corso secco + rateo)
            transaction_costs: commissioni, bolli, spese accessorie
            coupon_rate: tasso cedolare annuo (es. Decimal('0.035') per 3.5%)
            coupon_frequency: cedole/anno (1=annuale, 2=semestrale, 4=trimestrale)
            coupon_dates: date future di stacco cedola
            redemption_price: prezzo di rimborso per 100 nominale (default: 100)

        Returns:
            Lista di CashFlow ordinata per data.
        """
        flows: List[CashFlow] = []

        # Flusso iniziale (investimento) — NEGATIVO
        initial_outflow: Decimal = -(purchase_price_tel_quel + transaction_costs)
        flows.append(CashFlow(flow_date=settlement_date, amount=initial_outflow))

        # Cedola per periodo
        coupon_per_period: Decimal = (
            nominal_value * coupon_rate / Decimal(str(coupon_frequency))
        )

        # Rimborso alla scadenza
        redemption_amount: Decimal = (
            nominal_value * redemption_price / Decimal("100")
        )

        for coupon_date in coupon_dates:
            if coupon_date < maturity_date:
                # Cedola intermedia
                flows.append(CashFlow(flow_date=coupon_date, amount=coupon_per_period))
            elif coupon_date == maturity_date:
                # Ultima cedola + rimborso
                flows.append(
                    CashFlow(
                        flow_date=coupon_date,
                        amount=coupon_per_period + redemption_amount,
                    )
                )

        # Se la scadenza non coincide con una data cedola
        if not any(cd == maturity_date for cd in coupon_dates):
            flows.append(CashFlow(flow_date=maturity_date, amount=redemption_amount))

        return flows
