"""
Costanti per il motore contabile TitoliEngine.

Riferimenti normativi:
- OIC 20: Titoli di debito
- OIC 21: Partecipazioni
- OIC 32: Strumenti finanziari derivati
- Art. 2426 c.c.: Criteri di valutazione
- D.Lgs. 139/2015: Riforma bilanci
- D.M. 4/9/1996: White list paesi per regime fiscale agevolato

Tutte le aliquote e costanti sono espresse come Decimal per evitare
errori di arrotondamento nei calcoli contabili.
"""
from decimal import Decimal
from enum import Enum
from typing import FrozenSet


# ============================================================
# REGIMI FISCALI — Aliquote ritenuta su redditi da titoli
# ============================================================

class TaxRegime(Enum):
    """Regimi fiscali applicabili ai redditi da titoli."""
    GOVERNMENT_12_5 = "governo_12_5"   # Titoli di Stato e equiparati
    STANDARD_26 = "standard_26"        # Obbligazioni corporate, azioni, fondi
    PEX = "pex"                        # Participation Exemption
    EXEMPT = "esente"                  # Esente da ritenuta


# Aliquote di ritenuta per regime fiscale
TAX_RATES: dict[TaxRegime, Decimal] = {
    TaxRegime.GOVERNMENT_12_5: Decimal("0.1250"),   # 12,5%
    TaxRegime.STANDARD_26: Decimal("0.2600"),       # 26%
    TaxRegime.PEX: Decimal("0.0130"),               # 26% sul 5% = 1,3% effettivo
    TaxRegime.EXEMPT: Decimal("0"),
}


# ============================================================
# TIPI DI TITOLO
# ============================================================

class SecurityType(Enum):
    """Tipologie di titoli gestiti dal sistema."""
    BTP = "btp"                         # Buono del Tesoro Poliennale
    BOT = "bot"                         # Buono Ordinario del Tesoro
    CCT = "cct"                         # Certificato di Credito del Tesoro
    CTZ = "ctz"                         # Certificato del Tesoro Zero coupon
    CORPORATE_BOND = "corporate_bond"   # Obbligazione corporate
    GOVERNMENT_BOND = "government_bond" # Titolo di Stato estero
    EQUITY = "equity"                   # Azione
    ETF = "etf"                         # Exchange Traded Fund
    FUND = "fund"                       # Fondo comune


# Titoli di Stato italiani (ritenuta 12,5%)
GOVERNMENT_SECURITY_TYPES: FrozenSet[str] = frozenset({
    SecurityType.BTP.value,
    SecurityType.BOT.value,
    SecurityType.CCT.value,
    SecurityType.CTZ.value,
})


# ============================================================
# CONVENZIONI CALCOLO GIORNI
# ============================================================

class DayCountConventionType(Enum):
    """
    Convenzioni di calcolo giorni per interessi su titoli.

    Riferimento: OIC 20, ISDA Day Count Conventions.

    Regole di applicazione:
    - Titoli di Stato italiani (BTP, CCT): ACT/ACT (ICMA)
    - BOT/CTZ (zero coupon): ACT/360
    - Corporate bond EUR: generalmente 30/360 o ACT/ACT
    - Corporate bond USD: 30/360 (US)
    """
    ACT_ACT = "ACT/ACT"     # Actual/Actual (ICMA) — titoli di Stato
    ACT_360 = "ACT/360"     # Actual/360 — BOT, CTZ, money market
    THIRTY_360 = "30/360"   # 30/360 European — corporate bond EUR


# Mappa tipo titolo → convenzione giorni di default
DEFAULT_DAY_COUNT: dict[str, DayCountConventionType] = {
    SecurityType.BTP.value: DayCountConventionType.ACT_ACT,
    SecurityType.CCT.value: DayCountConventionType.ACT_ACT,
    SecurityType.BOT.value: DayCountConventionType.ACT_360,
    SecurityType.CTZ.value: DayCountConventionType.ACT_360,
    SecurityType.CORPORATE_BOND.value: DayCountConventionType.THIRTY_360,
    SecurityType.GOVERNMENT_BOND.value: DayCountConventionType.ACT_ACT,
}


# ============================================================
# WHITE LIST PAESI — Per regime fiscale agevolato 12,5%
# Riferimento: D.M. 4/9/1996 e successivi aggiornamenti
# ============================================================

WHITE_LIST_COUNTRIES: FrozenSet[str] = frozenset({
    "IT", "DE", "FR", "ES", "GB", "US", "JP", "CA", "AU",
    "AT", "BE", "NL", "LU", "IE", "PT", "FI", "SE", "DK",
    "NO", "CH", "NZ", "GR", "PL", "CZ", "SK", "HU", "SI",
    "HR", "EE", "LV", "LT", "CY", "MT", "RO", "BG", "IS",
})


