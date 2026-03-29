"""JWT token management e password hashing."""
import uuid
from datetime import datetime, timedelta, timezone

import bcrypt

try:
    from jose import jwt as jose_jwt
    _encode = jose_jwt.encode
    _decode = jose_jwt.decode
    from jose import JWTError
except ImportError:
    import jwt as pyjwt
    JWTError = pyjwt.PyJWTError  # type: ignore[assignment,misc]
    _encode = pyjwt.encode
    _decode = pyjwt.decode

from app.config import settings

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
REFRESH_TOKEN_EXPIRE_DAYS = 7


def hash_password(password: str) -> str:
    """Hash password con bcrypt."""
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    """Verifica password contro hash bcrypt."""
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def create_access_token(user_id: uuid.UUID, studio_id: uuid.UUID) -> str:
    """Crea JWT access token."""
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": str(user_id),
        "studio_id": str(studio_id),
        "exp": expire,
        "type": "access",
    }
    return _encode(payload, settings.secret_key, algorithm=ALGORITHM)


def create_refresh_token(user_id: uuid.UUID) -> str:
    """Crea JWT refresh token."""
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    payload = {
        "sub": str(user_id),
        "exp": expire,
        "type": "refresh",
    }
    return _encode(payload, settings.secret_key, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    """Decodifica e valida JWT token. Raises JWTError/PyJWTError se invalido."""
    return _decode(token, settings.secret_key, algorithms=[ALGORITHM])
