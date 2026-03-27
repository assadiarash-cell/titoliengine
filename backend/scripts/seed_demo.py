"""Seed ambiente demo completo per TitoliEngine.

Crea un ambiente dimostrativo funzionante con:
  - Studio professionale "Studio Rossi & Associati"
  - Utente "Marco Rossi" (admin)
  - Cliente "Alfa Investimenti SRL"
  - Piano dei conti standard OIC 20
  - Anagrafica titoli (20 governativi + 5 corporate)
  - 10 transazioni campione (acquisti, vendite, incassi cedole)
  - Scritture contabili generate per tutte le transazioni

Riferimenti:
  - OIC 20 "Titoli di debito"
  - Art. 2424/2425 Codice Civile
  - D.Lgs. 239/96 (regime fiscale titoli di Stato)

Uso:
    python -m scripts.seed_demo
"""

import asyncio
from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy import select

from app.database import async_session_factory
from app.models.tenant import Studio, Client, User
from app.models.security import Security
from app.models.transaction import Transaction
from app.models.journal_entry import JournalEntry, JournalLine
from app.utils.auth import hash_password

from scripts.seed_chart_of_accounts import seed_chart_of_accounts
from scripts.seed_securities import seed_securities


async def create_studio() -> "Studio":
    """Crea lo studio demo 'Studio Rossi & Associati'."""
    async with async_session_factory() as session:
        stmt = select(Studio).where(Studio.tax_code == "RSSMRC80A01H501Z")
        result = await session.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            print(f"  [skip] Studio '{existing.name}' gia esistente (id: {existing.id})")
            return existing

        studio = Studio(
            name="Studio Rossi & Associati",
            tax_code="RSSMRC80A01H501Z",
            email="info@studiorossi.it",
            phone="+39 06 1234567",
            address="Via Roma 42, 00186 Roma RM",
            subscription_tier="professional",
        )
        session.add(studio)
        await session.commit()
        await session.refresh(studio)
        print(f"  [new]  Studio '{studio.name}' (id: {studio.id})")
        return studio


