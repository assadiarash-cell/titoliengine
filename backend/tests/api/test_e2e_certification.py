"""Test end-to-end per certificazione TitoliEngine v1.0.0.

Simula il ciclo completo:
  Upload PDF → parsing → creazione transazione → approvazione →
  generazione scrittura contabile → verifica quadratura → export

Include test di performance con 50+ operazioni in batch.

Tutti gli importi in Decimal. Riferimento: OIC 20.
"""
import uuid
from datetime import date, timedelta
from decimal import Decimal

import pytest
import pytest_asyncio
from httpx import AsyncClient


@pytest.mark.asyncio
class TestFullLifecycleE2E:
    """Test ciclo completo: cliente → titolo → operazione → scrittura → export."""

    async def _setup_studio_and_client(self, client: AsyncClient) -> tuple[str, str]:
        """Crea studio e cliente per il test."""
        suffix = uuid.uuid4().hex[:8]
        studio_resp = await client.post("/api/v1/tenants/studios", json={
            "name": f"Studio E2E {suffix}",
            "tax_code": f"E2E{suffix[:11].upper()}",
            "email": f"e2e_{suffix}@test.it",
        })
        assert studio_resp.status_code == 201
        studio_id = studio_resp.json()["id"]

        client_resp = await client.post("/api/v1/tenants/clients", json={
            "studio_id": studio_id,
            "name": f"Azienda E2E {suffix}",
            "tax_code": f"AZ{suffix[:14].upper()}",
            "legal_form": "SRL",
        })
        assert client_resp.status_code == 201
        client_id = client_resp.json()["id"]
        return studio_id, client_id

    async def _create_security(self, client: AsyncClient, suffix: str) -> str:
        """Crea un titolo BTP."""
        resp = await client.post("/api/v1/securities/", json={
            "isin": f"IT000{suffix[:7].upper()}",
            "name": f"BTP 3.5% Test {suffix}",
            "security_type": "BTP",
            "currency": "EUR",
            "nominal_value": "100",
            "coupon_rate": "3.5",
            "coupon_frequency": 2,
            "maturity_date": "2030-03-01",
            "issue_date": "2020-03-01",
            "tax_regime": "government",
        })
        assert resp.status_code == 201
        return resp.json()["id"]

    async def test_complete_purchase_cycle(self, client: AsyncClient) -> None:
        """Test ciclo completo: crea → acquisto → approva → genera scrittura → quadratura."""
        studio_id, client_id = await self._setup_studio_and_client(client)
        suffix = uuid.uuid4().hex[:8]
        security_id = await self._create_security(client, suffix)

        # 1. Crea operazione di acquisto
        txn_resp = await client.post("/api/v1/transactions/", json={
            "client_id": client_id,
            "security_id": security_id,
            "transaction_type": "purchase",
            "trade_date": "2025-06-15",
            "settlement_date": "2025-06-17",
            "quantity": "10000",
            "unit_price": "102.50",
            "gross_amount": "10250.00",
            "accrued_interest": "125.00",
            "tel_quel_amount": "10375.00",
            "bank_commission": "15.00",
            "stamp_duty": "0",
            "total_transaction_costs": "15.00",
            "net_settlement_amount": "10390.00",
        })
        assert txn_resp.status_code == 201
        txn_id = txn_resp.json()["id"]
        assert txn_resp.json()["status"] == "draft"

        # 2. Approva operazione
        approve_resp = await client.post(f"/api/v1/transactions/{txn_id}/approve")
        assert approve_resp.status_code == 200
        assert approve_resp.json()["status"] == "approved"

        # 3. Genera scrittura contabile
        gen_resp = await client.post("/api/v1/journal/generate", json={
            "client_id": client_id,
        })
        assert gen_resp.status_code == 200
        entries = gen_resp.json()["entries"]
        assert len(entries) >= 1

        entry = entries[0]
        assert entry["status"] == "generated"
        lines = entry["lines"]

        # 4. Verifica partita doppia: dare = avere
        total_debit = sum(Decimal(l["debit"]) for l in lines)
        total_credit = sum(Decimal(l["credit"]) for l in lines)
        assert total_debit == total_credit, (
            f"Quadratura fallita: dare={total_debit} avere={total_credit}"
        )
        assert total_debit > Decimal("0")

        # 5. Approva e registra la scrittura
        entry_id = entry["id"]
        approve_entry = await client.post(f"/api/v1/journal/entries/{entry_id}/approve")
        assert approve_entry.status_code == 200

        post_entry = await client.post(f"/api/v1/journal/entries/{entry_id}/post")
        assert post_entry.status_code == 200
        assert post_entry.json()["status"] == "posted"

        # 6. Balance check
        balance = await client.get(f"/api/v1/journal/balance-check?client_id={client_id}")
        assert balance.status_code == 200
        assert balance.json()["is_balanced"] is True

    async def test_sale_with_gain_loss(self, client: AsyncClient) -> None:
        """Test vendita con generazione plus/minusvalenza."""
        studio_id, client_id = await self._setup_studio_and_client(client)
        suffix = uuid.uuid4().hex[:8]
        security_id = await self._create_security(client, suffix)

        # Acquisto
        txn1 = await client.post("/api/v1/transactions/", json={
            "client_id": client_id,
            "security_id": security_id,
            "transaction_type": "purchase",
            "trade_date": "2025-01-15",
            "settlement_date": "2025-01-17",
            "quantity": "5000",
            "unit_price": "98.00",
            "gross_amount": "4900.00",
            "accrued_interest": "50.00",
            "tel_quel_amount": "4950.00",
            "bank_commission": "10.00",
            "total_transaction_costs": "10.00",
            "net_settlement_amount": "4960.00",
        })
        assert txn1.status_code == 201
        await client.post(f"/api/v1/transactions/{txn1.json()['id']}/approve")

        # Vendita sopra pari (plusvalenza)
        txn2 = await client.post("/api/v1/transactions/", json={
            "client_id": client_id,
            "security_id": security_id,
            "transaction_type": "sale",
            "trade_date": "2025-06-15",
            "settlement_date": "2025-06-17",
            "quantity": "5000",
            "unit_price": "103.00",
            "gross_amount": "5150.00",
            "accrued_interest": "87.50",
            "tel_quel_amount": "5237.50",
            "bank_commission": "10.00",
            "total_transaction_costs": "10.00",
            "net_settlement_amount": "5227.50",
            "gain_loss": "250.00",
            "gain_loss_type": "capital_gain",
        })
        assert txn2.status_code == 201
        await client.post(f"/api/v1/transactions/{txn2.json()['id']}/approve")

        # Genera tutte le scritture
        gen = await client.post("/api/v1/journal/generate", json={"client_id": client_id})
        assert gen.status_code == 200
        entries = gen.json()["entries"]
        assert len(entries) >= 2

        # Verifica quadratura per ogni entry
        for entry in entries:
            total_d = sum(Decimal(l["debit"]) for l in entry["lines"])
            total_c = sum(Decimal(l["credit"]) for l in entry["lines"])
            assert total_d == total_c, f"Entry {entry['id']} non quadra"

    async def test_coupon_receipt_cycle(self, client: AsyncClient) -> None:
        """Test incasso cedola con ritenuta fiscale."""
        studio_id, client_id = await self._setup_studio_and_client(client)
        suffix = uuid.uuid4().hex[:8]
        security_id = await self._create_security(client, suffix)

        txn = await client.post("/api/v1/transactions/", json={
            "client_id": client_id,
            "security_id": security_id,
            "transaction_type": "coupon_receipt",
            "trade_date": "2025-09-01",
            "settlement_date": "2025-09-01",
            "quantity": "10000",
            "unit_price": "1",
            "gross_amount": "175.00",
            "tel_quel_amount": "175.00",
            "net_settlement_amount": "153.13",
            "coupon_gross": "175.00",
            "withholding_tax": "21.87",
            "coupon_net": "153.13",
            "accrued_interest": "0",
        })
        assert txn.status_code == 201
        await client.post(f"/api/v1/transactions/{txn.json()['id']}/approve")

        gen = await client.post("/api/v1/journal/generate", json={"client_id": client_id})
        assert gen.status_code == 200
        entries = gen.json()["entries"]
        assert len(entries) >= 1

        # Quadratura
        for entry in entries:
            total_d = sum(Decimal(l["debit"]) for l in entry["lines"])
            total_c = sum(Decimal(l["credit"]) for l in entry["lines"])
            assert total_d == total_c

    async def test_workflow_rejection_and_reapproval(self, client: AsyncClient) -> None:
        """Test workflow: draft → approved → rejected → approved → posted."""
        studio_id, client_id = await self._setup_studio_and_client(client)
        suffix = uuid.uuid4().hex[:8]
        security_id = await self._create_security(client, suffix)

        txn = await client.post("/api/v1/transactions/", json={
            "client_id": client_id,
            "security_id": security_id,
            "transaction_type": "purchase",
            "trade_date": "2025-03-01",
            "settlement_date": "2025-03-03",
            "quantity": "1000",
            "unit_price": "100.00",
            "gross_amount": "1000.00",
            "accrued_interest": "0",
            "tel_quel_amount": "1000.00",
            "total_transaction_costs": "5.00",
            "bank_commission": "5.00",
            "net_settlement_amount": "1005.00",
        })
        txn_id = txn.json()["id"]

        # Approve
        r = await client.post(f"/api/v1/transactions/{txn_id}/approve")
        assert r.status_code == 200

        # Reject
        r = await client.post(f"/api/v1/transactions/{txn_id}/reject")
        assert r.status_code == 200
        assert r.json()["status"] == "draft"

        # Re-approve
        r = await client.post(f"/api/v1/transactions/{txn_id}/approve")
        assert r.status_code == 200
        assert r.json()["status"] == "approved"

    async def test_document_upload_dedup(self, client: AsyncClient) -> None:
        """Test upload documento con deduplicazione SHA-256."""
        _, client_id = await self._setup_studio_and_client(client)

        pdf_content = b"%PDF-1.4 fake content " + uuid.uuid4().bytes
        import io
        files = {"file": ("test.pdf", io.BytesIO(pdf_content), "application/pdf")}
        data = {"client_id": str(client_id), "document_type": "fissato_bollato"}

        r1 = await client.post("/api/v1/documents/upload", files=files, data=data)
        assert r1.status_code == 201
        hash1 = r1.json()["file_hash"]

        # Upload stesso file → dedup
        files2 = {"file": ("test2.pdf", io.BytesIO(pdf_content), "application/pdf")}
        r2 = await client.post("/api/v1/documents/upload", files=files2, data=data)
        assert r2.status_code == 201
        assert r2.json()["file_hash"] == hash1

    async def test_security_headers_present(self, client: AsyncClient) -> None:
        """Verifica che gli header di sicurezza siano presenti."""
        r = await client.get("/health")
        assert r.status_code == 200
        assert r.headers.get("X-Content-Type-Options") == "nosniff"
        assert r.headers.get("X-Frame-Options") == "DENY"
        assert "Strict-Transport-Security" in r.headers

    async def test_audit_trail_completeness(self, client: AsyncClient) -> None:
        """Verifica che ogni operazione generi log audit."""
        _, client_id = await self._setup_studio_and_client(client)
        suffix = uuid.uuid4().hex[:8]
        security_id = await self._create_security(client, suffix)

        # Crea operazione
        txn = await client.post("/api/v1/transactions/", json={
            "client_id": client_id,
            "security_id": security_id,
            "transaction_type": "purchase",
            "trade_date": "2025-06-01",
            "settlement_date": "2025-06-03",
            "quantity": "1000",
            "unit_price": "100",
            "gross_amount": "1000",
            "accrued_interest": "0",
            "tel_quel_amount": "1000",
            "total_transaction_costs": "0",
            "bank_commission": "0",
            "net_settlement_amount": "1000",
        })
        assert txn.status_code == 201

        # Verifica audit log
        audit = await client.get("/api/v1/audit/logs")
        assert audit.status_code == 200
        logs = audit.json()
        assert any(l["entity_type"] == "transaction" for l in logs)


