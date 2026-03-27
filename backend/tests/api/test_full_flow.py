"""
Test integrazione API — flusso completo end-to-end.

Ogni test crea i propri dati con tax_code/ISIN unici
per evitare conflitti di unicità nel DB condiviso.
"""
import uuid
from decimal import Decimal

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio

# ── Helper per creare dati con ID unici ───────────────────────

async def _create_studio(c: AsyncClient, suffix: str = "") -> dict:
    tax = f"TC{uuid.uuid4().hex[:10].upper()}"
    resp = await c.post(
        "/api/v1/tenants/studios",
        json={"name": f"Studio{suffix}", "tax_code": tax, "email": f"s{tax}@test.it"},
    )
    assert resp.status_code == 201
    return resp.json()


async def _create_client(c: AsyncClient, studio_id: str, suffix: str = "") -> dict:
    tax = f"CL{uuid.uuid4().hex[:10].upper()}"
    resp = await c.post(
        "/api/v1/tenants/clients",
        json={
            "studio_id": studio_id,
            "name": f"Azienda{suffix} SRL",
            "tax_code": tax,
            "legal_form": "SRL",
        },
    )
    assert resp.status_code == 201
    return resp.json()


async def _create_security(c: AsyncClient, suffix: str = "") -> dict:
    isin = f"IT{uuid.uuid4().hex[:10].upper()}"
    resp = await c.post(
        "/api/v1/securities/",
        json={
            "isin": isin,
            "name": f"BTP Test{suffix}",
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


async def _create_purchase_txn(
    c: AsyncClient, client_id: str, security_id: str
) -> dict:
    resp = await c.post(
        "/api/v1/transactions/",
        json={
            "client_id": client_id,
            "security_id": security_id,
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
    return resp.json()


# ── Test classes ──────────────────────────────────────────────

class TestHealthCheck:
    async def test_health(self, client: AsyncClient) -> None:
        resp = await client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"


class TestTenantsAPI:
    async def test_create_studio(self, client: AsyncClient) -> None:
        data = await _create_studio(client)
        assert data["is_active"] is True

    async def test_create_and_list_clients(self, client: AsyncClient) -> None:
        studio = await _create_studio(client)
        cl = await _create_client(client, studio["id"])
        resp = await client.get("/api/v1/tenants/clients", params={"studio_id": studio["id"]})
        assert resp.status_code == 200
        assert any(c["id"] == cl["id"] for c in resp.json())

    async def test_get_client(self, client: AsyncClient) -> None:
        studio = await _create_studio(client)
        cl = await _create_client(client, studio["id"])
        resp = await client.get(f"/api/v1/tenants/clients/{cl['id']}")
        assert resp.status_code == 200
        assert resp.json()["id"] == cl["id"]

    async def test_update_client(self, client: AsyncClient) -> None:
        studio = await _create_studio(client)
        cl = await _create_client(client, studio["id"])
        resp = await client.put(
            f"/api/v1/tenants/clients/{cl['id']}",
            json={"balance_type": "abbreviato"},
        )
        assert resp.status_code == 200
        assert resp.json()["balance_type"] == "abbreviato"

    async def test_chart_of_accounts_crud(self, client: AsyncClient) -> None:
        studio = await _create_studio(client)
        cl = await _create_client(client, studio["id"])
        cid = cl["id"]

        # Create
        resp = await client.post(
            f"/api/v1/tenants/clients/{cid}/accounts",
            json={"code": "B.III.3.a", "name": "Titoli immobilizzati", "account_type": "asset"},
        )
        assert resp.status_code == 201

        # List
        resp = await client.get(f"/api/v1/tenants/clients/{cid}/accounts")
        assert resp.status_code == 200
        assert len(resp.json()) >= 1


class TestSecuritiesAPI:
    async def test_create_security(self, client: AsyncClient) -> None:
        data = await _create_security(client)
        assert data["security_type"] == "btp"

    async def test_list_securities(self, client: AsyncClient) -> None:
        await _create_security(client)
        resp = await client.get("/api/v1/securities/")
        assert resp.status_code == 200
        assert len(resp.json()) >= 1

    async def test_get_security(self, client: AsyncClient) -> None:
        sec = await _create_security(client)
        resp = await client.get(f"/api/v1/securities/{sec['id']}")
        assert resp.status_code == 200
        assert resp.json()["id"] == sec["id"]

    async def test_lookup_isin(self, client: AsyncClient) -> None:
        sec = await _create_security(client)
        resp = await client.get(f"/api/v1/securities/lookup/{sec['isin']}")
        assert resp.status_code == 200
        assert resp.json()["isin"] == sec["isin"]

    async def test_lookup_isin_not_found(self, client: AsyncClient) -> None:
        resp = await client.get("/api/v1/securities/lookup/XX0000000000")
        assert resp.status_code == 404

    async def test_update_security(self, client: AsyncClient) -> None:
        sec = await _create_security(client)
        resp = await client.put(
            f"/api/v1/securities/{sec['id']}",
            json={"issuer": "Rep. Italiana"},
        )
        assert resp.status_code == 200
        assert resp.json()["issuer"] == "Rep. Italiana"

    async def test_delete_security(self, client: AsyncClient) -> None:
        sec = await _create_security(client)
        resp = await client.delete(f"/api/v1/securities/{sec['id']}")
        assert resp.status_code == 204


class TestTransactionsAPI:
    async def test_create_transaction(self, client: AsyncClient) -> None:
        studio = await _create_studio(client)
        cl = await _create_client(client, studio["id"])
        sec = await _create_security(client)
        txn = await _create_purchase_txn(client, cl["id"], sec["id"])
        assert txn["status"] == "draft"
        assert txn["transaction_type"] == "purchase"

    async def test_validation_quantity_positive(self, client: AsyncClient) -> None:
        studio = await _create_studio(client)
        cl = await _create_client(client, studio["id"])
        sec = await _create_security(client)
        resp = await client.post(
            "/api/v1/transactions/",
            json={
                "client_id": cl["id"],
                "security_id": sec["id"],
                "transaction_type": "purchase",
                "trade_date": "2025-05-15",
                "settlement_date": "2025-05-17",
                "quantity": "-100",
                "unit_price": "100",
                "gross_amount": "10000",
                "tel_quel_amount": "10000",
                "net_settlement_amount": "10000",
            },
        )
        assert resp.status_code == 422

    async def test_validation_settlement_after_trade(self, client: AsyncClient) -> None:
        studio = await _create_studio(client)
        cl = await _create_client(client, studio["id"])
        sec = await _create_security(client)
        resp = await client.post(
            "/api/v1/transactions/",
            json={
                "client_id": cl["id"],
                "security_id": sec["id"],
                "transaction_type": "purchase",
                "trade_date": "2025-05-15",
                "settlement_date": "2025-05-10",
                "quantity": "100",
                "unit_price": "100",
                "gross_amount": "10000",
                "tel_quel_amount": "10000",
                "net_settlement_amount": "10000",
            },
        )
        assert resp.status_code == 422

    async def test_approve_reject_workflow(self, client: AsyncClient) -> None:
        studio = await _create_studio(client)
        cl = await _create_client(client, studio["id"])
        sec = await _create_security(client)
        txn = await _create_purchase_txn(client, cl["id"], sec["id"])

        # Approve
        resp = await client.post(f"/api/v1/transactions/{txn['id']}/approve")
        assert resp.status_code == 200
        assert resp.json()["status"] == "approved"

        # Reject → back to draft
        resp = await client.post(f"/api/v1/transactions/{txn['id']}/reject")
        assert resp.status_code == 200
        assert resp.json()["status"] == "draft"

    async def test_cannot_approve_nonexistent(self, client: AsyncClient) -> None:
        resp = await client.post(f"/api/v1/transactions/{uuid.uuid4()}/approve")
        assert resp.status_code == 400


class TestAuthAPI:
    async def test_login_invalid_credentials(self, client: AsyncClient) -> None:
        resp = await client.post(
            "/api/v1/auth/login",
            json={"email": "nobody@test.it", "password": "wrong"},
        )
        assert resp.status_code == 401

    async def test_login_success(self, client: AsyncClient) -> None:
        studio = await _create_studio(client)
        email = f"u{uuid.uuid4().hex[:8]}@test.it"
        await client.post(
            "/api/v1/tenants/users",
            json={
                "studio_id": studio["id"],
                "email": email,
                "password": "SecurePass123!",
                "full_name": "Test User",
                "role": "admin",
            },
        )
        resp = await client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": "SecurePass123!"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    async def test_refresh_token(self, client: AsyncClient) -> None:
        studio = await _create_studio(client)
        email = f"r{uuid.uuid4().hex[:8]}@test.it"
        await client.post(
            "/api/v1/tenants/users",
            json={
                "studio_id": studio["id"],
                "email": email,
                "password": "Pass123!",
                "full_name": "Refresh User",
            },
        )
        login = await client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": "Pass123!"},
        )
        resp = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": login.json()["refresh_token"]},
        )
        assert resp.status_code == 200
        assert "access_token" in resp.json()


class TestFullLifecycleFlow:
    """End-to-end: Cliente → Titolo → Operazione → Approva → Genera → Quadratura."""

    async def test_purchase_generates_balanced_entry(self, client: AsyncClient) -> None:
        studio = await _create_studio(client)
        cl = await _create_client(client, studio["id"])
        sec = await _create_security(client)
        txn = await _create_purchase_txn(client, cl["id"], sec["id"])

        # Approva
        await client.post(f"/api/v1/transactions/{txn['id']}/approve")

        # Genera scrittura
        resp = await client.post(
            "/api/v1/journal/generate",
            json={"client_id": cl["id"], "transaction_ids": [txn["id"]]},
        )
        assert resp.status_code == 200
        gen = resp.json()
        assert gen["entries_generated"] == 1

        entry = gen["entries"][0]
        assert entry["entry_type"] == "purchase_security"
        assert len(entry["lines"]) >= 2

        # Quadratura scrittura
        total_d = sum(Decimal(l["debit"]) for l in entry["lines"])
        total_c = sum(Decimal(l["credit"]) for l in entry["lines"])
        assert total_d == total_c, f"dare={total_d} != avere={total_c}"

        # Quadratura globale via API
        resp = await client.get(
            "/api/v1/journal/balance-check",
            params={"client_id": cl["id"]},
        )
        assert resp.status_code == 200
        check = resp.json()
        assert check["is_balanced"] is True

        # Approva e registra
        eid = entry["id"]
        resp = await client.post(f"/api/v1/journal/entries/{eid}/approve")
        assert resp.status_code == 200
        assert resp.json()["status"] == "approved"

        resp = await client.post(f"/api/v1/journal/entries/{eid}/post")
        assert resp.status_code == 200
        assert resp.json()["status"] == "posted"

    async def test_list_and_detail_entries(self, client: AsyncClient) -> None:
        studio = await _create_studio(client)
        cl = await _create_client(client, studio["id"])
        sec = await _create_security(client)
        txn = await _create_purchase_txn(client, cl["id"], sec["id"])
        await client.post(f"/api/v1/transactions/{txn['id']}/approve")
        await client.post(
            "/api/v1/journal/generate",
            json={"client_id": cl["id"], "transaction_ids": [txn["id"]]},
        )

        # Lista
        resp = await client.get(
            "/api/v1/journal/entries", params={"client_id": cl["id"]}
        )
        assert resp.status_code == 200
        entries = resp.json()
        assert len(entries) >= 1

        # Dettaglio
        resp = await client.get(f"/api/v1/journal/entries/{entries[0]['id']}")
        assert resp.status_code == 200
        assert len(resp.json()["lines"]) >= 2

    async def test_idempotent_generation(self, client: AsyncClient) -> None:
        studio = await _create_studio(client)
        cl = await _create_client(client, studio["id"])
        sec = await _create_security(client)
        txn = await _create_purchase_txn(client, cl["id"], sec["id"])
        await client.post(f"/api/v1/transactions/{txn['id']}/approve")

        # Prima generazione
        r1 = await client.post(
            "/api/v1/journal/generate",
            json={"client_id": cl["id"], "transaction_ids": [txn["id"]]},
        )
        assert r1.json()["entries_generated"] == 1

        # Seconda: idempotente
        r2 = await client.post(
            "/api/v1/journal/generate",
            json={"client_id": cl["id"], "transaction_ids": [txn["id"]]},
        )
        assert r2.json()["entries_generated"] == 0
