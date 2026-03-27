"""Utility per audit logging nel database."""
import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog


async def log_audit(
    session: AsyncSession,
    *,
    user_id: uuid.UUID | None = None,
    client_id: uuid.UUID | None = None,
    entity_type: str,
    entity_id: uuid.UUID,
    action: str,
    old_values: dict[str, Any] | None = None,
    new_values: dict[str, Any] | None = None,
    computation_rule: str | None = None,
    computation_params: dict[str, Any] | None = None,
    computation_result: dict[str, Any] | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> None:
    """Inserisce un record nell'audit log (append-only)."""
    entry = AuditLog(
        user_id=user_id,
        client_id=client_id,
        entity_type=entity_type,
        entity_id=entity_id,
        action=action,
        old_values=old_values,
        new_values=new_values,
        computation_rule=computation_rule,
        computation_params=computation_params,
        computation_result=computation_result,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    session.add(entry)
