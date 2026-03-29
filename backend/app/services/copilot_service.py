"""Copilot AI service — Claude-powered FULL agent orchestrator for TitoliEngine.

Covers ALL app functionality:
- Portfolio & securities management
- Transactions (CRUD + workflow)
- Journal entries (generation, approval, posting)
- Reports (portfolio, gains/losses, tax, OIC 20)
- Valuations (year-end, market prices)
- Documents
- Audit log
- Client management
- Balance check
- Analytics & trends
"""
import json
import logging
import uuid
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation

import anthropic
from sqlalchemy import select, func, and_, extract
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import settings
from app.models.security import Security
from app.models.transaction import Transaction
from app.models.journal_entry import JournalEntry, JournalLine
from app.models.valuation import Valuation, MarketPrice
from app.models.audit_log import AuditLog
from app.models.tenant import Client, Studio, User
from app.models.portfolio import PortfolioPosition, PortfolioLot
from app.models.document import Document
from app.models.chart_of_accounts import ChartOfAccounts

from typing import AsyncIterator

logger = logging.getLogger("titoliengine.copilot")


# ── JSON serializer helper ───────────────────────────────────────────

def _json_serial(obj):
    """JSON serializer for types not serializable by default."""
    if isinstance(obj, (date, datetime)):
        return obj.isoformat()
    if isinstance(obj, Decimal):
        return str(obj)
    if isinstance(obj, uuid.UUID):
        return str(obj)
    raise TypeError(f"Type {type(obj)} not serializable")


def _dumps(obj) -> str:
    return json.dumps(obj, default=_json_serial, ensure_ascii=False)


# ── System Prompt ────────────────────────────────────────────────────

SYSTEM_PROMPT = """Sei il Copilot di TitoliEngine — un assistente AI completamente integrato nel motore contabile per titoli di debito (OIC 20).

HAI ACCESSO COMPLETO A TUTTE LE FUNZIONALITÀ DELL'APP tramite i tool disponibili. Puoi:

📊 CONSULTARE — Portafoglio, titoli, operazioni, scritture, valutazioni, documenti, audit log
📈 ANALIZZARE — Report portafoglio, plus/minusvalenze, riepilogo fiscale, nota integrativa OIC 20, trend e andamenti
✏️ AGIRE — Creare operazioni, approvare/rifiutare transazioni, generare scritture contabili, approvare/postare scritture, eseguire valutazioni di fine esercizio
📋 ESPORTARE — Dati in formato CSV/Excel per gestionali (PROFIS, TeamSystem)
🔍 SPIEGARE — Concetti OIC 20, funzionalità dell'app, significato dei dati

REGOLE:
- Rispondi SEMPRE in italiano
- Per importi usa formato italiano: 1.234,56 €
- Quando fai operazioni di scrittura, descrivi chiaramente cosa stai per fare
- Usa i tool per accedere ai dati REALI — non inventare numeri
- Per analisi temporali (settimana scorsa, ultimo mese, etc.) calcola le date corrette
- Se non trovi dati, dillo chiaramente — non assumere
- Per report complessi, usa più tool in sequenza per raccogliere tutti i dati necessari

Data odierna: {today}
"""

# ── Tool Definitions ─────────────────────────────────────────────────

