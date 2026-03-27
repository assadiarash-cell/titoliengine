"""Seed piano dei conti standard per contabilizzazione titoli di debito (OIC 20).

Inserisce i conti previsti dallo standard OIC 20 per la gestione contabile
di titoli di debito: immobilizzazioni finanziarie, attivo circolante,
interessi attivi/passivi, plus/minusvalenze, svalutazioni e ripristini.

Riferimento normativo:
  - OIC 20 "Titoli di debito" (2016, aggiornato 2024)
  - Art. 2424/2425 Codice Civile — schema di bilancio

Uso:
    python -m scripts.seed_chart_of_accounts <client_id>
"""

import asyncio
import sys
import uuid

from sqlalchemy import select

from app.database import async_session_factory
from app.models.chart_of_accounts import ChartOfAccounts


# Piano dei conti standard OIC 20 per titoli di debito
STANDARD_ACCOUNTS = [
    # ── Attivo immobilizzato ──
    {
        "code": "B.III.3.a",
        "name": "Titoli di debito immobilizzati",
        "account_type": "asset",
        "parent_code": None,
        "notes": "OIC 20 — Titoli destinati a permanere durevolmente nel patrimonio (art. 2424 B.III.3)",
    },
    {
        "code": "B.III.3.a.bis",
        "name": "Fondo svalutazione titoli immobilizzati",
        "account_type": "asset",
        "parent_code": "B.III.3.a",
        "notes": "OIC 20 par. 58-62 — Rettifica di valore per perdite durevoli su titoli immobilizzati",
    },
    # ── Attivo circolante ──
    {
        "code": "C.III.6",
        "name": "Titoli di debito circolanti",
        "account_type": "asset",
        "parent_code": None,
        "notes": "OIC 20 — Titoli destinati alla negoziazione o non detenuti durevolmente (art. 2424 C.III.6)",
    },
    {
        "code": "D.18.d",
        "name": "Ratei attivi su cedole",
        "account_type": "asset",
        "parent_code": None,
        "notes": "OIC 20 par. 30-32 — Rateo attivo per interessi maturati e non ancora incassati",
    },
    {
        "code": "C.IV.1",
        "name": "Banca c/c",
        "account_type": "asset",
        "parent_code": None,
        "notes": "Conto corrente bancario — contropartita per regolamento operazioni su titoli",
    },
    {
        "code": "C.II.5-bis",
        "name": "Erario c/ritenute subite",
        "account_type": "asset",
        "parent_code": None,
        "notes": "Credito verso Erario per ritenute fiscali subite su cedole e capital gain (art. 26 DPR 600/73)",
    },
    # ── Ricavi finanziari ──
    {
        "code": "C.16.a",
        "name": "Interessi attivi su titoli",
        "account_type": "revenue",
        "parent_code": None,
        "notes": "OIC 20 par. 30-32 — Proventi da cedole e ratei di competenza (art. 2425 C.16)",
    },
    {
        "code": "C.16.b",
        "name": "Plusvalenze da negoziazione titoli",
        "account_type": "revenue",
        "parent_code": None,
        "notes": "OIC 20 par. 45-48 — Plusvalenze realizzate da cessione titoli non immobilizzati (art. 2425 C.16)",
    },
    {
        "code": "D.18.b",
        "name": "Ripristino di valore titoli",
        "account_type": "revenue",
        "parent_code": None,
        "notes": "OIC 20 par. 63 — Ripristino di valore di titoli immobilizzati precedentemente svalutati (art. 2425 D.18.b)",
    },
    # ── Costi finanziari ──
    {
        "code": "C.17.b",
        "name": "Minusvalenze da negoziazione titoli",
        "account_type": "expense",
        "parent_code": None,
        "notes": "OIC 20 par. 45-48 — Minusvalenze realizzate da cessione titoli non immobilizzati (art. 2425 C.17)",
    },
    {
        "code": "C.17",
        "name": "Interessi passivi e oneri finanziari",
        "account_type": "expense",
        "parent_code": None,
        "notes": "OIC 20 — Oneri finanziari generici, incluso ammortamento scarti di emissione (art. 2425 C.17)",
    },
    {
        "code": "D.19.b",
        "name": "Svalutazione titoli immobilizzati",
        "account_type": "expense",
        "parent_code": None,
        "notes": "OIC 20 par. 58-62 — Svalutazione per perdita durevole di valore titoli immobilizzati (art. 2425 D.19.b)",
    },
    {
        "code": "B.14",
        "name": "Commissioni e spese bancarie",
        "account_type": "expense",
        "parent_code": None,
        "notes": "Costi di transazione: commissioni bancarie, bolli, Tobin tax (OIC 20 par. 20-22)",
    },
]


async def seed_chart_of_accounts(client_id: uuid.UUID) -> list[ChartOfAccounts]:
    """Inserisce il piano dei conti standard OIC 20 per un cliente.

    Se un conto con lo stesso codice esiste gia per il cliente,
    viene saltato (upsert idempotente).

    Args:
        client_id: UUID del cliente per cui creare il piano dei conti.

    Returns:
        Lista degli oggetti ChartOfAccounts creati o gia esistenti.
    """
    created = []

    async with async_session_factory() as session:
        for account_data in STANDARD_ACCOUNTS:
            # Controlla se esiste gia
            stmt = select(ChartOfAccounts).where(
                ChartOfAccounts.client_id == client_id,
                ChartOfAccounts.code == account_data["code"],
            )
            result = await session.execute(stmt)
            existing = result.scalar_one_or_none()

            if existing:
                print(f"  [skip] {account_data['code']} — {account_data['name']} (gia esistente)")
                created.append(existing)
                continue

            account = ChartOfAccounts(
                client_id=client_id,
                code=account_data["code"],
                name=account_data["name"],
                account_type=account_data["account_type"],
                parent_code=account_data["parent_code"],
                notes=account_data["notes"],
            )
            session.add(account)
            created.append(account)
            print(f"  [new]  {account_data['code']} — {account_data['name']}")

        await session.commit()

    print(f"\nPiano dei conti OIC 20: {len(created)} conti totali per client {client_id}")
    return created


async def main() -> None:
    """Entry point: legge client_id da riga di comando e inserisce i conti."""
    if len(sys.argv) < 2:
        print("Uso: python -m scripts.seed_chart_of_accounts <client_id>")
        print("  client_id: UUID del cliente per cui inserire il piano dei conti")
        sys.exit(1)

    try:
        client_id = uuid.UUID(sys.argv[1])
    except ValueError:
        print(f"Errore: '{sys.argv[1]}' non e un UUID valido.")
        sys.exit(1)

    print(f"Seed piano dei conti OIC 20 per client: {client_id}")
    print("=" * 60)
    await seed_chart_of_accounts(client_id)
    print("=" * 60)
    print("Completato.")


if __name__ == "__main__":
    asyncio.run(main())
