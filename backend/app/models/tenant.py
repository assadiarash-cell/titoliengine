"""Modelli multi-tenancy: Studio, Client, User.

Architettura: Studio → N Client, Studio → N User.
Ogni operazione è sempre scoped a un client_id.
"""
import uuid
from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.chart_of_accounts import ChartOfAccounts
    from app.models.document import Document
    from app.models.journal_entry import JournalEntry
    from app.models.portfolio import PortfolioPosition
    from app.models.transaction import Transaction
    from app.models.valuation import Valuation


class Studio(UUIDPrimaryKeyMixin, TimestampMixin, BaseModel):
    """Studio professionale (commercialista)."""

    __tablename__ = "studios"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    tax_code: Mapped[str] = mapped_column(String(16), nullable=False, unique=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(50))
    address: Mapped[str | None] = mapped_column(Text)
    subscription_tier: Mapped[str] = mapped_column(
        String(50), server_default="standard"
    )
    is_active: Mapped[bool] = mapped_column(Boolean, server_default="true")

    # Relationships
    clients: Mapped[list["Client"]] = relationship(back_populates="studio")
    users: Mapped[list["User"]] = relationship(back_populates="studio")


class Client(UUIDPrimaryKeyMixin, TimestampMixin, BaseModel):
    """Cliente dello studio (società gestita)."""

    __tablename__ = "clients"

    studio_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("studios.id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    tax_code: Mapped[str] = mapped_column(String(16), nullable=False)
    legal_form: Mapped[str] = mapped_column(String(50), nullable=False)
    fiscal_year_start: Mapped[date] = mapped_column(
        Date, server_default="2025-01-01"
    )
    fiscal_year_end: Mapped[date] = mapped_column(
        Date, server_default="2025-12-31"
    )
    balance_type: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default="ordinario"
    )
    valuation_method: Mapped[str] = mapped_column(
        String(30), nullable=False, server_default="costo_ammortizzato"
    )
    cost_method: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default="costo_specifico"
    )
    is_active: Mapped[bool] = mapped_column(Boolean, server_default="true")

    # Relationships
    studio: Mapped["Studio"] = relationship(back_populates="clients")
    chart_of_accounts: Mapped[list["ChartOfAccounts"]] = relationship(
        back_populates="client"
    )
    portfolio_positions: Mapped[list["PortfolioPosition"]] = relationship(
        back_populates="client"
    )
    transactions: Mapped[list["Transaction"]] = relationship(
        back_populates="client"
    )
    journal_entries: Mapped[list["JournalEntry"]] = relationship(
        back_populates="client"
    )
    documents: Mapped[list["Document"]] = relationship(back_populates="client")
    valuations: Mapped[list["Valuation"]] = relationship(back_populates="client")

    __table_args__ = (
        {"comment": "Unique constraint: studio_id + tax_code"},
    )


class User(UUIDPrimaryKeyMixin, TimestampMixin, BaseModel):
    """Utente dello studio."""

    __tablename__ = "users"

    studio_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("studios.id"), nullable=False
    )
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(
        String(50), nullable=False, server_default="operator"
    )
    is_active: Mapped[bool] = mapped_column(Boolean, server_default="true")
    last_login: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Relationships
    studio: Mapped["Studio"] = relationship(back_populates="users")
