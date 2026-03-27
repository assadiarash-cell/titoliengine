"""
Conversione cambi per titoli denominati in valuta estera.

Riferimenti:
- OIC 26: Operazioni, attività e passività in valuta estera
- Art. 2426, comma 1, n. 8-bis c.c.: Criteri di conversione
- OIC 20, par. 65-70: Titoli di debito in valuta estera

REGOLE DI CONVERSIONE (OIC 26):

1. ISCRIZIONE INIZIALE:
   Costo in EUR = costo in valuta estera × cambio alla data di regolamento

2. VALUTAZIONE A FINE ESERCIZIO:
   - Immobilizzazioni: cambio storico (salvo perdite durevoli → cambio corrente)
   - Attivo circolante: cambio di chiusura

3. CESSIONE/RIMBORSO:
   Ricavo in EUR = ricavo in valuta × cambio alla data operazione

4. DIFFERENZE CAMBIO:
   - Utili su cambi: rilevati se realizzati, o se da attivo circolante
   - Perdite su cambi: sempre rilevate (principio di prudenza)

Tutti i calcoli usano decimal.Decimal, MAI float.
"""
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from enum import Enum
from typing import Optional

from .constants import (
    Classification,
    QUANTIZE_CALC,
    QUANTIZE_CENTS,
)


class FxDifferenceType(Enum):
    """
    Tipo di differenza cambio.

    Riferimento: OIC 26, par. 30-42.
    """
    GAIN = "fx_gain"       # Utile su cambi
    LOSS = "fx_loss"       # Perdita su cambi
    ZERO = "zero"          # Nessuna differenza


@dataclass
class FxConversionResult:
    """
    Risultato della conversione in valuta.

    Riferimento: OIC 26.

    Attributes:
        amount_foreign: importo in valuta estera
        currency: codice ISO valuta (es. USD, GBP)
        exchange_rate: tasso di cambio applicato (1 EUR = X valuta)
        amount_eur: importo convertito in EUR
        conversion_date: data del cambio utilizzato
    """
    amount_foreign: Decimal
    currency: str
    exchange_rate: Decimal
    amount_eur: Decimal
    conversion_date: date


@dataclass
class FxDifferenceResult:
    """
    Risultato del calcolo differenza cambio.

    Riferimento: OIC 26, par. 30-42.

    Attributes:
        original_eur: valore originale in EUR (al cambio storico)
        current_eur: valore corrente in EUR (al cambio corrente)
        fx_difference: differenza cambio (corrente - originale)
        difference_type: classificazione (gain, loss, zero)
        historical_rate: cambio storico originale
        current_rate: cambio corrente
        is_realized: True se la differenza è realizzata (cessione/incasso)
    """
    original_eur: Decimal
    current_eur: Decimal
    fx_difference: Decimal
    difference_type: FxDifferenceType
    historical_rate: Decimal
    current_rate: Decimal
    is_realized: bool


