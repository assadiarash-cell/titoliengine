# TitoliEngine

**Motore contabile deterministico per titoli di debito -- OIC 20**

<!-- badges -->
![Build Status](https://img.shields.io/badge/build-passing-brightgreen)
![Tests](https://img.shields.io/badge/tests-300%20passed-brightgreen)
![Coverage](https://img.shields.io/badge/coverage-100%25-brightgreen)
![Python](https://img.shields.io/badge/python-3.12+-blue)
![License](https://img.shields.io/badge/license-proprietary-lightgrey)

---

TitoliEngine e' un motore contabile completo per la gestione di titoli di debito (BTP, BOT, CCT, CTZ, obbligazioni corporate) conforme al principio contabile italiano **OIC 20**. Progettato per studi commercialisti, automatizza il ciclo completo dall'acquisto alla scadenza: calcolo TIR, costo ammortizzato, scritture contabili in partita doppia, ritenute fiscali, valutazione di fine esercizio e reportistica per nota integrativa.

---

## Funzionalita'

### Motore contabile

- Calcolo **TIR** (Tasso Interno di Rendimento) con Newton-Raphson, precisione 12 cifre decimali
- **Costo ammortizzato** con piano di ammortamento completo e convergenza garantita a scadenza
- Generazione automatica **scritture contabili** in partita doppia (acquisto, vendita, cedola, scadenza, svalutazione, ripristino, ratei, ammortamento scarto)
- **Quadratura deterministica** dare = avere su ogni scrittura
- Day count conventions: ACT/ACT, ACT/360, ACT/365, 30/360
- Tutti i calcoli in `Decimal`, mai `float`

### Fiscalita'

- Ritenute automatiche: 12,5% titoli di Stato / 26% corporate (Art. 26 DPR 600/73, D.Lgs. 239/1996)
- White list paesi per regime agevolato
- Test **societa' di comodo** (Art. 30 L. 724/1994) con coefficienti di legge
- Plus/minusvalenze per Art. 67-68 TUIR

### API REST

- Autenticazione JWT con access + refresh token
- Multi-tenant: studio -> clienti -> operazioni
- Workflow approvazione: draft -> approved -> posted
- Export per gestionali: PROFIS, TeamSystem, CSV, Excel
- Audit trail immutabile con before/after values
- Rate limiting e security headers

### Parsing documenti

- Estrazione automatica dati da fissati bollati PDF
- Parser specifici per 8 banche italiane (Intesa, UniCredit, Fineco, BPER, Mediolanum, Banca Sella, BPM)
- Fallback LLM (Anthropic Claude) per banche non supportate
- Sistema di confidence scoring (0.0-1.0)
- Riconciliazione documento vs transazione vs estratto conto
- Encryption at-rest dei documenti caricati

### Frontend

- Dashboard con statistiche e approvazioni pendenti
- Gestione titoli, operazioni, scritture contabili
- Upload documenti con parsing automatico
- Report portafoglio, fiscale, nota integrativa OIC 20
- Export multipli formati

---

## Architettura

```
titoliengine/
|
|-- backend/                     FastAPI + SQLAlchemy + PostgreSQL
|   |-- app/
|   |   |-- api/                 Endpoint REST (auth, tenants, securities,
|   |   |                        transactions, journal, documents,
|   |   |                        valuations, reports, export, audit)
|   |   |-- engine/              Motore contabile puro (zero I/O)
|   |   |   |-- tir.py           TIR con Newton-Raphson
|   |   |   |-- amortized_cost.py Costo ammortizzato OIC 20
|   |   |   |-- accruals.py      Ratei e competenza
|   |   |   |-- tax.py           Ritenute e societa' di comodo
|   |   |   |-- gains_losses.py  Plus/minusvalenze
|   |   |   |-- spread.py        Ammortamento scarto
|   |   |   |-- day_count.py     Convenzioni calcolo giorni
|   |   |   |-- fx.py            Conversione valuta
|   |   |   |-- valuation.py     Valutazione fine esercizio
|   |   |   |-- constants.py     Costanti, aliquote, enumerazioni
|   |   |   |-- journal/         Generatori scritture contabili
|   |   |   |   |-- purchase.py  Acquisto (costo storico + ammortizzato)
|   |   |   |   |-- sale.py      Vendita con plus/minus
|   |   |   |   |-- coupon.py    Incasso cedola
|   |   |   |   |-- maturity.py  Rimborso a scadenza
|   |   |   |   |-- impairment.py Svalutazione e ripristino
|   |   |   |   |-- accrual.py   Ratei fine esercizio
|   |   |   |   |-- amortization.py Ammortamento scarto
|   |   |   |   +-- templates.py Piano dei conti standard
|   |   |   +-- validators/      Validazione quadratura e coerenza
|   |   |-- parser/              Parsing documenti bancari
|   |   |   |-- base.py          Classe astratta, confidence scoring
|   |   |   |-- pdf_extractor.py Estrazione testo PDF
|   |   |   |-- llm_extractor.py Fallback LLM (Anthropic Claude)
|   |   |   |-- reconciler.py    Riconciliazione
|   |   |   +-- banks/           Parser per banca (8 banche + generic)
|   |   |-- models/              Modelli SQLAlchemy
|   |   |-- schemas/             Pydantic schemas
|   |   |-- services/            Business logic
|   |   |-- export/              Export CSV, Excel, PROFIS, TeamSystem
|   |   |-- middleware/          Security headers, rate limit, encryption
|   |   |-- utils/               Auth JWT, audit, date/decimal utils
|   |   +-- config.py            Configurazione con TE_ prefix
|   +-- tests/                   Test suite (35 file)
|       |-- engine/              Test motore contabile
|       |   |-- journal/         Test generatori scritture
|       |   +-- scenarios/       Test scenari completi end-to-end
|       |-- parser/              Test parser e riconciliazione
|       +-- api/                 Test API e integrazione
|
|-- frontend/                    React + TypeScript + Tailwind CSS
|   +-- src/
|       |-- pages/               Dashboard, Securities, Transactions,
|       |                        Journal, Documents, Valuations,
|       |                        Reports, Export, AuditLog, Settings
|       +-- components/          Layout, DataTable, MoneyDisplay, etc.
|
|-- docs/                        Documentazione
|-- docker-compose.yml           PostgreSQL + Redis (sviluppo)
|-- docker-compose.prod.yml      Stack completo (produzione)
|-- Dockerfile.backend
+-- Dockerfile.frontend
```

---

## Quick Start

### 1. Clona e avvia l'infrastruttura

```bash
git clone <repository-url> titoliengine
cd titoliengine

# Avvia PostgreSQL e Redis
docker compose up -d
```

### 2. Configura il backend

```bash
cd backend

# Crea virtual environment
python -m venv .venv
source .venv/bin/activate

# Installa dipendenze
pip install -r requirements.txt

# Crea il file .env
cat > .env <<EOF
TE_DATABASE_URL=postgresql+asyncpg://titoliengine:titoliengine_dev@localhost:5432/titoliengine
TE_REDIS_URL=redis://localhost:6379/0
TE_SECRET_KEY=$(python -c "import secrets; print(secrets.token_urlsafe(48))")
TE_DEBUG=true
EOF

# Esegui migrazioni
alembic upgrade head

# Avvia il backend
uvicorn app.main:app --reload --port 8000
```

### 3. Configura il frontend

```bash
cd frontend

# Installa dipendenze
npm install

# Avvia in modalita' sviluppo
npm run dev
```

### 4. Accedi

- **Frontend:** http://localhost:3000
- **API docs (Swagger):** http://localhost:8000/api/docs (solo con `TE_DEBUG=true`)
- **Health check:** http://localhost:8000/health

---

## Stack tecnologico

| Componente | Tecnologia |
|------------|------------|
| Backend framework | FastAPI |
| ORM | SQLAlchemy 2.0 (async) |
| Database | PostgreSQL 16 |
| Cache / Rate limit | Redis 7 |
| Autenticazione | JWT (python-jose + bcrypt) |
| Frontend | React 18 + TypeScript |
| Styling | Tailwind CSS |
| State management | Redux Toolkit + React Query |
| PDF parsing | pdfplumber |
| LLM fallback | Anthropic Claude |
| Excel export | openpyxl |
| Migrazioni DB | Alembic |
| Containerizzazione | Docker + Docker Compose |

---

## Testing

La test suite copre il motore contabile, i generatori di scritture, i parser, e le API.

```bash
cd backend

# Esegui tutti i test
pytest

# Con copertura
pytest --cov=app --cov-report=term-missing

# Solo test motore contabile
pytest tests/engine/

# Solo scenari end-to-end
pytest tests/engine/scenarios/

# Solo test API
pytest tests/api/
```

### Aree di test

| Area | File | Descrizione |
|------|------|-------------|
| TIR | `test_tir.py` | Newton-Raphson, convergenza, contro-verifica |
| Costo ammortizzato | `test_amortized_cost.py` | Piano ammortamento, valore a data |
| Ratei | `test_accruals.py` | Calcolo rateo per varie convenzioni |
| Fiscalita' | `test_tax.py` | Regimi, ritenute, societa' di comodo |
| Day count | `test_day_count.py` | ACT/ACT, ACT/360, ACT/365, 30/360 |
| Plus/minus | `test_gains_losses.py` | Calcolo gain/loss |
| Cambio | `test_fx.py` | Conversione valuta |
| Acquisto | `test_purchase.py` | Scritture acquisto costo storico e ammortizzato |
| Vendita | `test_sale.py` | Scritture vendita con plus/minus |
| Cedola | `test_coupon.py` | Incasso cedola con/senza rateo |
| Scadenza | `test_maturity.py` | Rimborso a pari e sotto/sopra pari |
| Svalutazione | `test_impairment_and_reversal.py` | Svalutazione e ripristino |
| Ratei esercizio | `test_accrual.py` | Ratei di fine anno |
| Quadratura | `test_balance_validation.py` | Dare = Avere su ogni scrittura |
| BTP lifecycle | `test_btp_full_lifecycle.py` | Ciclo completo dall'acquisto al rimborso |
| BOT zero coupon | `test_bot_zero_coupon.py` | Scarto emissione e ritenuta |
| Vendita anticipata | `test_early_sale.py` | Vendita con costo ammortizzato |
| Corporate bond | `test_corporate_bond.py` | Obbligazione con costi elevati |
| CCT variabile | `test_cct_variable_rate.py` | Tasso variabile |
| Multicurrency | `test_multicurrency.py` | Titoli in valuta estera |
| Parser | `test_pdf_extractor.py` | Estrazione testo da PDF |
| Riconciliazione | `test_reconciler.py` | Documento vs transazione |
| API auth | `test_auth.py` | Login, refresh, autorizzazione |
| API operazioni | `test_transactions.py` | CRUD e workflow approvazione |
| API journal | `test_journal.py` | Generazione e registrazione scritture |
| API full flow | `test_full_flow.py` | Flusso completo end-to-end |
| API e2e | `test_e2e_certification.py` | Certificazione end-to-end |

---

## Documentazione

| Documento | Descrizione |
|-----------|-------------|
| [API Reference](docs/API_REFERENCE.md) | Riferimento completo endpoint REST |
| [OIC 20 Rules](docs/OIC_20_RULES.md) | Mapping principi contabili -> codice |
| [Deployment](docs/DEPLOYMENT.md) | Guida deployment produzione |
| [Bank Parser Guide](docs/BANK_PARSER_GUIDE.md) | Come aggiungere un nuovo parser |

---

## Licenza

Proprietary. Tutti i diritti riservati.
