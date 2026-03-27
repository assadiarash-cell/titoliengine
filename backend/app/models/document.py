"""Modello documenti sorgente (PDF uploadati).

Tipi: fissato_bollato, cedolino, estratto_conto,
      dossier_titoli, report_fiscale.
"""
import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel, UUIDPrimaryKeyMixin

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.tenant import Client, User


class Document(UUIDPrimaryKeyMixin, BaseModel):
    """Documento sorgente caricato (fissato bollato, cedolino, etc.).

    Riferimento: schema DB sezione 2 — tabella documents.
    """

    __tablename__ = "documents"

    client_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("clients.id"), nullable=False
    )
    document_type: Mapped[str] = mapped_column(String(50), nullable=False)
    bank_name: Mapped[str | None] = mapped_column(String(100))
    original_filename: Mapped[str] = mapped_column(String(500), nullable=False)
    stored_path: Mapped[str] = mapped_column(String(500), nullable=False)
    file_hash: Mapped[str] = mapped_column(String(64), nullable=False)

    # Parsing
    parsing_status: Mapped[str] = mapped_column(
        String(20), server_default="pending"
    )
    parsed_data: Mapped[dict | None] = mapped_column(JSONB)
    parsing_confidence: Mapped[Decimal | None] = mapped_column(Numeric(5, 4))
    parsing_errors: Mapped[dict | None] = mapped_column(JSONB)

    # Metadata
    document_date: Mapped[date | None] = mapped_column(Date)
    bank_reference: Mapped[str | None] = mapped_column(String(100))

    # Upload / review
    uploaded_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id")
    )
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default="now()", nullable=False
    )
    reviewed_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id")
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Relationships
    client: Mapped["Client"] = relationship(back_populates="documents")
