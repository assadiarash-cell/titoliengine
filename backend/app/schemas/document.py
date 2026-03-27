"""Pydantic schemas per documenti sorgente."""
import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class DocumentUploadResponse(BaseModel):
    """Risposta dopo upload documento."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    client_id: uuid.UUID
    document_type: str
    bank_name: str | None = None
    original_filename: str
    file_hash: str
    parsing_status: str
    document_date: date | None = None
    uploaded_at: datetime


class DocumentRead(BaseModel):
    """Dettaglio documento completo."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    client_id: uuid.UUID
    document_type: str
    bank_name: str | None = None
    original_filename: str
    stored_path: str
    file_hash: str
    parsing_status: str
    parsed_data: dict | None = None
    parsing_confidence: Decimal | None = None
    parsing_errors: dict | None = None
    document_date: date | None = None
    bank_reference: str | None = None
    uploaded_by: uuid.UUID | None = None
    uploaded_at: datetime
    reviewed_by: uuid.UUID | None = None
    reviewed_at: datetime | None = None


class DocumentListItem(BaseModel):
    """Elemento lista documenti."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    client_id: uuid.UUID
    document_type: str
    bank_name: str | None = None
    original_filename: str
    file_hash: str
    parsing_status: str
    document_date: date | None = None
    uploaded_at: datetime
