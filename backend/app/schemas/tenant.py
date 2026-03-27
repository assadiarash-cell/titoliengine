"""Schemas per Studio, Client, User."""
import uuid
from datetime import date, datetime

from pydantic import BaseModel


# ── Studio ────────────────────────────────────────────────────
class StudioCreate(BaseModel):
    name: str
    tax_code: str
    email: str
    phone: str | None = None
    address: str | None = None


class StudioRead(BaseModel):
    id: uuid.UUID
    name: str
    tax_code: str
    email: str
    phone: str | None
    address: str | None
    subscription_tier: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Client ────────────────────────────────────────────────────
class ClientCreate(BaseModel):
    studio_id: uuid.UUID
    name: str
    tax_code: str
    legal_form: str
    fiscal_year_start: date = date(2025, 1, 1)
    fiscal_year_end: date = date(2025, 12, 31)
    balance_type: str = "ordinario"
    valuation_method: str = "costo_ammortizzato"
    cost_method: str = "costo_specifico"


class ClientUpdate(BaseModel):
    name: str | None = None
    legal_form: str | None = None
    fiscal_year_start: date | None = None
    fiscal_year_end: date | None = None
    balance_type: str | None = None
    valuation_method: str | None = None
    cost_method: str | None = None


class ClientRead(BaseModel):
    id: uuid.UUID
    studio_id: uuid.UUID
    name: str
    tax_code: str
    legal_form: str
    fiscal_year_start: date
    fiscal_year_end: date
    balance_type: str
    valuation_method: str
    cost_method: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# ── User ──────────────────────────────────────────────────────
class UserCreate(BaseModel):
    studio_id: uuid.UUID
    email: str
    password: str
    full_name: str
    role: str = "operator"


class UserRead(BaseModel):
    id: uuid.UUID
    studio_id: uuid.UUID
    email: str
    full_name: str
    role: str
    is_active: bool
    last_login: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Chart of Accounts ─────────────────────────────────────────
class AccountCreate(BaseModel):
    code: str
    name: str
    account_type: str
    parent_code: str | None = None
    notes: str | None = None


class AccountRead(BaseModel):
    id: uuid.UUID
    client_id: uuid.UUID
    code: str
    name: str
    account_type: str
    parent_code: str | None
    is_active: bool

    model_config = {"from_attributes": True}
