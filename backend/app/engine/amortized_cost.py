"""
Motore per il costo ammortizzato di titoli di debito.

Riferimento: OIC 20, par. 37-55.

Il costo ammortizzato è il valore a cui un titolo è iscritto inizialmente,
al netto dei rimborsi di capitale, aumentato o diminuito dell'ammortamento
cumulato (calcolato con il TIR) della differenza tra il valore iniziale e
il valore a scadenza.

Questo modulo orchestra:
1. Il calcolo del TIR (via tir.py)
2. L'ammortamento dello scarto periodo per periodo (via spread.py)
3. La generazione del piano completo di ammortamento
4. Il calcolo del valore contabile a qualsiasi data intermedia

Il valore iniziale di iscrizione include:
- Prezzo di acquisto (corso secco)
- Costi di transazione (commissioni, bolli, spese)
- Rateo maturato pagato all'acquisto (come da OIC 20, par. 50)

Tutti i calcoli usano decimal.Decimal, MAI float.
"""
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import List, Optional

from .constants import (
    DayCountConventionType,
    QUANTIZE_CALC,
    QUANTIZE_CENTS,
)
from .day_count import DayCountConvention
from .spread import AmortizationPeriod, SpreadAmortizationEngine
from .tir import CashFlow, TIRCalculator


@dataclass
class AmortizedCostSnapshot:
    """
    Snapshot del valore contabile a costo ammortizzato ad una data.

    Riferimento: OIC 20, par. 37-55.

    Attributes:
        reference_date: data di riferimento
        initial_book_value: valore iscrizione iniziale (costo + oneri)
        cumulative_amortization: ammortamento scarto cumulato fino alla data
        book_value: valore contabile corrente (initial + cumulative_amort)
        effective_rate: TIR del titolo
    """
    reference_date: date
    initial_book_value: Decimal
    cumulative_amortization: Decimal
    book_value: Decimal
    effective_rate: Decimal


