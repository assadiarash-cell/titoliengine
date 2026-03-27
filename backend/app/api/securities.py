"""API anagrafica titoli."""
import uuid

from fastapi import APIRouter, HTTPException

from app.api.deps import DbSession
from app.schemas.security import SecurityCreate, SecurityRead, SecurityUpdate
from app.services import security_service

router = APIRouter(prefix="/securities", tags=["securities"])


@router.post("/", response_model=SecurityRead, status_code=201)
async def create_security(body: SecurityCreate, session: DbSession):
    """Crea un nuovo titolo in anagrafica."""
    sec = await security_service.create_security(session, body)
    return sec


@router.get("/", response_model=list[SecurityRead])
async def list_securities(
    session: DbSession,
    isin: str | None = None,
    security_type: str | None = None,
):
    """Lista titoli con filtri."""
    return await security_service.list_securities(
        session, isin=isin, security_type=security_type
    )


@router.get("/lookup/{isin}", response_model=SecurityRead | None)
async def lookup_isin(isin: str, session: DbSession):
    """Cerca un titolo per codice ISIN."""
    results = await security_service.list_securities(session, isin=isin)
    if not results:
        raise HTTPException(status_code=404, detail=f"ISIN {isin} non trovato")
    return results[0]


@router.get("/{security_id}", response_model=SecurityRead)
async def get_security(security_id: uuid.UUID, session: DbSession):
    """Dettaglio titolo."""
    sec = await security_service.get_security(session, security_id)
    if not sec:
        raise HTTPException(status_code=404, detail="Titolo non trovato")
    return sec


@router.put("/{security_id}", response_model=SecurityRead)
async def update_security(
    security_id: uuid.UUID, body: SecurityUpdate, session: DbSession
):
    """Aggiorna un titolo."""
    sec = await security_service.update_security(session, security_id, body)
    if not sec:
        raise HTTPException(status_code=404, detail="Titolo non trovato")
    return sec


@router.delete("/{security_id}", status_code=204)
async def delete_security(security_id: uuid.UUID, session: DbSession):
    """Elimina un titolo."""
    ok = await security_service.delete_security(session, security_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Titolo non trovato")