TOOLS = [
    # ═══ RICERCA & CONSULTAZIONE ═══
    {
        "name": "search_securities",
        "description": "Cerca titoli nel catalogo per ISIN, nome, tipo o emittente. Restituisce dettagli completi: ISIN, nome, tipo, cedola, scadenza, emittente, regime fiscale.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Testo di ricerca: ISIN, nome, tipo (BTP, BOT, CCT, corporate), emittente"},
                "security_type": {"type": "string", "description": "Filtra per tipo specifico"},
                "limit": {"type": "integer", "description": "Max risultati (default 20)", "default": 20}
            },
            "required": ["query"]
        }
    },
    {
        "name": "get_security_detail",
        "description": "Ottieni il dettaglio completo di un singolo titolo per ID o ISIN, incluso prezzo di mercato corrente e posizioni in portafoglio.",
        "input_schema": {
            "type": "object",
            "properties": {
                "isin": {"type": "string", "description": "Codice ISIN del titolo"},
                "security_id": {"type": "string", "description": "UUID del titolo"}
            }
        }
    },
    {
        "name": "get_dashboard_stats",
        "description": "Statistiche complete della dashboard: conteggi entità, totali portafoglio, operazioni per stato, scritture per stato, andamento recente.",
        "input_schema": {
            "type": "object",
            "properties": {
                "client_id": {"type": "string", "description": "UUID cliente (opzionale)"}
            }
        }
    },

    # ═══ PORTAFOGLIO ═══
    {
        "name": "get_portfolio_positions",
        "description": "Elenco completo posizioni in portafoglio con quantità, valore contabile, costo ammortizzato, data acquisto, classificazione (attivo circolante/immobilizzato).",
        "input_schema": {
            "type": "object",
            "properties": {
                "client_id": {"type": "string", "description": "UUID cliente"},
                "active_only": {"type": "boolean", "default": True, "description": "Solo posizioni attive"}
            }
        }
    },
    {
        "name": "get_portfolio_report",
        "description": "Report portafoglio completo con confronto valore contabile vs mercato, plus/minusvalenze latenti, per una data specifica.",
        "input_schema": {
            "type": "object",
            "properties": {
                "client_id": {"type": "string", "description": "UUID cliente (obbligatorio)"},
                "report_date": {"type": "string", "format": "date", "description": "Data report (YYYY-MM-DD, default oggi)"}
            },
            "required": ["client_id"]
        }
    },

    # ═══ OPERAZIONI / TRANSAZIONI ═══
    {
        "name": "list_transactions",
        "description": "Elenca operazioni con filtri avanzati: tipo, stato, intervallo date, titolo specifico. Include importi completi, commissioni, ritenute.",
        "input_schema": {
            "type": "object",
            "properties": {
                "client_id": {"type": "string", "description": "UUID cliente"},
                "security_id": {"type": "string", "description": "UUID titolo"},
                "status": {"type": "string", "enum": ["draft", "approved", "posted"], "description": "Stato operazione"},
                "transaction_type": {"type": "string", "enum": ["purchase", "sale", "coupon_receipt", "maturity_redemption", "partial_redemption"], "description": "Tipo operazione"},
                "date_from": {"type": "string", "format": "date", "description": "Data inizio (YYYY-MM-DD)"},
                "date_to": {"type": "string", "format": "date", "description": "Data fine (YYYY-MM-DD)"},
                "limit": {"type": "integer", "default": 50}
            }
        }
    },
    {
        "name": "get_transaction_detail",
        "description": "Dettaglio completo di una singola operazione: importi, commissioni, ritenute, stato workflow, note, titolo associato.",
        "input_schema": {
            "type": "object",
            "properties": {
                "transaction_id": {"type": "string", "description": "UUID operazione"}
            },
            "required": ["transaction_id"]
        }
    },
    {
        "name": "approve_transaction",
        "description": "Approva un'operazione in stato draft. Cambia stato da draft → approved. AZIONE DI SCRITTURA.",
        "input_schema": {
            "type": "object",
            "properties": {
                "transaction_id": {"type": "string", "description": "UUID operazione da approvare"}
            },
            "required": ["transaction_id"]
        }
    },
    {
        "name": "reject_transaction",
        "description": "Rifiuta un'operazione approvata, riportandola a draft. AZIONE DI SCRITTURA.",
        "input_schema": {
            "type": "object",
            "properties": {
                "transaction_id": {"type": "string", "description": "UUID operazione da rifiutare"}
            },
            "required": ["transaction_id"]
        }
    },

    # ═══ SCRITTURE CONTABILI ═══
    {
        "name": "list_journal_entries",
        "description": "Elenca scritture contabili con filtri. Mostra righe dare/avere, conti, importi, stato.",
        "input_schema": {
            "type": "object",
            "properties": {
                "client_id": {"type": "string", "description": "UUID cliente"},
                "entry_type": {"type": "string", "description": "Tipo (purchase_security, sale_security, coupon_receipt, maturity, impairment, etc.)"},
                "status": {"type": "string", "enum": ["generated", "approved", "posted"]},
                "fiscal_year": {"type": "integer"},
                "date_from": {"type": "string", "format": "date"},
                "date_to": {"type": "string", "format": "date"},
                "limit": {"type": "integer", "default": 50}
            }
        }
    },
    {
        "name": "get_journal_entry_detail",
        "description": "Dettaglio completo di una scrittura: tutte le righe dare/avere con conti, importi, descrizione.",
        "input_schema": {
            "type": "object",
            "properties": {
                "entry_id": {"type": "string", "description": "UUID scrittura"}
            },
            "required": ["entry_id"]
        }
    },
    {
        "name": "generate_journal_entries",
        "description": "Genera scritture contabili dalle operazioni approvate. Usa il motore contabile OIC 20. AZIONE DI SCRITTURA.",
        "input_schema": {
            "type": "object",
            "properties": {
                "client_id": {"type": "string", "description": "UUID cliente (obbligatorio)"},
                "transaction_ids": {"type": "array", "items": {"type": "string"}, "description": "Lista UUID operazioni (opzionale, se vuoto genera per tutte le approvate)"}
            },
            "required": ["client_id"]
        }
    },
    {
        "name": "approve_journal_entry",
        "description": "Approva una scrittura contabile (generated → approved). AZIONE DI SCRITTURA.",
        "input_schema": {
            "type": "object",
            "properties": {
                "entry_id": {"type": "string", "description": "UUID scrittura"}
            },
            "required": ["entry_id"]
        }
    },
    {
        "name": "post_journal_entry",
        "description": "Posta una scrittura approvata nel libro giornale (approved → posted). Azione irreversibile. AZIONE DI SCRITTURA.",
        "input_schema": {
            "type": "object",
            "properties": {
                "entry_id": {"type": "string", "description": "UUID scrittura"}
            },
            "required": ["entry_id"]
        }
    },
    {
        "name": "balance_check",
        "description": "Verifica quadratura dare/avere del libro giornale per un cliente. Mostra totali e differenza.",
        "input_schema": {
            "type": "object",
            "properties": {
                "client_id": {"type": "string", "description": "UUID cliente"}
            },
            "required": ["client_id"]
        }
    },

    # ═══ REPORT & ANALISI ═══
    {
        "name": "gains_losses_report",
        "description": "Report plus/minusvalenze per un periodo. Mostra ogni vendita/scadenza con gain/loss, totali. Ideale per analisi andamenti.",
        "input_schema": {
            "type": "object",
            "properties": {
                "client_id": {"type": "string", "description": "UUID cliente"},
                "date_from": {"type": "string", "format": "date", "description": "Data inizio (YYYY-MM-DD)"},
                "date_to": {"type": "string", "format": "date", "description": "Data fine (YYYY-MM-DD)"}
            },
            "required": ["client_id", "date_from", "date_to"]
        }
    },
    {
        "name": "tax_summary_report",
        "description": "Riepilogo fiscale ritenute per anno: interessi lordi/netti, capital gain, ritenute totali per tipo.",
        "input_schema": {
            "type": "object",
            "properties": {
                "client_id": {"type": "string", "description": "UUID cliente"},
                "fiscal_year": {"type": "integer", "description": "Anno fiscale"}
            },
            "required": ["client_id", "fiscal_year"]
        }
    },
    {
        "name": "oic20_nota_integrativa",
        "description": "Genera dati per la Nota Integrativa OIC 20: composizione portafoglio, movimenti, proventi/oneri, svalutazioni/ripristini, costo ammortizzato.",
        "input_schema": {
            "type": "object",
            "properties": {
                "client_id": {"type": "string", "description": "UUID cliente"},
                "fiscal_year": {"type": "integer"}
            },
            "required": ["client_id", "fiscal_year"]
        }
    },
    {
        "name": "analyze_trends",
        "description": "Analisi andamenti e trend per periodo: volume operazioni per tipo, importi, confronto con periodo precedente, variazioni percentuali. Usa per domande tipo 'andamento settimana scorsa', 'trend ultimo mese'.",
        "input_schema": {
            "type": "object",
            "properties": {
                "date_from": {"type": "string", "format": "date", "description": "Inizio periodo analisi"},
                "date_to": {"type": "string", "format": "date", "description": "Fine periodo analisi"},
                "client_id": {"type": "string", "description": "UUID cliente (opzionale)"},
                "compare_previous": {"type": "boolean", "default": True, "description": "Confronta con periodo precedente di uguale durata"}
            },
            "required": ["date_from", "date_to"]
        }
    },

    # ═══ VALUTAZIONI ═══
    {
        "name": "list_valuations",
        "description": "Elenco valutazioni di fine esercizio con risultati: svalutazioni, ripristini, importi.",
        "input_schema": {
            "type": "object",
            "properties": {
                "client_id": {"type": "string"},
                "fiscal_year": {"type": "integer"},
                "limit": {"type": "integer", "default": 20}
            }
        }
    },
    {
        "name": "run_year_end_valuation",
        "description": "Esegui valutazione di fine esercizio: confronta valore contabile vs mercato, genera svalutazioni/ripristini e scritture. AZIONE DI SCRITTURA IMPORTANTE.",
        "input_schema": {
            "type": "object",
            "properties": {
                "client_id": {"type": "string", "description": "UUID cliente"},
                "valuation_date": {"type": "string", "format": "date", "description": "Data valutazione (es. 2025-12-31)"},
                "fiscal_year": {"type": "integer"}
            },
            "required": ["client_id", "valuation_date", "fiscal_year"]
        }
    },
    {
        "name": "get_market_prices",
        "description": "Storico prezzi di mercato per un titolo con date e fonte.",
        "input_schema": {
            "type": "object",
            "properties": {
                "security_id": {"type": "string", "description": "UUID titolo"},
                "isin": {"type": "string", "description": "ISIN titolo (alternativa a security_id)"},
                "limit": {"type": "integer", "default": 30}
            }
        }
    },

    # ═══ DOCUMENTI ═══
    {
        "name": "list_documents",
        "description": "Elenco documenti caricati: fissato bollato, cedolino, estratto conto, dossier titoli. Con stato parsing e confidenza.",
        "input_schema": {
            "type": "object",
            "properties": {
                "client_id": {"type": "string"},
                "document_type": {"type": "string", "enum": ["fissato_bollato", "cedolino", "estratto_conto", "dossier_titoli", "report_fiscale"]},
                "parsing_status": {"type": "string", "enum": ["pending", "completed", "failed"]},
                "limit": {"type": "integer", "default": 20}
            }
        }
    },

    # ═══ AUDIT LOG ═══
    {
        "name": "get_audit_log",
        "description": "Registro attività completo: chi ha fatto cosa, quando, su quale entità. Con filtri temporali e per tipo.",
        "input_schema": {
            "type": "object",
            "properties": {
                "entity_type": {"type": "string", "description": "Tipo entità (transaction, security, journal_entry, valuation, document)"},
                "action": {"type": "string", "description": "Azione (create, update, delete, approve, reject, post)"},
                "client_id": {"type": "string"},
                "date_from": {"type": "string", "format": "date"},
                "date_to": {"type": "string", "format": "date"},
                "limit": {"type": "integer", "default": 30}
            }
        }
    },

    # ═══ CLIENTI & CONFIGURAZIONE ═══
    {
        "name": "list_clients",
        "description": "Elenco clienti dello studio con configurazione: anno fiscale, metodo valutazione, forma giuridica.",
        "input_schema": {
            "type": "object",
            "properties": {
                "studio_id": {"type": "string", "description": "UUID studio (opzionale)"}
            }
        }
    },
    {
        "name": "get_chart_of_accounts",
        "description": "Piano dei conti del cliente: codice, nome, tipo conto (attivo, passivo, patrimonio, ricavo, costo).",
        "input_schema": {
            "type": "object",
            "properties": {
                "client_id": {"type": "string", "description": "UUID cliente"}
            },
            "required": ["client_id"]
        }
    },

    # ═══ NAVIGAZIONE & HELP ═══
    {
        "name": "navigate_page",
        "description": "Suggerisci all'utente di navigare verso una pagina dell'app.",
        "input_schema": {
            "type": "object",
            "properties": {
                "page": {
                    "type": "string",
                    "enum": ["dashboard", "securities", "transactions", "journal", "documents", "valuations", "reports", "export", "audit", "settings"],
                },
                "reason": {"type": "string"}
            },
            "required": ["page", "reason"]
        }
    },
]


