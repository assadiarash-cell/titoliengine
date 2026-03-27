"""
Test integrazione per le nuove API: documents, valuations, reports, export, audit, parser.

Ogni test crea i propri dati con ID unici per evitare conflitti.
"""
import io
import uuid
from decimal import Decimal

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


# ── Helper ───────────────────────────────────────────────────

async def _create_studio(c: AsyncClient) -> dict:
    tax = f"TC{uuid.uuid4().hex[:10].upper()}"
    resp = await c.post(
        "/api/v1/tenants/studios",
        json={"name": "StudioTest", "tax_code": tax, "email": f"s{tax}@test.it"},
    )
    assert resp.status_code == 201
    return resp.json()


async def _create_client(c: AsyncClient, studio_id: str) -> dict:
    tax = f"CL{uuid.uuid4().hex[:10].upper()}"
    resp = await c.post(
        "/api/v1/tenants/clients",
        json={
            "studio_id": studio_id,
            "name": "Azienda SRL",
            "tax_code": tax,
            "legal_form": "SRL",
        },
    )
    assert resp.status_code == 201
    return resp.json()


async def _create_security(c: AsyncClient) -> dict:
    isin = f"IT{uuid.uuid4().hex[:10].upper()}"
    resp = await c.post(
        "/api/v1/securities/",
        json={
            "isin": isin,
            "name": "BTP Test",
            "security_type": "btp",
            "issuer": "Repubblica Italiana",
            "nominal_value": "100000",
            "coupon_rate": "0.035",
            "coupon_frequency": 2,
            "maturity_date": "2030-03-01",
            "tax_regime": "governo_12_5",
            "withholding_rate": "0.1250",
        },
    )
    assert resp.status_code == 201
    return resp.json()


async def _create_full_setup(c: AsyncClient):
    """Crea studio + client + security + purchase transaction approvata."""
    studio = await _create_studio(c)
    cl = await _create_client(c, studio["id"])
    sec = await _create_security(c)

    # Crea transazione acquisto
    resp = await c.post(
        "/api/v1/transactions/",
        json={
            "client_id": cl["id"],
            "security_id": sec["id"],
            "transaction_type": "purchase",
            "trade_date": "2025-05-15",
            "settlement_date": "2025-05-17",
            "quantity": "100000",
            "unit_price": "101.20",
            "gross_amount": "101200.00",
            "accrued_interest": "713.32",
            "tel_quel_amount": "101913.32",
            "bank_commission": "166.00",
            "total_transaction_costs": "166.00",
            "net_settlement_amount": "102079.32",
        },
    )
    assert resp.status_code == 201
    txn = resp.json()

    # Approva
    await c.post(f"/api/v1/transactions/{txn['id']}/approve")

    # Genera scrittura
    await c.post(
        "/api/v1/journal/generate",
        json={"client_id": cl["id"], "transaction_ids": [txn["id"]]},
    )

    return studio, cl, sec, txn


# ── Test Documents API ───────────────────────────────────────

