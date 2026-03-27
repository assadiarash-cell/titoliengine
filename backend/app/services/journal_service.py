"""Service per generazione e gestione scritture contabili.

Ponte tra le API e il motore contabile (app.engine.journal.*).
"""
import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.journal_entry import JournalEntry as JournalEntryModel
from app.models.journal_entry import JournalLine as JournalLineModel
from app.models.security import Security
from app.models.transaction import Transaction
from app.engine.constants import Classification, QUANTIZE_CENTS
from app.engine.journal.purchase import PurchaseEntryGenerator
from app.engine.journal.coupon import CouponEntryGenerator
from app.engine.journal.sale import SaleEntryGenerator
from app.engine.journal.maturity import MaturityEntryGenerator
from app.engine.journal.base import JournalEntry as EngineEntry
from app.utils.audit import log_audit


async def generate_entries_for_transactions(
    session: AsyncSession,
    client_id: uuid.UUID,
    transaction_ids: list[uuid.UUID] | None = None,
) -> list[JournalEntryModel]:
    """Genera scritture contabili dalle operazioni approvate.

    Per ogni operazione approvata senza scrittura associata,
    chiama il generatore appropriato del motore contabile.
    """
    stmt = (
        select(Transaction)
        .where(Transaction.client_id == client_id)
        .where(Transaction.status == "approved")
    )
    if transaction_ids:
        stmt = stmt.where(Transaction.id.in_(transaction_ids))

    result = await session.execute(stmt)
    transactions = list(result.scalars().all())

    generated: list[JournalEntryModel] = []

    for txn in transactions:
        # Controlla se esiste già una scrittura per questa operazione
        existing = await session.execute(
            select(JournalEntryModel).where(
                JournalEntryModel.transaction_id == txn.id
            )
        )
        if existing.scalars().first():
            continue

        # Genera la scrittura dal motore contabile
        engine_entry = _generate_engine_entry(txn)
        if engine_entry is None:
            continue

        # Persisti nel database
        db_entry = _persist_entry(
            engine_entry=engine_entry,
            txn=txn,
        )
        session.add(db_entry)
        await session.flush()

        await log_audit(
            session,
            client_id=client_id,
            entity_type="journal_entry",
            entity_id=db_entry.id,
            action="create",
            computation_rule=f"engine.journal.{txn.transaction_type}",
        )
        generated.append(db_entry)

    # Marca le operazioni come posted
    for txn in transactions:
        txn.status = "posted"

    return generated


def _generate_engine_entry(txn: Transaction) -> EngineEntry | None:
    """Genera una EngineEntry dal motore contabile per un tipo di operazione."""
    if txn.transaction_type == "purchase":
        return PurchaseEntryGenerator.generate_historical_cost(
            entry_date=txn.settlement_date,
            security_description=f"Acquisto {txn.security_id}",
            purchase_price_clean=txn.gross_amount,
            transaction_costs=txn.total_transaction_costs,
            accrued_interest=txn.accrued_interest,
            classification=Classification.IMMOBILIZED,
        )

    if txn.transaction_type == "sale":
        sale_costs = txn.total_transaction_costs
        accrued = txn.accrued_interest if txn.accrued_interest else Decimal("0")
        return SaleEntryGenerator.generate(
            entry_date=txn.settlement_date,
            security_description=f"Vendita {txn.security_id}",
            sale_price_clean=txn.gross_amount,
            book_value=txn.gross_amount,  # Sarà aggiornato dal portfolio service
            sale_costs=sale_costs,
            accrued_interest_sold=accrued,
        )

    if txn.transaction_type == "coupon_receipt":
        withholding = (
            txn.withholding_tax if txn.withholding_tax else Decimal("0")
        )
        coupon_gross = (
            txn.coupon_gross if txn.coupon_gross else txn.net_settlement_amount + withholding
        )
        return CouponEntryGenerator.generate(
            entry_date=txn.settlement_date,
            security_description=f"Cedola {txn.security_id}",
            coupon_gross=coupon_gross,
            withholding_tax=withholding,
            accrued_at_purchase=txn.accrued_interest if txn.accrued_interest else Decimal("0"),
        )

    if txn.transaction_type == "maturity_redemption":
        withholding = (
            txn.withholding_tax if txn.withholding_tax else Decimal("0")
        )
        return MaturityEntryGenerator.generate_zero_coupon_maturity(
            entry_date=txn.settlement_date,
            security_description=f"Scadenza {txn.security_id}",
            redemption_value=txn.gross_amount,
            purchase_cost=txn.net_settlement_amount,
            withholding_tax=withholding,
            classification=Classification.CURRENT,
        )

    return None