# ── Tool Execution ───────────────────────────────────────────────────

async def execute_tool(tool_name: str, tool_input: dict, session: AsyncSession) -> str:
    """Execute a tool call and return JSON result."""
    try:
        handler = TOOL_HANDLERS.get(tool_name)
        if handler:
            return await handler(session, tool_input)
        return _dumps({"error": f"Tool sconosciuto: {tool_name}"})
    except Exception as e:
        logger.exception("Tool execution error: %s", tool_name)
        return _dumps({"error": str(e)})


# ── Tool Handler Functions ───────────────────────────────────────────

async def _search_securities(session: AsyncSession, p: dict) -> str:
    query = p["query"].strip()
    limit = p.get("limit", 20)
    q_upper = query.upper()
    stmt = select(Security).where(
        (Security.isin.ilike(f"%{q_upper}%"))
        | (Security.name.ilike(f"%{query}%"))
        | (Security.security_type.ilike(f"%{query}%"))
        | (Security.issuer.ilike(f"%{query}%"))
    ).limit(limit)
    if p.get("security_type"):
        stmt = stmt.where(Security.security_type.ilike(f"%{p['security_type']}%"))
    result = await session.execute(stmt)
    secs = result.scalars().all()
    return _dumps([{
        "id": s.id, "isin": s.isin, "name": s.name, "security_type": s.security_type,
        "issuer": s.issuer, "coupon_rate": s.coupon_rate, "coupon_frequency": s.coupon_frequency,
        "maturity_date": s.maturity_date, "nominal_value": s.nominal_value,
        "tax_regime": s.tax_regime, "withholding_rate": s.withholding_rate,
        "currency": s.currency, "is_listed": s.is_listed,
    } for s in secs])


