"""API gestione documenti: upload, lista, dettaglio."""
import uuid
from datetime import date
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.api.deps import DbSession
from app.config import settings
from app.schemas.document import DocumentListItem, DocumentRead, DocumentUploadResponse
from app.services import document_service

router = APIRouter(prefix="/documents", tags=["documents"])

# Directory per file uploadati (configurabile)
UPLOAD_DIR = Path(getattr(settings, "upload_dir", "uploads"))


@router.post("/upload", response_model=DocumentUploadResponse, status_code=201)
async def upload_document(
    session: DbSession,
    file: UploadFile = File(...),
    client_id: uuid.UUID = Form(...),
    document_type: str = Form("fissato_bollato"),
    bank_name: str | None = Form(None),
    document_date: date | None = Form(None),
):
    """Upload documento con deduplicazione SHA-256.

    Salva il file su disco e crea il record nel database.
    Se un file con lo stesso hash esiste già, restituisce il documento esistente.
    """
    content = await file.read()
    file_hash = await document_service.compute_file_hash(content)

    # Dedup: controlla se esiste già
    existing = await document_service.check_duplicate(session, file_hash)
    if existing:
        return existing

    # Salva file su disco con encryption at rest
    from app.middleware.encryption import encrypt_file_content

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    ext = Path(file.filename or "doc").suffix or ".pdf"
    stored_name = f"{uuid.uuid4().hex}{ext}.enc"
    stored_path = UPLOAD_DIR / stored_name
    encrypted = encrypt_file_content(content, settings.secret_key)
    stored_path.write_bytes(encrypted)

    doc = await document_service.create_document(
        session,
        client_id=client_id,
        document_type=document_type,
        bank_name=bank_name,
        original_filename=file.filename or "unknown",
        stored_path=str(stored_path),
        file_hash=file_hash,
        document_date=document_date,
    )
    return doc


@router.get("/", response_model=list[DocumentListItem])
async def list_documents(
    session: DbSession,
    client_id: uuid.UUID | None = None,
    document_type: str | None = None,
    parsing_status: str | None = None,
):
    """Lista documenti con filtri opzionali."""
    return await document_service.list_documents(
        session,
        client_id=client_id,
        document_type=document_type,
        parsing_status=parsing_status,
    )


@router.get("/{doc_id}", response_model=DocumentRead)
async def get_document(doc_id: uuid.UUID, session: DbSession):
    """Dettaglio documento."""
    doc = await document_service.get_document(session, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Documento non trovato")
    return doc
