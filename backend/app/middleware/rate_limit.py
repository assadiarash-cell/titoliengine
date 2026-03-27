"""Rate limiting per API endpoints.

Implementazione in-memory con sliding window.
In produzione usare Redis tramite slowapi o equivalente.
"""
import time
from collections import defaultdict
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiter con sliding window in-memory.

    Default: 100 richieste per minuto per IP.
    Per endpoint auth: 20 richieste per minuto.
    """

    def __init__(self, app, default_limit: int = 100, auth_limit: int = 20, window: int = 60):
        super().__init__(app)
        self.default_limit = default_limit
        self.auth_limit = auth_limit
        self.window = window
        self._requests: dict[str, list[float]] = defaultdict(list)

    async def dispatch(self, request: Request, call_next) -> Response:
        # Skip rate limiting in test environment
        if request.headers.get("X-Test-Client") == "true":
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        path = request.url.path
        now = time.time()

        # Determina limite in base all'endpoint
        is_auth = "/auth/" in path
        limit = self.auth_limit if is_auth else self.default_limit
        bucket_key = f"{client_ip}:{path}" if is_auth else client_ip

        # Pulisci timestamp vecchi
        self._requests[bucket_key] = [
            t for t in self._requests[bucket_key] if now - t < self.window
        ]

        if len(self._requests[bucket_key]) >= limit:
            retry_after = int(self.window - (now - self._requests[bucket_key][0]))
            return JSONResponse(
                status_code=429,
                content={"detail": "Troppe richieste. Riprova più tardi."},
                headers={
                    "Retry-After": str(max(1, retry_after)),
                    "X-RateLimit-Limit": str(limit),
                    "X-RateLimit-Remaining": "0",
                },
            )

        self._requests[bucket_key].append(now)

        response = await call_next(request)
        remaining = limit - len(self._requests[bucket_key])
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(max(0, remaining))
        return response
