"""
Calcolo ratei cedolari su titoli di debito.

Riferimento: OIC 20, par. 50:
"Non si comprende nel costo il rateo relativo alla cedola di interessi
maturata alla data di acquisto, che deve essere contabilizzato come tale."

Il rateo cedolare è la quota di cedola maturata tra l'ultima data di godimento
(o la data di emissione) e una data di riferimento (acquisto, chiusura esercizio, etc.).

Formula generale:
    rateo = nominale × tasso_cedolare / frequenza × year_fraction

dove year_fraction è calcolata con la convenzione giorni appropriata al titolo.

Tutti i calcoli usano decimal.Decimal, MAI float.
"""
from datetime import date
from decimal import Decimal
from typing import List, Optional

from .constants import (
    DayCountConventionType,
    QUANTIZE_CALC,
    QUANTIZE_CENTS,
)
from .day_count import DayCountConvention


class AccruedInterestCalculator:
    """
    Calcola il rateo cedolare maturato su un titolo di debito.

    Riferimento: OIC 20, par. 50.

    Il rateo viene calcolato usando la convenzione giorni corretta
    per il tipo di titolo e rappresenta la quota di cedola maturata
    dal godimento precedente alla data di calcolo.
    """

    @classmethod
    def calculate(
        cls,
        nominal_value: Decimal,
        coupon_rate: Decimal,
        coupon_frequency: int,
        accrual_start: date,
        accrual_end: date,
        day_count_convention: DayCountConventionType,
        period_start: Optional[date] = None,
        period_end: Optional[date] = None,
    ) -> Decimal:
        """
        Calcola il rateo cedolare maturato tra due date.

        Riferimento: OIC 20, par. 50.

        Formula:
            rateo = nominale × (tasso / frequenza) × year_fraction

        Per ACT/ACT, period_start e period_end definiscono il periodo
        cedolare completo. Se non forniti, vengono usati accrual_start
        e accrual_end come approssimazione.

        Args:
            nominal_value: valore nominale del titolo (es. Decimal('100000'))
            coupon_rate: tasso cedolare annuo (es. Decimal('0.035') per 3.5%)
            coupon_frequency: numero cedole/anno (1, 2, 4)
            accrual_start: data inizio maturazione rateo (ultimo godimento)
            accrual_end: data fine maturazione rateo (data calcolo)
            day_count_convention: convenzione calcolo giorni
            period_start: inizio periodo cedolare (per ACT/ACT)
            period_end: fine periodo cedolare (per ACT/ACT)

        Returns:
            Rateo maturato come Decimal quantizzato a 10 decimali.

        Raises:
            ValueError: se coupon_frequency è zero o negativo
            ValueError: se accrual_end è anteriore a accrual_start
        """
        if coupon_frequency <= 0:
            raise ValueError(
                f"Frequenza cedolare deve essere > 0, ricevuto: {coupon_frequency}"
            )

        if accrual_end < accrual_start:
            raise ValueError(
                f"Data fine rateo ({accrual_end}) anteriore a data inizio "
                f"({accrual_start})."
            )

        if accrual_start == accrual_end:
            return Decimal("0")

        # Cedola piena per periodo
        coupon_per_period: Decimal = (
            nominal_value * coupon_rate / Decimal(str(coupon_frequency))
        )

        # Calcola year fraction
        year_fraction: Decimal = DayCountConvention.calculate(
            convention=day_count_convention,
            start=accrual_start,
            end=accrual_end,
            period_start=period_start or accrual_start,
            period_end=period_end or accrual_end,
        )

        # Rateo = cedola piena × frazione di periodo
        accrued: Decimal = coupon_per_period * year_fraction

        return accrued.quantize(QUANTIZE_CALC)

    @classmethod
    def calculate_for_purchase(
        cls,
        nominal_value: Decimal,
        coupon_rate: Decimal,
        coupon_frequency: int,
        purchase_date: date,
        last_coupon_date: date,
        next_coupon_date: date,
        day_count_convention: DayCountConventionType,
    ) -> Decimal:
        """
        Calcola il rateo cedolare alla data di acquisto di un titolo.

        Riferimento: OIC 20, par. 50 — il rateo all'acquisto deve essere
        rilevato separatamente dal costo del titolo.

        Il rateo è la quota di cedola maturata dall'ultimo godimento
        alla data di acquisto.

        Args:
            nominal_value: valore nominale del titolo
            coupon_rate: tasso cedolare annuo
            coupon_frequency: cedole/anno
            purchase_date: data di acquisto
            last_coupon_date: data ultimo godimento (o emissione)
            next_coupon_date: data prossimo godimento
            day_count_convention: convenzione calcolo giorni

        Returns:
            Rateo maturato alla data di acquisto come Decimal.
        """
        return cls.calculate(
            nominal_value=nominal_value,
            coupon_rate=coupon_rate,
            coupon_frequency=coupon_frequency,
            accrual_start=last_coupon_date,
            accrual_end=purchase_date,
            day_count_convention=day_count_convention,
            period_start=last_coupon_date,
            period_end=next_coupon_date,
        )

    @classmethod
    def calculate_year_end(
        cls,
        nominal_value: Decimal,
        coupon_rate: Decimal,
        coupon_frequency: int,
        last_coupon_date: date,
        next_coupon_date: date,
        year_end_date: date,
        day_count_convention: DayCountConventionType,
    ) -> Decimal:
        """
        Calcola il rateo cedolare a fine esercizio per la rilevazione
        in bilancio tra i ratei attivi.

        Riferimento: OIC 20, par. 50; Art. 2424-bis c.c.

        Args:
            nominal_value: valore nominale
            coupon_rate: tasso cedolare annuo
            coupon_frequency: cedole/anno
            last_coupon_date: data ultimo godimento
            next_coupon_date: data prossimo godimento
            year_end_date: data chiusura esercizio (es. 31/12)
            day_count_convention: convenzione calcolo giorni

        Returns:
            Rateo da iscrivere in bilancio come Decimal.
        """
        return cls.calculate(
            nominal_value=nominal_value,
            coupon_rate=coupon_rate,
            coupon_frequency=coupon_frequency,
            accrual_start=last_coupon_date,
            accrual_end=year_end_date,
            day_count_convention=day_count_convention,
            period_start=last_coupon_date,
            period_end=next_coupon_date,
        )

    @classmethod
    def calculate_competence_interest(
        cls,
        coupon_gross: Decimal,
        accrued_at_purchase: Decimal,
    ) -> Decimal:
        """
        Calcola gli interessi di competenza all'incasso di una cedola.

        Riferimento: OIC 20, par. 50.

        All'incasso della cedola, la quota di competenza è:
            interessi_competenza = cedola_lorda - rateo_pagato_all_acquisto

        Il rateo pagato all'acquisto viene stornato (chiusura C.II.5),
        e solo la differenza è ricavo di competenza (C.16.a).

        Args:
            coupon_gross: importo lordo della cedola incassata
            accrued_at_purchase: rateo pagato al momento dell'acquisto

        Returns:
            Interessi di competenza come Decimal.
        """
        return coupon_gross - accrued_at_purchase
