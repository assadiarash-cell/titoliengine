"""
Convenzioni di calcolo giorni per interessi su titoli.

Riferimento: OIC 20, ISDA Day Count Conventions.

Implementa tre convenzioni:
1. ACT/ACT (ICMA) — per titoli di Stato italiani (BTP, CCT)
2. ACT/360 — per BOT, CTZ e strumenti money market
3. 30/360 European — per corporate bond EUR

REGOLA CRITICA: usare SEMPRE la convenzione corretta per tipo titolo.
Tutti i calcoli usano decimal.Decimal, MAI float.
"""
from datetime import date
from decimal import Decimal

from .constants import DayCountConventionType


class DayCountConvention:
    """
    Implementazione delle convenzioni di calcolo giorni per titoli.

    Ogni metodo restituisce una frazione d'anno (year fraction) come Decimal,
    usata per calcolare interessi maturati, ratei e ammortamento scarto.

    Riferimento: OIC 20, par. 37-55; ISDA 2006 Definitions, Section 4.16.
    """

    @staticmethod
    def act_act_icma(
        start: date,
        end: date,
        period_start: date,
        period_end: date,
    ) -> Decimal:
        """
        ACT/ACT (ICMA) — per titoli di Stato italiani.

        Calcola la frazione del periodo cedolare basata su giorni effettivi:
            year_fraction = giorni_effettivi / giorni_periodo_cedolare

        Riferimento: OIC 20, par. 37-55; ICMA Rule 251.1.

        Args:
            start: data inizio maturazione interessi
            end: data fine maturazione interessi
            period_start: data inizio del periodo cedolare completo
            period_end: data fine del periodo cedolare completo

        Returns:
            Frazione del periodo cedolare come Decimal.
            Restituisce Decimal('0') se il periodo cedolare ha durata zero.
        """
        actual_days: Decimal = Decimal(str((end - start).days))
        period_days: Decimal = Decimal(str((period_end - period_start).days))

        if period_days == Decimal("0"):
            return Decimal("0")

        return actual_days / period_days

    @staticmethod
    def act_360(start: date, end: date) -> Decimal:
        """
        ACT/360 — per BOT, CTZ e strumenti money market.

        Calcola la frazione d'anno basata su giorni effettivi su base 360:
            year_fraction = giorni_effettivi / 360

        Riferimento: OIC 20; ISDA 2006 Definitions, Section 4.16(e).

        Args:
            start: data inizio maturazione
            end: data fine maturazione

        Returns:
            Frazione d'anno come Decimal.
        """
        actual_days: Decimal = Decimal(str((end - start).days))
        return actual_days / Decimal("360")

    @staticmethod
    def thirty_360(start: date, end: date) -> Decimal:
        """
        30/360 European — per corporate bond EUR.

        Assume mesi da 30 giorni e anno da 360 giorni:
            giorni = (Y2-Y1)*360 + (M2-M1)*30 + (D2-D1)
            year_fraction = giorni / 360

        Regole per i giorni (convenzione europea):
        - D1 = min(giorno_start, 30)
        - D2 = min(giorno_end, 30)

        Riferimento: ISDA 2006 Definitions, Section 4.16(h) (30E/360).

        Args:
            start: data inizio maturazione
            end: data fine maturazione

        Returns:
            Frazione d'anno come Decimal.
        """
        d1: int = min(start.day, 30)
        d2: int = min(end.day, 30)

        days: Decimal = (
            Decimal(str(end.year - start.year)) * Decimal("360")
            + Decimal(str(end.month - start.month)) * Decimal("30")
            + Decimal(str(d2 - d1))
        )

        return days / Decimal("360")

    @classmethod
    def calculate(
        cls,
        convention: DayCountConventionType,
        start: date,
        end: date,
        period_start: date | None = None,
        period_end: date | None = None,
    ) -> Decimal:
        """
        Dispatcher: calcola la year fraction con la convenzione specificata.

        Riferimento: OIC 20, par. 37-55.

        Args:
            convention: tipo di convenzione da applicare
            start: data inizio
            end: data fine
            period_start: inizio periodo cedolare (richiesto per ACT/ACT)
            period_end: fine periodo cedolare (richiesto per ACT/ACT)

        Returns:
            Year fraction come Decimal.

        Raises:
            ValueError: se ACT/ACT è richiesto senza period_start/period_end
            ValueError: se la convenzione non è riconosciuta
        """
        if convention == DayCountConventionType.ACT_ACT:
            if period_start is None or period_end is None:
                raise ValueError(
                    "ACT/ACT (ICMA) richiede period_start e period_end "
                    "per definire il periodo cedolare completo."
                )
            return cls.act_act_icma(start, end, period_start, period_end)

        if convention == DayCountConventionType.ACT_360:
            return cls.act_360(start, end)

        if convention == DayCountConventionType.THIRTY_360:
            return cls.thirty_360(start, end)

        raise ValueError(f"Convenzione non riconosciuta: {convention}")
