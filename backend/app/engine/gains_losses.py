"""
Calcolo plusvalenze e minusvalenze su cessione/rimborso titoli.

Riferimenti:
- OIC 20, par. 56-62: Cancellazione titoli di debito
- OIC 20, par. 14-30: Costo storico
- OIC 20, par. 37-55: Costo ammortizzato
- Art. 67-68 TUIR: Plusvalenze e minusvalenze (redditi diversi)
- Art. 86-101 TUIR: Plusvalenze e minusvalenze patrimoniali (reddito d'impresa)

DUE METODI DI CALCOLO:

1. COSTO STORICO (bilancio abbreviato/micro):
   gain_loss = prezzo_vendita - costo_acquisto_con_oneri
   Il costo include: corso secco + commissioni acquisto.
   NON include il rateo pagato (già rilevato separatamente).

2. COSTO AMMORTIZZATO (bilancio ordinario):
   gain_loss = prezzo_vendita - valore_contabile_ammortizzato_alla_data
   Il valore contabile tiene conto dell'ammortamento scarto
   accumulato dalla data di acquisto alla data di vendita.

CLASSIFICAZIONE CONTABILE:
- Capital gain/loss: differenza tra prezzo e valore contabile → C.16.b / C.17
- Ordinary income: interessi maturati (rateo) → C.16.a

Tutti i calcoli usano decimal.Decimal, MAI float.
"""
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from enum import Enum
from typing import Optional

from .constants import (
    QUANTIZE_CALC,
    QUANTIZE_CENTS,
    ValuationMethod,
)


class GainLossType(Enum):
    """
    Classificazione della plus/minusvalenza.

    Riferimento: Art. 67-68 TUIR (redditi diversi),
                 Art. 86-101 TUIR (reddito d'impresa).
    """
    CAPITAL_GAIN = "capital_gain"       # Plusvalenza da negoziazione
    CAPITAL_LOSS = "capital_loss"       # Minusvalenza da negoziazione
    ZERO = "zero"                       # Nessuna plus/minus


@dataclass
class GainLossResult:
    """
    Risultato del calcolo plus/minusvalenza.

    Riferimento: OIC 20, par. 56-62.

    Attributes:
        sale_date: data di cessione/rimborso
        sale_price: prezzo di vendita (netto commissioni vendita)
        book_value: valore contabile alla data di cessione
        gain_loss: importo plus/minus (positivo = gain, negativo = loss)
        gain_loss_type: classificazione (capital_gain, capital_loss, zero)
        valuation_method: metodo di valutazione usato
        accrued_interest_sold: rateo cedolare maturato venduto (se presente)
        net_proceeds: ricavo netto totale (sale_price + accrued)
        sale_costs: commissioni e spese di vendita
    """
    sale_date: date
    sale_price: Decimal
    book_value: Decimal
    gain_loss: Decimal
    gain_loss_type: GainLossType
    valuation_method: ValuationMethod
    accrued_interest_sold: Decimal
    net_proceeds: Decimal
    sale_costs: Decimal


