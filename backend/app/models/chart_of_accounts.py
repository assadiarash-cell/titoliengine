"""Piano dei conti configurabile per cliente.

Ogni cliente ha un proprio piano dei conti che può personalizzare.
I conti standard per titoli vengono inseriti automaticamente alla creazione.
"""
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel, UUIDPrimaryKeyMixin

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.tenant import Client


class ChartOfAccounts(UUIDPrimaryKeyMixin, BaseModel):
    """Conto del piano dei conti per un cliente.

    Riferimento: schema DB sezione 2 — tabella chart_of_accounts.
    Tipi: asset, liability, equity, revenue, expense.
    """

    __tablename__ = "chart_of_accounts"

    client_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("clients.id"), nullable=False
    )
    code: Mapped[str] = mapped_column(String(20), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    account_type: Mapped[str] = mapped_column(String(20), nullable=False)
    parent_code: Mapped[str | None] = mapped_column(String(20))
    is_active: Mapped[bool] = mapped_column(Boolean, server_default="true")
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default="now()", nullable=False
    )

    # Relationships
    client: Mapped["Client"] = relationship(back_populates="chart_of_accounts")

    __table_args__ = (
        UniqueConstraint(
            "client_id", "code",
            name="uq_chart_of_accounts_client_code",
        ),
    )
