# TitoliEngine API Reference

> **Base URL:** `https://your-domain.com/api/v1`
> **Versione:** 1.0.0
> **Formato:** JSON (UTF-8)
> **Autenticazione:** Bearer JWT (header `Authorization: Bearer <token>`)

---

## Indice

1. [Autenticazione](#1-autenticazione)
2. [Tenants (Studio, Utenti, Clienti)](#2-tenants)
3. [Anagrafica Titoli](#3-anagrafica-titoli)
4. [Operazioni (Transactions)](#4-operazioni)
5. [Scritture Contabili (Journal)](#5-scritture-contabili)
6. [Documenti](#6-documenti)
7. [Valutazioni](#7-valutazioni)
8. [Report](#8-report)
9. [Export](#9-export)
10. [Audit Log](#10-audit-log)
11. [Health Check](#11-health-check)
12. [Codici di Stato](#12-codici-di-stato)
13. [Paginazione e Filtri](#13-paginazione-e-filtri)

---

## 1. Autenticazione

Tutte le API (eccetto `/health` e `/api/v1/auth/*`) richiedono un JWT valido nell'header `Authorization`.

### POST /api/v1/auth/login

Autenticazione con email e password. Restituisce access token e refresh token.

**Autenticazione:** Nessuna

**Request Body:**

```json
{
  "email": "mario.rossi@studio.it",
  "password": "SecurePass123!"
}
```

**Response 200:**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer"
}
```

**Response 401:**

```json
{
  "detail": "Credenziali non valide"
}
```

**Response 403:**

```json
{
  "detail": "Utente disabilitato"
}
```

---

### POST /api/v1/auth/refresh

Rinnova l'access token tramite refresh token.

**Autenticazione:** Nessuna

**Request Body:**

```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
}
```

**Response 200:**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer"
}
```

**Response 401:**

```json
{
  "detail": "Token non valido"
}
```

---

## 2. Tenants

Gestione studi professionali, utenti e clienti. Architettura multi-tenant per studi commercialisti.

### POST /api/v1/tenants/studios

Crea un nuovo studio professionale.

**Autenticazione:** Bearer JWT

**Request Body:**

```json
{
  "name": "Studio Rossi & Associati",
  "tax_code": "RSSMRA80A01H501Z",
  "vat_number": "IT01234567890",
  "address": "Via Roma 1, 20100 Milano"
}
```

**Response 201:**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Studio Rossi & Associati",
  "tax_code": "RSSMRA80A01H501Z",
  "vat_number": "IT01234567890",
  "address": "Via Roma 1, 20100 Milano",
  "created_at": "2025-01-15T10:30:00Z"
}
```

---

### POST /api/v1/tenants/users

Crea un nuovo utente per uno studio.

**Autenticazione:** Bearer JWT

**Request Body:**

```json
{
  "studio_id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "mario.rossi@studio.it",
  "password": "SecurePass123!",
  "full_name": "Mario Rossi",
  "role": "admin"
}
```

**Response 201:**

```json
{
  "id": "660e8400-e29b-41d4-a716-446655440001",
  "studio_id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "mario.rossi@studio.it",
  "full_name": "Mario Rossi",
  "role": "admin",
  "is_active": true,
  "created_at": "2025-01-15T10:35:00Z"
}
```

---

### POST /api/v1/tenants/clients

Crea un nuovo cliente.

**Autenticazione:** Bearer JWT

**Request Body:**

```json
{
  "studio_id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Alfa S.r.l.",
  "tax_code": "01234567890",
  "vat_number": "IT01234567890",
  "fiscal_year_end_month": 12,
  "valuation_method": "amortized_cost",
  "classification": "immobilized"
}
```

**Response 201:**

```json
{
  "id": "770e8400-e29b-41d4-a716-446655440002",
  "studio_id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Alfa S.r.l.",
  "tax_code": "01234567890",
  "vat_number": "IT01234567890",
  "fiscal_year_end_month": 12,
  "valuation_method": "amortized_cost",
  "classification": "immobilized",
  "is_active": true,
  "created_at": "2025-01-15T10:40:00Z"
}
```

---

### GET /api/v1/tenants/clients

Lista clienti con filtro opzionale per studio.

**Autenticazione:** Bearer JWT

**Query Parameters:**

| Parametro   | Tipo | Obbligatorio | Descrizione               |
|-------------|------|:------------:|---------------------------|
| `studio_id` | UUID | No           | Filtra per studio         |

**Response 200:**

```json
[
  {
    "id": "770e8400-e29b-41d4-a716-446655440002",
    "name": "Alfa S.r.l.",
    "tax_code": "01234567890",
    "valuation_method": "amortized_cost",
    "is_active": true
  }
]
```

---

### GET /api/v1/tenants/clients/{client_id}

Dettaglio cliente.

**Response 200:** Oggetto ClientRead completo.

**Response 404:**

```json
{
  "detail": "Cliente non trovato"
}
```

---

### PUT /api/v1/tenants/clients/{client_id}

Aggiorna un cliente. Supporta aggiornamento parziale (solo i campi inviati vengono modificati).

**Response 200:** Oggetto ClientRead aggiornato.

**Response 404:**

```json
{
  "detail": "Cliente non trovato"
}
```

---

### DELETE /api/v1/tenants/clients/{client_id}

Disattiva un cliente (soft delete: `is_active = false`).

**Response 204:** Nessun contenuto.

---

### GET /api/v1/tenants/clients/{client_id}/accounts

Piano dei conti di un cliente.

**Response 200:**

```json
[
  {
    "code": "2520",
    "name": "Titoli immobilizzati",
    "account_type": "asset",
    "category": "B.III.3",
    "is_active": true
  },
  {
    "code": "4100",
    "name": "Interessi attivi su titoli",
    "account_type": "revenue",
    "category": "C.16.b",
    "is_active": true
  }
]
```

---

### POST /api/v1/tenants/clients/{client_id}/accounts

Aggiungi un conto al piano dei conti del cliente.

**Request Body:**

```json
{
  "code": "2530",
  "name": "Obbligazioni corporate",
  "account_type": "asset",
  "category": "B.III.3"
}
```

**Response 201:** Oggetto AccountRead.

---

### PUT /api/v1/tenants/clients/{client_id}/accounts/{code}

Aggiorna un conto nel piano dei conti.

**Response 200:** Oggetto AccountRead aggiornato.

**Response 404:**

```json
{
  "detail": "Conto non trovato"
}
```

---

## 3. Anagrafica Titoli

CRUD titoli di debito con lookup per codice ISIN.

### POST /api/v1/securities/

Crea un nuovo titolo in anagrafica.

**Autenticazione:** Bearer JWT

**Request Body:**

```json
{
  "isin": "IT0005560948",
  "name": "BTP 4.20% 01/03/2028",
  "security_type": "BTP",
  "issuer": "Repubblica Italiana",
  "issuer_country": "IT",
  "currency": "EUR",
  "nominal_value": 100000.00,
  "coupon_rate": 0.042,
  "coupon_frequency": 2,
  "issue_date": "2023-03-01",
  "maturity_date": "2028-03-01",
  "day_count_convention": "ACT_ACT"
}
```

**Response 201:**

```json
{
  "id": "880e8400-e29b-41d4-a716-446655440003",
  "isin": "IT0005560948",
  "name": "BTP 4.20% 01/03/2028",
  "security_type": "BTP",
  "issuer": "Repubblica Italiana",
  "issuer_country": "IT",
  "currency": "EUR",
  "nominal_value": "100000.00",
  "coupon_rate": "0.042000",
  "coupon_frequency": 2,
  "issue_date": "2023-03-01",
  "maturity_date": "2028-03-01",
  "day_count_convention": "ACT_ACT",
  "created_at": "2025-01-15T11:00:00Z"
}
```

---

### GET /api/v1/securities/

Lista titoli con filtri.

**Query Parameters:**

| Parametro       | Tipo   | Obbligatorio | Descrizione                               |
|-----------------|--------|:------------:|-------------------------------------------|
| `isin`          | string | No           | Filtra per codice ISIN                    |
| `security_type` | string | No           | Filtra per tipo (BTP, BOT, CCT, CORPORATE_BOND) |

**Response 200:** Array di SecurityRead.

---

### GET /api/v1/securities/lookup/{isin}

Cerca un titolo per codice ISIN.

**Path Parameters:**

| Parametro | Tipo   | Descrizione                 |
|-----------|--------|-----------------------------|
| `isin`    | string | Codice ISIN (12 caratteri)  |

**Response 200:** Oggetto SecurityRead.

**Response 404:**

```json
{
  "detail": "ISIN IT9999999999 non trovato"
}
```

---

### GET /api/v1/securities/{security_id}

Dettaglio titolo per UUID.

**Response 200:** Oggetto SecurityRead.

**Response 404:**

```json
{
  "detail": "Titolo non trovato"
}
```

---

### PUT /api/v1/securities/{security_id}

Aggiorna un titolo.

**Response 200:** Oggetto SecurityRead aggiornato.

---

### DELETE /api/v1/securities/{security_id}

Elimina un titolo.

**Response 204:** Nessun contenuto.

**Response 404:**

```json
{
  "detail": "Titolo non trovato"
}
```

---

## 4. Operazioni

CRUD operazioni su titoli con workflow di approvazione: `draft` -> `approved` -> (genera scritture).

### POST /api/v1/transactions/

Crea una nuova operazione in stato `draft`.

**Autenticazione:** Bearer JWT

**Request Body:**

```json
{
  "client_id": "770e8400-e29b-41d4-a716-446655440002",
  "security_id": "880e8400-e29b-41d4-a716-446655440003",
  "transaction_type": "purchase",
  "trade_date": "2025-01-15",
  "settlement_date": "2025-01-17",
  "quantity": 100000.00,
  "unit_price": 98.50,
  "accrued_interest": 1925.00,
  "bank_commission": 150.00,
  "stamp_duty": 0.00,
  "tobin_tax": 0.00,
  "notes": "Acquisto BTP sul secondario"
}
```

**Response 201:**

```json
{
  "id": "990e8400-e29b-41d4-a716-446655440004",
  "client_id": "770e8400-e29b-41d4-a716-446655440002",
  "security_id": "880e8400-e29b-41d4-a716-446655440003",
  "transaction_type": "purchase",
  "status": "draft",
  "trade_date": "2025-01-15",
  "settlement_date": "2025-01-17",
  "quantity": "100000.00",
  "unit_price": "98.50",
  "gross_amount": "98500.00",
  "accrued_interest": "1925.00",
  "bank_commission": "150.00",
  "stamp_duty": "0.00",
  "tobin_tax": "0.00",
  "net_settlement_amount": "100575.00",
  "created_at": "2025-01-15T12:00:00Z"
}
```

**Tipi di operazione (`transaction_type`):**

| Valore     | Descrizione                          |
|------------|--------------------------------------|
| `purchase` | Acquisto titolo                      |
| `sale`     | Vendita titolo                       |
| `coupon`   | Incasso cedola                       |
| `maturity` | Scadenza / rimborso                  |

---

### GET /api/v1/transactions/

Lista operazioni con filtri.

**Query Parameters:**

| Parametro          | Tipo   | Obbligatorio | Descrizione                              |
|--------------------|--------|:------------:|------------------------------------------|
| `client_id`        | UUID   | No           | Filtra per cliente                       |
| `security_id`      | UUID   | No           | Filtra per titolo                        |
| `transaction_type` | string | No           | `purchase`, `sale`, `coupon`, `maturity` |
| `status`           | string | No           | `draft`, `approved`, `posted`            |
| `date_from`        | string | No           | Data inizio (YYYY-MM-DD)                 |
| `date_to`          | string | No           | Data fine (YYYY-MM-DD)                   |

---

### GET /api/v1/transactions/{txn_id}

Dettaglio operazione.

**Response 200:** Oggetto TransactionRead.

**Response 404:**

```json
{
  "detail": "Operazione non trovata"
}
```

---

### PUT /api/v1/transactions/{txn_id}

Aggiorna un'operazione. Consentito solo per operazioni in stato `draft`.

**Response 200:** Oggetto TransactionRead aggiornato.

**Response 400:**

```json
{
  "detail": "Operazione non trovata o non modificabile (solo draft)"
}
```

---

### POST /api/v1/transactions/{txn_id}/approve

Approva un'operazione: `draft` -> `approved`.

**Response 200:** Oggetto TransactionRead con `status: "approved"`.

**Response 400:**

```json
{
  "detail": "Operazione non trovata o non in stato draft"
}
```

---

### POST /api/v1/transactions/{txn_id}/reject

Rigetta un'operazione: `approved` -> `draft`.

**Response 200:** Oggetto TransactionRead con `status: "draft"`.

**Response 400:**

```json
{
  "detail": "Operazione non trovata o non in stato approved"
}
```

---

### DELETE /api/v1/transactions/{txn_id}

Elimina un'operazione. Consentito solo per operazioni in stato `draft`.

**Response 204:** Nessun contenuto.

**Response 400:**

```json
{
  "detail": "Operazione non trovata o non eliminabile (solo draft)"
}
```

---

## 5. Scritture Contabili

Generazione, approvazione e registrazione scritture contabili in partita doppia (dare/avere).

**Workflow:** `generated` -> `approved` -> `posted`

### GET /api/v1/journal/entries

Lista scritture contabili con filtri.

**Autenticazione:** Bearer JWT

**Query Parameters:**

| Parametro     | Tipo   | Obbligatorio | Descrizione                                                                       |
|---------------|--------|:------------:|-----------------------------------------------------------------------------------|
| `client_id`   | UUID   | No           | Filtra per cliente                                                                |
| `entry_type`  | string | No           | `purchase`, `sale`, `coupon`, `maturity`, `impairment`, `accrual`, `amortization` |
| `status`      | string | No           | `generated`, `approved`, `posted`                                                 |
| `fiscal_year` | int    | No           | Anno fiscale                                                                      |

**Response 200:**

```json
[
  {
    "id": "aa0e8400-e29b-41d4-a716-446655440005",
    "entry_date": "2025-01-17",
    "entry_type": "purchase",
    "status": "generated",
    "description": "Acquisto BTP 4.20% 01/03/2028 - IT0005560948",
    "fiscal_year": 2025,
    "lines": [
      {
        "line_number": 1,
        "account_code": "2520",
        "account_name": "Titoli immobilizzati",
        "description": "Iscrizione costo titolo",
        "debit": "98650.00",
        "credit": "0.00"
      },
      {
        "line_number": 2,
        "account_code": "1820",
        "account_name": "Ratei attivi su titoli",
        "description": "Rateo cedolare maturato",
        "debit": "1925.00",
        "credit": "0.00"
      },
      {
        "line_number": 3,
        "account_code": "1810",
        "account_name": "Banca c/c",
        "description": "Addebito banca",
        "debit": "0.00",
        "credit": "100575.00"
      }
    ]
  }
]
```

---

### GET /api/v1/journal/entries/{entry_id}

Dettaglio scrittura con tutte le righe dare/avere.

**Response 200:** Oggetto JournalEntryRead completo con `lines`.

**Response 404:**

```json
{
  "detail": "Scrittura non trovata"
}
```

---

### POST /api/v1/journal/generate

Genera scritture contabili dalle operazioni approvate. Invoca il motore contabile per ogni operazione approvata senza scrittura associata.

**Request Body:**

```json
{
  "client_id": "770e8400-e29b-41d4-a716-446655440002",
  "transaction_ids": [
    "990e8400-e29b-41d4-a716-446655440004"
  ]
}
```

Se `transaction_ids` non viene specificato, genera per tutte le operazioni approvate del cliente.

**Response 200:**

```json
{
  "entries_generated": 1,
  "entries": [
    {
      "id": "aa0e8400-e29b-41d4-a716-446655440005",
      "entry_date": "2025-01-17",
      "entry_type": "purchase",
      "status": "generated",
      "description": "Acquisto BTP 4.20% 01/03/2028",
      "lines": [...]
    }
  ]
}
```

---

### POST /api/v1/journal/entries/{entry_id}/approve

Approva una scrittura: `generated` -> `approved`.

**Response 200:** Oggetto JournalEntryRead con `status: "approved"`.

**Response 400:**

```json
{
  "detail": "Scrittura non trovata o non in stato generated"
}
```

---

### POST /api/v1/journal/entries/{entry_id}/post

Registra definitivamente una scrittura: `approved` -> `posted`.

Una volta registrata, la scrittura non e' piu' modificabile.

**Response 200:** Oggetto JournalEntryRead con `status: "posted"`.

**Response 400:**

```json
{
  "detail": "Scrittura non trovata o non in stato approved"
}
```

---

### GET /api/v1/journal/balance-check

Verifica quadratura globale dare = avere per un cliente.

**Query Parameters:**

| Parametro   | Tipo | Obbligatorio | Descrizione       |
|-------------|------|:------------:|-------------------|
| `client_id` | UUID | Si           | UUID del cliente  |

**Response 200:**

```json
{
  "client_id": "770e8400-e29b-41d4-a716-446655440002",
  "total_debit": "100575.00",
  "total_credit": "100575.00",
  "is_balanced": true,
  "difference": "0.00",
  "entries_checked": 15
}
```

---

## 6. Documenti

Upload e gestione documenti bancari (fissati bollati, estratti conto). I file sono criptati at-rest e deduplicati via SHA-256.

### POST /api/v1/documents/upload

Upload documento con deduplicazione automatica.

**Autenticazione:** Bearer JWT

**Content-Type:** `multipart/form-data`

**Form Parameters:**

| Parametro       | Tipo   | Obbligatorio | Descrizione                              |
|-----------------|--------|:------------:|------------------------------------------|
| `file`          | file   | Si           | File PDF o immagine                      |
| `client_id`     | UUID   | Si           | UUID del cliente                         |
| `document_type` | string | No           | Default: `fissato_bollato`               |
| `bank_name`     | string | No           | Nome banca (es. `intesa`, `unicredit`)   |
| `document_date` | date   | No           | Data documento (YYYY-MM-DD)              |

**Response 201:**

```json
{
  "id": "bb0e8400-e29b-41d4-a716-446655440006",
  "client_id": "770e8400-e29b-41d4-a716-446655440002",
  "original_filename": "fissato_bollato_btp.pdf",
  "document_type": "fissato_bollato",
  "bank_name": "intesa",
  "parsing_status": "pending",
  "file_hash": "sha256:a1b2c3d4e5f6...",
  "created_at": "2025-01-15T14:00:00Z"
}
```

Se il file esiste gia' (stesso hash SHA-256), restituisce il documento esistente senza duplicazione.

---

### GET /api/v1/documents/

Lista documenti con filtri.

**Query Parameters:**

| Parametro        | Tipo   | Obbligatorio | Descrizione                                |
|------------------|--------|:------------:|--------------------------------------------|
| `client_id`      | UUID   | No           | Filtra per cliente                         |
| `document_type`  | string | No           | `fissato_bollato`, `estratto_conto`        |
| `parsing_status` | string | No           | `pending`, `parsed`, `failed`, `review`    |

**Response 200:** Array di DocumentListItem.

---

### GET /api/v1/documents/{doc_id}

Dettaglio documento con metadati di parsing e dati estratti.

**Response 200:** Oggetto DocumentRead completo.

**Response 404:**

```json
{
  "detail": "Documento non trovato"
}
```

---

## 7. Valutazioni

Valutazione titoli a fine esercizio e gestione prezzi di mercato.

Riferimento: OIC 20, par. 63-80.

### POST /api/v1/valuations/market-prices

Importa un singolo prezzo di mercato.

**Autenticazione:** Bearer JWT

**Request Body:**

```json
{
  "security_id": "880e8400-e29b-41d4-a716-446655440003",
  "price_date": "2025-12-31",
  "close_price": 101.25,
  "source": "borsa_italiana"
}
```

**Response 201:** Oggetto MarketPriceRead.

---

### POST /api/v1/valuations/market-prices/bulk

Import massivo prezzi di mercato.

**Request Body:**

```json
{
  "prices": [
    {
      "security_id": "880e8400-...",
      "price_date": "2025-12-31",
      "close_price": 101.25,
      "source": "borsa_italiana"
    },
    {
      "security_id": "990e8400-...",
      "price_date": "2025-12-31",
      "close_price": 99.80,
      "source": "borsa_italiana"
    }
  ]
}
```

**Response 200:**

```json
{
  "imported": 2,
  "skipped": 0,
  "errors": []
}
```

---

### POST /api/v1/valuations/year-end

Lancia la valutazione di fine esercizio per tutti i titoli in portafoglio di un cliente.

Per ogni posizione attiva confronta valore contabile con valore di mercato:
- Se mercato < contabile -> genera svalutazione (OIC 20, par. 63-75)
- Se mercato > contabile con svalutazione pregressa -> genera ripristino (OIC 20, par. 76-80)

**Request Body:**

```json
{
  "client_id": "770e8400-e29b-41d4-a716-446655440002",
  "valuation_date": "2025-12-31",
  "fiscal_year": 2025
}
```

**Response 200:**

```json
{
  "client_id": "770e8400-...",
  "valuation_date": "2025-12-31",
  "fiscal_year": 2025,
  "positions_evaluated": 5,
  "impairments_generated": 1,
  "reversals_generated": 0,
  "valuations": [
    {
      "security_id": "880e8400-...",
      "isin": "IT0005560948",
      "book_value": "98650.00",
      "market_value": "95200.00",
      "impairment": "3450.00",
      "action": "impairment"
    }
  ]
}
```

---

### GET /api/v1/valuations/

Lista valutazioni effettuate.

**Query Parameters:**

| Parametro     | Tipo | Obbligatorio | Descrizione       |
|---------------|------|:------------:|-------------------|
| `client_id`   | UUID | No           | Filtra per cliente|
| `fiscal_year` | int  | No           | Anno fiscale      |

**Response 200:** Array di ValuationRead.

---

## 8. Report

Report contabili e fiscali generati dal motore di calcolo.

### GET /api/v1/reports/portfolio

Report portafoglio dettagliato con posizioni e valori correnti.

Riferimento: OIC 20, par. 81.

**Autenticazione:** Bearer JWT

**Query Parameters:**

| Parametro     | Tipo | Obbligatorio | Descrizione                      |
|---------------|------|:------------:|----------------------------------|
| `client_id`   | UUID | Si           | UUID del cliente                 |
| `report_date` | date | No           | Data riferimento (default: oggi) |

**Response 200:**

```json
{
  "client_id": "770e8400-...",
  "report_date": "2025-12-31",
  "total_book_value": "495200.00",
  "total_market_value": "502100.00",
  "total_unrealized_gain_loss": "6900.00",
  "positions": [
    {
      "isin": "IT0005560948",
      "name": "BTP 4.20% 01/03/2028",
      "security_type": "BTP",
      "classification": "immobilized",
      "quantity": "100000.00",
      "book_value": "98650.00",
      "book_value_per_unit": "98.65",
      "market_price": "101.25",
      "market_value": "101250.00",
      "unrealized_gain_loss": "2600.00"
    }
  ]
}
```

---

### GET /api/v1/reports/gains-losses

Report plus/minusvalenze realizzate per periodo.

Riferimento: Art. 67-68 TUIR.

**Query Parameters:**

| Parametro   | Tipo | Obbligatorio | Descrizione           |
|-------------|------|:------------:|-----------------------|
| `client_id` | UUID | Si           | UUID del cliente      |
| `date_from` | date | Si           | Data inizio periodo   |
| `date_to`   | date | Si           | Data fine periodo     |

**Response 200:**

```json
{
  "client_id": "770e8400-...",
  "date_from": "2025-01-01",
  "date_to": "2025-12-31",
  "total_gains": "5200.00",
  "total_losses": "-1800.00",
  "net_gain_loss": "3400.00",
  "transactions": [
    {
      "transaction_id": "...",
      "isin": "IT0005560948",
      "transaction_type": "sale",
      "sale_date": "2025-06-15",
      "proceeds": "102500.00",
      "book_value": "98650.00",
      "gain_loss": "3850.00",
      "tax_regime": "government_12_5"
    }
  ]
}
```

---

### GET /api/v1/reports/tax-summary

Riepilogo fiscale ritenute per anno fiscale.

Riferimento: Art. 26 D.P.R. 600/1973.

**Query Parameters:**

| Parametro     | Tipo | Obbligatorio | Descrizione       |
|---------------|------|:------------:|-------------------|
| `client_id`   | UUID | Si           | UUID del cliente  |
| `fiscal_year` | int  | Si           | Anno fiscale      |

**Response 200:**

```json
{
  "client_id": "770e8400-...",
  "fiscal_year": 2025,
  "total_gross_income": "12500.00",
  "total_withholding_tax": "1562.50",
  "total_net_income": "10937.50",
  "by_regime": {
    "government_12_5": {
      "gross": "8400.00",
      "tax": "1050.00",
      "net": "7350.00"
    },
    "standard_26": {
      "gross": "4100.00",
      "tax": "1066.00",
      "net": "3034.00"
    }
  }
}
```

---

### GET /api/v1/reports/oic20

Dati per la Nota Integrativa OIC 20.

Riferimento: OIC 20, par. 81-85. Prospetto movimentazione titoli per anno fiscale.

**Query Parameters:**

| Parametro     | Tipo | Obbligatorio | Descrizione       |
|---------------|------|:------------:|-------------------|
| `client_id`   | UUID | Si           | UUID del cliente  |
| `fiscal_year` | int  | Si           | Anno fiscale      |

**Response 200:**

```json
{
  "client_id": "770e8400-...",
  "fiscal_year": 2025,
  "opening_balance": "480000.00",
  "purchases": "98650.00",
  "sales": "-52000.00",
  "maturities": "-100000.00",
  "amortization": "1200.00",
  "impairments": "-3450.00",
  "reversals": "0.00",
  "closing_balance": "424400.00",
  "fair_value_total": "430200.00"
}
```

---

### POST /api/v1/reports/societa-comodo

Test societa' di comodo (Art. 30 L. 724/1994). Verifica se la societa' e' operativa confrontando ricavi effettivi con ricavo minimo presunto calcolato sui coefficienti di legge.

**Request Body:**

```json
{
  "titoli_e_crediti": 500000.00,
  "immobili": 1200000.00,
  "immobili_a10": 300000.00,
  "altre_immobilizzazioni": 100000.00,
  "actual_revenue": 80000.00
}
```

**Response 200:**

```json
{
  "total_assets": "2100000.00",
  "minimum_revenue": "112000.00",
  "actual_revenue": "80000.00",
  "is_comodo": true,
  "details": {
    "titoli_e_crediti": {
      "valore": "500000.00",
      "coefficiente": "0.02",
      "ricavo_minimo": "10000.00"
    },
    "immobili": {
      "valore": "1200000.00",
      "coefficiente": "0.06",
      "ricavo_minimo": "72000.00"
    },
    "immobili_a10": {
      "valore": "300000.00",
      "coefficiente": "0.05",
      "ricavo_minimo": "15000.00"
    },
    "altre_immobilizzazioni": {
      "valore": "100000.00",
      "coefficiente": "0.15",
      "ricavo_minimo": "15000.00"
    }
  }
}
```

---

## 9. Export

Export dati in vari formati: CSV generico, Excel formattato, e strutture per gestionali contabili.

### GET /api/v1/export/journal/csv

Export scritture contabili in formato CSV (delimitatore `;`).

**Autenticazione:** Bearer JWT

**Query Parameters:**

| Parametro     | Tipo   | Obbligatorio | Descrizione                       |
|---------------|--------|:------------:|-----------------------------------|
| `client_id`   | UUID   | Si           | UUID del cliente                  |
| `fiscal_year` | int    | No           | Anno fiscale                      |
| `status`      | string | No           | Filtra per stato scrittura        |

**Response 200:** File CSV (`text/csv`).

**Colonne:**

```
entry_id;entry_date;description;entry_type;status;line_number;account_code;account_name;debit;credit
```

---

### GET /api/v1/export/portfolio/csv

Export portafoglio in formato CSV.

**Query Parameters:**

| Parametro     | Tipo | Obbligatorio | Descrizione                      |
|---------------|------|:------------:|----------------------------------|
| `client_id`   | UUID | Si           | UUID del cliente                 |
| `report_date` | date | No           | Data riferimento (default: oggi) |

**Response 200:** File CSV (`text/csv`).

**Colonne:**

```
isin;name;security_type;classification;quantity;book_value;book_value_per_unit;market_price;market_value;unrealized_gain_loss
```

---

### GET /api/v1/export/journal/excel

Export scritture contabili in formato Excel (.xlsx) con formattazione, intestazioni in grassetto e colonne auto-width.

**Query Parameters:** Come per `/export/journal/csv`.

**Response 200:** File Excel (`application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`).

**Requisiti:** `openpyxl` deve essere installato (errore 501 se mancante).

---

### GET /api/v1/export/gestionale/profis

Export in formato PROFIS (Sistemi S.p.A.). Esporta solo scritture con stato `posted`.

**Query Parameters:**

| Parametro     | Tipo | Obbligatorio | Descrizione       |
|---------------|------|:------------:|-------------------|
| `client_id`   | UUID | Si           | UUID del cliente  |
| `fiscal_year` | int  | No           | Anno fiscale      |

**Response 200:** File CSV con struttura PROFIS.

**Colonne:**

```
TIPO_REG;DATA_REG;CAUSALE;COD_CONTO;DESCRIZIONE;IMPORTO_DARE;IMPORTO_AVERE
```

`TIPO_REG` e' sempre `CN` (Contabilita' Normale). Le date sono in formato `DD/MM/YYYY`.

---

### GET /api/v1/export/gestionale/teamsystem

Export in formato TeamSystem. Esporta solo scritture con stato `posted`.

**Query Parameters:** Come per PROFIS.

**Response 200:** File CSV con struttura TeamSystem.

**Colonne:**

```
DATA;NUMERO_REG;CAUSALE;SOTTOCONTO;DARE;AVERE;DESCRIZIONE
```

Le date sono in formato `DD/MM/YYYY`.

---

## 10. Audit Log

Log di audit immutabile per tracciabilita' completa delle operazioni. Registra ogni modifica con old/new values, parametri di calcolo e risultati computazionali.

### GET /api/v1/audit/logs

Query audit log con filtri multipli. Ordinamento cronologico inverso (piu' recenti prima).

**Autenticazione:** Bearer JWT

**Query Parameters:**

| Parametro     | Tipo   | Obbligatorio | Descrizione                                              |
|---------------|--------|:------------:|----------------------------------------------------------|
| `entity_type` | string | No           | `transaction`, `journal_entry`, `security`, `client`     |
| `entity_id`   | UUID   | No           | UUID dell'entita'                                        |
| `client_id`   | UUID   | No           | Filtra per cliente                                       |
| `user_id`     | UUID   | No           | Filtra per utente                                        |
| `action`      | string | No           | `create`, `update`, `approve`, `post`, `generate`        |
| `date_from`   | date   | No           | Data inizio (YYYY-MM-DD)                                 |
| `date_to`     | date   | No           | Data fine (YYYY-MM-DD)                                   |
| `limit`       | int    | No           | Max risultati (default: 100)                             |
| `offset`      | int    | No           | Offset per paginazione (default: 0)                      |

**Response 200:**

```json
[
  {
    "id": 1042,
    "timestamp": "2025-01-15T14:30:00Z",
    "user_id": "660e8400-...",
    "client_id": "770e8400-...",
    "entity_type": "transaction",
    "entity_id": "990e8400-...",
    "action": "approve",
    "old_values": {"status": "draft"},
    "new_values": {"status": "approved"},
    "computation_rule": null,
    "computation_params": null,
    "computation_result": null,
    "ip_address": "192.168.1.100",
    "user_agent": "Mozilla/5.0..."
  }
]
```

---

### GET /api/v1/audit/entity/{entity_type}/{entity_id}

Storico completo di un'entita' specifica. Ordinamento cronologico ascendente.

**Path Parameters:**

| Parametro     | Tipo   | Descrizione                                         |
|---------------|--------|-----------------------------------------------------|
| `entity_type` | string | `transaction`, `journal_entry`, `security`, `client` |
| `entity_id`   | UUID   | UUID dell'entita'                                   |

**Response 200:** Array di AuditLogRead ordinato per `timestamp ASC`.

---

## 11. Health Check

### GET /health

Verifica stato dell'applicazione. Non richiede autenticazione. Non ha prefisso `/api/v1`.

**Response 200:**

```json
{
  "status": "ok",
  "version": "1.0.0"
}
```

---

## 12. Codici di Stato

| Codice | Descrizione                                            |
|--------|--------------------------------------------------------|
| `200`  | Successo                                               |
| `201`  | Creazione riuscita                                     |
| `204`  | Cancellazione riuscita (nessun contenuto)              |
| `400`  | Richiesta non valida / operazione non consentita       |
| `401`  | Non autenticato / token scaduto                        |
| `403`  | Non autorizzato (utente disabilitato)                  |
| `404`  | Risorsa non trovata                                    |
| `422`  | Errore di validazione (Pydantic)                       |
| `429`  | Rate limit superato (100 req/min, 20 req/min per auth) |
| `500`  | Errore interno del server                              |
| `501`  | Funzionalita' non disponibile (dipendenza mancante)    |

### Formato errori standard

```json
{
  "detail": "Descrizione dell'errore in italiano"
}
```

Per errori di validazione (422):

```json
{
  "detail": [
    {
      "loc": ["body", "email"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

---

## 13. Paginazione e Filtri

- Le liste supportano filtri tramite query parameters
- L'audit log supporta `limit` e `offset` per paginazione
- I risultati sono ordinati per data di creazione (piu' recenti prima) salvo diversa indicazione
- Tutti gli importi sono restituiti come stringhe Decimal per evitare perdita di precisione floating-point
- Le date sono in formato ISO 8601 (`YYYY-MM-DD` per date, `YYYY-MM-DDTHH:MM:SSZ` per timestamp)
- Gli UUID sono nel formato standard a 36 caratteri con trattini

---

## Headers di Risposta

| Header                   | Descrizione                                |
|--------------------------|--------------------------------------------|
| `X-Process-Time`         | Tempo di elaborazione in secondi           |
| `X-RateLimit-Remaining`  | Richieste rimanenti nella finestra         |
| `Content-Disposition`    | Nome file per download (export endpoints)  |

---

## Rate Limiting

- **API generali:** 100 richieste / 60 secondi
- **Endpoint auth:** 20 richieste / 60 secondi
- Superato il limite: HTTP 429 con header `X-RateLimit-Remaining: 0`

---

## Note Tecniche

- **Precisione numerica:** tutti i calcoli contabili usano `decimal.Decimal`, mai `float`. Gli importi nelle response sono stringhe per preservare la precisione.
- **Idempotenza upload:** l'upload documenti e' idempotente grazie alla deduplicazione SHA-256.
- **Encryption at-rest:** i documenti caricati sono criptati prima del salvataggio su disco.
- **Soft delete:** la cancellazione clienti e' logica (`is_active = false`), non fisica.
- **Audit trail:** ogni operazione di modifica viene registrata nell'audit log con before/after values.