class FxEngine:
    """
    Motore di conversione cambi per titoli in valuta estera.

    Riferimento: OIC 26, OIC 20 par. 65-70.
    """

    @classmethod
    def convert_to_eur(
        cls,
        amount_foreign: Decimal,
        exchange_rate: Decimal,
        conversion_date: date,
        currency: str = "USD",
    ) -> FxConversionResult:
        """
        Converte un importo da valuta estera a EUR.

        Riferimento: OIC 26, par. 10-15.

        Il tasso di cambio è espresso come: 1 EUR = X valuta estera.
        Esempio: EUR/USD = 1.08 significa 1 EUR = 1.08 USD.
        Quindi: amount_EUR = amount_foreign / exchange_rate.

        Args:
            amount_foreign: importo in valuta estera
            exchange_rate: tasso di cambio (1 EUR = X valuta)
            conversion_date: data del cambio utilizzato
            currency: codice ISO valuta (default: USD)

        Returns:
            FxConversionResult con importo convertito.

        Raises:
            ValueError: se il tasso di cambio è zero o negativo.
        """
        if exchange_rate <= Decimal("0"):
            raise ValueError(
                f"Il tasso di cambio deve essere positivo. "
                f"Ricevuto: {exchange_rate}"
            )

        amount_eur: Decimal = (amount_foreign / exchange_rate).quantize(QUANTIZE_CENTS)

        return FxConversionResult(
            amount_foreign=amount_foreign,
            currency=currency.upper(),
            exchange_rate=exchange_rate,
            amount_eur=amount_eur,
            conversion_date=conversion_date,
        )

    @classmethod
    def convert_from_eur(
        cls,
        amount_eur: Decimal,
        exchange_rate: Decimal,
        conversion_date: date,
        currency: str = "USD",
    ) -> FxConversionResult:
        """
        Converte un importo da EUR a valuta estera.

        Riferimento: OIC 26.

        Args:
            amount_eur: importo in EUR
            exchange_rate: tasso di cambio (1 EUR = X valuta)
            conversion_date: data del cambio
            currency: codice ISO valuta

        Returns:
            FxConversionResult con importo convertito.

        Raises:
            ValueError: se il tasso di cambio è zero o negativo.
        """
        if exchange_rate <= Decimal("0"):
            raise ValueError(
                f"Il tasso di cambio deve essere positivo. "
                f"Ricevuto: {exchange_rate}"
            )

        amount_foreign: Decimal = (amount_eur * exchange_rate).quantize(QUANTIZE_CENTS)

        return FxConversionResult(
            amount_foreign=amount_foreign,
            currency=currency.upper(),
            exchange_rate=exchange_rate,
            amount_eur=amount_eur,
            conversion_date=conversion_date,
        )

    @classmethod
    def calculate_fx_difference(
        cls,
        amount_foreign: Decimal,
        historical_rate: Decimal,
        current_rate: Decimal,
        is_realized: bool = False,
    ) -> FxDifferenceResult:
        """
        Calcola la differenza di cambio tra due date.

        Riferimento: OIC 26, par. 30-42.

        Args:
            amount_foreign: importo in valuta estera
            historical_rate: cambio storico (alla data di iscrizione)
            current_rate: cambio corrente (alla data di valutazione)
            is_realized: True se l'operazione è stata conclusa (cessione/incasso)

        Returns:
            FxDifferenceResult con dettaglio differenza cambio.

        Raises:
            ValueError: se un tasso di cambio è zero o negativo.
        """
        if historical_rate <= Decimal("0") or current_rate <= Decimal("0"):
            raise ValueError(
                "I tassi di cambio devono essere positivi. "
                f"Storico: {historical_rate}, corrente: {current_rate}"
            )

        original_eur: Decimal = (
            amount_foreign / historical_rate
        ).quantize(QUANTIZE_CENTS)

        current_eur: Decimal = (
            amount_foreign / current_rate
        ).quantize(QUANTIZE_CENTS)

        fx_difference: Decimal = current_eur - original_eur

        if fx_difference > Decimal("0"):
            difference_type = FxDifferenceType.GAIN
        elif fx_difference < Decimal("0"):
            difference_type = FxDifferenceType.LOSS
        else:
            difference_type = FxDifferenceType.ZERO

        return FxDifferenceResult(
            original_eur=original_eur,
            current_eur=current_eur,
            fx_difference=fx_difference.quantize(QUANTIZE_CENTS),
            difference_type=difference_type,
            historical_rate=historical_rate,
            current_rate=current_rate,
            is_realized=is_realized,
        )

    @classmethod
    def year_end_revaluation(
        cls,
        amount_foreign: Decimal,
        historical_rate: Decimal,
        closing_rate: Decimal,
        classification: Classification,
    ) -> FxDifferenceResult:
        """
        Calcola la differenza cambio per la valutazione di fine esercizio.

        Riferimento: OIC 26, par. 30-42; Art. 2426, comma 1, n. 8-bis c.c.

        Regole:
        - Attivo circolante (C.III): SEMPRE al cambio di chiusura
        - Immobilizzazioni (B.III): cambio storico, salvo perdite durevoli

        Per le immobilizzazioni, la differenza cambio viene calcolata
        ma la rilevazione contabile dipende dalla valutazione di durevolezza
        della perdita (non gestita in questo modulo).

        Args:
            amount_foreign: importo in valuta estera
            historical_rate: cambio alla data di acquisto
            closing_rate: cambio alla data di chiusura esercizio
            classification: classificazione contabile (immobilized/current)

        Returns:
            FxDifferenceResult con differenza cambio non realizzata.
        """
        result: FxDifferenceResult = cls.calculate_fx_difference(
            amount_foreign=amount_foreign,
            historical_rate=historical_rate,
            current_rate=closing_rate,
            is_realized=False,
        )

        return result