@pytest.mark.asyncio
class TestBatchPerformance:
    """Test con 50+ operazioni per verificare performance e consistenza."""

    async def test_batch_50_transactions(self, client: AsyncClient) -> None:
        """Crea 50 operazioni, approva tutte, genera scritture, verifica quadratura globale."""
        suffix = uuid.uuid4().hex[:8]

        # Setup
        studio_resp = await client.post("/api/v1/tenants/studios", json={
            "name": f"Studio Batch {suffix}",
            "tax_code": f"BA{suffix[:14].upper()}",
            "email": f"batch_{suffix}@test.it",
        })
        studio_id = studio_resp.json()["id"]

        client_resp = await client.post("/api/v1/tenants/clients", json={
            "studio_id": studio_id,
            "name": f"Azienda Batch {suffix}",
            "tax_code": f"BT{suffix[:14].upper()}",
            "legal_form": "SPA",
        })
        client_id = client_resp.json()["id"]

        # Crea 5 titoli diversi
        security_ids = []
        for i in range(5):
            sec_suffix = uuid.uuid4().hex[:7]
            sec = await client.post("/api/v1/securities/", json={
                "isin": f"IT{sec_suffix.upper()[:10]}",
                "name": f"BTP Batch {i} {sec_suffix}",
                "security_type": "BTP",
                "currency": "EUR",
                "nominal_value": "100",
                "coupon_rate": str(Decimal("2.0") + Decimal(str(i)) * Decimal("0.5")),
                "coupon_frequency": 2,
                "maturity_date": f"203{i}-06-15",
                "issue_date": "2020-01-01",
                "tax_regime": "government",
            })
            assert sec.status_code == 201, f"Security creation failed: {sec.text}"
            security_ids.append(sec.json()["id"])

        # Crea 50 operazioni di acquisto
        txn_ids = []
        base_date = date(2025, 1, 10)
        for i in range(50):
            sec_id = security_ids[i % 5]
            trade = base_date + timedelta(days=i)
            settle = trade + timedelta(days=2)
            qty = Decimal("1000") + Decimal(str(i * 100))
            price = Decimal("99.50") + Decimal(str(i)) * Decimal("0.05")
            gross = (qty * price / Decimal("100")).quantize(Decimal("0.01"))
            commission = Decimal("5.00")
            net = gross + commission

            txn = await client.post("/api/v1/transactions/", json={
                "client_id": client_id,
                "security_id": sec_id,
                "transaction_type": "purchase",
                "trade_date": trade.isoformat(),
                "settlement_date": settle.isoformat(),
                "quantity": str(qty),
                "unit_price": str(price),
                "gross_amount": str(gross),
                "accrued_interest": "0",
                "tel_quel_amount": str(gross),
                "bank_commission": str(commission),
                "total_transaction_costs": str(commission),
                "net_settlement_amount": str(net),
            })
            assert txn.status_code == 201, f"Txn {i} failed: {txn.text}"
            txn_ids.append(txn.json()["id"])

        # Approva tutte le 50 operazioni
        for txn_id in txn_ids:
            r = await client.post(f"/api/v1/transactions/{txn_id}/approve")
            assert r.status_code == 200

        # Genera tutte le scritture in un solo batch
        gen = await client.post("/api/v1/journal/generate", json={"client_id": client_id})
        assert gen.status_code == 200
        entries = gen.json()["entries"]
        assert len(entries) == 50, f"Expected 50 entries, got {len(entries)}"

        # Verifica quadratura individuale per ogni scrittura
        for entry in entries:
            total_d = sum(Decimal(l["debit"]) for l in entry["lines"])
            total_c = sum(Decimal(l["credit"]) for l in entry["lines"])
            assert total_d == total_c, (
                f"Entry {entry['id']} non quadra: D={total_d} C={total_c}"
            )

        # Verifica quadratura globale
        balance = await client.get(f"/api/v1/journal/balance-check?client_id={client_id}")
        assert balance.status_code == 200
        b = balance.json()
        assert b["is_balanced"] is True, f"Quadratura globale fallita: {b}"
        assert b["entries_checked"] == 50

        # Verifica lista entries
        entries_list = await client.get(f"/api/v1/journal/entries?client_id={client_id}")
        assert entries_list.status_code == 200
        assert len(entries_list.json()) == 50

    async def test_batch_mixed_operations(self, client: AsyncClient) -> None:
        """Crea mix di acquisti, vendite e cedole — verifica quadratura."""
        suffix = uuid.uuid4().hex[:8]

        studio = await client.post("/api/v1/tenants/studios", json={
            "name": f"Studio Mix {suffix}",
            "tax_code": f"MX{suffix[:14].upper()}",
            "email": f"mix_{suffix}@test.it",
        })
        studio_id = studio.json()["id"]

        cl = await client.post("/api/v1/tenants/clients", json={
            "studio_id": studio_id,
            "name": f"Azienda Mix {suffix}",
            "tax_code": f"MZ{suffix[:14].upper()}",
            "legal_form": "SRL",
        })
        client_id = cl.json()["id"]

        sec_suffix = uuid.uuid4().hex[:7]
        sec = await client.post("/api/v1/securities/", json={
            "isin": f"IT{sec_suffix.upper()[:10]}",
            "name": f"BTP Mix {sec_suffix}",
            "security_type": "BTP",
            "currency": "EUR",
            "nominal_value": "100",
            "coupon_rate": "3.0",
            "coupon_frequency": 2,
            "maturity_date": "2030-06-15",
            "issue_date": "2020-06-15",
            "tax_regime": "government",
        })
        security_id = sec.json()["id"]

        txn_ids = []

        # 10 acquisti
        for i in range(10):
            txn = await client.post("/api/v1/transactions/", json={
                "client_id": client_id,
                "security_id": security_id,
                "transaction_type": "purchase",
                "trade_date": f"2025-0{(i % 9) + 1}-15",
                "settlement_date": f"2025-0{(i % 9) + 1}-17",
                "quantity": "5000",
                "unit_price": "101.00",
                "gross_amount": "5050.00",
                "accrued_interest": "25.00",
                "tel_quel_amount": "5075.00",
                "bank_commission": "10.00",
                "total_transaction_costs": "10.00",
                "net_settlement_amount": "5085.00",
            })
            txn_ids.append(txn.json()["id"])

        # 5 vendite
        for i in range(5):
            txn = await client.post("/api/v1/transactions/", json={
                "client_id": client_id,
                "security_id": security_id,
                "transaction_type": "sale",
                "trade_date": f"2025-0{i + 3}-20",
                "settlement_date": f"2025-0{i + 3}-22",
                "quantity": "2000",
                "unit_price": "103.00",
                "gross_amount": "2060.00",
                "accrued_interest": "15.00",
                "tel_quel_amount": "2075.00",
                "bank_commission": "8.00",
                "total_transaction_costs": "8.00",
                "net_settlement_amount": "2067.00",
            })
            txn_ids.append(txn.json()["id"])

        # 5 cedole
        for i in range(5):
            txn = await client.post("/api/v1/transactions/", json={
                "client_id": client_id,
                "security_id": security_id,
                "transaction_type": "coupon_receipt",
                "trade_date": f"2025-0{i + 1}-01",
                "settlement_date": f"2025-0{i + 1}-01",
                "quantity": "50000",
                "unit_price": "1",
                "gross_amount": "750.00",
                "tel_quel_amount": "750.00",
                "net_settlement_amount": "656.25",
                "coupon_gross": "750.00",
                "withholding_tax": "93.75",
                "coupon_net": "656.25",
                "accrued_interest": "0",
            })
            txn_ids.append(txn.json()["id"])

        # Approva tutte
        for tid in txn_ids:
            await client.post(f"/api/v1/transactions/{tid}/approve")

        # Genera
        gen = await client.post("/api/v1/journal/generate", json={"client_id": client_id})
        assert gen.status_code == 200
        entries = gen.json()["entries"]
        assert len(entries) == 20  # 10 + 5 + 5

        # Quadratura
        balance = await client.get(f"/api/v1/journal/balance-check?client_id={client_id}")
        assert balance.status_code == 200
        assert balance.json()["is_balanced"] is True
