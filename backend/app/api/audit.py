"""API audit log: query filtrate e storico entità."""
import uuid
from datetime import date, datetime

from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import DbSession
from app.models.audit_log import AuditLog

router = APIRouter(prefix="/audit", tags=["audit"])


class AuditLogRead(BaseModel):
    """Schema lettura audit log."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    timestamp: datetime
    user_id: uuid.UUID | None = None
    client_id: uuid.UUID | None = None
    entity_type: str
    entity_id: uuid.UUID
    action: str
    old_values: dict | None = None
    new_values: dict | None = None
    computation_rule: str | None = None
    computation_params: dict | None = None
    computation_result: dict | None = None
    ip_address: str | None = None
    user_agent: str | None = None


@router.get("/logs", response_model=list[AuditLogRead])
async def list_audit_logs(
    session: DbSession,
    entity_type: str | None = None,
    entity_id: uuid.UUID | None = None,
    client_id: uuid.UUID | None = None,
    user_id: uuid.UUID | None = None,
    action: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    limit: int = 100,
    offset: int = 0,
):
    """Query audit log con filtri multipli.

    Supporta filtri per entità, utente, data, azione.
    Ordinamento cronologico inverso (più recenti prima).
    """
    stmt = select(AuditLog)

    if entity_type:
        stmt = stmt.where(AuditLog.entity_type == entity_type)
    if entity_id:
        stmt = stmt.where(AuditLog.entity_id == entity_id)
    if client_id:
        stmt = stmt.where(AuditLog.client_id == client_id)
    if user_id:
        stmt = stmt.where(AuditLog.user_id == user_id)
    if action:
        stmt = stmt.where(AuditLog.action == action)
    if date_from:
        stmt = stmt.where(func.date(AuditLog.timestamp) >= date_from)
    if date_to:
        stmt = stmt.where(func.date(AuditLog.timestamp) <= date_to)

    stmt = stmt.order_by(AuditLog.timestamp.desc()).limit(limit).offset(offset)
    result = await session.execute(stmt)
    return list(result.scalars().all())


@router.get("/entity/{entity_type}/{entity_id}", response_model=list[AuditLogRead])
async def entity_history(
    entity_type: str,
    entity_id: uuid.UUID,
    session: DbSession,
):
    """Storico completo di un'entità specifica.

    Restituisce tutte le operazioni effettuate su un'entità,
    ordinate cronologicamente.
    """
    stmt = (
        select(AuditLog)
        .where(
            AuditLog.entity_type == entity_type,
            AuditLog.entity_id == entity_id,
        )
        .order_by(AuditLog.timestamp.asc())
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())
