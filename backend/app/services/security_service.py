"""Service per anagrafica titoli."""
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.security import Security
from app.schemas.security import SecurityCreate, SecurityUpdate
from app.utils.audit import log_audit


async def create_security(
    session: AsyncSession, data: SecurityCreate
) -> Security:
    """Crea un nuovo titolo in anagrafica."""
    sec = Security(**data.model_dump())
    session.add(sec)
    await session.flush()
    await log_audit(
        session,
        entity_type="security",
        entity_id=sec.id,
        action="create",
        new_values=data.model_dump(mode="json"),
    )
    return sec


async def get_security(session: AsyncSession, security_id: uuid.UUID) -> Security | None:
    """Recupera un titolo per ID."""
    return await session.get(Security, security_id)


async def list_securities(
    session: AsyncSession,
    *,
    isin: str | None = None,
    security_type: str | None = None,
) -> list[Security]:
    """Lista titoli con filtri opzionali."""
    stmt = select(Security)
    if isin:
        stmt = stmt.where(Security.isin == isin)
    if security_type:
        stmt = stmt.where(Security.security_type == security_type)
    result = await session.execute(stmt.order_by(Security.name))
    return list(result.scalars().all())


async def update_security(
    session: AsyncSession, security_id: uuid.UUID, data: SecurityUpdate
) -> Security | None:
    """Aggiorna un titolo esistente."""
    sec = await session.get(Security, security_id)
    if not sec:
        return None
    updates = data.model_dump(exclude_unset=True)
    for k, v in updates.items():
        setattr(sec, k, v)
    await session.flush()
    await log_audit(
        session,
        entity_type="security",
        entity_id=sec.id,
        action="update",
        new_values=updates,
    )
    return sec


async def delete_security(session: AsyncSession, security_id: uuid.UUID) -> bool:
    """Elimina un titolo."""
    sec = await session.get(Security, security_id)
    if not sec:
        return False
    await log_audit(
        session,
        entity_type="security",
        entity_id=sec.id,
        action="delete",
    )
    await session.delete(sec)
    return True
