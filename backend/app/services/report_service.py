"""Service layer per report contabili e fiscali.

Riferimenti:
- OIC 20, par. 81-85: Nota Integrativa
- Art. 30 L. 724/1994: Società di comodo
- TUIR Art. 44-67: Redditi da capitale e diversi
"""
import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.engine.constants import QUANTIZE_CENTS
from app.engine.tax import TaxEngine
from app.models.journal_entry import JournalEntry, JournalLine
from app.models.portfolio import PortfolioPosition
from app.models.security import Security
from app.models.transaction import Transaction
from app.models.valuation import MarketPrice, Valuation


async def portfolio_report(
    session: AsyncSession,
    *,
    client_id: uuid.UUID,
    report_date: date,
) -> dict:
    """Report portafoglio dettagliato con posizioni, valori contabili e di mercato.

    Riferimento: OIC 20, par. 81 — Composizione titoli in portafoglio.
    """
    stmt = (
        select(PortfolioPosition)
        .where(
            PortfolioPosition.client_id == client_id,
            PortfolioPosition.is_active.is_(True),
        )
    )
    result = await session.execute(stmt)
    positions = list(result.scalars().all())

    details: list[dict] = []
    total_book = Decimal("0")
    total_market = Decimal("0")
    total_unrealized = Decimal("0")
    has_market_data = False

    for pos in positions:
        sec = await session.get(Security, pos.security_id)
        if not sec:
            continue

        book_val = pos.book_value or Decimal("0")
        qty = pos.quantity or Decimal("0")
        bv_per_unit = (
            (book_val / qty * Decimal("100")).quantize(QUANTIZE_CENTS)
            if qty > 0 else Decimal("0")
        )

        # Prezzo di mercato più recente
        mp_stmt = (
            select(MarketPrice)
            .where(
                MarketPrice.security_id == pos.security_id,
                MarketPrice.price_date <= report_date,
            )
            .order_by(MarketPrice.price_date.desc())
            .limit(1)
        )
        mp_result = await session.execute(mp_stmt)
        mp = mp_result.scalars().first()

        market_price = mp.close_price if mp else None
        market_value = (
            (market_price * qty / Decimal("100")).quantize(QUANTIZE_CENTS)
            if market_price is not None else None
        )
        unrealized = (
            (market_value - book_val).quantize(QUANTIZE_CENTS)
            if market_value is not None else None
        )

        total_book += book_val
        if market_value is not None:
            has_market_data = True
            total_market += market_value
            total_unrealized += unrealized

        details.append({
            "security_id": pos.security_id,
            "isin": sec.isin,
            "name": sec.name,
            "security_type": sec.security_type,
            "classification": pos.classification or "current",
            "quantity": qty,
            "book_value": book_val,
            "book_value_per_unit": bv_per_unit,
            "market_price": market_price,
            "market_value": market_value,
            "unrealized_gain_loss": unrealized,
            "maturity_date": sec.maturity_date,
            "coupon_rate": sec.coupon_rate,
        })

    return {
        "client_id": client_id,
        "report_date": report_date,
        "total_book_value": total_book,
        "total_market_value": total_market if has_market_data else None,
        "total_unrealized_gain_loss": total_unrealized if has_market_data else None,
        "positions": details,
    }


