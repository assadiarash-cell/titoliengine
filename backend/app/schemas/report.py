"""Pydantic schemas per report e riepilogo fiscale."""
import uuid
from datetime import date
from decimal import Decimal

from pydantic import BaseModel


# ── Portfolio Report ─────────────────────────────────────────

class PortfolioPositionDetail(BaseModel):
    """Singola posizione nel report portafoglio."""

    security_id: uuid.UUID
    isin: str
    name: str
    security_type: str
    classification: str
    quantity: Decimal
    book_value: Decimal
    book_value_per_unit: Decimal
    market_price: Decimal | None = None
    market_value: Decimal | None = None
    unrealized_gain_loss: Decimal | None = None
    accrued_interest: Decimal | None = None
    maturity_date: date | None = None
    coupon_rate: Decimal | None = None


class PortfolioReportResponse(BaseModel):
    """Report portafoglio completo."""

    client_id: uuid.UUID
    report_date: date
    total_book_value: Decimal
    total_market_value: Decimal | None = None
    total_unrealized_gain_loss: Decimal | None = None
    positions: list[PortfolioPositionDetail]


# ── Gains/Losses Report ─────────────────────────────────────

class GainLossDetail(BaseModel):
    """Singola operazione nel report plus/minusvalenze."""

    transaction_id: uuid.UUID
    trade_date: date
    isin: str
    security_name: str
    transaction_type: str
    quantity: Decimal
    sale_price: Decimal
    book_value: Decimal
    gain_loss: Decimal
    gain_loss_type: str


class GainLossReportResponse(BaseModel):
    """Report plus/minusvalenze per periodo."""

    client_id: uuid.UUID
    date_from: date
    date_to: date
    total_gains: Decimal
    total_losses: Decimal
    net_gain_loss: Decimal
    operations: list[GainLossDetail]


# ── Tax Summary Report ───────────────────────────────────────

class WithholdingDetail(BaseModel):
    """Singola ritenuta nel riepilogo fiscale."""

    transaction_id: uuid.UUID
    trade_date: date
    isin: str
    security_name: str
    income_type: str
    gross_amount: Decimal
    tax_regime: str
    tax_rate: Decimal
    withholding_tax: Decimal
    net_amount: Decimal


class TaxSummaryResponse(BaseModel):
    """Riepilogo fiscale ritenute per periodo."""

    client_id: uuid.UUID
    fiscal_year: int
    total_gross_interest: Decimal
    total_withholding_interest: Decimal
    total_gross_gains: Decimal
    total_withholding_gains: Decimal
    total_withholding: Decimal
    details: list[WithholdingDetail]


# ── OIC 20 Nota Integrativa ──────────────────────────────────

class OIC20SecurityDetail(BaseModel):
    """Dettaglio titolo per Nota Integrativa OIC 20."""

    isin: str
    name: str
    security_type: str
    classification: str
    nominal_value: Decimal
    book_value: Decimal
    market_value: Decimal | None = None
    amortized_cost: Decimal | None = None
    effective_rate: Decimal | None = None
    coupon_rate: Decimal | None = None
    maturity_date: date | None = None
    impairment_cumulative: Decimal | None = None
    interest_income_period: Decimal | None = None
    amortization_period: Decimal | None = None


class OIC20ReportResponse(BaseModel):
    """Dati per Nota Integrativa OIC 20.

    Riferimento: OIC 20, par. 81-85 — Informazioni in nota integrativa.
    """

    client_id: uuid.UUID
    fiscal_year: int
    total_nominal: Decimal
    total_book_value: Decimal
    total_market_value: Decimal | None = None
    total_interest_income: Decimal
    total_amortization: Decimal
    total_impairments: Decimal
    total_reversals: Decimal
    securities: list[OIC20SecurityDetail]


# ── Società di Comodo ─────────────────────────────────────────

class SocietaComodoRequest(BaseModel):
    """Richiesta test società di comodo (Art. 30 L. 724/1994)."""

    titoli_e_crediti: Decimal
    immobili: Decimal
    immobili_a10: Decimal
    altre_immobilizzazioni: Decimal
    actual_revenue: Decimal


class SocietaComodoResponse(BaseModel):
    """Risultato test società di comodo."""

    total_assets: Decimal
    minimum_revenue: Decimal
    actual_revenue: Decimal
    is_comodo: bool
    details: dict
