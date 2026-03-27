"""Schemas per scritture contabili."""
import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel


class JournalLineRead(BaseModel):
    id: uuid.UUID
    line_number: int
    account_code: str
    account_name: str
    debit: Decimal
    credit: Decimal
    description: str | None

    model_config = {"from_attributes": True}


class JournalEntryRead(BaseModel):
    id: uuid.UUID
    client_id: uuid.UUID
    transaction_id: uuid.UUID | None
    entry_date: date
    competence_date: date
    description: str
    entry_type: str
    fiscal_year: int
    status: str
    generation_rule: str | None
    created_at: datetime
    lines: list[JournalLineRead] = []

    model_config = {"from_attributes": True}


class JournalEntrySummary(BaseModel):
    id: uuid.UUID
    entry_date: date
    description: str
    entry_type: str
    status: str
    total_debit: Decimal
    total_credit: Decimal

    model_config = {"from_attributes": True}


class GenerateRequest(BaseModel):
    client_id: uuid.UUID
    transaction_ids: list[uuid.UUID] | None = None


class GenerateResponse(BaseModel):
    entries_generated: int
    entries: list[JournalEntryRead]


class BalanceCheckResponse(BaseModel):
    client_id: uuid.UUID
    is_balanced: bool
    total_debit: Decimal
    total_credit: Decimal
    difference: Decimal
    entries_checked: int