async def _get_security_detail(session: AsyncSession, p: dict) -> str:
    sec = None
    if p.get("security_id"):
        sec = await session.get(Security, uuid.UUID(p["security_id"]))
    elif p.get("isin"):
        result = await session.execute(
            select(Security).where(Security.isin == p["isin"].upper())
        )
        sec = result.scalars().first()
    if not sec:
        return _dumps({"error": "Titolo non trovato"})

    # Latest market price
    mp_stmt = select(MarketPrice).where(
        MarketPrice.security_id == sec.id
    ).order_by(MarketPrice.price_date.desc()).limit(1)
    mp = (await session.execute(mp_stmt)).scalars().first()

    # Portfolio positions
    pos_stmt = select(PortfolioPosition).where(
        PortfolioPosition.security_id == sec.id, PortfolioPosition.is_active.is_(True)
    )
    positions = (await session.execute(pos_stmt)).scalars().all()

    return _dumps({
        "id": sec.id, "isin": sec.isin, "name": sec.name, "security_type": sec.security_type,
        "issuer": sec.issuer, "coupon_rate": sec.coupon_rate, "coupon_frequency": sec.coupon_frequency,
        "coupon_dates": sec.coupon_dates, "coupon_day_count": sec.coupon_day_count,
        "maturity_date": sec.maturity_date, "issue_date": sec.issue_date,
        "issue_price": sec.issue_price, "nominal_value": sec.nominal_value,
        "tax_regime": sec.tax_regime, "withholding_rate": sec.withholding_rate,
        "is_listed": sec.is_listed, "market": sec.market,
        "latest_market_price": {"price": mp.close_price, "date": mp.price_date, "source": mp.source} if mp else None,
        "portfolio_positions": [{
            "client_id": pos.client_id, "quantity": pos.quantity, "book_value": pos.book_value,
            "classification": pos.classification, "amortized_cost": pos.amortized_cost,
            "acquisition_date": pos.acquisition_date,
        } for pos in positions],
    })


async def _get_dashboard_stats(session: AsyncSession, p: dict) -> str:
    filters = []
    client_id = p.get("client_id")

    sec_count = (await session.execute(select(func.count(Security.id)))).scalar() or 0
    txn_q = select(func.count(Transaction.id))
    je_q = select(func.count(JournalEntry.id))
    val_q = select(func.count(Valuation.id))
    doc_q = select(func.count(Document.id))
    if client_id:
        uid = uuid.UUID(client_id)
        txn_q = txn_q.where(Transaction.client_id == uid)
        je_q = je_q.where(JournalEntry.client_id == uid)
        val_q = val_q.where(Valuation.client_id == uid)
        doc_q = doc_q.where(Document.client_id == uid)

    txn_count = (await session.execute(txn_q)).scalar() or 0
    je_count = (await session.execute(je_q)).scalar() or 0
    val_count = (await session.execute(val_q)).scalar() or 0
    doc_count = (await session.execute(doc_q)).scalar() or 0

    # Status breakdown
    txn_by_status = {}
    for s in ["draft", "approved", "posted"]:
        q = select(func.count(Transaction.id)).where(Transaction.status == s)
        if client_id:
            q = q.where(Transaction.client_id == uuid.UUID(client_id))
        txn_by_status[s] = (await session.execute(q)).scalar() or 0

    je_by_status = {}
    for s in ["generated", "approved", "posted"]:
        q = select(func.count(JournalEntry.id)).where(JournalEntry.status == s)
        if client_id:
            q = q.where(JournalEntry.client_id == uuid.UUID(client_id))
        je_by_status[s] = (await session.execute(q)).scalar() or 0

    # Portfolio totals
    pos_q = select(
        func.sum(PortfolioPosition.book_value),
        func.count(PortfolioPosition.id)
    ).where(PortfolioPosition.is_active.is_(True))
    if client_id:
        pos_q = pos_q.where(PortfolioPosition.client_id == uuid.UUID(client_id))
    pos_result = (await session.execute(pos_q)).one()
    total_book_value = pos_result[0] or Decimal("0")
    active_positions = pos_result[1] or 0

    # Recent activity (last 7 days)
    week_ago = date.today() - timedelta(days=7)
    recent_txn = (await session.execute(
        select(func.count(Transaction.id)).where(Transaction.trade_date >= week_ago)
    )).scalar() or 0

    # Client count
    client_count = (await session.execute(select(func.count(Client.id)).where(Client.is_active.is_(True)))).scalar() or 0

    return _dumps({
        "totals": {
            "securities": sec_count, "transactions": txn_count, "journal_entries": je_count,
            "valuations": val_count, "documents": doc_count, "active_clients": client_count,
        },
        "transactions_by_status": txn_by_status,
        "journal_entries_by_status": je_by_status,
        "portfolio": {
            "active_positions": active_positions,
            "total_book_value": total_book_value,
        },
        "recent_activity": {"transactions_last_7_days": recent_txn},
    })


async def _get_portfolio_positions(session: AsyncSession, p: dict) -> str:
    stmt = select(PortfolioPosition)
    if p.get("client_id"):
        stmt = stmt.where(PortfolioPosition.client_id == uuid.UUID(p["client_id"]))
    if p.get("active_only", True):
        stmt = stmt.where(PortfolioPosition.is_active.is_(True))
    result = await session.execute(stmt)
    positions = result.scalars().all()

    items = []
    for pos in positions:
        sec = await session.get(Security, pos.security_id)
        items.append({
            "id": pos.id, "client_id": pos.client_id, "security_id": pos.security_id,
            "isin": sec.isin if sec else None, "security_name": sec.name if sec else None,
            "classification": pos.classification, "quantity": pos.quantity,
            "book_value": pos.book_value, "book_value_per_unit": pos.book_value_per_unit,
            "amortized_cost": pos.amortized_cost, "effective_interest_rate": pos.effective_interest_rate,
            "acquisition_date": pos.acquisition_date, "acquisition_price": pos.acquisition_price,
        })
    return _dumps(items)


