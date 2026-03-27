"""Middleware di sicurezza per TitoliEngine.

- Security headers (equivalente Helmet.js)
- Input sanitization
- Request size limiting
"""
import time
import re
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse

# Pattern pericolosi per input sanitization
_DANGEROUS_PATTERNS = [
    re.compile(r"<script", re.IGNORECASE),
    re.compile(r"javascript:", re.IGNORECASE),
    re.compile(r"on\w+\s*=", re.IGNORECASE),
    re.compile(r"(--|;)\s*(drop|alter|delete|insert|update)\s", re.IGNORECASE),
]

MAX_BODY_SIZE = 10 * 1024 * 1024  # 10 MB


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Aggiunge security headers a ogni response.

    Equivalente di Helmet.js per Express.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains"
        )
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = (
            "camera=(), microphone=(), geolocation=()"
        )
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; img-src 'self' data:; connect-src 'self'"
        )
        return response


class InputSanitizationMiddleware(BaseHTTPMiddleware):
    """Sanitizza input per prevenire XSS e SQL injection basilari.

    Nota: questo è un layer difensivo aggiuntivo. La protezione primaria
    è fornita da SQLAlchemy (parametri bound) e Pydantic (validazione).
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        # Controlla dimensione body
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > MAX_BODY_SIZE:
            return JSONResponse(
                status_code=413,
                content={"detail": "Request body troppo grande"},
            )

        # Controlla query parameters
        for key, value in request.query_params.items():
            if _contains_dangerous_pattern(value):
                return JSONResponse(
                    status_code=400,
                    content={"detail": f"Input non valido nel parametro: {key}"},
                )

        return await call_next(request)


def _contains_dangerous_pattern(value: str) -> bool:
    """Verifica se una stringa contiene pattern potenzialmente pericolosi."""
    for pattern in _DANGEROUS_PATTERNS:
        if pattern.search(value):
            return True
    return False
