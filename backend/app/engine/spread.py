"""
Ammortamento dello scarto di negoziazione/emissione su titoli di debito.

Riferimento: OIC 20, par. 37-55 (costo ammortizzato); par. 14-30 (costo storico).

Lo scarto è la differenza tra:
- Prezzo di acquisto (corso secco + costi di transazione) e
- Valore nominale di rimborso

Se acquisto > nominale → scarto negativo (sopra la pari) → ammortamento in diminuzione
Se acquisto < nominale → scarto positivo (sotto la pari) → ammortamento in aumento

DUE METODI di ammortamento:

1. COSTO AMMORTIZZATO (OIC 20, par. 37-55):
   Lo scarto viene ammortizzato usando il TIR (Tasso Interno di Rendimento).
   Ad ogni periodo:
     interessi_effettivi = valore_contabile × TIR × year_fraction
     interessi_nominali = nominale × tasso_cedolare / frequenza × year_fraction
     ammortamento = interessi_effettivi - interessi_nominali

2. PRO-RATA TEMPORIS LINEARE (alternativa semplificata per costo storico):
   Lo scarto viene ripartito linearmente sulla vita residua del titolo.
   ammortamento_periodo = scarto_totale × (giorni_periodo / giorni_totali)

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


@dataclass
class AmortizationPeriod:
    """
    Risultato dell'ammortamento per un singolo periodo.

    Riferimento: OIC 20, par. 37-55.

    Attributes:
        period_start: data inizio periodo
        period_end: data fine periodo
        opening_book_value: valore contabile ad apertura periodo
        effective_interest: interessi calcolati al TIR
        nominal_interest: interessi al tasso nominale (cedola)
        amortization: ammortamento scarto (effective - nominal)
        coupon_received: cedola incassata nel periodo
        closing_book_value: valore contabile a chiusura periodo
        year_fraction: frazione d'anno del periodo
    """
    period_start: date
    period_end: date
    opening_book_value: Decimal
    effective_interest: Decimal
    nominal_interest: Decimal
    amortization: Decimal
    coupon_received: Decimal
    closing_book_value: Decimal
    year_fraction: Decimal


class SpreadAmortizationEngine:
    """
    Motore di ammortamento dello scarto di negoziazione/emissione.

    Supporta sia il metodo del costo ammortizzato (con TIR) sia
    il metodo lineare pro-rata temporis.

    Riferimento: OIC 20, par. 37-55 e par. 14-30.
    """

    @classmethod
    def compute_spread(
        cls,
        acquisition_cost: Decimal,
        nominal_value: Decimal,
        redemption_price: Decimal = Decimal("100"),
    ) -> Decimal:
        """
        Calcola lo scarto tra costo di acquisto e valore di rimborso.

        Riferimento: OIC 20, par. 14.

        Args:
            acquisition_cost: costo di acquisto totale (corso secco + oneri)
            nominal_value: valore nominale del titolo
            redemption_price: prezzo di rimborso per 100 nominale (default: 100)

        Returns:
            Scarto come Decimal.
            Positivo se acquisto < rimborso (sotto la pari, guadagno).
            Negativo se acquisto > rimborso (sopra la pari, perdita).
        """
        redemption_value: Decimal = nominal_value * redemption_price / Decimal("100")
        return redemption_value - acquisition_cost

    @classmethod
    def amortize_effective_rate(
        cls,
        nominal_value: Decimal,
        initial_book_value: Decimal,
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
        Calcola l'ammortamento per un periodo con il metodo del costo ammortizzato.

        Riferimento: OIC 20, par. 37-55.

        Procedimento:
        1. Interessi effettivi = valore_contabile × TIR × year_fraction
        2. Interessi nominali = nominale × tasso / frequenza × year_fraction
        3. Ammortamento scarto = effettivi - nominali
        4. Nuovo valore contabile = precedente + effettivi - incassi

        Args:
            nominal_value: valore nominale del titolo
            initial_book_value: valore contabile all'inizio del periodo
            effective_rate: TIR calcolato
            coupon_rate: tasso cedolare annuo
            coupon_frequency: cedole/anno
            period_start: inizio periodo
            period_end: fine periodo
            day_count_convention: convenzione calcolo giorni
            coupon_start: inizio periodo cedolare (per ACT/ACT)
            coupon_end: fine periodo cedolare (per ACT/ACT)
            coupon_received: importo cedola incassata nel periodo

        Returns:
            AmortizationPeriod con tutti i valori calcolati.
        """
        # Year fraction per interessi nominali (cedola pro-rata)
        # Usa la convenzione del titolo (ACT/ACT dà fraction del periodo cedolare)
        coupon_year_fraction: Decimal = DayCountConvention.calculate(
            convention=day_count_convention,
            start=period_start,
            end=period_end,
            period_start=coupon_start or period_start,
            period_end=coupon_end or period_end,
        )

        # Year fraction per interessi effettivi (TIR è annuale)
        # SEMPRE giorni_effettivi / 365 per coerenza col TIR calcolato su base annua
        actual_days: Decimal = Decimal(str((period_end - period_start).days))
        effective_year_fraction: Decimal = actual_days / Decimal("365")

        # Interessi effettivi (al TIR annuale × frazione di anno reale)
        effective_interest: Decimal = (
            initial_book_value * effective_rate * effective_year_fraction
        )

        # Interessi nominali (cedola per periodo × fraction periodo cedolare)
        nominal_interest: Decimal = (
            nominal_value
            * coupon_rate
            / Decimal(str(coupon_frequency))
            * coupon_year_fraction
        )

        year_fraction: Decimal = coupon_year_fraction

        # Ammortamento scarto
        amortization: Decimal = effective_interest - nominal_interest

        # Nuovo valore contabile
        closing_book_value: Decimal = (
            initial_book_value + effective_interest - coupon_received
        )

        return AmortizationPeriod(
            period_start=period_start,
            period_end=period_end,
            opening_book_value=initial_book_value.quantize(QUANTIZE_CALC),
            effective_interest=effective_interest.quantize(QUANTIZE_CALC),
            nominal_interest=nominal_interest.quantize(QUANTIZE_CALC),
            amortization=amortization.quantize(QUANTIZE_CALC),
            coupon_received=coupon_received,
            closing_book_value=closing_book_value.quantize(QUANTIZE_CALC),
            year_fraction=year_fraction.quantize(QUANTIZE_CALC),
        )

    @classmethod
    def generate_amortization_schedule_effective(
        cls,
        nominal_value: Decimal,
        initial_book_value: Decimal,
        effective_rate: Decimal,
        coupon_rate: Decimal,
        coupon_frequency: int,
        acquisition_date: date,
        coupon_dates: List[date],
        day_count_convention: DayCountConventionType,
    ) -> List[AmortizationPeriod]:
        """
        Genera il piano di ammortamento completo con metodo costo ammortizzato.

        Riferimento: OIC 20, par. 37-55.

        Usato per la Nota Integrativa e per le scritture periodiche
        di ammortamento scarto.

        Args:
            nominal_value: valore nominale
            initial_book_value: valore contabile iniziale (acquisto + costi)
            effective_rate: TIR calcolato
            coupon_rate: tasso cedolare annuo
            coupon_frequency: cedole/anno
            acquisition_date: data di acquisto
            coupon_dates: lista date cedole future (ordinate cronologicamente)
            day_count_convention: convenzione calcolo giorni

        Returns:
            Lista di AmortizationPeriod, uno per ogni periodo cedolare.
        """
        schedule: List[AmortizationPeriod] = []
        current_book_value: Decimal = initial_book_value
        period_start: date = acquisition_date

        coupon_per_period: Decimal = (
            nominal_value * coupon_rate / Decimal(str(coupon_frequency))
        )

        for i, coupon_date in enumerate(coupon_dates):
            coupon_start: date = coupon_dates[i - 1] if i > 0 else acquisition_date
            coupon_end: date = coupon_date

            period: AmortizationPeriod = cls.amortize_effective_rate(
                nominal_value=nominal_value,
                initial_book_value=current_book_value,
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

            schedule.append(period)
            current_book_value = period.closing_book_value
            period_start = coupon_date

        return schedule

    @classmethod
    def amortize_linear(
        cls,
        total_spread: Decimal,
        acquisition_date: date,
        maturity_date: date,
        period_start: date,
        period_end: date,
    ) -> Decimal:
        """
        Ammortamento lineare pro-rata temporis dello scarto.

        Metodo semplificato usato per bilancio abbreviato/micro
        quando non si applica il costo ammortizzato.

        Riferimento: OIC 20, par. 14-30.

        Formula:
            ammortamento = scarto_totale × (giorni_periodo / giorni_vita_residua)

        Args:
            total_spread: scarto totale da ammortizzare
            acquisition_date: data di acquisto del titolo
            maturity_date: data di scadenza del titolo
            period_start: inizio del periodo di ammortamento
            period_end: fine del periodo di ammortamento

        Returns:
            Ammortamento del periodo come Decimal.

        Raises:
            ValueError: se la vita residua totale è zero
        """
        total_days: Decimal = Decimal(
            str((maturity_date - acquisition_date).days)
        )
        if total_days == Decimal("0"):
            raise ValueError(
                "Vita residua del titolo è zero: "
                f"acquisizione={acquisition_date}, scadenza={maturity_date}"
            )

        period_days: Decimal = Decimal(str((period_end - period_start).days))

        amortization: Decimal = total_spread * period_days / total_days
        return amortization.quantize(QUANTIZE_CALC)

    @classmethod
    def generate_linear_schedule(
        cls,
        total_spread: Decimal,
        acquisition_date: date,
        maturity_date: date,
        period_end_dates: List[date],
    ) -> List[dict]:
        """
        Genera il piano di ammortamento lineare completo.

        Riferimento: OIC 20, par. 14-30.

        Args:
            total_spread: scarto totale da ammortizzare
            acquisition_date: data acquisto
            maturity_date: data scadenza
            period_end_dates: date fine di ogni periodo (es. fine anno, date cedola)

        Returns:
            Lista di dict con dettaglio ammortamento per ogni periodo.
        """
        schedule: List[dict] = []
        cumulative: Decimal = Decimal("0")
        period_start: date = acquisition_date

        for period_end in period_end_dates:
            amortization: Decimal = cls.amortize_linear(
                total_spread=total_spread,
                acquisition_date=acquisition_date,
                maturity_date=maturity_date,
                period_start=period_start,
                period_end=period_end,
            )

            cumulative += amortization

            schedule.append({
                "period_start": period_start,
                "period_end": period_end,
                "amortization": amortization.quantize(QUANTIZE_CALC),
                "cumulative_amortization": cumulative.quantize(QUANTIZE_CALC),
                "remaining_spread": (
                    (total_spread - cumulative).quantize(QUANTIZE_CALC)
                ),
            })

            period_start = period_end

        return schedule
