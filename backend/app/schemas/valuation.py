"""Pydantic schemas per valutazioni fine esercizio e prezzi di mercato."""
import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class MarketPriceCreate(BaseModel):
    """Importazione prezzo di mercato."""

    security_id: uuid.UUID
    price_date: date
    close_price: Decimal
    source: str = "manual"


class MarketPriceRead(BaseModel):
    """Lettura prezzo di mercato."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    security_id: uuid.UUID
    price_date: date
    close_price: Decimal
    source: str
    created_at: datetime


class MarketPriceBulkImport(BaseModel):
    """Import massivo prezzi di mercato."""

    prices: list[MarketPriceCreate]


class MarketPriceBulkResponse(BaseModel):
    """Risposta import massivo."""

    imported: int
    skipped: int
    errors: list[str]


class YearEndRequest(BaseModel):
    """Richiesta valutazione fine esercizio."""

    client_id: uuid.UUID
    valuation_date: date
    fiscal_year: int


class ValuationRead(BaseModel):
    """Lettura valutazione."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    client_id: uuid.UUID
    position_id: uuid.UUID
    valuation_date: date
    fiscal_year: int
    book_value: Decimal
    market_price: Decimal | None = None
    market_value: Decimal | None = None
    fair_value: Decimal | None = None
    valuation_result: str | None = None
    impairment_amount: Decimal | None = None
    reversal_amount: Decimal | None = None
    amortized_cost_value: Decimal | None = None
    amortization_for_period: Decimal | None = None
    is_durable_loss: bool | None = None
    justification: str | None = None
    journal_entry_id: uuid.UUID | None = None
    status: str | None = None
    created_at: datetime


class YearEndResponse(BaseModel):
    """Risposta valutazione fine esercizio."""

    client_id: uuid.UUID
    fiscal_year: int
    valuation_date: date
    positions_evaluated: int
    impairments_generated: int
    reversals_generated: int
    entries_generated: int
    valuations: list[ValuationRead]