class GainLossCalculator:
    """
    Calcolatore di plusvalenze e minusvalenze su titoli.

    Supporta sia il costo storico sia il costo ammortizzato.

    Riferimento: OIC 20, par. 56-62.
    """

    @classmethod
    def calculate_historical_cost(
        cls,
        sale_price_clean: Decimal,
        acquisition_cost: Decimal,
        transaction_costs_buy: Decimal = Decimal("0"),
        sale_costs: Decimal = Decimal("0"),
        accrued_interest_sold: Decimal = Decimal("0"),
    ) -> GainLossResult:
        """
        Calcola plus/minusvalenza con metodo costo storico.

        Riferimento: OIC 20, par. 14-30, par. 56-62.

        Formula:
            gain_loss = (prezzo_vendita - commissioni_vendita)
                        - (costo_acquisto + commissioni_acquisto)

        Il rateo cedolare maturato e venduto NON fa parte della
        plus/minusvalenza: è classificato come interesse attivo (C.16.a).

        Args:
            sale_price_clean: prezzo di vendita corso secco
            acquisition_cost: costo di acquisto corso secco originale
            transaction_costs_buy: commissioni e oneri di acquisto
            sale_costs: commissioni e spese di vendita
            accrued_interest_sold: rateo cedolare venduto (rilevato separatamente)

        Returns:
            GainLossResult con dettaglio plus/minusvalenza.
        """
        # Valore contabile a costo storico = acquisto + oneri acquisto
        book_value: Decimal = acquisition_cost + transaction_costs_buy

        # Prezzo netto di vendita (al netto commissioni vendita)
        net_sale: Decimal = sale_price_clean - sale_costs

        # Plus/minusvalenza
        gain_loss: Decimal = net_sale - book_value

        gain_loss_type: GainLossType = cls._classify(gain_loss)

        net_proceeds: Decimal = net_sale + accrued_interest_sold

        return GainLossResult(
            sale_date=date.today(),
            sale_price=net_sale.quantize(QUANTIZE_CENTS),
            book_value=book_value.quantize(QUANTIZE_CENTS),
            gain_loss=gain_loss.quantize(QUANTIZE_CENTS),
            gain_loss_type=gain_loss_type,
            valuation_method=ValuationMethod.COSTO_STORICO,
            accrued_interest_sold=accrued_interest_sold.quantize(QUANTIZE_CENTS),
            net_proceeds=net_proceeds.quantize(QUANTIZE_CENTS),
            sale_costs=sale_costs.quantize(QUANTIZE_CENTS),
        )

    @classmethod
    def calculate_amortized_cost(
        cls,
        sale_price_clean: Decimal,
        amortized_book_value: Decimal,
        sale_costs: Decimal = Decimal("0"),
        accrued_interest_sold: Decimal = Decimal("0"),
    ) -> GainLossResult:
        """
        Calcola plus/minusvalenza con metodo costo ammortizzato.

        Riferimento: OIC 20, par. 37-55, par. 56-62.

        Formula:
            gain_loss = (prezzo_vendita - commissioni_vendita)
                        - valore_contabile_ammortizzato

        Il valore contabile ammortizzato tiene già conto dello scarto
        ammortizzato dalla data di acquisto alla data di vendita.

        Args:
            sale_price_clean: prezzo di vendita corso secco
            amortized_book_value: valore contabile a costo ammortizzato alla data
            sale_costs: commissioni e spese di vendita
            accrued_interest_sold: rateo cedolare venduto

        Returns:
            GainLossResult con dettaglio plus/minusvalenza.
        """
        net_sale: Decimal = sale_price_clean - sale_costs
        gain_loss: Decimal = net_sale - amortized_book_value

        gain_loss_type: GainLossType = cls._classify(gain_loss)

        net_proceeds: Decimal = net_sale + accrued_interest_sold

        return GainLossResult(
            sale_date=date.today(),
            sale_price=net_sale.quantize(QUANTIZE_CENTS),
            book_value=amortized_book_value.quantize(QUANTIZE_CENTS),
            gain_loss=gain_loss.quantize(QUANTIZE_CENTS),
            gain_loss_type=gain_loss_type,
            valuation_method=ValuationMethod.COSTO_AMMORTIZZATO,
            accrued_interest_sold=accrued_interest_sold.quantize(QUANTIZE_CENTS),
            net_proceeds=net_proceeds.quantize(QUANTIZE_CENTS),
            sale_costs=sale_costs.quantize(QUANTIZE_CENTS),
        )

    @classmethod
    def calculate(
        cls,
        sale_price_clean: Decimal,
        book_value: Decimal,
        valuation_method: ValuationMethod,
        sale_costs: Decimal = Decimal("0"),
        accrued_interest_sold: Decimal = Decimal("0"),
    ) -> GainLossResult:
        """
        Calcolo generico plus/minusvalenza (dispatcher).

        Riferimento: OIC 20, par. 56-62.

        Args:
            sale_price_clean: prezzo di vendita corso secco
            book_value: valore contabile (storico o ammortizzato)
            valuation_method: metodo di valutazione
            sale_costs: commissioni vendita
            accrued_interest_sold: rateo cedolare venduto

        Returns:
            GainLossResult con dettaglio.
        """
        net_sale: Decimal = sale_price_clean - sale_costs
        gain_loss: Decimal = net_sale - book_value

        gain_loss_type: GainLossType = cls._classify(gain_loss)

        net_proceeds: Decimal = net_sale + accrued_interest_sold

        return GainLossResult(
            sale_date=date.today(),
            sale_price=net_sale.quantize(QUANTIZE_CENTS),
            book_value=book_value.quantize(QUANTIZE_CENTS),
            gain_loss=gain_loss.quantize(QUANTIZE_CENTS),
            gain_loss_type=gain_loss_type,
            valuation_method=valuation_method,
            accrued_interest_sold=accrued_interest_sold.quantize(QUANTIZE_CENTS),
            net_proceeds=net_proceeds.quantize(QUANTIZE_CENTS),
            sale_costs=sale_costs.quantize(QUANTIZE_CENTS),
        )

    @staticmethod
    def _classify(gain_loss: Decimal) -> GainLossType:
        """
        Classifica la plus/minusvalenza.

        Args:
            gain_loss: importo della plus/minusvalenza

        Returns:
            GainLossType appropriato.
        """
        if gain_loss > Decimal("0"):
            return GainLossType.CAPITAL_GAIN
        elif gain_loss < Decimal("0"):
            return GainLossType.CAPITAL_LOSS
        return GainLossType.ZERO
