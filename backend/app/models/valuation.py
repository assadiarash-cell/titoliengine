"""Modelli valutazione di fine esercizio e prezzi di mercato.

Valuation: valutazione di una posizione al 31/12.
MarketPrice: storico prezzi di mercato per security.
"""
import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel, UUIDPrimaryKeyMixin

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.journal_entry import JournalEntry
    from app.models.portfolio import PortfolioPosition
    from app.models.security import Security
    from app.models.tenant import Client, User


class Valuation(UUIDPrimaryKeyMixin, BaseModel):
    """Valutazione di fine esercizio per una posizione.

    Riferimento: schema DB sezione 2 — tabella valuations.
    Risultati: no_action, impairment, reversal.
    """

    __tablename__ = "valuations"

    client_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("clients.id"), nullable=False
    )
    position_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("portfolio_positions.id"), nullable=False
    )
    valuation_date: Mapped[date] = mapped_column(Date, nullable=False)
    fiscal_year: Mapped[int] = mapped_column(Integer, nullable=False)

    # Valori
    book_value: Mapped[Decimal] = mapped_column(Numeric(20, 10), nullable=False)
    market_price: Mapped[Decimal | None] = mapped_column(Numeric(20, 10))
    market_value: Mapped[Decimal | None] = mapped_column(Numeric(20, 10))
    fair_value: Mapped[Decimal | None] = mapped_column(Numeric(20, 10))

    # Risultato valutazione
    valuation_result: Mapped[str] = mapped_column(String(30), nullable=False)
    impairment_amount: Mapped[Decimal] = mapped_column(
        Numeric(20, 10), server_default="0"
    )
    reversal_amount: Mapped[Decimal] = mapped_column(
        Numeric(20, 10), server_default="0"
    )

    # Per costo ammortizzato
    amortized_cost_value: Mapped[Decimal | None] = mapped_column(Numeric(20, 10))
    amortization_for_period: Mapped[Decimal | None] = mapped_column(
        Numeric(20, 10)
    )

    # Giustificazione (per audit)
    is_durable_loss: Mapped[bool] = mapped_column(
        Boolean, server_default="false"
    )
    justification: Mapped[str | None] = mapped_column(Text)

    # Journal entry generato
    journal_entry_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("journal_entries.id")
    )

    # Status
    status: Mapped[str] = mapped_column(String(20), server_default="draft")
    approved_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id")
    )
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default="now()", nullable=False
    )

    # Relationships
    client: Mapped["Client"] = relationship(back_populates="valuations")
    position: Mapped["PortfolioPosition"] = relationship(
        back_populates="valuations"
    )


class MarketPrice(UUIDPrimaryKeyMixin, BaseModel):
    """Prezzo di mercato storico per un titolo.

    Riferimento: schema DB sezione 2 — tabella market_prices.
    """

    __tablename__ = "market_prices"

    security_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("securities.id"), nullable=False
    )
    price_date: Mapped[date] = mapped_column(Date, nullable=False)
    close_price: Mapped[Decimal] = mapped_column(
        Numeric(20, 10), nullable=False
    )
    source: Mapped[str] = mapped_column(String(50), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default="now()", nullable=False
    )

    # Relationships
    security: Mapped["Security"] = relationship(back_populates="market_prices")

    __table_args__ = (
        UniqueConstraint(
            "security_id", "price_date", "source",
            name="uq_market_price_security_date_source",
        ),
    )