async def gains_losses_report(
    session: AsyncSession,
    *,
    client_id: uuid.UUID,
    date_from: date,
    date_to: date,
) -> dict:
    """Report plus/minusvalenze per periodo.

    Riferimento: Art. 67-68 TUIR.
    """
    stmt = (
        select(Transaction)
        .where(
            Transaction.client_id == client_id,
            Transaction.transaction_type.in_(["sale", "maturity_redemption"]),
            Transaction.trade_date >= date_from,
            Transaction.trade_date <= date_to,
        )
        .order_by(Transaction.trade_date)
    )
    result = await session.execute(stmt)
    transactions = list(result.scalars().all())

    operations: list[dict] = []
    total_gains = Decimal("0")
    total_losses = Decimal("0")

    for txn in transactions:
        sec = await session.get(Security, txn.security_id)
        gl = txn.gain_loss or Decimal("0")
        gl_type = txn.gain_loss_type or ("capital_gain" if gl >= 0 else "capital_loss")

        if gl > 0:
            total_gains += gl
        elif gl < 0:
            total_losses += abs(gl)

        operations.append({
            "transaction_id": txn.id,
            "trade_date": txn.trade_date,
            "isin": sec.isin if sec else "N/A",
            "security_name": sec.name if sec else "N/A",
            "transaction_type": txn.transaction_type,
            "quantity": txn.quantity,
            "sale_price": txn.gross_amount,
            "book_value": txn.net_settlement_amount,
            "gain_loss": gl,
            "gain_loss_type": gl_type,
        })

    return {
        "client_id": client_id,
        "date_from": date_from,
        "date_to": date_to,
        "total_gains": total_gains.quantize(QUANTIZE_CENTS),
        "total_losses": total_losses.quantize(QUANTIZE_CENTS),
        "net_gain_loss": (total_gains - total_losses).quantize(QUANTIZE_CENTS),
        "operations": operations,
    }


async def tax_summary_report(
    session: AsyncSession,
    *,
    client_id: uuid.UUID,
    fiscal_year: int,
) -> dict:
    """Riepilogo fiscale ritenute per anno.

    Riferimento: Art. 26 D.P.R. 600/1973; D.Lgs. 239/1996.
    """
    # Transazioni con ritenute (cedole e vendite)
    stmt = (
        select(Transaction)
        .where(
            Transaction.client_id == client_id,
            func.extract("year", Transaction.trade_date) == fiscal_year,
            Transaction.withholding_tax.isnot(None),
            Transaction.withholding_tax > 0,
        )
        .order_by(Transaction.trade_date)
    )
    result = await session.execute(stmt)
    transactions = list(result.scalars().all())

    details: list[dict] = []
    total_gross_interest = Decimal("0")
    total_wh_interest = Decimal("0")
    total_gross_gains = Decimal("0")
    total_wh_gains = Decimal("0")

    for txn in transactions:
        sec = await session.get(Security, txn.security_id)
        is_interest = txn.transaction_type in ("coupon_receipt",)
        gross = txn.coupon_gross or txn.gross_amount or Decimal("0")
        wh = txn.withholding_tax or Decimal("0")
        rate = txn.withholding_tax / gross if gross > 0 else Decimal("0")

        if is_interest:
            total_gross_interest += gross
            total_wh_interest += wh
            income_type = "interest"
        else:
            total_gross_gains += gross
            total_wh_gains += wh
            income_type = "capital_gain"

        details.append({
            "transaction_id": txn.id,
            "trade_date": txn.trade_date,
            "isin": sec.isin if sec else "N/A",
            "security_name": sec.name if sec else "N/A",
            "income_type": income_type,
            "gross_amount": gross,
            "tax_regime": sec.tax_regime if sec else "standard_26",
            "tax_rate": rate.quantize(Decimal("0.0001")),
            "withholding_tax": wh,
            "net_amount": gross - wh,
        })

    return {
        "client_id": client_id,
        "fiscal_year": fiscal_year,
        "total_gross_interest": total_gross_interest.quantize(QUANTIZE_CENTS),
        "total_withholding_interest": total_wh_interest.quantize(QUANTIZE_CENTS),
        "total_gross_gains": total_gross_gains.quantize(QUANTIZE_CENTS),
        "total_withholding_gains": total_wh_gains.quantize(QUANTIZE_CENTS),
        "total_withholding": (total_wh_interest + total_wh_gains).quantize(QUANTIZE_CENTS),
        "details": details,
    }


