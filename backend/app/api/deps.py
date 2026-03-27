"""Dependency injection per API routes."""
import uuid
from typing import Annotated

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.models.tenant import User
from app.utils.auth import decode_token

from jose import JWTError


async def get_db() -> AsyncSession:
    """Fornisce una sessione DB per ogni request."""
    async for session in get_session():
        yield session


async def get_current_user(
    authorization: Annotated[str | None, Header()] = None,
    session: AsyncSession = Depends(get_db),
) -> User | None:
    """Estrae l'utente corrente dal JWT token (opzionale)."""
    if not authorization or not authorization.startswith("Bearer "):
        return None
    token = authorization[7:]
    try:
        payload = decode_token(token)
        if payload.get("type") != "access":
            return None
        user_id = uuid.UUID(payload["sub"])
    except (JWTError, ValueError, KeyError):
        return None
    return await session.get(User, user_id)


async def require_auth(
    user: Annotated[User | None, Depends(get_current_user)],
) -> User:
    """Richiede autenticazione. Raise 401 se non autenticato."""
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Autenticazione richiesta",
        )
    return user


DbSession = Annotated[AsyncSession, Depends(get_db)]
CurrentUser = Annotated[User, Depends(require_auth)]
OptionalUser = Annotated[User | None, Depends(get_current_user)]