async def _get_portfolio_report(session: AsyncSession, p: dict) -> str:
    from app.services.report_service import portfolio_report
    client_id = uuid.UUID(p["client_id"])
    report_date = date.fromisoformat(p.get("report_date", date.today().isoformat()))
    result = await portfolio_report(session, client_id=client_id, report_date=report_date)
    return _dumps(result)


async def _list_transactions(session: AsyncSession, p: dict) -> str:
    limit = p.get("limit", 50)
    stmt = select(Transaction).order_by(Transaction.trade_date.desc()).limit(limit)
    if p.get("client_id"):
        stmt = stmt.where(Transaction.client_id == uuid.UUID(p["client_id"]))
    if p.get("security_id"):
        stmt = stmt.where(Transaction.security_id == uuid.UUID(p["security_id"]))
    if p.get("status"):
        stmt = stmt.where(Transaction.status == p["status"])
    if p.get("transaction_type"):
        stmt = stmt.where(Transaction.transaction_type == p["transaction_type"])
    if p.get("date_from"):
        stmt = stmt.where(Transaction.trade_date >= date.fromisoformat(p["date_from"]))
    if p.get("date_to"):
        stmt = stmt.where(Transaction.trade_date <= date.fromisoformat(p["date_to"]))

    result = await session.execute(stmt)
    txns = result.scalars().all()
    items = []
    for t in txns:
        sec = await session.get(Security, t.security_id)
        items.append({
            "id": t.id, "transaction_type": t.transaction_type, "status": t.status,
            "trade_date": t.trade_date, "settlement_date": t.settlement_date,
            "isin": sec.isin if sec else None, "security_name": sec.name if sec else None,
            "quantity": t.quantity, "unit_price": t.unit_price,
            "gross_amount": t.gross_amount, "accrued_interest": t.accrued_interest,
            "net_settlement_amount": t.net_settlement_amount,
            "bank_commission": t.bank_commission, "total_transaction_costs": t.total_transaction_costs,
            "coupon_gross": t.coupon_gross, "withholding_tax": t.withholding_tax,
            "coupon_net": t.coupon_net, "gain_loss": t.gain_loss, "gain_loss_type": t.gain_loss_type,
            "currency": t.currency, "notes": t.notes,
        })
    return _dumps(items)


async def _get_transaction_detail(session: AsyncSession, p: dict) -> str:
    txn = await session.get(Transaction, uuid.UUID(p["transaction_id"]))
    if not txn:
        return _dumps({"error": "Operazione non trovata"})
    sec = await session.get(Security, txn.security_id)
    return _dumps({
        "id": txn.id, "transaction_type": txn.transaction_type, "status": txn.status,
        "trade_date": txn.trade_date, "settlement_date": txn.settlement_date,
        "isin": sec.isin if sec else None, "security_name": sec.name if sec else None,
        "quantity": txn.quantity, "unit_price": txn.unit_price,
        "gross_amount": txn.gross_amount, "accrued_interest": txn.accrued_interest,
        "tel_quel_amount": txn.tel_quel_amount,
        "bank_commission": txn.bank_commission, "stamp_duty": txn.stamp_duty,
        "tobin_tax": txn.tobin_tax, "other_costs": txn.other_costs,
        "total_transaction_costs": txn.total_transaction_costs,
        "net_settlement_amount": txn.net_settlement_amount,
        "coupon_gross": txn.coupon_gross, "withholding_tax": txn.withholding_tax,
        "coupon_net": txn.coupon_net, "gain_loss": txn.gain_loss,
        "gain_loss_type": txn.gain_loss_type, "currency": txn.currency,
        "exchange_rate": txn.exchange_rate, "notes": txn.notes,
        "approved_by": txn.approved_by, "approved_at": txn.approved_at,
        "parsing_confidence": txn.parsing_confidence, "manually_verified": txn.manually_verified,
    })


async def _approve_transaction(session: AsyncSession, p: dict) -> str:
    from app.services.transaction_service import approve_transaction
    txn = await approve_transaction(session, uuid.UUID(p["transaction_id"]))
    if not txn:
        return _dumps({"error": "Impossibile approvare: operazione non trovata o non in stato draft"})
    return _dumps({"success": True, "message": f"Operazione {txn.id} approvata", "new_status": txn.status})


async def _reject_transaction(session: AsyncSession, p: dict) -> str:
    from app.services.transaction_service import reject_transaction
    txn = await reject_transaction(session, uuid.UUID(p["transaction_id"]))
    if not txn:
        return _dumps({"error": "Impossibile rifiutare: operazione non trovata o non in stato approved"})
    return _dumps({"success": True, "message": f"Operazione {txn.id} rifiutata, ritornata a draft", "new_status": txn.status})


async def _list_journal_entries(session: AsyncSession, p: dict) -> str:
    limit = p.get("limit", 50)
    stmt = select(JournalEntry).options(selectinload(JournalEntry.lines)).order_by(JournalEntry.entry_date.desc()).limit(limit)
    if p.get("client_id"):
        stmt = stmt.where(JournalEntry.client_id == uuid.UUID(p["client_id"]))
    if p.get("entry_type"):
        stmt = stmt.where(JournalEntry.entry_type == p["entry_type"])
    if p.get("status"):
        stmt = stmt.where(JournalEntry.status == p["status"])
    if p.get("fiscal_year"):
        stmt = stmt.where(JournalEntry.fiscal_year == p["fiscal_year"])
    if p.get("date_from"):
        stmt = stmt.where(JournalEntry.entry_date >= date.fromisoformat(p["date_from"]))
    if p.get("date_to"):
        stmt = stmt.where(JournalEntry.entry_date <= date.fromisoformat(p["date_to"]))

    result = await session.execute(stmt)
    entries = result.scalars().unique().all()
    items = []
    for e in entries:
        total_debit = sum(l.debit for l in e.lines)
        total_credit = sum(l.credit for l in e.lines)
        items.append({
            "id": e.id, "entry_date": e.entry_date, "description": e.description,
            "entry_type": e.entry_type, "status": e.status, "fiscal_year": e.fiscal_year,
            "total_debit": total_debit, "total_credit": total_credit,
            "lines_count": len(e.lines),
            "lines": [{
                "line_number": l.line_number, "account_code": l.account_code,
                "account_name": l.account_name, "debit": l.debit, "credit": l.credit,
                "description": l.description,
            } for l in sorted(e.lines, key=lambda x: x.line_number)],
        })
    return _dumps(items)


