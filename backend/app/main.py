"""TitoliEngine — FastAPI application entry point.

Motore contabile deterministico per titoli di debito.
Riferimento: OIC 20.
"""
import time
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.middleware.security import SecurityHeadersMiddleware, InputSanitizationMiddleware
from app.middleware.rate_limit import RateLimitMiddleware

logger = logging.getLogger("titoliengine")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/shutdown events."""
    logger.info("TitoliEngine v%s starting up", settings.app_version)
    yield
    logger.info("TitoliEngine shutting down")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Motore contabile deterministico per titoli di debito — OIC 20",
    lifespan=lifespan,
    docs_url="/api/docs" if settings.debug else None,
    redoc_url="/api/redoc" if settings.debug else None,
)

# ── Security middleware (ordine: ultimo aggiunto = primo eseguito) ──

# 1. CORS restrittivo
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
    expose_headers=["X-Process-Time", "X-RateLimit-Remaining"],
    max_age=600,
)

# 2. Security headers (Helmet equivalente)
app.add_middleware(SecurityHeadersMiddleware)

# 3. Input sanitization
app.add_middleware(InputSanitizationMiddleware)

# 4. Rate limiting
app.add_middleware(RateLimitMiddleware, default_limit=100, auth_limit=20, window=60)


# ── Request timing middleware ─────────────────────────────────
@app.middleware("http")
async def add_process_time(request: Request, call_next):
    """Aggiunge X-Process-Time header a ogni response."""
    start = time.perf_counter()
    response = await call_next(request)
    elapsed = time.perf_counter() - start
    response.headers["X-Process-Time"] = f"{elapsed:.4f}"
    return response


# ── Global exception handler ─────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Cattura eccezioni non gestite e restituisce 500 strutturato."""
    logger.exception("Unhandled exception: %s", exc)
    return JSONResponse(
        status_code=500,
        content={"detail": "Errore interno del server"},
    )


# ── Routes ────────────────────────────────────────────────────
from app.api.auth import router as auth_router
from app.api.tenants import router as tenants_router
from app.api.securities import router as securities_router
from app.api.transactions import router as transactions_router
from app.api.journal import router as journal_router
from app.api.documents import router as documents_router
from app.api.valuations import router as valuations_router
from app.api.reports import router as reports_router
from app.api.export import router as export_router
from app.api.audit import router as audit_router

app.include_router(auth_router, prefix="/api/v1")
app.include_router(tenants_router, prefix="/api/v1")
app.include_router(securities_router, prefix="/api/v1")
app.include_router(transactions_router, prefix="/api/v1")
app.include_router(journal_router, prefix="/api/v1")
app.include_router(documents_router, prefix="/api/v1")
app.include_router(valuations_router, prefix="/api/v1")
app.include_router(reports_router, prefix="/api/v1")
app.include_router(export_router, prefix="/api/v1")
app.include_router(audit_router, prefix="/api/v1")


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok", "version": settings.app_version}
