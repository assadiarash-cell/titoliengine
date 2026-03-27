"""Conftest per test API — SQLite async in-memory.

Adatta modelli PostgreSQL per SQLite, fornisce fixture HTTP client.
"""
import asyncio
import uuid as uuid_mod
from collections.abc import AsyncGenerator
from datetime import datetime, timezone

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import BigInteger, Boolean, ColumnDefault, Integer, String, event
from sqlalchemy.dialects.postgresql import INET, JSONB, UUID
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.types import JSON, TypeDecorator

from app.models.base import BaseModel
import app.models  # noqa: F401


class SQLiteUUID(TypeDecorator):
    """UUID → String(36) per SQLite."""
    impl = String(36)
    cache_ok = True

    def process_bind_param(self, value, dialect):
        return str(value) if value is not None else None

    def process_result_value(self, value, dialect):
        if value is not None and not isinstance(value, uuid_mod.UUID):
            return uuid_mod.UUID(value)
        return value


def _adapt_metadata_for_sqlite():
    for table in BaseModel.metadata.tables.values():
        for column in table.columns:
            if isinstance(column.type, JSONB):
                column.type = JSON()
            elif isinstance(column.type, UUID):
                column.type = SQLiteUUID()
            elif isinstance(column.type, INET):
                column.type = String(45)
            elif isinstance(column.type, BigInteger) and column.primary_key:
                column.type = Integer()
            if column.server_default is not None:
                sd = column.server_default
                sd_text = ""
                if hasattr(sd, "arg"):
                    arg = sd.arg
                    sd_text = (arg.text if hasattr(arg, "text") else str(arg)).lower()
                if any(x in sd_text for x in ("gen_random_uuid", "uuid_generate")):
                    column.server_default = None
                elif "now()" in sd_text:
                    column.server_default = None
                    if column.default is None:
                        column.default = ColumnDefault(
                            lambda: datetime.now(timezone.utc)
                        )
                # Fix boolean server_defaults for SQLite ('true'/'false' → 1/0)
                elif isinstance(column.type, Boolean) and sd_text in ("true", "'true'"):
                    column.server_default = None
                    if column.default is None:
                        column.default = ColumnDefault(True)
                elif isinstance(column.type, Boolean) and sd_text in ("false", "'false'"):
                    column.server_default = None
                    if column.default is None:
                        column.default = ColumnDefault(False)


_adapt_metadata_for_sqlite()

# Shared session-scoped engine
_engine = None
_session_factory = None


@pytest_asyncio.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def engine():
    eng = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)

    @event.listens_for(eng.sync_engine, "connect")
    def _fk(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    async with eng.begin() as conn:
        await conn.run_sync(BaseModel.metadata.create_all)
    yield eng
    await eng.dispose()


@pytest_asyncio.fixture
async def db_session(engine) -> AsyncGenerator[AsyncSession, None]:
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as sess:
        yield sess


@pytest_asyncio.fixture
async def client(engine, db_session) -> AsyncGenerator[AsyncClient, None]:
    from app.main import app
    from app.api.deps import get_db

    async def override():
        yield db_session

    app.dependency_overrides[get_db] = override
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()
