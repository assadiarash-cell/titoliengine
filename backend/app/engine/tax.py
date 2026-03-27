"""
Modulo fiscale per titoli — Ritenute, regimi fiscali e test società di comodo.

Riferimenti normativi:
- Art. 44-45 TUIR: Redditi di capitale e redditi diversi
- Art. 26 D.P.R. 600/1973: Ritenute su interessi e redditi da capitale
- Art. 27 D.P.R. 600/1973: Ritenute su dividendi
- D.Lgs. 239/1996: Titoli di Stato e equiparati (aliquota 12,5%)
- Art. 30 L. 724/1994: Società di comodo (test operatività)
- D.M. 4/9/1996: White list paesi per regime agevolato

Tutti i calcoli usano decimal.Decimal, MAI float.
"""
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from enum import Enum
from typing import Optional

from .constants import (
    GOVERNMENT_SECURITY_TYPES,
    QUANTIZE_CALC,
    QUANTIZE_CENTS,
    SOCIETA_COMODO_RATES,
    SecurityType,
    TAX_RATES,
    TaxRegime,
    WHITE_LIST_COUNTRIES,
)


@dataclass
class WithholdingResult:
    """
    Risultato del calcolo ritenuta fiscale.

    Riferimento: Art. 26 D.P.R. 600/1973.

    Attributes:
        gross_amount: importo lordo soggetto a ritenuta
        tax_regime: regime fiscale applicato
        tax_rate: aliquota applicata (es. 0.1250 per 12,5%)
        withholding_tax: importo della ritenuta
        net_amount: importo netto dopo ritenuta
    """
    gross_amount: Decimal
    tax_regime: TaxRegime
    tax_rate: Decimal
    withholding_tax: Decimal
    net_amount: Decimal


class IncomeType(Enum):
    """
    Tipo di reddito ai fini fiscali.

    Riferimento: Art. 44-67 TUIR.
    """
    INTEREST = "interest"             # Interessi (reddito di capitale)
    CAPITAL_GAIN = "capital_gain"     # Plusvalenza (reddito diverso)
    DIVIDEND = "dividend"             # Dividendo (reddito di capitale)


@dataclass
class SocietaComodoResult:
    """
    Risultato del test società di comodo (art. 30 L. 724/1994).

    Attributes:
        total_assets: totale attivo patrimoniale rilevante
        minimum_revenue: ricavo minimo presunto
        actual_revenue: ricavo effettivo dichiarato
        is_comodo: True se società è di comodo (ricavi < minimo)
        details: dettaglio per categoria di attivo
    """
    total_assets: Decimal
    minimum_revenue: Decimal
    actual_revenue: Decimal
    is_comodo: bool
    details: dict