async def _get_journal_entry_detail(session: AsyncSession, p: dict) -> str:
    stmt = select(JournalEntry).options(selectinload(JournalEntry.lines)).where(
        JournalEntry.id == uuid.UUID(p["entry_id"])
    )
    result = await session.execute(stmt)
    e = result.scalars().first()
    if not e:
        return _dumps({"error": "Scrittura non trovata"})
    return _dumps({
        "id": e.id, "entry_date": e.entry_date, "competence_date": e.competence_date,
        "description": e.description, "entry_type": e.entry_type, "status": e.status,
        "fiscal_year": e.fiscal_year, "document_ref": e.document_ref,
        "generation_rule": e.generation_rule, "generation_params": e.generation_params,
        "approved_by": e.approved_by, "approved_at": e.approved_at,
        "posted_by": e.posted_by, "posted_at": e.posted_at,
        "lines": [{
            "line_number": l.line_number, "account_code": l.account_code,
            "account_name": l.account_name, "debit": l.debit, "credit": l.credit,
            "description": l.description,
        } for l in sorted(e.lines, key=lambda x: x.line_number)],
    })


async def _generate_journal_entries(session: AsyncSession, p: dict) -> str:
    from app.services.journal_service import generate_entries_for_transactions
    client_id = uuid.UUID(p["client_id"])
    txn_ids = [uuid.UUID(t) for t in p.get("transaction_ids", [])] or None
    entries = await generate_entries_for_transactions(session, client_id, txn_ids)
    return _dumps({
        "success": True,
        "entries_generated": len(entries),
        "entries": [{"id": e.id, "description": e.description, "entry_type": e.entry_type} for e in entries],
    })


async def _approve_journal_entry(session: AsyncSession, p: dict) -> str:
    from app.services.journal_service import approve_entry
    entry = await approve_entry(session, uuid.UUID(p["entry_id"]))
    if not entry:
        return _dumps({"error": "Impossibile approvare: scrittura non trovata o non in stato generated"})
    return _dumps({"success": True, "message": f"Scrittura {entry.id} approvata", "new_status": entry.status})


async def _post_journal_entry(session: AsyncSession, p: dict) -> str:
    from app.services.journal_service import post_entry
    entry = await post_entry(session, uuid.UUID(p["entry_id"]))
    if not entry:
        return _dumps({"error": "Impossibile postare: scrittura non trovata o non in stato approved"})
    return _dumps({"success": True, "message": f"Scrittura {entry.id} postata nel libro giornale", "new_status": entry.status})


async def _balance_check(session: AsyncSession, p: dict) -> str:
    from app.services.journal_service import balance_check
    result = await balance_check(session, uuid.UUID(p["client_id"]))
    return _dumps(result)


async def _gains_losses_report(session: AsyncSession, p: dict) -> str:
    from app.services.report_service import gains_losses_report
    result = await gains_losses_report(
        session,
        client_id=uuid.UUID(p["client_id"]),
        date_from=date.fromisoformat(p["date_from"]),
        date_to=date.fromisoformat(p["date_to"]),
    )
    return _dumps(result)


async def _tax_summary_report(session: AsyncSession, p: dict) -> str:
    from app.services.report_service import tax_summary_report
    result = await tax_summary_report(
        session,
        client_id=uuid.UUID(p["client_id"]),
        fiscal_year=p["fiscal_year"],
    )
    return _dumps(result)


async def _oic20_nota_integrativa(session: AsyncSession, p: dict) -> str:
    from app.services.report_service import oic20_nota_integrativa
    result = await oic20_nota_integrativa(
        session,
        client_id=uuid.UUID(p["client_id"]),
        fiscal_year=p["fiscal_year"],
    )
    return _dumps(result)


async def _analyze_trends(session: AsyncSession, p: dict) -> str:
    """Analisi trend per un periodo con confronto periodo precedente."""
    d_from = date.fromisoformat(p["date_from"])
    d_to = date.fromisoformat(p["date_to"])
    period_days = (d_to - d_from).days + 1
    prev_from = d_from - timedelta(days=period_days)
    prev_to = d_from - timedelta(days=1)

    client_filter = []
    if p.get("client_id"):
        client_filter = [Transaction.client_id == uuid.UUID(p["client_id"])]

    # Current period
    cur_stmt = select(Transaction).where(
        Transaction.trade_date >= d_from, Transaction.trade_date <= d_to, *client_filter
    )
    cur_txns = (await session.execute(cur_stmt)).scalars().all()

    # Previous period for comparison
    prev_txns = []
    if p.get("compare_previous", True):
        prev_stmt = select(Transaction).where(
            Transaction.trade_date >= prev_from, Transaction.trade_date <= prev_to, *client_filter
        )
        prev_txns = (await session.execute(prev_stmt)).scalars().all()

    def summarize(txns):
        by_type = {}
        total_volume = Decimal("0")
        total_gains = Decimal("0")
        total_losses = Decimal("0")
        statuses = {"draft": 0, "approved": 0, "posted": 0}
        for t in txns:
            tp = t.transaction_type
            by_type.setdefault(tp, {"count": 0, "volume": Decimal("0")})
            by_type[tp]["count"] += 1
            by_type[tp]["volume"] += t.net_settlement_amount or Decimal("0")
            total_volume += t.net_settlement_amount or Decimal("0")
            if t.gain_loss and t.gain_loss > 0:
                total_gains += t.gain_loss
            elif t.gain_loss and t.gain_loss < 0:
                total_losses += abs(t.gain_loss)
            statuses[t.status] = statuses.get(t.status, 0) + 1
        return {
            "total_transactions": len(txns),
            "total_volume": total_volume,
            "total_gains": total_gains,
            "total_losses": total_losses,
            "net_gain_loss": total_gains - total_losses,
            "by_type": {k: {"count": v["count"], "volume": v["volume"]} for k, v in by_type.items()},
            "by_status": statuses,
        }

    current = summarize(cur_txns)
    previous = summarize(prev_txns) if prev_txns or p.get("compare_previous", True) else None

    # Calculate deltas
    deltas = None
    if previous and previous["total_transactions"] > 0:
        prev_vol = previous["total_volume"] or Decimal("1")
        deltas = {
            "transactions_delta": current["total_transactions"] - previous["total_transactions"],
            "volume_delta_pct": float(((current["total_volume"] - previous["total_volume"]) / prev_vol * 100)) if prev_vol else None,
            "gain_loss_delta": current["net_gain_loss"] - previous["net_gain_loss"],
        }

    # Journal entries in period
    je_stmt = select(func.count(JournalEntry.id)).where(
        JournalEntry.entry_date >= d_from, JournalEntry.entry_date <= d_to
    )
    if p.get("client_id"):
        je_stmt = je_stmt.where(JournalEntry.client_id == uuid.UUID(p["client_id"]))
    je_count = (await session.execute(je_stmt)).scalar() or 0

    # Audit events in period
    audit_stmt = select(func.count(AuditLog.id)).where(
        AuditLog.timestamp >= datetime.combine(d_from, datetime.min.time()),
        AuditLog.timestamp <= datetime.combine(d_to, datetime.max.time()),
    )
    audit_count = (await session.execute(audit_stmt)).scalar() or 0

    return _dumps({
        "period": {"from": d_from, "to": d_to, "days": period_days},
        "current_period": current,
        "previous_period": previous,
        "deltas": deltas,
        "journal_entries_in_period": je_count,
        "audit_events_in_period": audit_count,
    })


