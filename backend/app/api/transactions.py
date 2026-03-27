"""API operazioni su titoli con workflow approvazione."""
import uuid

from fastapi import APIRouter, HTTPException, Query

from app.api.deps import DbSession
from app.schemas.transaction import (
    TransactionCreate,
    TransactionRead,
    TransactionUpdate,
)
from app.services import transaction_service

router = APIRouter(prefix="/transactions", tags=["transactions"])


@router.post("/", response_model=TransactionRead, status_code=201)
async def create_transaction(body: TransactionCreate, session: DbSession):
    """Crea una nuova operazione in stato draft."""
    txn = await transaction_service.create_transaction(session, body)
    return txn


@router.get("/", response_model=list[TransactionRead])
async def list_transactions(
    session: DbSession,
    client_id: uuid.UUID | None = None,
    security_id: uuid.UUID | None = None,
    transaction_type: str | None = None,
    status: str | None = None,
    date_from: str | None = Query(None, description="YYYY-MM-DD"),
    date_to: str | None = Query(None, description="YYYY-MM-DD"),
):
    """Lista operazioni con filtri."""
    return await transaction_service.list_transactions(
        session,
        client_id=client_id,
        security_id=security_id,
        transaction_type=transaction_type,
        status=status,
        date_from=date_from,
        date_to=date_to,
    )


@router.get("/{txn_id}", response_model=TransactionRead)
async def get_transaction(txn_id: uuid.UUID, session: DbSession):
    """Dettaglio operazione."""
    txn = await transaction_service.get_transaction(session, txn_id)
    if not txn:
        raise HTTPException(status_code=404, detail="Operazione non trovata")
    return txn


@router.put("/{txn_id}", response_model=TransactionRead)
async def update_transaction(
    txn_id: uuid.UUID, body: TransactionUpdate, session: DbSession
):
    """Aggiorna un'operazione (solo se draft)."""
    txn = await transaction_service.update_transaction(session, txn_id, body)
    if not txn:
        raise HTTPException(
            status_code=400,
            detail="Operazione non trovata o non modificabile (solo draft)",
        )
    return txn


@router.post("/{txn_id}/approve", response_model=TransactionRead)
async def approve_transaction(txn_id: uuid.UUID, session: DbSession):
    """Approva un'operazione (draft → approved)."""
    txn = await transaction_service.approve_transaction(session, txn_id)
    if not txn:
        raise HTTPException(
            status_code=400,
            detail="Operazione non trovata o non in stato draft",
        )
    return txn


@router.post("/{txn_id}/reject", response_model=TransactionRead)
async def reject_transaction(txn_id: uuid.UUID, session: DbSession):
    """Rigetta un'operazione approvata (approved → draft)."""
    txn = await transaction_service.reject_transaction(session, txn_id)
    if not txn:
        raise HTTPException(
            status_code=400,
            detail="Operazione non trovata o non in stato approved",
        )
    return txn


@router.delete("/{txn_id}", status_code=204)
async def delete_transaction(txn_id: uuid.UUID, session: DbSession):
    """Elimina un'operazione (solo se draft)."""
    ok = await transaction_service.delete_transaction(session, txn_id)
    if not ok:
        raise HTTPException(
            status_code=400,
            detail="Operazione non trovata o non eliminabile (solo draft)",
        )