# ============================================================
# CLASSIFICAZIONE CONTABILE
# ============================================================

class Classification(Enum):
    """Classificazione contabile dei titoli in bilancio."""
    IMMOBILIZED = "immobilized"   # Immobilizzazioni finanziarie (B.III)
    CURRENT = "current"           # Attivo circolante (C.III)


# ============================================================
# METODO DI VALUTAZIONE
# ============================================================

class ValuationMethod(Enum):
    """
    Metodo di valutazione dei titoli.

    Riferimento: OIC 20, par. 37-55 (costo ammortizzato), par. 14-30 (costo storico).
    - Costo ammortizzato: obbligatorio per bilancio ordinario (D.Lgs. 139/2015)
    - Costo storico: facoltativo per bilancio abbreviato/micro (art. 2435-bis/ter c.c.)
    """
    COSTO_AMMORTIZZATO = "costo_ammortizzato"
    COSTO_STORICO = "costo_storico"


class CostMethod(Enum):
    """Metodo di determinazione del costo per cessioni parziali."""
    COSTO_SPECIFICO = "costo_specifico"
    FIFO = "fifo"
    LIFO = "lifo"
    COSTO_MEDIO = "costo_medio"


# ============================================================
# PIANO DEI CONTI — Codici conto di default per titoli
# Riferimento: Schema civilistico art. 2424/2425 c.c.
# ============================================================

class DefaultAccounts:
    """Codici conto di default per operazioni su titoli."""

    # CONTI PATRIMONIALI ATTIVI
    SECURITIES_IMMOBILIZED = "B.III.3.a"        # Titoli di debito immobilizzati
    SECURITIES_IMMOBILIZED_FUND = "B.III.3.b"   # Fondo svalutazione (-)
    SECURITIES_CURRENT = "C.III.6"              # Titoli di debito circolante
    ACCRUED_INTEREST = "C.II.5"                 # Ratei attivi su cedole
    BANK_ACCOUNT = "C.IV.1"                     # Banca c/c

    # CONTI ECONOMICI — RICAVI
    INTEREST_INCOME = "C.16.a"                  # Interessi attivi su titoli
    TRADING_INCOME = "C.16.b"                   # Proventi da titoli (plus)
    REVERSAL_INCOME = "D.18.b"                  # Rivalutazioni immobilizzazioni

    # CONTI ECONOMICI — COSTI
    FINANCIAL_CHARGES = "C.17"                  # Interessi passivi e oneri finanziari
    IMPAIRMENT_COST = "D.19.b"                  # Svalutazioni immobilizzazioni

    # CONTI FISCALI
    WITHHOLDING_TAX = "Erario.rit"              # Erario c/ritenute subite
    STAMP_DUTY = "B.14"                         # Imposte e tasse


# ============================================================
# SOCIETÀ DI COMODO — Coefficienti test (art. 30 L. 724/1994)
# ============================================================

SOCIETA_COMODO_RATES: dict[str, Decimal] = {
    "titoli_e_crediti": Decimal("0.02"),      # 2% su titoli e crediti
    "immobili": Decimal("0.06"),              # 6% su immobili (5% per A/10)
    "immobili_a10": Decimal("0.05"),          # 5% su immobili cat. A/10
    "altre_immobilizzazioni": Decimal("0.15"), # 15% su altre immobilizzazioni
}


# ============================================================
# PRECISIONE E TOLLERANZE
# ============================================================

# Precisione per quantizzazione importi contabili (2 decimali = centesimi)
QUANTIZE_CENTS: Decimal = Decimal("0.01")

# Precisione per calcoli intermedi (10 decimali come da spec)
QUANTIZE_CALC: Decimal = Decimal("1E-10")

# Tolleranza per convergenza TIR (12 cifre)
TIR_TOLERANCE: Decimal = Decimal("1E-12")

# Massimo iterazioni Newton-Raphson per TIR
TIR_MAX_ITERATIONS: int = 1000

# Tolleranza per verifica NPV residuo dopo calcolo TIR
TIR_VERIFY_TOLERANCE: Decimal = Decimal("0.01")

# Giorni per anno (per conversione giorni → anni nei calcoli TIR)
DAYS_PER_YEAR: Decimal = Decimal("365.25")


# ============================================================
# FREQUENZE CEDOLARI
# ============================================================

class CouponFrequency(Enum):
    """Frequenza di pagamento cedole."""
    ANNUAL = 1
    SEMIANNUAL = 2
    QUARTERLY = 4
    ZERO_COUPON = 0
