"""API valutazioni fine esercizio e prezzi di mercato.

Riferimento: OIC 20, par. 63-80.
"""
import uuid

from fastapi import APIRouter, HTTPException

from app.api.deps import DbSession
from app.schemas.valuation import (
    MarketPriceBulkImport,
    MarketPriceBulkResponse,
    MarketPriceCreate,
    MarketPriceRead,
    ValuationRead,
    YearEndRequest,
    YearEndResponse,
)
from app.services import valuation_service

router = APIRouter(prefix="/valuations", tags=["valuations"])


# ── Prezzi di mercato ────────────────────────────────────────

@router.post("/market-prices", response_model=MarketPriceRead, status_code=201)
async def import_market_price(body: MarketPriceCreate, session: DbSession):
    """Importa un singolo prezzo di mercato."""
    mp = await valuation_service.import_market_price(
        session,
        security_id=body.security_id,
        price_date=body.price_date,
        close_price=body.close_price,
        source=body.source,
    )
    return mp


@router.post("/market-prices/bulk", response_model=MarketPriceBulkResponse)
async def bulk_import_prices(body: MarketPriceBulkImport, session: DbSession):
    """Import massivo prezzi di mercato."""
    prices = [p.model_dump() for p in body.prices]
    result = await valuation_service.bulk_import_prices(session, prices)
    return result


# ── Valutazione fine esercizio ───────────────────────────────

@router.post("/year-end", response_model=YearEndResponse)
async def run_year_end(body: YearEndRequest, session: DbSession):
    """Lancia valutazione fine esercizio per tutti i titoli in portafoglio.

    Riferimento: OIC 20, par. 63-80.

    Per ogni posizione attiva confronta valore contabile con mercato:
    - Se market < book → genera svalutazione
    - Se market > book con svalutazione pregressa → genera ripristino
    """
    result = await valuation_service.run_year_end_valuation(
        session,
        client_id=body.client_id,
        valuation_date=body.valuation_date,
        fiscal_year=body.fiscal_year,
    )
    return result


@router.get("/", response_model=list[ValuationRead])
async def list_valuations(
    session: DbSession,
    client_id: uuid.UUID | None = None,
    fiscal_year: int | None = None,
):
    """Lista valutazioni con filtri."""
    return await valuation_service.list_valuations(
        session,
        client_id=client_id,
        fiscal_year=fiscal_year,
    )
