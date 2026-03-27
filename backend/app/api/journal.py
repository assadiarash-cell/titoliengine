"""API scritture contabili: lista, dettaglio, genera, approva, registra, quadratura."""
import uuid
from decimal import Decimal

from fastapi import APIRouter, HTTPException

from app.api.deps import DbSession
from app.schemas.journal_entry import (
    BalanceCheckResponse,
    GenerateRequest,
    GenerateResponse,
    JournalEntryRead,
)
from app.services import journal_service

router = APIRouter(prefix="/journal", tags=["journal"])


@router.get("/entries", response_model=list[JournalEntryRead])
async def list_entries(
    session: DbSession,
    client_id: uuid.UUID | None = None,
    entry_type: str | None = None,
    status: str | None = None,
    fiscal_year: int | None = None,
):
    """Lista scritture contabili con filtri."""
    entries = await journal_service.list_entries(
        session,
        client_id=client_id,
        entry_type=entry_type,
        status=status,
        fiscal_year=fiscal_year,
    )
    return entries


@router.get("/entries/{entry_id}", response_model=JournalEntryRead)
async def get_entry(entry_id: uuid.UUID, session: DbSession):
    """Dettaglio scrittura con righe dare/avere."""
    entry = await journal_service.get_entry(session, entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Scrittura non trovata")
    return entry


@router.post("/generate", response_model=GenerateResponse)
async def generate_entries(body: GenerateRequest, session: DbSession):
    """Genera scritture contabili dalle operazioni approvate.

    Chiama il motore contabile per ogni operazione approvata
    senza scrittura associata.
    """
    entries = await journal_service.generate_entries_for_transactions(
        session,
        client_id=body.client_id,
        transaction_ids=body.transaction_ids,
    )
    # Reload entries with lines
    loaded = []
    for e in entries:
        full = await journal_service.get_entry(session, e.id)
        if full:
            loaded.append(full)
    return GenerateResponse(
        entries_generated=len(loaded),
        entries=loaded,
    )


@router.post("/entries/{entry_id}/approve", response_model=JournalEntryRead)
async def approve_entry(entry_id: uuid.UUID, session: DbSession):
    """Approva una scrittura (generated → approved)."""
    entry = await journal_service.approve_entry(session, entry_id)
    if not entry:
        raise HTTPException(
            status_code=400,
            detail="Scrittura non trovata o non in stato generated",
        )
    # Reload with lines
    return await journal_service.get_entry(session, entry_id)


@router.post("/entries/{entry_id}/post", response_model=JournalEntryRead)
async def post_entry(entry_id: uuid.UUID, session: DbSession):
    """Registra definitivamente una scrittura (approved → posted)."""
    entry = await journal_service.post_entry(session, entry_id)
    if not entry:
        raise HTTPException(
            status_code=400,
            detail="Scrittura non trovata o non in stato approved",
        )
    return await journal_service.get_entry(session, entry_id)


@router.get("/balance-check", response_model=BalanceCheckResponse)
async def balance_check(client_id: uuid.UUID, session: DbSession):
    """Verifica quadratura globale dare=avere per un cliente."""
    result = await journal_service.balance_check(session, client_id)
    return BalanceCheckResponse(**result)