async def _list_valuations(session: AsyncSession, p: dict) -> str:
    limit = p.get("limit", 20)
    stmt = select(Valuation).order_by(Valuation.created_at.desc()).limit(limit)
    if p.get("client_id"):
        stmt = stmt.where(Valuation.client_id == uuid.UUID(p["client_id"]))
    if p.get("fiscal_year"):
        stmt = stmt.where(Valuation.fiscal_year == p["fiscal_year"])
    result = await session.execute(stmt)
    vals = result.scalars().all()
    items = []
    for v in vals:
        pos = await session.get(PortfolioPosition, v.position_id) if v.position_id else None
        sec = await session.get(Security, pos.security_id) if pos else None
        items.append({
            "id": v.id, "valuation_date": v.valuation_date, "fiscal_year": v.fiscal_year,
            "isin": sec.isin if sec else None, "security_name": sec.name if sec else None,
            "book_value": v.book_value, "market_price": v.market_price,
            "market_value": v.market_value, "valuation_result": v.valuation_result,
            "impairment_amount": v.impairment_amount, "reversal_amount": v.reversal_amount,
            "status": v.status,
        })
    return _dumps(items)


async def _run_year_end_valuation(session: AsyncSession, p: dict) -> str:
    from app.services.valuation_service import run_year_end_valuation
    result = await run_year_end_valuation(
        session,
        client_id=uuid.UUID(p["client_id"]),
        valuation_date=date.fromisoformat(p["valuation_date"]),
        fiscal_year=p["fiscal_year"],
    )
    # Don't serialize the full Valuation objects
    return _dumps({
        "client_id": result["client_id"],
        "fiscal_year": result["fiscal_year"],
        "valuation_date": result["valuation_date"],
        "positions_evaluated": result["positions_evaluated"],
        "impairments_generated": result["impairments_generated"],
        "reversals_generated": result["reversals_generated"],
        "entries_generated": result["entries_generated"],
    })


async def _get_market_prices(session: AsyncSession, p: dict) -> str:
    limit = p.get("limit", 30)
    sec_id = None
    if p.get("security_id"):
        sec_id = uuid.UUID(p["security_id"])
    elif p.get("isin"):
        result = await session.execute(select(Security.id).where(Security.isin == p["isin"].upper()))
        row = result.first()
        sec_id = row[0] if row else None
    if not sec_id:
        return _dumps({"error": "Titolo non trovato"})

    stmt = select(MarketPrice).where(MarketPrice.security_id == sec_id).order_by(MarketPrice.price_date.desc()).limit(limit)
    prices = (await session.execute(stmt)).scalars().all()
    return _dumps([{
        "price_date": mp.price_date, "close_price": mp.close_price, "source": mp.source,
    } for mp in prices])


async def _list_documents(session: AsyncSession, p: dict) -> str:
    limit = p.get("limit", 20)
    stmt = select(Document).order_by(Document.uploaded_at.desc()).limit(limit)
    if p.get("client_id"):
        stmt = stmt.where(Document.client_id == uuid.UUID(p["client_id"]))
    if p.get("document_type"):
        stmt = stmt.where(Document.document_type == p["document_type"])
    if p.get("parsing_status"):
        stmt = stmt.where(Document.parsing_status == p["parsing_status"])
    docs = (await session.execute(stmt)).scalars().all()
    return _dumps([{
        "id": d.id, "document_type": d.document_type, "bank_name": d.bank_name,
        "original_filename": d.original_filename, "parsing_status": d.parsing_status,
        "parsing_confidence": d.parsing_confidence, "document_date": d.document_date,
        "uploaded_at": d.uploaded_at,
    } for d in docs])


async def _get_audit_log(session: AsyncSession, p: dict) -> str:
    limit = p.get("limit", 30)
    stmt = select(AuditLog).order_by(AuditLog.timestamp.desc()).limit(limit)
    if p.get("entity_type"):
        stmt = stmt.where(AuditLog.entity_type == p["entity_type"])
    if p.get("action"):
        stmt = stmt.where(AuditLog.action == p["action"])
    if p.get("client_id"):
        stmt = stmt.where(AuditLog.client_id == uuid.UUID(p["client_id"]))
    if p.get("date_from"):
        stmt = stmt.where(AuditLog.timestamp >= datetime.combine(date.fromisoformat(p["date_from"]), datetime.min.time()))
    if p.get("date_to"):
        stmt = stmt.where(AuditLog.timestamp <= datetime.combine(date.fromisoformat(p["date_to"]), datetime.max.time()))
    logs = (await session.execute(stmt)).scalars().all()
    return _dumps([{
        "id": l.id, "timestamp": l.timestamp, "entity_type": l.entity_type,
        "entity_id": l.entity_id, "action": l.action, "user_id": l.user_id,
        "computation_rule": l.computation_rule,
        "new_values_summary": str(l.new_values)[:200] if l.new_values else None,
    } for l in logs])


