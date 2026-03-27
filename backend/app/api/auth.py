"""API autenticazione: login JWT, refresh token, password bcrypt."""
from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.api.deps import DbSession
from app.models.tenant import User
from app.schemas.auth import LoginRequest, RefreshRequest, TokenResponse
from app.utils.auth import (
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_password,
)

from jose import JWTError

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, session: DbSession):
    """Autenticazione con email + password → JWT access + refresh token."""
    result = await session.execute(
        select(User).where(User.email == body.email)
    )
    user = result.scalars().first()
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenziali non valide",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Utente disabilitato",
        )
    return TokenResponse(
        access_token=create_access_token(user.id, user.studio_id),
        refresh_token=create_refresh_token(user.id),
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh(body: RefreshRequest, session: DbSession):
    """Rinnova access token tramite refresh token."""
    try:
        payload = decode_token(body.refresh_token)
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Token non valido")
        user = await session.get(User, payload["sub"])
    except (JWTError, KeyError):
        raise HTTPException(status_code=401, detail="Token non valido")

    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="Utente non trovato")

    return TokenResponse(
        access_token=create_access_token(user.id, user.studio_id),
        refresh_token=create_refresh_token(user.id),
    )
