"""Modelli portafoglio: posizioni e lotti.

PortfolioPosition: posizione aggregata per client+security+classification.
PortfolioLot: singolo lotto per gestione FIFO/LIFO/costo specifico.
"""
import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Numeric, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel, TimestampMixin, UUIDPrimaryKeyMixin

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.security import Security
    from app.models.tenant import Client
    from app.models.valuation import Valuation


class PortfolioPosition(UUIDPrimaryKeyMixin, TimestampMixin, BaseModel):
    """Posizione in portafoglio per un titolo specifico.

    Riferimento: schema DB sezione 2 — tabella portfolio_positions.
    """

    __tablename__ = "portfolio_positions"

    client_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("clients.id"), nullable=False
    )
    security_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("securities.id"), nullable=False
    )

    # Classificazione contabile
    classification: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default="current"
    )

    # Posizione corrente
    quantity: Mapped[Decimal] = mapped_column(
        Numeric(20, 10), nullable=False, server_default="0"
    )

    # Valori contabili
    book_value: Mapped[Decimal] = mapped_column(
        Numeric(20, 10), nullable=False, server_default="0"
    )
    book_value_per_unit: Mapped[Decimal | None] = mapped_column(Numeric(20, 10))
    amortized_cost: Mapped[Decimal | None] = mapped_column(Numeric(20, 10))
    effective_interest_rate: Mapped[Decimal | None] = mapped_column(
        Numeric(15, 10)
    )

    # Dati acquisto
    acquisition_date: Mapped[date | None] = mapped_column(Date)
    acquisition_price: Mapped[Decimal | None] = mapped_column(Numeric(20, 10))
    acquisition_cost_total: Mapped[Decimal | None] = mapped_column(
        Numeric(20, 10)
    )

    is_active: Mapped[bool] = mapped_column(Boolean, server_default="true")

    # Relationships
    client: Mapped["Client"] = relationship(back_populates="portfolio_positions")
    security: Mapped["Security"] = relationship(
        back_populates="portfolio_positions"
    )
    lots: Mapped[list["PortfolioLot"]] = relationship(back_populates="position")
    valuations: Mapped[list["Valuation"]] = relationship(
        back_populates="position"
    )

    __table_args__ = (
        UniqueConstraint(
            "client_id", "security_id", "classification",
            name="uq_position_client_security_class",
        ),
    )


class PortfolioLot(UUIDPrimaryKeyMixin, BaseModel):
    """Singolo lotto di acquisto per gestione FIFO/LIFO/costo specifico.

    Riferimento: schema DB sezione 2 — tabella portfolio_lots.
    """

    __tablename__ = "portfolio_lots"

    position_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("portfolio_positions.id"), nullable=False
    )
    lot_date: Mapped[date] = mapped_column(Date, nullable=False)
    lot_quantity: Mapped[Decimal] = mapped_column(
        Numeric(20, 10), nullable=False
    )
    remaining_quantity: Mapped[Decimal] = mapped_column(
        Numeric(20, 10), nullable=False
    )
    unit_cost: Mapped[Decimal] = mapped_column(Numeric(20, 10), nullable=False)
    total_cost: Mapped[Decimal] = mapped_column(Numeric(20, 10), nullable=False)
    transaction_costs: Mapped[Decimal] = mapped_column(
        Numeric(20, 10), server_default="0"
    )
    effective_rate: Mapped[Decimal | None] = mapped_column(Numeric(15, 10))
    amortized_cost: Mapped[Decimal | None] = mapped_column(Numeric(20, 10))

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default="now()"
    )

    # Relationships
    position: Mapped["PortfolioPosition"] = relationship(back_populates="lots")
