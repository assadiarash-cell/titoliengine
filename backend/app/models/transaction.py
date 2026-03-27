"""Modello operazioni/transazioni su titoli.

Tipi: purchase, sale, coupon_receipt, maturity_redemption,
      partial_redemption, coupon_reinvestment, reclassification.

Tutti gli importi in NUMERIC(20,10).
"""
import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel, TimestampMixin, UUIDPrimaryKeyMixin

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.journal_entry import JournalEntry
    from app.models.security import Security
    from app.models.tenant import Client, User


class Transaction(UUIDPrimaryKeyMixin, TimestampMixin, BaseModel):
    """Operazione su titolo di debito.

    Riferimento: schema DB sezione 2 — tabella transactions.
    """

    __tablename__ = "transactions"

    client_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("clients.id"), nullable=False, index=True
    )
    security_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("securities.id"), nullable=False, index=True
    )
    document_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("documents.id")
    )

    # Tipo operazione
    transaction_type: Mapped[str] = mapped_column(String(30), nullable=False)

    # Date
    trade_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    settlement_date: Mapped[date] = mapped_column(Date, nullable=False)

    # Importi dal fissato bollato
    quantity: Mapped[Decimal] = mapped_column(Numeric(20, 10), nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(20, 10), nullable=False)
    gross_amount: Mapped[Decimal] = mapped_column(Numeric(20, 10), nullable=False)
    accrued_interest: Mapped[Decimal] = mapped_column(
        Numeric(20, 10), server_default="0"
    )
    tel_quel_amount: Mapped[Decimal] = mapped_column(
        Numeric(20, 10), nullable=False
    )

    # Costi di transazione
    bank_commission: Mapped[Decimal] = mapped_column(
        Numeric(20, 10), server_default="0"
    )
    stamp_duty: Mapped[Decimal] = mapped_column(
        Numeric(20, 10), server_default="0"
    )
    tobin_tax: Mapped[Decimal] = mapped_column(
        Numeric(20, 10), server_default="0"
    )
    other_costs: Mapped[Decimal] = mapped_column(
        Numeric(20, 10), server_default="0"
    )
    total_transaction_costs: Mapped[Decimal] = mapped_column(
        Numeric(20, 10), server_default="0"
    )

    # Importo effettivo movimentato in c/c
    net_settlement_amount: Mapped[Decimal] = mapped_column(
        Numeric(20, 10), nullable=False
    )

    # Per cedole
    coupon_gross: Mapped[Decimal | None] = mapped_column(Numeric(20, 10))
    withholding_tax: Mapped[Decimal | None] = mapped_column(Numeric(20, 10))
    coupon_net: Mapped[Decimal | None] = mapped_column(Numeric(20, 10))

    # Per vendite
    gain_loss: Mapped[Decimal | None] = mapped_column(Numeric(20, 10))
    gain_loss_type: Mapped[str | None] = mapped_column(String(20))

    # Valuta estera
    currency: Mapped[str] = mapped_column(String(3), server_default="EUR")
    exchange_rate: Mapped[Decimal] = mapped_column(
        Numeric(15, 8), server_default="1"
    )
    amount_eur: Mapped[Decimal | None] = mapped_column(Numeric(20, 10))

    # Status workflow
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default="draft", index=True
    )
    approved_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id")
    )
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Dati di parsing
    parsing_confidence: Mapped[Decimal | None] = mapped_column(Numeric(5, 4))
    parsing_warnings: Mapped[dict | None] = mapped_column(JSONB)
    manually_verified: Mapped[bool] = mapped_column(
        Boolean, server_default="false"
    )
    notes: Mapped[str | None] = mapped_column(Text)

    # Relationships
    client: Mapped["Client"] = relationship(back_populates="transactions")
    security: Mapped["Security"] = relationship(back_populates="transactions")
    journal_entries: Mapped[list["JournalEntry"]] = relationship(
        back_populates="transaction"
    )
