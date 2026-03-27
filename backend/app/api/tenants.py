"""API gestione clienti e piano dei conti."""
import uuid

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.api.deps import DbSession
from app.models.chart_of_accounts import ChartOfAccounts
from app.models.tenant import Client, Studio
from app.schemas.tenant import (
    AccountCreate,
    AccountRead,
    ClientCreate,
    ClientRead,
    ClientUpdate,
    StudioCreate,
    StudioRead,
    UserCreate,
    UserRead,
)
from app.models.tenant import User
from app.utils.audit import log_audit
from app.utils.auth import hash_password

router = APIRouter(prefix="/tenants", tags=["tenants"])


# ── Studios ───────────────────────────────────────────────────
@router.post("/studios", response_model=StudioRead, status_code=201)
async def create_studio(body: StudioCreate, session: DbSession):
    """Crea un nuovo studio professionale."""
    studio = Studio(**body.model_dump())
    session.add(studio)
    await session.flush()
    return studio


# ── Users ─────────────────────────────────────────────────────
@router.post("/users", response_model=UserRead, status_code=201)
async def create_user(body: UserCreate, session: DbSession):
    """Crea un nuovo utente per uno studio."""
    user = User(
        studio_id=body.studio_id,
        email=body.email,
        password_hash=hash_password(body.password),
        full_name=body.full_name,
        role=body.role,
    )
    session.add(user)
    await session.flush()
    return user


# ── Clients ───────────────────────────────────────────────────
@router.post("/clients", response_model=ClientRead, status_code=201)
async def create_client(body: ClientCreate, session: DbSession):
    """Crea un nuovo cliente."""
    client = Client(**body.model_dump())
    session.add(client)
    await session.flush()
    await log_audit(
        session,
        client_id=client.id,
        entity_type="client",
        entity_id=client.id,
        action="create",
        new_values=body.model_dump(mode="json"),
    )
    return client


@router.get("/clients", response_model=list[ClientRead])
async def list_clients(
    session: DbSession,
    studio_id: uuid.UUID | None = None,
):
    """Lista clienti con filtro opzionale per studio."""
    stmt = select(Client).where(Client.is_active.is_(True))
    if studio_id:
        stmt = stmt.where(Client.studio_id == studio_id)
    result = await session.execute(stmt.order_by(Client.name))
    return list(result.scalars().all())


@router.get("/clients/{client_id}", response_model=ClientRead)
async def get_client(client_id: uuid.UUID, session: DbSession):
    """Dettaglio cliente."""
    client = await session.get(Client, client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Cliente non trovato")
    return client


@router.put("/clients/{client_id}", response_model=ClientRead)
async def update_client(
    client_id: uuid.UUID, body: ClientUpdate, session: DbSession
):
    """Aggiorna un cliente."""
    client = await session.get(Client, client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Cliente non trovato")
    updates = body.model_dump(exclude_unset=True)
    for k, v in updates.items():
        setattr(client, k, v)
    await session.flush()
    await log_audit(
        session,
        client_id=client.id,
        entity_type="client",
        entity_id=client.id,
        action="update",
        new_values=updates,
    )
    return client


@router.delete("/clients/{client_id}", status_code=204)
async def delete_client(client_id: uuid.UUID, session: DbSession):
    """Disattiva un cliente (soft delete)."""
    client = await session.get(Client, client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Cliente non trovato")
    client.is_active = False
    await session.flush()


# ── Chart of Accounts ─────────────────────────────────────────
@router.get(
    "/clients/{client_id}/accounts",
    response_model=list[AccountRead],
)
async def list_accounts(client_id: uuid.UUID, session: DbSession):
    """Piano dei conti di un cliente."""
    stmt = (
        select(ChartOfAccounts)
        .where(ChartOfAccounts.client_id == client_id)
        .where(ChartOfAccounts.is_active.is_(True))
        .order_by(ChartOfAccounts.code)
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())


@router.post(
    "/clients/{client_id}/accounts",
    response_model=AccountRead,
    status_code=201,
)
async def create_account(
    client_id: uuid.UUID, body: AccountCreate, session: DbSession
):
    """Aggiungi un conto al piano dei conti del cliente."""
    account = ChartOfAccounts(client_id=client_id, **body.model_dump())
    session.add(account)
    await session.flush()
    return account


@router.put(
    "/clients/{client_id}/accounts/{code}",
    response_model=AccountRead,
)
async def update_account(
    client_id: uuid.UUID,
    code: str,
    body: AccountCreate,
    session: DbSession,
):
    """Aggiorna un conto nel piano dei conti."""
    stmt = (
        select(ChartOfAccounts)
        .where(ChartOfAccounts.client_id == client_id)
        .where(ChartOfAccounts.code == code)
    )
    result = await session.execute(stmt)
    account = result.scalars().first()
    if not account:
        raise HTTPException(status_code=404, detail="Conto non trovato")
    for k, v in body.model_dump().items():
        setattr(account, k, v)
    await session.flush()
    return account