async def oic20_nota_integrativa(
    session: AsyncSession,
    *,
    client_id: uuid.UUID,
    fiscal_year: int,
) -> dict:
    """Dati per Nota Integrativa OIC 20.

    Riferimento: OIC 20, par. 81-85.

    Informazioni richieste:
    - Criteri di valutazione adottati
    - Composizione e movimenti delle voci
    - Proventi e oneri per categoria
    - Ammortamento scarto emissione/negoziazione
    """
    # Posizioni attive
    pos_stmt = (
        select(PortfolioPosition)
        .where(
            PortfolioPosition.client_id == client_id,
            PortfolioPosition.is_active.is_(True),
        )
    )
    pos_result = await session.execute(pos_stmt)
    positions = list(pos_result.scalars().all())

    securities_data: list[dict] = []
    total_nominal = Decimal("0")
    total_book = Decimal("0")
    total_market = Decimal("0")
    has_market = False

    # Totali da scritture contabili
    total_interest = Decimal("0")
    total_amortization = Decimal("0")
    total_impairments = Decimal("0")
    total_reversals = Decimal("0")

    # Interessi da journal entries
    int_stmt = (
        select(func.coalesce(func.sum(JournalLine.credit), 0))
        .select_from(JournalLine)
        .join(JournalEntry, JournalLine.entry_id == JournalEntry.id)
        .where(
            JournalEntry.client_id == client_id,
            JournalEntry.fiscal_year == fiscal_year,
            JournalLine.account_code == "C.16.a",
        )
    )
    int_result = await session.execute(int_stmt)
    total_interest = Decimal(str(int_result.scalar() or 0))

    # Svalutazioni
    imp_stmt = (
        select(func.coalesce(func.sum(JournalLine.debit), 0))
        .select_from(JournalLine)
        .join(JournalEntry, JournalLine.entry_id == JournalEntry.id)
        .where(
            JournalEntry.client_id == client_id,
            JournalEntry.fiscal_year == fiscal_year,
            JournalLine.account_code == "D.19.b",
        )
    )
    imp_result = await session.execute(imp_stmt)
    total_impairments = Decimal(str(imp_result.scalar() or 0))

    # Ripristini
    rev_stmt = (
        select(func.coalesce(func.sum(JournalLine.credit), 0))
        .select_from(JournalLine)
        .join(JournalEntry, JournalLine.entry_id == JournalEntry.id)
        .where(
            JournalEntry.client_id == client_id,
            JournalEntry.fiscal_year == fiscal_year,
            JournalLine.account_code == "D.18.b",
        )
    )
    rev_result = await session.execute(rev_stmt)
    total_reversals = Decimal(str(rev_result.scalar() or 0))

    for pos in positions:
        sec = await session.get(Security, pos.security_id)
        if not sec:
            continue

        qty = pos.quantity or Decimal("0")
        nominal = (sec.nominal_value * qty / Decimal("100")).quantize(QUANTIZE_CENTS)
        book = pos.book_value or Decimal("0")
        total_nominal += nominal
        total_book += book

        # Prezzo mercato
        mp_stmt = (
            select(MarketPrice)
            .where(MarketPrice.security_id == sec.id)
            .order_by(MarketPrice.price_date.desc())
            .limit(1)
        )
        mp_result = await session.execute(mp_stmt)
        mp = mp_result.scalars().first()
        market_val = None
        if mp:
            has_market = True
            market_val = (mp.close_price * qty / Decimal("100")).quantize(QUANTIZE_CENTS)
            total_market += market_val

        securities_data.append({
            "isin": sec.isin,
            "name": sec.name,
            "security_type": sec.security_type,
            "classification": pos.classification or "current",
            "nominal_value": nominal,
            "book_value": book,
            "market_value": market_val,
            "amortized_cost": pos.amortized_cost,
            "effective_rate": pos.effective_interest_rate,
            "coupon_rate": sec.coupon_rate,
            "maturity_date": sec.maturity_date,
        })

    return {
        "client_id": client_id,
        "fiscal_year": fiscal_year,
        "total_nominal": total_nominal.quantize(QUANTIZE_CENTS),
        "total_book_value": total_book.quantize(QUANTIZE_CENTS),
        "total_market_value": total_market.quantize(QUANTIZE_CENTS) if has_market else None,
        "total_interest_income": total_interest.quantize(QUANTIZE_CENTS),
        "total_amortization": total_amortization.quantize(QUANTIZE_CENTS),
        "total_impairments": total_impairments.quantize(QUANTIZE_CENTS),
        "total_reversals": total_reversals.quantize(QUANTIZE_CENTS),
        "securities": securities_data,
    }
