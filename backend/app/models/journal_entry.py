"""Modelli scritture contabili: JournalEntry e JournalLine.

VINCOLO CRITICO: ogni JournalEntry deve quadrare (dare = avere).
Implementato via trigger PostgreSQL check_journal_balance().
Ogni riga ha DARE oppure AVERE, mai entrambi.

Tutti gli importi in NUMERIC(20,10).
"""
import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel, TimestampMixin, UUIDPrimaryKeyMixin

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.tenant import Client, User
    from app.models.transaction import Transaction


class JournalEntry(UUIDPrimaryKeyMixin, TimestampMixin, BaseModel):
    """Scrittura contabile generata dal motore.

    Riferimento: schema DB sezione 2 — tabella journal_entries.
    Tipi: purchase_security, sale_security, coupon_receipt, maturity,
          accrual_interest, amortize_spread, impairment, reversal_impairment,
          year_end_valuation, reclassification, fx_adjustment.
    """

    __tablename__ = "journal_entries"

    client_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("clients.id"), nullable=False
    )
    transaction_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("transactions.id")
    )

    # Date
    entry_date: Mapped[date] = mapped_column(Date, nullable=False)
    competence_date: Mapped[date] = mapped_column(Date, nullable=False)

    # Descrizione
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    entry_type: Mapped[str] = mapped_column(String(50), nullable=False)

    # Riferimenti
    document_ref: Mapped[str | None] = mapped_column(String(100))
    fiscal_year: Mapped[int] = mapped_column(Integer, nullable=False)

    # Status
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default="generated"
    )
    approved_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id")
    )
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    posted_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id")
    )
    posted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Audit computazionale
    generation_rule: Mapped[str | None] = mapped_column(String(100))
    generation_params: Mapped[dict | None] = mapped_column(JSONB)

    # Relationships
    client: Mapped["Client"] = relationship(back_populates="journal_entries")
    transaction: Mapped["Transaction"] = relationship(
        back_populates="journal_entries"
    )
    lines: Mapped[list["JournalLine"]] = relationship(
        back_populates="entry", cascade="all, delete-orphan"
    )


class JournalLine(UUIDPrimaryKeyMixin, BaseModel):
    """Riga di scrittura contabile.

    Riferimento: schema DB sezione 2 — tabella journal_lines.
    VINCOLO: debit > 0 AND credit = 0 OR debit = 0 AND credit > 0.
    """

    __tablename__ = "journal_lines"

    entry_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("journal_entries.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    line_number: Mapped[int] = mapped_column(Integer, nullable=False)
    account_code: Mapped[str] = mapped_column(String(20), nullable=False)
    account_name: Mapped[str] = mapped_column(String(255), nullable=False)
    debit: Mapped[Decimal] = mapped_column(
        Numeric(20, 10), server_default="0"
    )
    credit: Mapped[Decimal] = mapped_column(
        Numeric(20, 10), server_default="0"
    )
    description: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default="now()",
        nullable=False,
    )

    # Relationships
    entry: Mapped["JournalEntry"] = relationship(back_populates="lines")

    __table_args__ = (
        CheckConstraint(
            "(debit > 0 AND credit = 0) OR (debit = 0 AND credit > 0)",
            name="chk_debit_or_credit",
        ),
    )
