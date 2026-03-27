"""Service layer per gestione documenti sorgente.

Gestisce upload, deduplicazione via SHA-256, e query documenti.
"""
import hashlib
import uuid
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Document
from app.utils.audit import log_audit


async def compute_file_hash(content: bytes) -> str:
    """Calcola SHA-256 hash del contenuto file."""
    return hashlib.sha256(content).hexdigest()


async def check_duplicate(session: AsyncSession, file_hash: str) -> Document | None:
    """Verifica se esiste già un documento con lo stesso hash."""
    stmt = select(Document).where(Document.file_hash == file_hash)
    result = await session.execute(stmt)
    return result.scalars().first()


async def create_document(
    session: AsyncSession,
    *,
    client_id: uuid.UUID,
    document_type: str,
    bank_name: str | None,
    original_filename: str,
    stored_path: str,
    file_hash: str,
    document_date=None,
    uploaded_by: uuid.UUID | None = None,
) -> Document:
    """Crea record documento nel database."""
    doc = Document(
        client_id=client_id,
        document_type=document_type,
        bank_name=bank_name,
        original_filename=original_filename,
        stored_path=stored_path,
        file_hash=file_hash,
        document_date=document_date,
        uploaded_by=uploaded_by,
    )
    session.add(doc)
    await session.flush()
    await log_audit(
        session,
        client_id=client_id,
        entity_type="document",
        entity_id=doc.id,
        action="create",
        new_values={
            "document_type": document_type,
            "original_filename": original_filename,
            "file_hash": file_hash,
        },
    )
    return doc


async def get_document(session: AsyncSession, doc_id: uuid.UUID) -> Document | None:
    """Recupera documento per ID."""
    return await session.get(Document, doc_id)


async def list_documents(
    session: AsyncSession,
    *,
    client_id: uuid.UUID | None = None,
    document_type: str | None = None,
    parsing_status: str | None = None,
) -> list[Document]:
    """Lista documenti con filtri opzionali."""
    stmt = select(Document)
    if client_id:
        stmt = stmt.where(Document.client_id == client_id)
    if document_type:
        stmt = stmt.where(Document.document_type == document_type)
    if parsing_status:
        stmt = stmt.where(Document.parsing_status == parsing_status)
    stmt = stmt.order_by(Document.uploaded_at.desc())
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def update_parsing_result(
    session: AsyncSession,
    doc_id: uuid.UUID,
    *,
    parsed_data: dict | None = None,
    parsing_confidence: float | None = None,
    parsing_errors: dict | None = None,
    parsing_status: str = "completed",
) -> Document | None:
    """Aggiorna risultato parsing di un documento."""
    doc = await session.get(Document, doc_id)
    if not doc:
        return None
    doc.parsing_status = parsing_status
    if parsed_data is not None:
        doc.parsed_data = parsed_data
    if parsing_confidence is not None:
        from decimal import Decimal
        doc.parsing_confidence = Decimal(str(parsing_confidence))
    if parsing_errors is not None:
        doc.parsing_errors = parsing_errors
    await session.flush()
    return doc
