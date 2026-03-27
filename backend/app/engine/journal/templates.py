"""
Piano dei conti di default configurabile per scritture contabili su titoli.

Riferimento: Schema civilistico art. 2424/2425 c.c.

Questo modulo definisce i codici conto di default usati dal generatore
di scritture contabili. I codici possono essere personalizzati dal
tenant per adattarsi al proprio piano dei conti.

Convenzione codici:
- B.III.*  → Immobilizzazioni finanziarie (Stato Patrimoniale Attivo)
- C.III.*  → Attività finanziarie circolanti (SP Attivo)
- C.IV.*   → Disponibilità liquide (SP Attivo)
- C.II.*   → Ratei e risconti attivi (SP Attivo)
- D.*      → Ratei e risconti passivi (SP Passivo)
- C.16.*   → Proventi finanziari (Conto Economico)
- C.17.*   → Oneri finanziari (Conto Economico)
- D.18.*   → Rivalutazioni (CE)
- D.19.*   → Svalutazioni (CE)

Tutti gli importi in Decimal, MAI float.
"""
from dataclasses import dataclass, field
from typing import Dict


@dataclass
class AccountTemplate:
    """
    Template per un singolo conto contabile.

    Attributes:
        code: codice conto (es. "B.III.3.a")
        name: nome descrittivo del conto
        section: sezione di bilancio (SP_ATTIVO, SP_PASSIVO, CE_RICAVI, CE_COSTI)
    """
    code: str
    name: str
    section: str


@dataclass
class ChartOfAccounts:
    """
    Piano dei conti configurabile per operazioni su titoli.

    Riferimento: Art. 2424/2425 c.c.

    Ogni attributo è un AccountTemplate con codice e nome.
    Il tenant può sovrascrivere i valori per adattarli al proprio piano dei conti.
    """
    # ── STATO PATRIMONIALE ATTIVO ──────────────────────────────────
    # Titoli immobilizzati
    securities_immobilized: AccountTemplate = field(
        default_factory=lambda: AccountTemplate(
            code="B.III.3.a",
            name="Titoli di debito immobilizzati",
            section="SP_ATTIVO",
        )
    )
    # Fondo svalutazione titoli immobilizzati
    securities_impairment_fund: AccountTemplate = field(
        default_factory=lambda: AccountTemplate(
            code="B.III.3.a.bis",
            name="Fondo svalutazione titoli immobilizzati",
            section="SP_ATTIVO",
        )
    )
    # Titoli circolanti
    securities_current: AccountTemplate = field(
        default_factory=lambda: AccountTemplate(
            code="C.III.6",
            name="Titoli di debito circolanti",
            section="SP_ATTIVO",
        )
    )
    # Ratei attivi
    accrued_interest_asset: AccountTemplate = field(
        default_factory=lambda: AccountTemplate(
            code="D.18.d",
            name="Ratei attivi su cedole",
            section="SP_ATTIVO",
        )
    )
    # Banca c/c
    bank_account: AccountTemplate = field(
        default_factory=lambda: AccountTemplate(
            code="C.IV.1",
            name="Banca c/c",
            section="SP_ATTIVO",
        )
    )

    # ── CONTO ECONOMICO — RICAVI ──────────────────────────────────
    # Interessi attivi
    interest_income: AccountTemplate = field(
        default_factory=lambda: AccountTemplate(
            code="C.16.a",
            name="Interessi attivi su titoli",
            section="CE_RICAVI",
        )
    )
    # Plusvalenza da negoziazione
    capital_gain: AccountTemplate = field(
        default_factory=lambda: AccountTemplate(
            code="C.16.b",
            name="Plusvalenze da negoziazione titoli",
            section="CE_RICAVI",
        )
    )
    # Rivalutazione
    reversal_income: AccountTemplate = field(
        default_factory=lambda: AccountTemplate(
            code="D.18.b",
            name="Ripristino di valore titoli",
            section="CE_RICAVI",
        )
    )

    # ── CONTO ECONOMICO — COSTI ──────────────────────────────────
    # Minusvalenza da negoziazione
    capital_loss: AccountTemplate = field(
        default_factory=lambda: AccountTemplate(
            code="C.17.b",
            name="Minusvalenze da negoziazione titoli",
            section="CE_COSTI",
        )
    )
    # Oneri finanziari generici
    financial_charges: AccountTemplate = field(
        default_factory=lambda: AccountTemplate(
            code="C.17",
            name="Interessi passivi e oneri finanziari",
            section="CE_COSTI",
        )
    )
    # Svalutazione
    impairment_cost: AccountTemplate = field(
        default_factory=lambda: AccountTemplate(
            code="D.19.b",
            name="Svalutazione titoli immobilizzati",
            section="CE_COSTI",
        )
    )
    # Commissioni e spese
    transaction_costs: AccountTemplate = field(
        default_factory=lambda: AccountTemplate(
            code="B.14",
            name="Commissioni e spese bancarie",
            section="CE_COSTI",
        )
    )

    # ── CONTI FISCALI ─────────────────────────────────────────────
    # Erario c/ritenute
    withholding_tax: AccountTemplate = field(
        default_factory=lambda: AccountTemplate(
            code="C.II.5-bis",
            name="Erario c/ritenute subite",
            section="SP_ATTIVO",
        )
    )


# Istanza di default del piano dei conti
DEFAULT_CHART: ChartOfAccounts = ChartOfAccounts()
