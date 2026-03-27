"""Service layer per valutazioni fine esercizio.

Riferimento: OIC 20, par. 63-80 — Valutazione titoli a fine esercizio.

Gestisce:
- Importazione prezzi di mercato
- Valutazione fine esercizio per tutti i titoli in portafoglio
- Generazione scritture di svalutazione/ripristino
"""
import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.portfolio import PortfolioPosition
from app.models.security import Security
from app.models.valuation import MarketPrice, Valuation
from app.engine.constants import QUANTIZE_CENTS
from app.engine.journal.impairment import ImpairmentEntryGenerator
from app.services import journal_service
from app.utils.audit import log_audit


async def import_market_price(
    session: AsyncSession,
    *,
    security_id: uuid.UUID,
    price_date: date,
    close_price: Decimal,
    source: str = "manual",
) -> MarketPrice:
    """Importa un prezzo di mercato per un titolo.

    Riferimento: OIC 20, par. 63 — Valore di mercato per confronto.
    """
    mp = MarketPrice(
        security_id=security_id,
        price_date=price_date,
        close_price=close_price,
        source=source,
    )
    session.add(mp)
    await session.flush()
    return mp


async def bulk_import_prices(
    session: AsyncSession,
    prices: list[dict],
) -> dict:
    """Import massivo prezzi di mercato.

    Returns:
        Dict con conteggi imported/skipped/errors.
    """
    imported = 0
    skipped = 0
    errors: list[str] = []

    for p in prices:
        try:
            # Controlla duplicati
            stmt = select(MarketPrice).where(
                MarketPrice.security_id == p["security_id"],
                MarketPrice.price_date == p["price_date"],
                MarketPrice.source == p.get("source", "manual"),
            )
            existing = (await session.execute(stmt)).scalars().first()
            if existing:
                skipped += 1
                continue

            await import_market_price(
                session,
                security_id=p["security_id"],
                price_date=p["price_date"],
                close_price=p["close_price"],
                source=p.get("source", "manual"),
            )
            imported += 1
        except Exception as e:
            errors.append(f"Errore per security {p.get('security_id')}: {e}")

    return {"imported": imported, "skipped": skipped, "errors": errors}


async def get_market_price(
    session: AsyncSession,
    security_id: uuid.UUID,
    price_date: date,
) -> Decimal | None:
    """Recupera il prezzo di mercato più recente fino alla data indicata.

    Riferimento: OIC 20, par. 63.
    """
    stmt = (
        select(MarketPrice)
        .where(
            MarketPrice.security_id == security_id,
            MarketPrice.price_date <= price_date,
        )
        .order_by(MarketPrice.price_date.desc())
        .limit(1)
    )
    result = await session.execute(stmt)
    mp = result.scalars().first()
    return mp.close_price if mp else None


