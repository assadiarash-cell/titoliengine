"""Service per operazioni su titoli con workflow approvazione."""
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.transaction import Transaction
from app.schemas.transaction import TransactionCreate, TransactionUpdate
from app.utils.audit import log_audit


async def create_transaction(
    session: AsyncSession, data: TransactionCreate
) -> Transaction:
    """Crea una nuova operazione in stato draft."""
    txn = Transaction(**data.model_dump(), status="draft")
    session.add(txn)
    await session.flush()
    await log_audit(
        session,
        client_id=txn.client_id,
        entity_type="transaction",
        entity_id=txn.id,
        action="create",
        new_values=data.model_dump(mode="json"),
    )
    return txn


async def get_transaction(
    session: AsyncSession, txn_id: uuid.UUID
) -> Transaction | None:
    """Recupera un'operazione per ID."""
    return await session.get(Transaction, txn_id)


async def list_transactions(
    session: AsyncSession,
    *,
    client_id: uuid.UUID | None = None,
    security_id: uuid.UUID | None = None,
    transaction_type: str | None = None,
    status: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
) -> list[Transaction]:
    """Lista operazioni con filtri."""
    stmt = select(Transaction)
    if client_id:
        stmt = stmt.where(Transaction.client_id == client_id)
    if security_id:
        stmt = stmt.where(Transaction.security_id == security_id)
    if transaction_type:
        stmt = stmt.where(Transaction.transaction_type == transaction_type)
    if status:
        stmt = stmt.where(Transaction.status == status)
    if date_from:
        stmt = stmt.where(Transaction.trade_date >= date_from)
    if date_to:
        stmt = stmt.where(Transaction.trade_date <= date_to)
    result = await session.execute(stmt.order_by(Transaction.trade_date.desc()))
    return list(result.scalars().all())


async def update_transaction(
    session: AsyncSession, txn_id: uuid.UUID, data: TransactionUpdate
) -> Transaction | None:
    """Aggiorna un'operazione (solo se draft)."""
    txn = await session.get(Transaction, txn_id)
    if not txn or txn.status != "draft":
        return None
    updates = data.model_dump(exclude_unset=True)
    for k, v in updates.items():
        setattr(txn, k, v)
    await session.flush()
    await log_audit(
        session,
        client_id=txn.client_id,
        entity_type="transaction",
        entity_id=txn.id,
        action="update",
        new_values=updates,
    )
    return txn


async def approve_transaction(
    session: AsyncSession,
    txn_id: uuid.UUID,
    approved_by: uuid.UUID | None = None,
) -> Transaction | None:
    """Approva un'operazione (draft → approved)."""
    txn = await session.get(Transaction, txn_id)
    if not txn or txn.status != "draft":
        return None
    txn.status = "approved"
    txn.approved_by = approved_by
    txn.approved_at = datetime.now(timezone.utc)
    await session.flush()
    await log_audit(
        session,
        client_id=txn.client_id,
        entity_type="transaction",
        entity_id=txn.id,
        action="approve",
    )
    return txn


async def reject_transaction(
    session: AsyncSession, txn_id: uuid.UUID
) -> Transaction | None:
    """Rigetta un'operazione (torna a draft)."""
    txn = await session.get(Transaction, txn_id)
    if not txn or txn.status != "approved":
        return None
    txn.status = "draft"
    txn.approved_by = None
    txn.approved_at = None
    await session.flush()
    await log_audit(
        session,
        client_id=txn.client_id,
        entity_type="transaction",
        entity_id=txn.id,
        action="reject",
    )
    return txn


async def delete_transaction(session: AsyncSession, txn_id: uuid.UUID) -> bool:
    """Elimina un'operazione (solo se draft)."""
    txn = await session.get(Transaction, txn_id)
    if not txn or txn.status != "draft":
        return False
    await log_audit(
        session,
        client_id=txn.client_id,
        entity_type="transaction",
        entity_id=txn.id,
        action="delete",
    )
    await session.delete(txn)
    return True
