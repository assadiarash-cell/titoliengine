"""Schemas per anagrafica titoli."""
import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel


class SecurityCreate(BaseModel):
    isin: str
    name: str
    security_type: str
    issuer: str | None = None
    currency: str = "EUR"
    nominal_value: Decimal = Decimal("100")
    coupon_rate: Decimal | None = None
    coupon_frequency: int | None = None
    coupon_dates: list[str] | None = None
    coupon_day_count: str = "ACT/ACT"
    maturity_date: date | None = None
    issue_date: date | None = None
    issue_price: Decimal | None = None
    tax_regime: str = "standard"
    withholding_rate: Decimal = Decimal("0.2600")
    is_listed: bool = True
    market: str | None = None


class SecurityUpdate(BaseModel):
    name: str | None = None
    issuer: str | None = None
    coupon_rate: Decimal | None = None
    coupon_frequency: int | None = None
    coupon_dates: list[str] | None = None
    maturity_date: date | None = None
    tax_regime: str | None = None
    withholding_rate: Decimal | None = None
    market: str | None = None


class SecurityRead(BaseModel):
    id: uuid.UUID
    isin: str
    name: str
    security_type: str
    issuer: str | None
    currency: str
    nominal_value: Decimal
    coupon_rate: Decimal | None
    coupon_frequency: int | None
    coupon_dates: list[str] | None
    coupon_day_count: str
    maturity_date: date | None
    issue_date: date | None
    issue_price: Decimal | None
    tax_regime: str
    withholding_rate: Decimal
    is_listed: bool
    market: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