async def create_user(studio_id) -> "User":
    """Crea l'utente demo 'Marco Rossi'."""
    async with async_session_factory() as session:
        stmt = select(User).where(User.email == "marco@studiorossi.it")
        result = await session.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            print(f"  [skip] Utente '{existing.full_name}' gia esistente (id: {existing.id})")
            return existing

        user = User(
            studio_id=studio_id,
            email="marco@studiorossi.it",
            password_hash=hash_password("demo2025"),
            full_name="Marco Rossi",
            role="admin",
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        print(f"  [new]  Utente '{user.full_name}' — {user.email} (id: {user.id})")
        return user


async def create_client(studio_id) -> "Client":
    """Crea il cliente demo 'Alfa Investimenti SRL'."""
    async with async_session_factory() as session:
        stmt = select(Client).where(
            Client.studio_id == studio_id,
            Client.tax_code == "12345678901",
        )
        result = await session.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            print(f"  [skip] Cliente '{existing.name}' gia esistente (id: {existing.id})")
            return existing

        client = Client(
            studio_id=studio_id,
            name="Alfa Investimenti SRL",
            tax_code="12345678901",
            legal_form="SRL",
            fiscal_year_start=date(2025, 1, 1),
            fiscal_year_end=date(2025, 12, 31),
            balance_type="ordinario",
            valuation_method="costo_ammortizzato",
            cost_method="costo_specifico",
        )
        session.add(client)
        await session.commit()
        await session.refresh(client)
        print(f"  [new]  Cliente '{client.name}' — P.IVA {client.tax_code} (id: {client.id})")
        return client


async def get_securities_map() -> dict[str, Security]:
    """Restituisce un dizionario ISIN -> Security per i titoli in anagrafica."""
    async with async_session_factory() as session:
        stmt = select(Security)
        result = await session.execute(stmt)
        securities = result.scalars().all()
        return {s.isin: s for s in securities}


async def create_sample_transactions(client_id, user_id) -> list[Transaction]:
    """Crea 10 transazioni demo: acquisti, vendite, incassi cedole.

    Le transazioni coprono diversi scenari previsti da OIC 20:
    1-3. Acquisti BTP a prezzi diversi (sopra/sotto la pari)
    4.   Acquisto BOT zero coupon (sotto la pari)
    5.   Acquisto corporate bond ENI
    6-7. Incasso cedole BTP (con ritenuta 12.50%)
    8.   Incasso cedola ENI corporate (con ritenuta 26%)
    9.   Vendita parziale BTP con plusvalenza
    10.  Vendita BTP con minusvalenza
    """
    async with async_session_factory() as session:
        # Controlla se ci sono gia transazioni per questo client
        stmt = select(Transaction).where(Transaction.client_id == client_id)
        result = await session.execute(stmt)
        existing = result.scalars().all()
        if existing:
            print(f"  [skip] {len(existing)} transazioni gia presenti per il client")
            return existing

    sec_map = await get_securities_map()

    # Dati transazioni campione
    transactions_data = [
        # 1. Acquisto BTP 2.0% 2028 — sotto la pari
        {
            "client_id": client_id,
            "security_id": sec_map["IT0005323032"].id,
            "transaction_type": "purchase",
            "trade_date": date(2025, 1, 15),
            "settlement_date": date(2025, 1, 17),
            "quantity": Decimal("50000.0000000000"),
            "unit_price": Decimal("97.5000000000"),
            "gross_amount": Decimal("48750.0000000000"),
            "accrued_interest": Decimal("458.3333333333"),
            "tel_quel_amount": Decimal("49208.3333333333"),
            "bank_commission": Decimal("50.0000000000"),
            "stamp_duty": Decimal("0.0000000000"),
            "tobin_tax": Decimal("0.0000000000"),
            "other_costs": Decimal("0.0000000000"),
            "total_transaction_costs": Decimal("50.0000000000"),
            "net_settlement_amount": Decimal("49258.3333333333"),
            "status": "approved",
            "approved_by": user_id,
            "approved_at": datetime(2025, 1, 15, 10, 0, 0, tzinfo=timezone.utc),
            "notes": "Acquisto BTP 2.0% 01/02/2028 sotto la pari",
        },
        # 2. Acquisto BTP 3.0% 2029 — sopra la pari
        {
            "client_id": client_id,
            "security_id": sec_map["IT0005365165"].id,
            "transaction_type": "purchase",
            "trade_date": date(2025, 2, 10),
            "settlement_date": date(2025, 2, 12),
            "quantity": Decimal("100000.0000000000"),
            "unit_price": Decimal("102.3000000000"),
            "gross_amount": Decimal("102300.0000000000"),
            "accrued_interest": Decimal("83.3333333333"),
            "tel_quel_amount": Decimal("102383.3333333333"),
            "bank_commission": Decimal("100.0000000000"),
            "stamp_duty": Decimal("0.0000000000"),
            "tobin_tax": Decimal("0.0000000000"),
            "other_costs": Decimal("0.0000000000"),
            "total_transaction_costs": Decimal("100.0000000000"),
            "net_settlement_amount": Decimal("102483.3333333333"),
            "status": "approved",
            "approved_by": user_id,
            "approved_at": datetime(2025, 2, 10, 14, 30, 0, tzinfo=timezone.utc),
            "notes": "Acquisto BTP 3.0% 01/08/2029 sopra la pari",
        },
        # 3. Acquisto BTP 4.0% 2037 — immobilizzato
        {
            "client_id": client_id,
            "security_id": sec_map["IT0003934657"].id,
            "transaction_type": "purchase",
            "trade_date": date(2025, 2, 20),
            "settlement_date": date(2025, 2, 24),
            "quantity": Decimal("200000.0000000000"),
            "unit_price": Decimal("95.2500000000"),
            "gross_amount": Decimal("190500.0000000000"),
            "accrued_interest": Decimal("438.8888888889"),
            "tel_quel_amount": Decimal("190938.8888888889"),
            "bank_commission": Decimal("150.0000000000"),
            "stamp_duty": Decimal("0.0000000000"),
            "tobin_tax": Decimal("0.0000000000"),
            "other_costs": Decimal("0.0000000000"),
            "total_transaction_costs": Decimal("150.0000000000"),
            "net_settlement_amount": Decimal("191088.8888888889"),
            "status": "approved",
            "approved_by": user_id,
            "approved_at": datetime(2025, 2, 20, 9, 0, 0, tzinfo=timezone.utc),
            "notes": "Acquisto BTP 4.0% 2037 — destinato a immobilizzazioni finanziarie",
        },
        # 4. Acquisto BOT 12M — zero coupon
        {
            "client_id": client_id,
            "security_id": sec_map["IT0005580110"].id,
            "transaction_type": "purchase",
            "trade_date": date(2025, 3, 5),
            "settlement_date": date(2025, 3, 7),
            "quantity": Decimal("100000.0000000000"),
            "unit_price": Decimal("97.1500000000"),
            "gross_amount": Decimal("97150.0000000000"),
            "accrued_interest": Decimal("0.0000000000"),
            "tel_quel_amount": Decimal("97150.0000000000"),
            "bank_commission": Decimal("30.0000000000"),
            "stamp_duty": Decimal("0.0000000000"),
            "tobin_tax": Decimal("0.0000000000"),
            "other_costs": Decimal("0.0000000000"),
            "total_transaction_costs": Decimal("30.0000000000"),
            "net_settlement_amount": Decimal("97180.0000000000"),
            "status": "approved",
            "approved_by": user_id,
            "approved_at": datetime(2025, 3, 5, 11, 0, 0, tzinfo=timezone.utc),
            "notes": "Acquisto BOT 12M — zero coupon, sconto di emissione",
        },
        # 5. Acquisto ENI corporate bond
        {
            "client_id": client_id,
            "security_id": sec_map["XS2456789012"].id,
            "transaction_type": "purchase",
            "trade_date": date(2025, 3, 15),
            "settlement_date": date(2025, 3, 19),
            "quantity": Decimal("50.0000000000"),
            "unit_price": Decimal("101.2500000000"),
            "gross_amount": Decimal("50625.0000000000"),
            "accrued_interest": Decimal("812.5000000000"),
            "tel_quel_amount": Decimal("51437.5000000000"),
            "bank_commission": Decimal("75.0000000000"),
            "stamp_duty": Decimal("0.0000000000"),
            "tobin_tax": Decimal("0.0000000000"),
            "other_costs": Decimal("0.0000000000"),
            "total_transaction_costs": Decimal("75.0000000000"),
            "net_settlement_amount": Decimal("51512.5000000000"),
            "status": "approved",
            "approved_by": user_id,
            "approved_at": datetime(2025, 3, 15, 15, 0, 0, tzinfo=timezone.utc),
            "notes": "Acquisto ENI 3.625% 2029 — corporate bond, nominale EUR 1000",
        },
        # 6. Incasso cedola BTP 2.0% 2028
        {
            "client_id": client_id,
            "security_id": sec_map["IT0005323032"].id,
            "transaction_type": "coupon_receipt",
            "trade_date": date(2025, 2, 1),
            "settlement_date": date(2025, 2, 1),
            "quantity": Decimal("50000.0000000000"),
            "unit_price": Decimal("100.0000000000"),
            "gross_amount": Decimal("0.0000000000"),
            "accrued_interest": Decimal("0.0000000000"),
            "tel_quel_amount": Decimal("0.0000000000"),
            "bank_commission": Decimal("0.0000000000"),
            "stamp_duty": Decimal("0.0000000000"),
            "tobin_tax": Decimal("0.0000000000"),
            "other_costs": Decimal("0.0000000000"),
            "total_transaction_costs": Decimal("0.0000000000"),
            "net_settlement_amount": Decimal("437.5000000000"),
            "coupon_gross": Decimal("500.0000000000"),
            "withholding_tax": Decimal("62.5000000000"),
            "coupon_net": Decimal("437.5000000000"),
            "status": "approved",
            "approved_by": user_id,
            "approved_at": datetime(2025, 2, 1, 8, 0, 0, tzinfo=timezone.utc),
            "notes": "Cedola semestrale BTP 2.0% — ritenuta 12.50% (titolo di Stato)",
        },
        # 7. Incasso cedola BTP 3.0% 2029
        {
            "client_id": client_id,
            "security_id": sec_map["IT0005365165"].id,
            "transaction_type": "coupon_receipt",
            "trade_date": date(2025, 8, 1),
            "settlement_date": date(2025, 8, 1),
            "quantity": Decimal("100000.0000000000"),
            "unit_price": Decimal("100.0000000000"),
            "gross_amount": Decimal("0.0000000000"),
            "accrued_interest": Decimal("0.0000000000"),
            "tel_quel_amount": Decimal("0.0000000000"),
            "bank_commission": Decimal("0.0000000000"),
            "stamp_duty": Decimal("0.0000000000"),
            "tobin_tax": Decimal("0.0000000000"),
            "other_costs": Decimal("0.0000000000"),
            "total_transaction_costs": Decimal("0.0000000000"),
            "net_settlement_amount": Decimal("1312.5000000000"),
            "coupon_gross": Decimal("1500.0000000000"),
            "withholding_tax": Decimal("187.5000000000"),
            "coupon_net": Decimal("1312.5000000000"),
            "status": "approved",
            "approved_by": user_id,
            "approved_at": datetime(2025, 8, 1, 8, 0, 0, tzinfo=timezone.utc),
            "notes": "Cedola semestrale BTP 3.0% — ritenuta 12.50%",
        },
        # 8. Incasso cedola ENI corporate (ritenuta 26%)
        {
            "client_id": client_id,
            "security_id": sec_map["XS2456789012"].id,
            "transaction_type": "coupon_receipt",
            "trade_date": date(2025, 10, 10),
            "settlement_date": date(2025, 10, 10),
            "quantity": Decimal("50.0000000000"),
            "unit_price": Decimal("100.0000000000"),
            "gross_amount": Decimal("0.0000000000"),
            "accrued_interest": Decimal("0.0000000000"),
            "tel_quel_amount": Decimal("0.0000000000"),
            "bank_commission": Decimal("0.0000000000"),
            "stamp_duty": Decimal("0.0000000000"),
            "tobin_tax": Decimal("0.0000000000"),
            "other_costs": Decimal("0.0000000000"),
            "total_transaction_costs": Decimal("0.0000000000"),
            "net_settlement_amount": Decimal("1341.2500000000"),
            "coupon_gross": Decimal("1812.5000000000"),
            "withholding_tax": Decimal("471.2500000000"),
            "coupon_net": Decimal("1341.2500000000"),
            "status": "approved",
            "approved_by": user_id,
            "approved_at": datetime(2025, 10, 10, 8, 0, 0, tzinfo=timezone.utc),
            "notes": "Cedola annuale ENI 3.625% — ritenuta 26.00% (corporate bond)",
        },
        # 9. Vendita parziale BTP 2.0% 2028 — plusvalenza
        {
            "client_id": client_id,
            "security_id": sec_map["IT0005323032"].id,
            "transaction_type": "sale",
            "trade_date": date(2025, 6, 15),
            "settlement_date": date(2025, 6, 17),
            "quantity": Decimal("20000.0000000000"),
            "unit_price": Decimal("99.2500000000"),
            "gross_amount": Decimal("19850.0000000000"),
            "accrued_interest": Decimal("148.8888888889"),
            "tel_quel_amount": Decimal("19998.8888888889"),
            "bank_commission": Decimal("30.0000000000"),
            "stamp_duty": Decimal("0.0000000000"),
            "tobin_tax": Decimal("0.0000000000"),
            "other_costs": Decimal("0.0000000000"),
            "total_transaction_costs": Decimal("30.0000000000"),
            "net_settlement_amount": Decimal("19968.8888888889"),
            "gain_loss": Decimal("350.0000000000"),
            "gain_loss_type": "plusvalenza",
            "status": "approved",
            "approved_by": user_id,
            "approved_at": datetime(2025, 6, 15, 16, 0, 0, tzinfo=timezone.utc),
            "notes": "Vendita parziale BTP 2.0% 2028 — plusvalenza da negoziazione",
        },
        # 10. Vendita BTP 3.0% 2029 parziale — minusvalenza
        {
            "client_id": client_id,
            "security_id": sec_map["IT0005365165"].id,
            "transaction_type": "sale",
            "trade_date": date(2025, 9, 20),
            "settlement_date": date(2025, 9, 22),
            "quantity": Decimal("30000.0000000000"),
            "unit_price": Decimal("101.0000000000"),
            "gross_amount": Decimal("30300.0000000000"),
            "accrued_interest": Decimal("122.5000000000"),
            "tel_quel_amount": Decimal("30422.5000000000"),
            "bank_commission": Decimal("40.0000000000"),
            "stamp_duty": Decimal("0.0000000000"),
            "tobin_tax": Decimal("0.0000000000"),
            "other_costs": Decimal("0.0000000000"),
            "total_transaction_costs": Decimal("40.0000000000"),
            "net_settlement_amount": Decimal("30382.5000000000"),
            "gain_loss": Decimal("-390.0000000000"),
            "gain_loss_type": "minusvalenza",
            "status": "approved",
            "approved_by": user_id,
            "approved_at": datetime(2025, 9, 20, 11, 0, 0, tzinfo=timezone.utc),
            "notes": "Vendita parziale BTP 3.0% 2029 — minusvalenza da negoziazione",
        },
    ]

    created = []
    async with async_session_factory() as session:
        for i, tx_data in enumerate(transactions_data, 1):
            tx = Transaction(**tx_data)
            session.add(tx)
            created.append(tx)
            print(f"  [new]  TX #{i}: {tx_data['transaction_type']} — {tx_data['notes'][:60]}")

        await session.commit()
        # Refresh to get IDs
        for tx in created:
            await session.refresh(tx)

    print(f"\nTransazioni: {len(created)} create")
    return created


async def generate_journal_entries(client_id, transactions: list[Transaction]) -> list[JournalEntry]:
    """Genera le scritture contabili per tutte le transazioni approvate.

    Le scritture seguono i template OIC 20:
    - Acquisto: DARE titoli / AVERE banca + rateo
    - Vendita con plusvalenza: DARE banca / AVERE titoli + plusvalenza
    - Vendita con minusvalenza: DARE banca + minusvalenza / AVERE titoli
    - Cedola: DARE banca + ritenute / AVERE interessi attivi
    """
    entries = []

    async with async_session_factory() as session:
        # Controlla se ci sono gia journal entries
        stmt = select(JournalEntry).where(JournalEntry.client_id == client_id)
        result = await session.execute(stmt)
        existing = result.scalars().all()
        if existing:
            print(f"  [skip] {len(existing)} scritture contabili gia presenti")
            return existing

        for tx in transactions:
            if tx.transaction_type == "purchase":
                entry = JournalEntry(
                    client_id=client_id,
                    transaction_id=tx.id,
                    entry_date=tx.settlement_date,
                    competence_date=tx.trade_date,
                    description=f"Acquisto titoli — regolamento {tx.settlement_date.isoformat()}",
                    entry_type="purchase_security",
                    fiscal_year=tx.trade_date.year,
                    status="generated",
                    generation_rule="OIC20_PURCHASE",
                )
                session.add(entry)
                await session.flush()

                lines = []
                line_num = 1

                # DARE: Titoli di debito (circolanti o immobilizzati)
                lines.append(JournalLine(
                    entry_id=entry.id,
                    line_number=line_num,
                    account_code="C.III.6",
                    account_name="Titoli di debito circolanti",
                    debit=tx.gross_amount + tx.total_transaction_costs,
                    credit=Decimal("0"),
                    description=f"Costo titolo + oneri accessori",
                ))
                line_num += 1

                # DARE: Rateo attivo (se presente)
                if tx.accrued_interest and tx.accrued_interest > 0:
                    lines.append(JournalLine(
                        entry_id=entry.id,
                        line_number=line_num,
                        account_code="D.18.d",
                        account_name="Ratei attivi su cedole",
                        debit=tx.accrued_interest,
                        credit=Decimal("0"),
                        description="Rateo interessi maturati dal cedente",
                    ))
                    line_num += 1

                # AVERE: Banca c/c
                lines.append(JournalLine(
                    entry_id=entry.id,
                    line_number=line_num,
                    account_code="C.IV.1",
                    account_name="Banca c/c",
                    debit=Decimal("0"),
                    credit=tx.net_settlement_amount,
                    description="Addebito c/c per regolamento",
                ))

                for line in lines:
                    session.add(line)
                entries.append(entry)

            elif tx.transaction_type == "sale":
                entry = JournalEntry(
                    client_id=client_id,
                    transaction_id=tx.id,
                    entry_date=tx.settlement_date,
                    competence_date=tx.trade_date,
                    description=f"Vendita titoli — regolamento {tx.settlement_date.isoformat()}",
                    entry_type="sale_security",
                    fiscal_year=tx.trade_date.year,
                    status="generated",
                    generation_rule="OIC20_SALE",
                )
                session.add(entry)
                await session.flush()

                lines = []
                line_num = 1

                # DARE: Banca c/c
                lines.append(JournalLine(
                    entry_id=entry.id,
                    line_number=line_num,
                    account_code="C.IV.1",
                    account_name="Banca c/c",
                    debit=tx.net_settlement_amount,
                    credit=Decimal("0"),
                    description="Accredito c/c per regolamento vendita",
                ))
                line_num += 1

                # Calcolo valore di carico proporzionale (semplificato)
                book_value_sold = tx.quantity * tx.unit_price / Decimal("100")

                if tx.gain_loss and tx.gain_loss > 0:
                    # Plusvalenza
                    # DARE: Commissioni
                    if tx.total_transaction_costs > 0:
                        lines.append(JournalLine(
                            entry_id=entry.id,
                            line_number=line_num,
                            account_code="B.14",
                            account_name="Commissioni e spese bancarie",
                            debit=tx.total_transaction_costs,
                            credit=Decimal("0"),
                            description="Commissioni di vendita",
                        ))
                        line_num += 1

                    # AVERE: Titoli
                    lines.append(JournalLine(
                        entry_id=entry.id,
                        line_number=line_num,
                        account_code="C.III.6",
                        account_name="Titoli di debito circolanti",
                        debit=Decimal("0"),
                        credit=book_value_sold,
                        description="Scarico titoli venduti al valore di carico",
                    ))
                    line_num += 1

                    # AVERE: Plusvalenza
                    plus_amount = tx.net_settlement_amount + tx.total_transaction_costs - book_value_sold
                    lines.append(JournalLine(
                        entry_id=entry.id,
                        line_number=line_num,
                        account_code="C.16.b",
                        account_name="Plusvalenze da negoziazione titoli",
                        debit=Decimal("0"),
                        credit=plus_amount,
                        description="Plusvalenza realizzata",
                    ))

                elif tx.gain_loss and tx.gain_loss < 0:
                    # Minusvalenza
                    minus_amount = book_value_sold - tx.net_settlement_amount - tx.total_transaction_costs
                    lines.append(JournalLine(
                        entry_id=entry.id,
                        line_number=line_num,
                        account_code="C.17.b",
                        account_name="Minusvalenze da negoziazione titoli",
                        debit=minus_amount,
                        credit=Decimal("0"),
                        description="Minusvalenza realizzata",
                    ))
                    line_num += 1

                    # DARE: Commissioni
                    if tx.total_transaction_costs > 0:
                        lines.append(JournalLine(
                            entry_id=entry.id,
                            line_number=line_num,
                            account_code="B.14",
                            account_name="Commissioni e spese bancarie",
                            debit=tx.total_transaction_costs,
                            credit=Decimal("0"),
                            description="Commissioni di vendita",
                        ))
                        line_num += 1

                    # AVERE: Titoli
                    lines.append(JournalLine(
                        entry_id=entry.id,
                        line_number=line_num,
                        account_code="C.III.6",
                        account_name="Titoli di debito circolanti",
                        debit=Decimal("0"),
                        credit=book_value_sold,
                        description="Scarico titoli venduti al valore di carico",
                    ))

                for line in lines:
                    session.add(line)
                entries.append(entry)

            elif tx.transaction_type == "coupon_receipt":
                entry = JournalEntry(
                    client_id=client_id,
                    transaction_id=tx.id,
                    entry_date=tx.settlement_date,
                    competence_date=tx.trade_date,
                    description=f"Incasso cedola — {tx.trade_date.isoformat()}",
                    entry_type="coupon_receipt",
                    fiscal_year=tx.trade_date.year,
                    status="generated",
                    generation_rule="OIC20_COUPON",
                )
                session.add(entry)
                await session.flush()

                lines = []
                line_num = 1

                # DARE: Banca c/c (netto)
                lines.append(JournalLine(
                    entry_id=entry.id,
                    line_number=line_num,
                    account_code="C.IV.1",
                    account_name="Banca c/c",
                    debit=tx.coupon_net,
                    credit=Decimal("0"),
                    description="Accredito cedola netta",
                ))
                line_num += 1

                # DARE: Erario c/ritenute (ritenuta fiscale)
                if tx.withholding_tax and tx.withholding_tax > 0:
                    lines.append(JournalLine(
                        entry_id=entry.id,
                        line_number=line_num,
                        account_code="C.II.5-bis",
                        account_name="Erario c/ritenute subite",
                        debit=tx.withholding_tax,
                        credit=Decimal("0"),
                        description="Ritenuta fiscale su cedola",
                    ))
                    line_num += 1

                # AVERE: Interessi attivi (lordo)
                lines.append(JournalLine(
                    entry_id=entry.id,
                    line_number=line_num,
                    account_code="C.16.a",
                    account_name="Interessi attivi su titoli",
                    debit=Decimal("0"),
                    credit=tx.coupon_gross,
                    description="Cedola lorda di competenza",
                ))

                for line in lines:
                    session.add(line)
                entries.append(entry)

        await session.commit()

    print(f"\nScritture contabili: {len(entries)} generate")
    return entries


async def main() -> None:
    """Entry point: crea l'intero ambiente demo."""
    print("=" * 60)
    print("  TitoliEngine — Seed ambiente demo")
    print("  OIC 20 - Titoli di debito")
    print("=" * 60)

    # 1. Studio
    print("\n[1/6] Creazione studio professionale...")
    studio = await create_studio()

    # 2. Utente
    print("\n[2/6] Creazione utente admin...")
    user = await create_user(studio.id)

    # 3. Cliente
    print("\n[3/6] Creazione cliente demo...")
    client = await create_client(studio.id)

    # 4. Piano dei conti OIC 20
    print("\n[4/6] Inserimento piano dei conti OIC 20...")
    await seed_chart_of_accounts(client.id)

    # 5. Anagrafica titoli
    print("\n[5/6] Inserimento anagrafica titoli...")
    await seed_securities()

    # 6. Transazioni e scritture contabili
    print("\n[6/6] Creazione transazioni e scritture contabili...")
    transactions = await create_sample_transactions(client.id, user.id)
    await generate_journal_entries(client.id, transactions)

    # Riepilogo
    print("\n" + "=" * 60)
    print("  RIEPILOGO AMBIENTE DEMO")
    print("=" * 60)
    print(f"  Studio:   {studio.name} (id: {studio.id})")
    print(f"  Utente:   {user.full_name} — {user.email}")
    print(f"            Password: demo2025")
    print(f"  Cliente:  {client.name} — P.IVA {client.tax_code}")
    print(f"  Client ID (per API): {client.id}")
    print("=" * 60)
    print("Ambiente demo pronto.")


if __name__ == "__main__":
    asyncio.run(main())
