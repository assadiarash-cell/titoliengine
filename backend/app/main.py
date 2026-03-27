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

logger = logging.getLogger("titoliengine")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/shutdown events."""
    logger.info("TitoliEngine starting up")
    yield
    logger.info("TitoliEngine shutting down")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Motore contabile deterministico per titoli di debito — OIC 20",
    lifespan=lifespan,
)

# ── CORS ──────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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

app.include_router(auth_router, prefix="/api/v1")
app.include_router(tenants_router, prefix="/api/v1")
app.include_router(securities_router, prefix="/api/v1")
app.include_router(transactions_router, prefix="/api/v1")
app.include_router(journal_router, prefix="/api/v1")


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok", "version": settings.app_version}