def _persist_entry(
    engine_entry: EngineEntry,
    txn: Transaction,
) -> JournalEntryModel:
    """Converte una EngineEntry del motore in modello DB."""
    db_entry = JournalEntryModel(
        client_id=txn.client_id,
        transaction_id=txn.id,
        entry_date=engine_entry.entry_date,
        competence_date=engine_entry.entry_date,
        description=engine_entry.description,
        entry_type=f"{txn.transaction_type}_security",
        fiscal_year=engine_entry.entry_date.year,
        status="generated",
        generation_rule=f"engine.journal.{txn.transaction_type}",
    )
    for idx, line in enumerate(engine_entry.lines, start=1):
        db_line = JournalLineModel(
            line_number=idx,
            account_code=line.account_code,
            account_name=line.account_name,
            debit=line.debit,
            credit=line.credit,
            description=line.description,
        )
        db_entry.lines.append(db_line)
    return db_entry


async def get_entry(
    session: AsyncSession, entry_id: uuid.UUID
) -> JournalEntryModel | None:
    """Recupera una scrittura con le sue righe."""
    stmt = (
        select(JournalEntryModel)
        .options(selectinload(JournalEntryModel.lines))
        .where(JournalEntryModel.id == entry_id)
    )
    result = await session.execute(stmt)
    return result.scalars().first()


async def list_entries(
    session: AsyncSession,
    *,
    client_id: uuid.UUID | None = None,
    entry_type: str | None = None,
    status: str | None = None,
    fiscal_year: int | None = None,
) -> list[JournalEntryModel]:
    """Lista scritture con filtri."""
    stmt = select(JournalEntryModel).options(
        selectinload(JournalEntryModel.lines)
    )
    if client_id:
        stmt = stmt.where(JournalEntryModel.client_id == client_id)
    if entry_type:
        stmt = stmt.where(JournalEntryModel.entry_type == entry_type)
    if status:
        stmt = stmt.where(JournalEntryModel.status == status)
    if fiscal_year:
        stmt = stmt.where(JournalEntryModel.fiscal_year == fiscal_year)
    result = await session.execute(
        stmt.order_by(JournalEntryModel.entry_date.desc())
    )
    return list(result.scalars().unique().all())


async def approve_entry(
    session: AsyncSession,
    entry_id: uuid.UUID,
    approved_by: uuid.UUID | None = None,
) -> JournalEntryModel | None:
    """Approva una scrittura (generated → approved)."""
    entry = await session.get(JournalEntryModel, entry_id)
    if not entry or entry.status != "generated":
        return None
    entry.status = "approved"
    entry.approved_by = approved_by
    entry.approved_at = datetime.now(timezone.utc)
    await session.flush()
    await log_audit(
        session,
        client_id=entry.client_id,
        entity_type="journal_entry",
        entity_id=entry.id,
        action="approve",
    )
    return entry


async def post_entry(
    session: AsyncSession,
    entry_id: uuid.UUID,
    posted_by: uuid.UUID | None = None,
) -> JournalEntryModel | None:
    """Registra definitivamente una scrittura (approved → posted)."""
    entry = await session.get(JournalEntryModel, entry_id)
    if not entry or entry.status != "approved":
        return None
    entry.status = "posted"
    entry.posted_by = posted_by
    entry.posted_at = datetime.now(timezone.utc)
    await session.flush()
    await log_audit(
        session,
        client_id=entry.client_id,
        entity_type="journal_entry",
        entity_id=entry.id,
        action="post",
    )
    return entry


async def balance_check(
    session: AsyncSession, client_id: uuid.UUID
) -> dict:
    """Verifica quadratura globale di tutte le scritture di un cliente."""
    stmt = (
        select(
            func.coalesce(func.sum(JournalLineModel.debit), 0).label("total_debit"),
            func.coalesce(func.sum(JournalLineModel.credit), 0).label("total_credit"),
            func.count(func.distinct(JournalEntryModel.id)).label("entries_count"),
        )
        .select_from(JournalLineModel)
        .join(JournalEntryModel, JournalLineModel.entry_id == JournalEntryModel.id)
        .where(JournalEntryModel.client_id == client_id)
    )
    result = await session.execute(stmt)
    row = result.one()
    total_debit = Decimal(str(row.total_debit))
    total_credit = Decimal(str(row.total_credit))
    return {
        "client_id": client_id,
        "is_balanced": total_debit == total_credit,
        "total_debit": total_debit,
        "total_credit": total_credit,
        "difference": total_debit - total_credit,
        "entries_checked": row.entries_count,
    }