class AmortizedCostEngine:
    """
    Motore di calcolo per il costo ammortizzato (OIC 20, par. 37-55).

    Combina il calcolo del TIR e l'ammortamento dello scarto per
    produrre il piano di ammortamento completo e il valore contabile
    a qualsiasi data.
    """

    @classmethod
    def compute_initial_book_value(
        cls,
        purchase_price_clean: Decimal,
        transaction_costs: Decimal,
    ) -> Decimal:
        """
        Calcola il valore iniziale di iscrizione a costo ammortizzato.

        Riferimento: OIC 20, par. 37-38.

        Il valore iniziale comprende il prezzo di acquisto (corso secco)
        e i costi di transazione direttamente attribuibili.
        Il rateo maturato NON è incluso (è rilevato separatamente).

        Args:
            purchase_price_clean: prezzo di acquisto corso secco
            transaction_costs: commissioni, bolli, spese accessorie

        Returns:
            Valore iniziale di iscrizione come Decimal.
        """
        return (purchase_price_clean + transaction_costs).quantize(QUANTIZE_CALC)

    @classmethod
    def compute_effective_rate(
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
    ) -> Decimal:
        """
        Calcola il TIR (tasso effettivo) per il costo ammortizzato.

        Riferimento: OIC 20, par. 37-45.

        Costruisce i flussi di cassa e calcola il TIR tramite Newton-Raphson.

        Args:
            settlement_date: data regolamento acquisto
            maturity_date: data scadenza titolo
            nominal_value: valore nominale
            purchase_price_tel_quel: prezzo tel quel pagato
            transaction_costs: costi di transazione
            coupon_rate: tasso cedolare annuo
            coupon_frequency: cedole/anno
            coupon_dates: date future di stacco cedola
            redemption_price: prezzo rimborso per 100 nominale (default: 100)

        Returns:
            TIR come Decimal.
        """
        flows: List[CashFlow] = TIRCalculator.build_bond_cash_flows(
            settlement_date=settlement_date,
            maturity_date=maturity_date,
            nominal_value=nominal_value,
            purchase_price_tel_quel=purchase_price_tel_quel,
            transaction_costs=transaction_costs,
            coupon_rate=coupon_rate,
            coupon_frequency=coupon_frequency,
            coupon_dates=coupon_dates,
            redemption_price=redemption_price,
        )
        return TIRCalculator.calculate(flows)

    @classmethod
    def compute_period_values(
        cls,
        nominal_value: Decimal,
        opening_book_value: Decimal,
        effective_rate: Decimal,
        coupon_rate: Decimal,
        coupon_frequency: int,
        period_start: date,
        period_end: date,
        day_count_convention: DayCountConventionType,
        coupon_start: Optional[date] = None,
        coupon_end: Optional[date] = None,
        coupon_received: Decimal = Decimal("0"),
    ) -> AmortizationPeriod:
        """
        Calcola tutti i valori di un singolo periodo a costo ammortizzato.

        Riferimento: OIC 20, par. 42-45.

        Per ogni periodo calcola:
        - Interessi effettivi = valore_contabile × TIR × year_fraction
        - Interessi nominali = nominale × tasso_cedola / frequenza × year_fraction
        - Ammortamento scarto = effettivi - nominali
        - Nuovo valore contabile = precedente + effettivi - incassi

        Args:
            nominal_value: valore nominale del titolo
            opening_book_value: valore contabile ad inizio periodo
            effective_rate: TIR calcolato
            coupon_rate: tasso cedolare annuo
            coupon_frequency: cedole/anno
            period_start: data inizio periodo
            period_end: data fine periodo
            day_count_convention: convenzione calcolo giorni
            coupon_start: inizio periodo cedolare (per ACT/ACT)
            coupon_end: fine periodo cedolare (per ACT/ACT)
            coupon_received: importo cedola incassata nel periodo

        Returns:
            AmortizationPeriod con tutti i valori calcolati.
        """
        return SpreadAmortizationEngine.amortize_effective_rate(
            nominal_value=nominal_value,
            initial_book_value=opening_book_value,
            effective_rate=effective_rate,
            coupon_rate=coupon_rate,
            coupon_frequency=coupon_frequency,
            period_start=period_start,
            period_end=period_end,
            day_count_convention=day_count_convention,
            coupon_start=coupon_start,
            coupon_end=coupon_end,
            coupon_received=coupon_received,
        )

    @classmethod
    def generate_amortization_schedule(
        cls,
        nominal_value: Decimal,
        initial_book_value: Decimal,
        effective_rate: Decimal,
        coupon_rate: Decimal,
        coupon_frequency: int,
        acquisition_date: date,
        maturity_date: date,
        coupon_dates: List[date],
        day_count_convention: DayCountConventionType,
        redemption_price: Decimal = Decimal("100"),
    ) -> List[AmortizationPeriod]:
        """
        Genera il piano di ammortamento completo a costo ammortizzato.

        Riferimento: OIC 20, par. 37-55.

        Genera una riga per ciascuna data cedola, dalla data di acquisto
        alla scadenza. L'ultimo periodo include l'aggiustamento per
        far convergere il valore contabile al valore di rimborso.

        Args:
            nominal_value: valore nominale
            initial_book_value: valore contabile iniziale
            effective_rate: TIR calcolato
            coupon_rate: tasso cedolare annuo
            coupon_frequency: cedole/anno
            acquisition_date: data acquisto
            maturity_date: data scadenza
            coupon_dates: date cedole future (ordinate cronologicamente)
            day_count_convention: convenzione calcolo giorni
            redemption_price: prezzo rimborso per 100 nominale

        Returns:
            Lista di AmortizationPeriod dalla data acquisto alla scadenza.
        """
        schedule: List[AmortizationPeriod] = []
        current_book_value: Decimal = initial_book_value
        period_start: date = acquisition_date

        coupon_per_period: Decimal = (
            nominal_value * coupon_rate / Decimal(str(coupon_frequency))
        )

        redemption_value: Decimal = (
            nominal_value * redemption_price / Decimal("100")
        )

        for i, coupon_date in enumerate(coupon_dates):
            coupon_start: date = (
                coupon_dates[i - 1] if i > 0 else acquisition_date
            )
            coupon_end: date = coupon_date

            is_last: bool = (i == len(coupon_dates) - 1)

            period: AmortizationPeriod = cls.compute_period_values(
                nominal_value=nominal_value,
                opening_book_value=current_book_value,
                effective_rate=effective_rate,
                coupon_rate=coupon_rate,
                coupon_frequency=coupon_frequency,
                period_start=period_start,
                period_end=coupon_date,
                day_count_convention=day_count_convention,
                coupon_start=coupon_start,
                coupon_end=coupon_end,
                coupon_received=coupon_per_period,
            )

            # Ultimo periodo: forza convergenza al valore di rimborso
            if is_last and coupon_date == maturity_date:
                # Ricalcola per forzare closing = redemption_value
                forced_effective: Decimal = (
                    redemption_value + coupon_per_period - current_book_value
                )
                forced_amortization: Decimal = (
                    forced_effective - period.nominal_interest
                )
                period = AmortizationPeriod(
                    period_start=period.period_start,
                    period_end=period.period_end,
                    opening_book_value=current_book_value.quantize(QUANTIZE_CALC),
                    effective_interest=forced_effective.quantize(QUANTIZE_CALC),
                    nominal_interest=period.nominal_interest,
                    amortization=forced_amortization.quantize(QUANTIZE_CALC),
                    coupon_received=coupon_per_period,
                    closing_book_value=redemption_value.quantize(QUANTIZE_CALC),
                    year_fraction=period.year_fraction,
                )

            schedule.append(period)
            current_book_value = period.closing_book_value
            period_start = coupon_date

        return schedule

    @classmethod
    def get_book_value_at_date(
        cls,
        schedule: List[AmortizationPeriod],
        target_date: date,
        initial_book_value: Decimal,
    ) -> AmortizedCostSnapshot:
        """
        Ottiene il valore contabile a costo ammortizzato ad una data specifica.

        Riferimento: OIC 20, par. 37-55.

        Utile per:
        - Valutazione di bilancio a fine esercizio
        - Calcolo plus/minusvalenza in caso di vendita anticipata
        - Nota integrativa

        Args:
            schedule: piano di ammortamento generato
            target_date: data a cui si vuole il valore contabile
            initial_book_value: valore contabile iniziale

        Returns:
            AmortizedCostSnapshot con il valore contabile alla data.

        Raises:
            ValueError: se la data è anteriore all'inizio del piano.
        """
        if not schedule:
            raise ValueError("Il piano di ammortamento è vuoto.")

        if target_date < schedule[0].period_start:
            raise ValueError(
                f"La data richiesta ({target_date}) è anteriore "
                f"all'inizio del piano ({schedule[0].period_start})."
            )

        # Cerca l'ultimo periodo completato prima/alla target_date
        book_value: Decimal = initial_book_value
        cumulative_amortization: Decimal = Decimal("0")
        effective_rate: Decimal = Decimal("0")

        for period in schedule:
            if period.period_end <= target_date:
                book_value = period.closing_book_value
                cumulative_amortization += period.amortization
            else:
                # Periodo parziale: interpola pro-rata
                if period.period_start < target_date:
                    total_days: Decimal = Decimal(
                        str((period.period_end - period.period_start).days)
                    )
                    elapsed_days: Decimal = Decimal(
                        str((target_date - period.period_start).days)
                    )
                    if total_days > Decimal("0"):
                        fraction: Decimal = elapsed_days / total_days
                        partial_amort: Decimal = (
                            period.amortization * fraction
                        ).quantize(QUANTIZE_CALC)
                        book_value = (
                            period.opening_book_value + partial_amort
                        )
                        cumulative_amortization += partial_amort
                break

        return AmortizedCostSnapshot(
            reference_date=target_date,
            initial_book_value=initial_book_value.quantize(QUANTIZE_CALC),
            cumulative_amortization=cumulative_amortization.quantize(QUANTIZE_CALC),
            book_value=book_value.quantize(QUANTIZE_CALC),
            effective_rate=effective_rate,
        )
