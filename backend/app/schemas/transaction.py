"""Schemas per operazioni su titoli."""
import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, field_validator


class TransactionCreate(BaseModel):
    client_id: uuid.UUID
    security_id: uuid.UUID
    transaction_type: str
    trade_date: date
    settlement_date: date
    quantity: Decimal
    unit_price: Decimal
    gross_amount: Decimal
    accrued_interest: Decimal = Decimal("0")
    tel_quel_amount: Decimal
    bank_commission: Decimal = Decimal("0")
    stamp_duty: Decimal = Decimal("0")
    tobin_tax: Decimal = Decimal("0")
    other_costs: Decimal = Decimal("0")
    total_transaction_costs: Decimal = Decimal("0")
    net_settlement_amount: Decimal
    coupon_gross: Decimal | None = None
    withholding_tax: Decimal | None = None
    coupon_net: Decimal | None = None
    gain_loss: Decimal | None = None
    gain_loss_type: str | None = None
    currency: str = "EUR"
    exchange_rate: Decimal = Decimal("1")
    amount_eur: Decimal | None = None
    notes: str | None = None

    @field_validator("quantity")
    @classmethod
    def quantity_positive(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError("quantity must be > 0")
        return v

    @field_validator("unit_price")
    @classmethod
    def price_positive(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError("unit_price must be > 0")
        return v

    @field_validator("settlement_date")
    @classmethod
    def settlement_after_trade(cls, v: date, info) -> date:
        trade = info.data.get("trade_date")
        if trade and v < trade:
            raise ValueError("settlement_date must be >= trade_date")
        return v


class TransactionUpdate(BaseModel):
    trade_date: date | None = None
    settlement_date: date | None = None
    quantity: Decimal | None = None
    unit_price: Decimal | None = None
    gross_amount: Decimal | None = None
    accrued_interest: Decimal | None = None
    tel_quel_amount: Decimal | None = None
    net_settlement_amount: Decimal | None = None
    notes: str | None = None


class TransactionRead(BaseModel):
    id: uuid.UUID
    client_id: uuid.UUID
    security_id: uuid.UUID
    transaction_type: str
    trade_date: date
    settlement_date: date
    quantity: Decimal
    unit_price: Decimal
    gross_amount: Decimal
    accrued_interest: Decimal
    tel_quel_amount: Decimal
    bank_commission: Decimal
    stamp_duty: Decimal
    tobin_tax: Decimal
    other_costs: Decimal
    total_transaction_costs: Decimal
    net_settlement_amount: Decimal
    coupon_gross: Decimal | None
    withholding_tax: Decimal | None
    coupon_net: Decimal | None
    gain_loss: Decimal | None
    gain_loss_type: str | None
    currency: str
    exchange_rate: Decimal
    amount_eur: Decimal | None
    status: str
    notes: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