async def _list_clients(session: AsyncSession, p: dict) -> str:
    stmt = select(Client).where(Client.is_active.is_(True))
    if p.get("studio_id"):
        stmt = stmt.where(Client.studio_id == uuid.UUID(p["studio_id"]))
    clients = (await session.execute(stmt)).scalars().all()
    return _dumps([{
        "id": c.id, "name": c.name, "tax_code": c.tax_code,
        "legal_form": c.legal_form, "fiscal_year_start": c.fiscal_year_start,
        "fiscal_year_end": c.fiscal_year_end, "balance_type": c.balance_type,
        "valuation_method": c.valuation_method, "cost_method": c.cost_method,
    } for c in clients])


async def _get_chart_of_accounts(session: AsyncSession, p: dict) -> str:
    stmt = select(ChartOfAccounts).where(
        ChartOfAccounts.client_id == uuid.UUID(p["client_id"]),
        ChartOfAccounts.is_active.is_(True),
    ).order_by(ChartOfAccounts.code)
    accounts = (await session.execute(stmt)).scalars().all()
    return _dumps([{
        "code": a.code, "name": a.name, "account_type": a.account_type,
        "parent_code": a.parent_code,
    } for a in accounts])


async def _navigate_page(session: AsyncSession, p: dict) -> str:
    return _dumps({"action": "navigate", "page": p["page"], "reason": p.get("reason", "")})


# ── Handler Map ──────────────────────────────────────────────────────

TOOL_HANDLERS = {
    "search_securities": _search_securities,
    "get_security_detail": _get_security_detail,
    "get_dashboard_stats": _get_dashboard_stats,
    "get_portfolio_positions": _get_portfolio_positions,
    "get_portfolio_report": _get_portfolio_report,
    "list_transactions": _list_transactions,
    "get_transaction_detail": _get_transaction_detail,
    "approve_transaction": _approve_transaction,
    "reject_transaction": _reject_transaction,
    "list_journal_entries": _list_journal_entries,
    "get_journal_entry_detail": _get_journal_entry_detail,
    "generate_journal_entries": _generate_journal_entries,
    "approve_journal_entry": _approve_journal_entry,
    "post_journal_entry": _post_journal_entry,
    "balance_check": _balance_check,
    "gains_losses_report": _gains_losses_report,
    "tax_summary_report": _tax_summary_report,
    "oic20_nota_integrativa": _oic20_nota_integrativa,
    "analyze_trends": _analyze_trends,
    "list_valuations": _list_valuations,
    "run_year_end_valuation": _run_year_end_valuation,
    "get_market_prices": _get_market_prices,
    "list_documents": _list_documents,
    "get_audit_log": _get_audit_log,
    "list_clients": _list_clients,
    "get_chart_of_accounts": _get_chart_of_accounts,
    "navigate_page": _navigate_page,
}


# ── Streaming Chat ───────────────────────────────────────────────────

async def stream_chat(
    messages: list[dict],
    session: AsyncSession,
    context: dict | None = None,
) -> AsyncIterator[str]:
    """Stream copilot chat response with full tool use agentic loop.

    Yields SSE events:
    - data: {"type": "text", "content": "..."} — text chunks
    - data: {"type": "tool_use", "name": "...", "input": {...}} — tool call
    - data: {"type": "done"} — complete
    - data: {"type": "error", "content": "..."} — error
    """
    if not settings.anthropic_api_key:
        yield f'data: {json.dumps({"type": "error", "content": "API key Anthropic non configurata. Configura TE_ANTHROPIC_API_KEY nel .env del backend."})}\n\n'
        return

    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

    system = SYSTEM_PROMPT.format(today=date.today().isoformat())
    if context:
        page = context.get("page", "dashboard")
        system += f"\n\nL'utente si trova nella pagina: {page}"
        if context.get("selected_data"):
            system += f"\nDati contestuali: {json.dumps(context['selected_data'], ensure_ascii=False, default=_json_serial)}"

    current_messages = list(messages)
    max_iterations = 8  # Allow more iterations for complex multi-step queries

    for iteration in range(max_iterations):
        try:
            response = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=4096,
                system=system,
                tools=TOOLS,
                messages=current_messages,
            )
        except anthropic.APIError as e:
            yield f'data: {json.dumps({"type": "error", "content": f"Errore API Claude: {str(e)}"})}\n\n'
            return

        has_tool_use = any(block.type == "tool_use" for block in response.content)

        if not has_tool_use or response.stop_reason == "end_turn":
            for block in response.content:
                if block.type == "text":
                    yield f'data: {json.dumps({"type": "text", "content": block.text})}\n\n'
            yield f'data: {json.dumps({"type": "done"})}\n\n'
            return

        # Process tool calls
        assistant_content = []
        tool_results = []

        for block in response.content:
            if block.type == "text":
                assistant_content.append({"type": "text", "text": block.text})
                yield f'data: {json.dumps({"type": "text", "content": block.text})}\n\n'
            elif block.type == "tool_use":
                assistant_content.append({
                    "type": "tool_use",
                    "id": block.id,
                    "name": block.name,
                    "input": block.input,
                })
                yield f'data: {json.dumps({"type": "tool_use", "name": block.name, "input": block.input})}\n\n'

                result_str = await execute_tool(block.name, block.input, session)
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": result_str,
                })

        current_messages.append({"role": "assistant", "content": assistant_content})
        current_messages.append({"role": "user", "content": tool_results})

    yield f'data: {json.dumps({"type": "text", "content": "Ho raggiunto il limite di iterazioni. Prova a riformulare la richiesta in modo più specifico."})}\n\n'
    yield f'data: {json.dumps({"type": "done"})}\n\n'
