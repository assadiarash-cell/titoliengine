"""Audit log immutabile — APPEND-ONLY.

Registra ogni operazione con contesto computazionale completo.
Nessun UPDATE o DELETE permesso su questa tabella.
"""
import uuid
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import INET, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class AuditLog(BaseModel):
    """Log di audit immutabile.

    Riferimento: schema DB sezione 2 — tabella audit_log.
    Azioni: create, update, delete, approve, reject, post, reverse.
    """

    __tablename__ = "audit_log"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id")
    )
    client_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("clients.id"), index=True
    )

    # Entità modificata
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    entity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False
    )
    action: Mapped[str] = mapped_column(String(20), nullable=False)

    # Cosa è cambiato
    old_values: Mapped[dict | None] = mapped_column(JSONB)
    new_values: Mapped[dict | None] = mapped_column(JSONB)

    # Contesto computazionale
    computation_rule: Mapped[str | None] = mapped_column(String(200))
    computation_params: Mapped[dict | None] = mapped_column(JSONB)
    computation_result: Mapped[dict | None] = mapped_column(JSONB)

    # Request context
    ip_address: Mapped[str | None] = mapped_column(INET)
    user_agent: Mapped[str | None] = mapped_column(Text)

    __table_args__ = (
        {"comment": "Audit log APPEND-ONLY: no UPDATE or DELETE allowed"},
    )