class TestDocumentsAPI:
    async def test_upload_document(self, client: AsyncClient) -> None:
        studio = await _create_studio(client)
        cl = await _create_client(client, studio["id"])

        # Upload un file finto
        fake_pdf = b"%PDF-1.4 fake content for testing"
        resp = await client.post(
            "/api/v1/documents/upload",
            files={"file": ("test.pdf", io.BytesIO(fake_pdf), "application/pdf")},
            data={
                "client_id": cl["id"],
                "document_type": "fissato_bollato",
                "bank_name": "Banca Test",
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["document_type"] == "fissato_bollato"
        assert data["file_hash"]  # SHA-256 hash presente
        assert len(data["file_hash"]) == 64  # SHA-256 = 64 hex chars

    async def test_upload_dedup(self, client: AsyncClient) -> None:
        studio = await _create_studio(client)
        cl = await _create_client(client, studio["id"])

        content = b"identical content for dedup test " + uuid.uuid4().bytes
        # Upload 1
        r1 = await client.post(
            "/api/v1/documents/upload",
            files={"file": ("a.pdf", io.BytesIO(content), "application/pdf")},
            data={"client_id": cl["id"], "document_type": "fissato_bollato"},
        )
        assert r1.status_code == 201

        # Upload 2 — stesso contenuto → restituisce il primo
        r2 = await client.post(
            "/api/v1/documents/upload",
            files={"file": ("b.pdf", io.BytesIO(content), "application/pdf")},
            data={"client_id": cl["id"], "document_type": "fissato_bollato"},
        )
        assert r2.status_code == 200 or r2.status_code == 201
        assert r2.json()["id"] == r1.json()["id"]

    async def test_list_documents(self, client: AsyncClient) -> None:
        studio = await _create_studio(client)
        cl = await _create_client(client, studio["id"])

        content = b"list test " + uuid.uuid4().bytes
        await client.post(
            "/api/v1/documents/upload",
            files={"file": ("t.pdf", io.BytesIO(content), "application/pdf")},
            data={"client_id": cl["id"], "document_type": "cedolino"},
        )

        resp = await client.get("/api/v1/documents/", params={"client_id": cl["id"]})
        assert resp.status_code == 200
        assert len(resp.json()) >= 1

    async def test_get_document_detail(self, client: AsyncClient) -> None:
        studio = await _create_studio(client)
        cl = await _create_client(client, studio["id"])

        content = b"detail test " + uuid.uuid4().bytes
        r = await client.post(
            "/api/v1/documents/upload",
            files={"file": ("d.pdf", io.BytesIO(content), "application/pdf")},
            data={"client_id": cl["id"], "document_type": "estratto_conto"},
        )
        doc_id = r.json()["id"]

        resp = await client.get(f"/api/v1/documents/{doc_id}")
        assert resp.status_code == 200
        assert resp.json()["original_filename"] == "d.pdf"

    async def test_get_document_not_found(self, client: AsyncClient) -> None:
        resp = await client.get(f"/api/v1/documents/{uuid.uuid4()}")
        assert resp.status_code == 404


# ── Test Valuations API ──────────────────────────────────────

class TestValuationsAPI:
    async def test_import_market_price(self, client: AsyncClient) -> None:
        sec = await _create_security(client)
        resp = await client.post(
            "/api/v1/valuations/market-prices",
            json={
                "security_id": sec["id"],
                "price_date": "2025-12-31",
                "close_price": "99.50",
                "source": "manual",
            },
        )
        assert resp.status_code == 201
        assert resp.json()["close_price"] == "99.50"

    async def test_bulk_import_prices(self, client: AsyncClient) -> None:
        sec = await _create_security(client)
        resp = await client.post(
            "/api/v1/valuations/market-prices/bulk",
            json={
                "prices": [
                    {
                        "security_id": sec["id"],
                        "price_date": "2025-12-30",
                        "close_price": "98.75",
                    },
                    {
                        "security_id": sec["id"],
                        "price_date": "2025-12-31",
                        "close_price": "99.00",
                    },
                ]
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["imported"] == 2
        assert data["skipped"] == 0

    async def test_year_end_valuation_no_positions(self, client: AsyncClient) -> None:
        studio = await _create_studio(client)
        cl = await _create_client(client, studio["id"])

        resp = await client.post(
            "/api/v1/valuations/year-end",
            json={
                "client_id": cl["id"],
                "valuation_date": "2025-12-31",
                "fiscal_year": 2025,
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["positions_evaluated"] == 0

    async def test_list_valuations(self, client: AsyncClient) -> None:
        studio = await _create_studio(client)
        cl = await _create_client(client, studio["id"])

        resp = await client.get(
            "/api/v1/valuations/",
            params={"client_id": cl["id"]},
        )
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)


# ── Test Reports API ─────────────────────────────────────────

class TestReportsAPI:
    async def test_portfolio_report_empty(self, client: AsyncClient) -> None:
        studio = await _create_studio(client)
        cl = await _create_client(client, studio["id"])

        resp = await client.get(
            "/api/v1/reports/portfolio",
            params={"client_id": cl["id"], "report_date": "2025-12-31"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_book_value"] == "0"
        assert data["positions"] == []

    async def test_gains_losses_report(self, client: AsyncClient) -> None:
        studio = await _create_studio(client)
        cl = await _create_client(client, studio["id"])

        resp = await client.get(
            "/api/v1/reports/gains-losses",
            params={
                "client_id": cl["id"],
                "date_from": "2025-01-01",
                "date_to": "2025-12-31",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_gains"] == "0.00"
        assert data["total_losses"] == "0.00"

    async def test_tax_summary(self, client: AsyncClient) -> None:
        studio = await _create_studio(client)
        cl = await _create_client(client, studio["id"])

        resp = await client.get(
            "/api/v1/reports/tax-summary",
            params={"client_id": cl["id"], "fiscal_year": 2025},
        )
        assert resp.status_code == 200
        assert resp.json()["fiscal_year"] == 2025

    async def test_oic20_report(self, client: AsyncClient) -> None:
        studio = await _create_studio(client)
        cl = await _create_client(client, studio["id"])

        resp = await client.get(
            "/api/v1/reports/oic20",
            params={"client_id": cl["id"], "fiscal_year": 2025},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["fiscal_year"] == 2025
        assert data["securities"] == []

    async def test_societa_comodo(self, client: AsyncClient) -> None:
        resp = await client.post(
            "/api/v1/reports/societa-comodo",
            json={
                "titoli_e_crediti": "500000",
                "immobili": "1000000",
                "immobili_a10": "200000",
                "altre_immobilizzazioni": "100000",
                "actual_revenue": "50000",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "is_comodo" in data
        assert "minimum_revenue" in data
        # Con 500k titoli (2%) + 1M immobili (6%) + 200k A10 (5%) + 100k altre (15%)
        # = 10000 + 60000 + 10000 + 15000 = 95000
        # actual_revenue 50000 < 95000 → is_comodo = True
        assert data["is_comodo"] is True


# ── Test Export API ──────────────────────────────────────────

class TestExportAPI:
    async def test_journal_csv_export(self, client: AsyncClient) -> None:
        _, cl, _, _ = await _create_full_setup(client)

        resp = await client.get(
            "/api/v1/export/journal/csv",
            params={"client_id": cl["id"]},
        )
        assert resp.status_code == 200
        assert "text/csv" in resp.headers["content-type"]
        content = resp.text
        assert "entry_id" in content  # Header presente
        assert "account_code" in content

    async def test_portfolio_csv_export(self, client: AsyncClient) -> None:
        studio = await _create_studio(client)
        cl = await _create_client(client, studio["id"])

        resp = await client.get(
            "/api/v1/export/portfolio/csv",
            params={"client_id": cl["id"]},
        )
        assert resp.status_code == 200
        assert "text/csv" in resp.headers["content-type"]

    async def test_profis_export(self, client: AsyncClient) -> None:
        studio = await _create_studio(client)
        cl = await _create_client(client, studio["id"])

        resp = await client.get(
            "/api/v1/export/gestionale/profis",
            params={"client_id": cl["id"]},
        )
        assert resp.status_code == 200
        assert "TIPO_REG" in resp.text

    async def test_teamsystem_export(self, client: AsyncClient) -> None:
        studio = await _create_studio(client)
        cl = await _create_client(client, studio["id"])

        resp = await client.get(
            "/api/v1/export/gestionale/teamsystem",
            params={"client_id": cl["id"]},
        )
        assert resp.status_code == 200
        assert "NUMERO_REG" in resp.text


# ── Test Audit API ───────────────────────────────────────────

class TestAuditAPI:
    async def test_list_audit_logs(self, client: AsyncClient) -> None:
        # Crea dati per generare audit entries
        studio = await _create_studio(client)
        cl = await _create_client(client, studio["id"])

        resp = await client.get(
            "/api/v1/audit/logs",
            params={"client_id": cl["id"]},
        )
        assert resp.status_code == 200
        logs = resp.json()
        assert len(logs) >= 1  # Almeno il create del client

    async def test_audit_logs_filter_by_action(self, client: AsyncClient) -> None:
        studio = await _create_studio(client)
        cl = await _create_client(client, studio["id"])

        resp = await client.get(
            "/api/v1/audit/logs",
            params={"entity_type": "client", "action": "create"},
        )
        assert resp.status_code == 200
        for log in resp.json():
            assert log["action"] == "create"
            assert log["entity_type"] == "client"

    async def test_entity_history(self, client: AsyncClient) -> None:
        studio = await _create_studio(client)
        cl = await _create_client(client, studio["id"])

        # Aggiorna il client per avere 2 audit entries
        await client.put(
            f"/api/v1/tenants/clients/{cl['id']}",
            json={"balance_type": "abbreviato"},
        )

        resp = await client.get(
            f"/api/v1/audit/entity/client/{cl['id']}",
        )
        assert resp.status_code == 200
        logs = resp.json()
        assert len(logs) >= 2  # create + update


# ── Test Parser (unit-level, senza PDF reali) ────────────────

class TestParserBase:
    def test_parse_result_to_dict(self) -> None:
        from app.parser.base import ExtractedField, ParseResult

        result = ParseResult()
        result.fields["isin"] = ExtractedField(
            name="isin", value="IT0005580094", confidence=0.95
        )
        d = result.to_dict()
        assert d["fields"]["isin"]["value"] == "IT0005580094"
        assert d["fields"]["isin"]["confidence"] == 0.95

    def test_cross_validate_detects_errors(self) -> None:
        from app.parser.base import ExtractedField, ParseResult
        from app.parser.pdf_extractor import PDFExtractor
        from decimal import Decimal

        result = ParseResult(overall_confidence=0.90)
        result.fields["gross_amount"] = ExtractedField(
            name="gross_amount", value=Decimal("100000")
        )
        result.fields["accrued_interest"] = ExtractedField(
            name="accrued_interest", value=Decimal("500")
        )
        result.fields["tel_quel_amount"] = ExtractedField(
            name="tel_quel_amount", value=Decimal("999999")  # Sbagliato
        )

        parser = PDFExtractor()
        validated = parser.cross_validate(result)
        assert len(validated.warnings) >= 1
        assert validated.overall_confidence < 0.90

    def test_reconciler_match(self) -> None:
        from app.parser.reconciler import TransactionReconciler
        from decimal import Decimal

        rec = TransactionReconciler()
        result = rec.reconcile_with_statement(
            transaction_amount=Decimal("102079.32"),
            statement_amount=Decimal("102079.32"),
        )
        assert result.is_reconciled is True
        assert len(result.discrepancies) == 0

    def test_reconciler_mismatch(self) -> None:
        from app.parser.reconciler import TransactionReconciler
        from decimal import Decimal

        rec = TransactionReconciler()
        result = rec.reconcile_with_statement(
            transaction_amount=Decimal("102079.32"),
            statement_amount=Decimal("100000.00"),
        )
        assert result.is_reconciled is False
        assert len(result.discrepancies) >= 1
        assert result.has_errors

    def test_reconciler_document_vs_transaction(self) -> None:
        from app.parser.reconciler import TransactionReconciler
        from decimal import Decimal

        rec = TransactionReconciler()
        result = rec.reconcile_document_vs_transaction(
            document_data={
                "net_settlement_amount": Decimal("102079.32"),
                "gross_amount": Decimal("101200.00"),
                "isin": "IT0005580094",
            },
            transaction_data={
                "net_settlement_amount": Decimal("102079.32"),
                "gross_amount": Decimal("101200.00"),
                "isin": "IT0005580094",
            },
        )
        assert result.is_reconciled is True

    def test_reconciler_isin_mismatch_is_critical(self) -> None:
        from app.parser.reconciler import TransactionReconciler

        rec = TransactionReconciler()
        result = rec.reconcile_document_vs_transaction(
            document_data={"isin": "IT0005580094"},
            transaction_data={"isin": "IT9999999999"},
        )
        assert any(d.severity.value == "critical" for d in result.discrepancies)