async def run_year_end_valuation(
    session: AsyncSession,
    *,
    client_id: uuid.UUID,
    valuation_date: date,
    fiscal_year: int,
) -> dict:
    """Esegue valutazione fine esercizio per tutti i titoli in portafoglio.

    Riferimento: OIC 20, par. 63-80.

    Per ogni posizione attiva:
    1. Recupera prezzo di mercato alla data
    2. Confronta valore contabile con valore di mercato
    3. Se market < book → svalutazione (impairment)
    4. Se market > book e c'è svalutazione pregressa → ripristino (reversal)
    5. Genera scritture contabili se necessario
    """
    # Recupera tutte le posizioni attive del cliente
    stmt = (
        select(PortfolioPosition)
        .where(
            PortfolioPosition.client_id == client_id,
            PortfolioPosition.is_active.is_(True),
        )
    )
    result = await session.execute(stmt)
    positions = list(result.scalars().all())

    valuations: list[Valuation] = []
    entries_generated = 0
    impairments = 0
    reversals = 0

    for pos in positions:
        # Recupera security per descrizione
        security = await session.get(Security, pos.security_id)
        if not security:
            continue

        # Prezzo di mercato
        market_price = await get_market_price(session, pos.security_id, valuation_date)
        book_value = pos.book_value or Decimal("0")
        quantity = pos.quantity or Decimal("0")

        if quantity <= 0:
            continue

        market_value = (
            (market_price * quantity / Decimal("100")).quantize(QUANTIZE_CENTS)
            if market_price is not None
            else None
        )

        # Determina risultato valutazione
        valuation_result = "no_action"
        impairment_amount = Decimal("0")
        reversal_amount = Decimal("0")

        if market_value is not None and book_value > Decimal("0"):
            diff = market_value - book_value

            if diff < Decimal("0"):
                # Perdita di valore → svalutazione
                valuation_result = "impairment"
                impairment_amount = abs(diff).quantize(QUANTIZE_CENTS)
                impairments += 1
            elif diff > Decimal("0") and (pos.amortized_cost or Decimal("0")) > book_value:
                # Recupero valore (solo fino al costo ammortizzato originale)
                max_reversal = (pos.amortized_cost or Decimal("0")) - book_value
                reversal_amount = min(diff, max_reversal).quantize(QUANTIZE_CENTS)
                if reversal_amount > Decimal("0"):
                    valuation_result = "reversal"
                    reversals += 1

        # Crea record valutazione
        val = Valuation(
            client_id=client_id,
            position_id=pos.id,
            valuation_date=valuation_date,
            fiscal_year=fiscal_year,
            book_value=book_value,
            market_price=market_price,
            market_value=market_value,
            valuation_result=valuation_result,
            impairment_amount=impairment_amount,
            reversal_amount=reversal_amount,
            amortized_cost_value=pos.amortized_cost,
            status="generated",
        )
        session.add(val)
        await session.flush()

        # Genera scritture contabili se necessario
        if valuation_result == "impairment" and impairment_amount > Decimal("0"):
            engine_entry = ImpairmentEntryGenerator.generate_impairment(
                entry_date=valuation_date,
                security_description=f"{security.name} ({security.isin})",
                impairment_amount=impairment_amount,
            )
            db_entries = await journal_service.persist_engine_entry(
                session,
                engine_entry=engine_entry,
                client_id=client_id,
                fiscal_year=fiscal_year,
            )
            if db_entries:
                val.journal_entry_id = db_entries.id
                entries_generated += 1

        elif valuation_result == "reversal" and reversal_amount > Decimal("0"):
            engine_entry = ImpairmentEntryGenerator.generate_reversal(
                entry_date=valuation_date,
                security_description=f"{security.name} ({security.isin})",
                reversal_amount=reversal_amount,
            )
            db_entries = await journal_service.persist_engine_entry(
                session,
                engine_entry=engine_entry,
                client_id=client_id,
                fiscal_year=fiscal_year,
            )
            if db_entries:
                val.journal_entry_id = db_entries.id
                entries_generated += 1

        valuations.append(val)

        await log_audit(
            session,
            client_id=client_id,
            entity_type="valuation",
            entity_id=val.id,
            action="create",
            computation_rule="year_end_valuation_oic20",
            new_values={
                "valuation_result": valuation_result,
                "book_value": str(book_value),
                "market_value": str(market_value) if market_value else None,
                "impairment_amount": str(impairment_amount),
                "reversal_amount": str(reversal_amount),
            },
        )

    return {
        "client_id": client_id,
        "fiscal_year": fiscal_year,
        "valuation_date": valuation_date,
        "positions_evaluated": len(valuations),
        "impairments_generated": impairments,
        "reversals_generated": reversals,
        "entries_generated": entries_generated,
        "valuations": valuations,
    }


async def list_valuations(
    session: AsyncSession,
    *,
    client_id: uuid.UUID | None = None,
    fiscal_year: int | None = None,
) -> list[Valuation]:
    """Lista valutazioni con filtri."""
    stmt = select(Valuation)
    if client_id:
        stmt = stmt.where(Valuation.client_id == client_id)
    if fiscal_year:
        stmt = stmt.where(Valuation.fiscal_year == fiscal_year)
    stmt = stmt.order_by(Valuation.valuation_date.desc())
    result = await session.execute(stmt)
    return list(result.scalars().all())