class TaxEngine:
    """
    Motore fiscale per operazioni su titoli.

    Gestisce la determinazione del regime fiscale, il calcolo
    delle ritenute e il test società di comodo.

    Riferimenti: TUIR, D.P.R. 600/1973, D.Lgs. 239/1996, L. 724/1994.
    """

    @classmethod
    def determine_regime(
        cls,
        security_type: SecurityType,
        issuer_country: str = "IT",
        is_pex: bool = False,
    ) -> TaxRegime:
        """
        Determina il regime fiscale applicabile a un titolo.

        Riferimento:
        - D.Lgs. 239/1996: titoli di Stato italiani e white list → 12,5%
        - Art. 26 D.P.R. 600/1973: altri titoli → 26%
        - Art. 87 TUIR: PEX su partecipazioni qualificate

        Args:
            security_type: tipo di titolo (BTP, BOT, CORPORATE_BOND, ecc.)
            issuer_country: codice ISO 2 del paese emittente (default: IT)
            is_pex: True se si applica la Participation Exemption

        Returns:
            TaxRegime applicabile.
        """
        # PEX ha priorità se specificato (azioni con requisiti art. 87 TUIR)
        if is_pex and security_type == SecurityType.EQUITY:
            return TaxRegime.PEX

        # Titoli di Stato italiani → sempre 12,5%
        if security_type.value in GOVERNMENT_SECURITY_TYPES:
            return TaxRegime.GOVERNMENT_12_5

        # Titoli di Stato esteri di paesi white list → 12,5%
        if (
            security_type == SecurityType.GOVERNMENT_BOND
            and issuer_country.upper() in WHITE_LIST_COUNTRIES
        ):
            return TaxRegime.GOVERNMENT_12_5

        # Titoli di Stato esteri di paesi NON white list → 26%
        if security_type == SecurityType.GOVERNMENT_BOND:
            return TaxRegime.STANDARD_26

        # Tutti gli altri titoli → 26%
        return TaxRegime.STANDARD_26

    @classmethod
    def calculate_withholding(
        cls,
        gross_amount: Decimal,
        security_type: SecurityType,
        income_type: IncomeType = IncomeType.INTEREST,
        issuer_country: str = "IT",
        is_pex: bool = False,
        regime_override: Optional[TaxRegime] = None,
    ) -> WithholdingResult:
        """
        Calcola la ritenuta fiscale su un importo lordo.

        Riferimento: Art. 26 D.P.R. 600/1973; D.Lgs. 239/1996.

        Args:
            gross_amount: importo lordo soggetto a ritenuta
            security_type: tipo di titolo
            income_type: tipo di reddito (interessi, capital gain, dividendo)
            issuer_country: codice ISO 2 del paese emittente
            is_pex: True se PEX applicabile
            regime_override: forza un regime specifico (ignora auto-detect)

        Returns:
            WithholdingResult con lordo, ritenuta e netto.
        """
        if regime_override is not None:
            regime: TaxRegime = regime_override
        else:
            regime = cls.determine_regime(
                security_type=security_type,
                issuer_country=issuer_country,
                is_pex=is_pex,
            )

        rate: Decimal = TAX_RATES[regime]
        withholding: Decimal = (gross_amount * rate).quantize(QUANTIZE_CENTS)
        net: Decimal = gross_amount - withholding

        return WithholdingResult(
            gross_amount=gross_amount,
            tax_regime=regime,
            tax_rate=rate,
            withholding_tax=withholding,
            net_amount=net,
        )

    @classmethod
    def societa_comodo_test(
        cls,
        titoli_e_crediti: Decimal,
        immobili: Decimal,
        immobili_a10: Decimal,
        altre_immobilizzazioni: Decimal,
        actual_revenue: Decimal,
    ) -> SocietaComodoResult:
        """
        Esegue il test di operatività per società di comodo.

        Riferimento: Art. 30 L. 724/1994.

        Il test confronta i ricavi effettivi con un ricavo minimo presunto,
        calcolato applicando coefficienti percentuali al valore delle attività:
        - 2% su titoli e crediti
        - 6% su immobili (5% per cat. A/10)
        - 15% su altre immobilizzazioni

        Se i ricavi effettivi sono inferiori al minimo presunto,
        la società è considerata "di comodo" (non operativa).

        Args:
            titoli_e_crediti: valore titoli e crediti in bilancio
            immobili: valore immobili (esclusi A/10)
            immobili_a10: valore immobili categoria catastale A/10
            altre_immobilizzazioni: valore altre immobilizzazioni
            actual_revenue: ricavi effettivi dell'esercizio

        Returns:
            SocietaComodoResult con esito del test e dettaglio.

        Raises:
            ValueError: se un importo è negativo.
        """
        if any(
            v < Decimal("0")
            for v in [
                titoli_e_crediti, immobili, immobili_a10,
                altre_immobilizzazioni, actual_revenue,
            ]
        ):
            raise ValueError(
                "Gli importi per il test società di comodo "
                "non possono essere negativi."
            )

        # Calcolo ricavo minimo presunto per categoria
        min_titoli: Decimal = (
            titoli_e_crediti * SOCIETA_COMODO_RATES["titoli_e_crediti"]
        ).quantize(QUANTIZE_CENTS)

        min_immobili: Decimal = (
            immobili * SOCIETA_COMODO_RATES["immobili"]
        ).quantize(QUANTIZE_CENTS)

        min_immobili_a10: Decimal = (
            immobili_a10 * SOCIETA_COMODO_RATES["immobili_a10"]
        ).quantize(QUANTIZE_CENTS)

        min_altre: Decimal = (
            altre_immobilizzazioni
            * SOCIETA_COMODO_RATES["altre_immobilizzazioni"]
        ).quantize(QUANTIZE_CENTS)

        minimum_revenue: Decimal = (
            min_titoli + min_immobili + min_immobili_a10 + min_altre
        )

        total_assets: Decimal = (
            titoli_e_crediti + immobili + immobili_a10 + altre_immobilizzazioni
        )

        is_comodo: bool = actual_revenue < minimum_revenue

        details: dict = {
            "titoli_e_crediti": {
                "valore": titoli_e_crediti,
                "coefficiente": SOCIETA_COMODO_RATES["titoli_e_crediti"],
                "ricavo_minimo": min_titoli,
            },
            "immobili": {
                "valore": immobili,
                "coefficiente": SOCIETA_COMODO_RATES["immobili"],
                "ricavo_minimo": min_immobili,
            },
            "immobili_a10": {
                "valore": immobili_a10,
                "coefficiente": SOCIETA_COMODO_RATES["immobili_a10"],
                "ricavo_minimo": min_immobili_a10,
            },
            "altre_immobilizzazioni": {
                "valore": altre_immobilizzazioni,
                "coefficiente": SOCIETA_COMODO_RATES["altre_immobilizzazioni"],
                "ricavo_minimo": min_altre,
            },
        }

        return SocietaComodoResult(
            total_assets=total_assets,
            minimum_revenue=minimum_revenue,
            actual_revenue=actual_revenue,
            is_comodo=is_comodo,
            details=details,
        )
