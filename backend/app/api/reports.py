"""API report: portafoglio, plus/minusvalenze, riepilogo fiscale, OIC 20, società di comodo."""
import uuid
from datetime import date

from fastapi import APIRouter

from app.api.deps import DbSession
from app.engine.tax import TaxEngine
from app.schemas.report import (
    GainLossReportResponse,
    OIC20ReportResponse,
    PortfolioReportResponse,
    SocietaComodoRequest,
    SocietaComodoResponse,
    TaxSummaryResponse,
)
from app.services import report_service

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/portfolio", response_model=PortfolioReportResponse)
async def portfolio_report(
    client_id: uuid.UUID,
    session: DbSession,
    report_date: date | None = None,
):
    """Report portafoglio dettagliato con posizioni e valori.

    Riferimento: OIC 20, par. 81.
    """
    if report_date is None:
        report_date = date.today()
    result = await report_service.portfolio_report(
        session, client_id=client_id, report_date=report_date,
    )
    return result


@router.get("/gains-losses", response_model=GainLossReportResponse)
async def gains_losses_report(
    client_id: uuid.UUID,
    date_from: date,
    date_to: date,
    session: DbSession,
):
    """Report plus/minusvalenze per periodo.

    Riferimento: Art. 67-68 TUIR.
    """
    result = await report_service.gains_losses_report(
        session, client_id=client_id, date_from=date_from, date_to=date_to,
    )
    return result


@router.get("/tax-summary", response_model=TaxSummaryResponse)
async def tax_summary(
    client_id: uuid.UUID,
    fiscal_year: int,
    session: DbSession,
):
    """Riepilogo fiscale ritenute per anno.

    Riferimento: Art. 26 D.P.R. 600/1973.
    """
    result = await report_service.tax_summary_report(
        session, client_id=client_id, fiscal_year=fiscal_year,
    )
    return result


@router.get("/oic20", response_model=OIC20ReportResponse)
async def oic20_report(
    client_id: uuid.UUID,
    fiscal_year: int,
    session: DbSession,
):
    """Dati per Nota Integrativa OIC 20.

    Riferimento: OIC 20, par. 81-85.
    """
    result = await report_service.oic20_nota_integrativa(
        session, client_id=client_id, fiscal_year=fiscal_year,
    )
    return result


@router.post("/societa-comodo", response_model=SocietaComodoResponse)
async def societa_comodo_test(body: SocietaComodoRequest):
    """Test società di comodo (Art. 30 L. 724/1994).

    Verifica se la società è operativa confrontando ricavi effettivi
    con ricavo minimo presunto calcolato sui coefficienti di legge.
    """
    result = TaxEngine.societa_comodo_test(
        titoli_e_crediti=body.titoli_e_crediti,
        immobili=body.immobili,
        immobili_a10=body.immobili_a10,
        altre_immobilizzazioni=body.altre_immobilizzazioni,
        actual_revenue=body.actual_revenue,
    )
    return SocietaComodoResponse(
        total_assets=result.total_assets,
        minimum_revenue=result.minimum_revenue,
        actual_revenue=result.actual_revenue,
        is_comodo=result.is_comodo,
        details=result.details,
    )
