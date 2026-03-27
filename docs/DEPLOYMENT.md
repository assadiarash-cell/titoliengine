# TitoliEngine -- Guida al Deployment in Produzione

---

## Indice

1. [Prerequisiti](#1-prerequisiti)
2. [Architettura](#2-architettura)
3. [Docker Compose (Sviluppo)](#3-docker-compose-sviluppo)
4. [Docker Compose (Produzione)](#4-docker-compose-produzione)
5. [Variabili d'ambiente](#5-variabili-dambiente)
6. [Database e Migrazioni](#6-database-e-migrazioni)
7. [Build Frontend](#7-build-frontend)
8. [Avvio Backend](#8-avvio-backend)
9. [NGINX Reverse Proxy](#9-nginx-reverse-proxy)
10. [SSL con Let's Encrypt](#10-ssl-con-lets-encrypt)
11. [Monitoraggio](#11-monitoraggio)
12. [Backup](#12-backup)
13. [Sicurezza](#13-sicurezza)
14. [Troubleshooting](#14-troubleshooting)

---

## 1. Prerequisiti

| Componente   | Versione minima | Note                                 |
|--------------|-----------------|--------------------------------------|
| Python       | 3.12+           | Con supporto `asyncio`               |
| Node.js      | 20+             | Per build frontend                   |
| PostgreSQL   | 16              | Con estensione `uuid-ossp`           |
| Redis        | 7               | Per rate limiting e cache            |
| Docker       | 24+             | Opzionale, raccomandato              |
| Docker Compose | 2.20+         | Opzionale, raccomandato              |

### Dipendenze Python principali

```
fastapi
uvicorn[standard]
sqlalchemy[asyncio]
asyncpg
pydantic-settings
python-jose[cryptography]
passlib[bcrypt]
redis
openpyxl
pdfplumber
anthropic
alembic
```

---

## 2. Architettura

```
                    +-----------+
                    |  Browser  |
                    +-----+-----+
                          |
                    +-----v-----+
                    |   NGINX   |  :443 (SSL)
                    +-----+-----+
                          |
              +-----------+-----------+
              |                       |
        +-----v-----+          +-----v-----+
        |  Frontend  |          |  Backend   |
        |  (static)  |          |  (uvicorn) |
        |  :3000     |          |  :8000     |
        +------------+          +-----+-----+
                                      |
                          +-----------+-----------+
                          |                       |
                    +-----v-----+          +-----v-----+
                    | PostgreSQL|          |   Redis   |
                    |   :5432   |          |   :6379   |
                    +-----------+          +-----------+
```

---

## 3. Docker Compose (Sviluppo)

Il file `docker-compose.yml` nella root del progetto avvia PostgreSQL e Redis per lo sviluppo locale.

```bash
# Avvia i servizi infrastrutturali
cd /path/to/titoliengine
docker compose up -d

# Verifica stato
docker compose ps

# Log
docker compose logs -f postgres
docker compose logs -f redis
```

Il database e' accessibile su `localhost:5432` con utente `titoliengine` e database `titoliengine`.

---

## 4. Docker Compose (Produzione)

Per la produzione, usare `docker-compose.prod.yml` che include backend e frontend containerizzati.

```bash
# Build e avvio completo
docker compose -f docker-compose.prod.yml up -d --build

# Verifica
docker compose -f docker-compose.prod.yml ps
```

### Dockerfile.backend

Il Dockerfile backend:
1. Installa le dipendenze Python
2. Copia il codice applicativo
3. Espone la porta 8000
4. Avvia con `uvicorn`

### Dockerfile.frontend

Il Dockerfile frontend:
1. Installa le dipendenze Node
2. Esegue `npm run build`
3. Serve i file statici tramite NGINX

---

## 5. Variabili d'ambiente

TitoliEngine usa il prefisso `TE_` per tutte le variabili d'ambiente. Configurazione tramite file `.env` nella directory `backend/`.

### Creare il file .env

```bash
cp backend/.env.example backend/.env
# Modificare con i valori di produzione
```

### Variabili disponibili

| Variabile | Default | Descrizione |
|-----------|---------|-------------|
| `TE_DATABASE_URL` | `postgresql+asyncpg://titoliengine:titoliengine_dev@localhost:5432/titoliengine` | Connection string PostgreSQL |
| `TE_DATABASE_ECHO` | `false` | Log query SQL (solo debug) |
| `TE_DATABASE_POOL_SIZE` | `10` | Dimensione pool connessioni |
| `TE_DATABASE_MAX_OVERFLOW` | `20` | Connessioni extra oltre il pool |
| `TE_REDIS_URL` | `redis://localhost:6379/0` | Connection string Redis |
| `TE_APP_NAME` | `TitoliEngine` | Nome applicazione |
| `TE_APP_VERSION` | `1.0.0` | Versione applicazione |
| `TE_DEBUG` | `false` | Modalita' debug (abilita Swagger UI) |
| `TE_SECRET_KEY` | `change-me-in-production` | Chiave segreta per JWT e encryption |
| `TE_CORS_ORIGINS` | `["http://localhost:3000"]` | Origini CORS consentite (JSON array) |
| `TE_UPLOAD_DIR` | `uploads` | Directory per file caricati |
| `TE_ANTHROPIC_API_KEY` | (vuoto) | API key Anthropic per LLM extraction |
| `TE_LOG_LEVEL` | `INFO` | Livello di log (DEBUG, INFO, WARNING, ERROR) |

### Esempio .env di produzione

```env
TE_DATABASE_URL=postgresql+asyncpg://titoliengine:STRONG_PASSWORD@db.internal:5432/titoliengine_prod
TE_DATABASE_POOL_SIZE=20
TE_DATABASE_MAX_OVERFLOW=40
TE_REDIS_URL=redis://redis.internal:6379/0
TE_DEBUG=false
TE_SECRET_KEY=una-chiave-segreta-lunga-almeno-32-caratteri-generata-random
TE_CORS_ORIGINS=["https://titoliengine.example.com"]
TE_UPLOAD_DIR=/var/lib/titoliengine/uploads
TE_ANTHROPIC_API_KEY=sk-ant-...
TE_LOG_LEVEL=WARNING
```

**IMPORTANTE:** `TE_SECRET_KEY` deve essere una stringa casuale lunga e unica. Viene usata per:
- Firma dei JWT (access e refresh token)
- Encryption at-rest dei documenti caricati

Generare con:

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

---

## 6. Database e Migrazioni

### Setup iniziale

```bash
cd backend

# Crea il database (se non esiste)
createdb -U titoliengine titoliengine_prod

# Esegui le migrazioni
alembic upgrade head
```

### Creare una nuova migrazione

```bash
# Dopo aver modificato i modelli SQLAlchemy
alembic revision --autogenerate -m "descrizione della modifica"

# Verifica la migrazione generata in alembic/versions/
# Poi applica
alembic upgrade head
```

### Rollback

```bash
# Torna indietro di una migrazione
alembic downgrade -1

# Torna a una revisione specifica
alembic downgrade <revision_id>

# Vedi lo storico
alembic history --verbose
```

### Verifica stato

```bash
# Mostra la revisione corrente
alembic current

# Mostra migrazioni pending
alembic heads
```

---

## 7. Build Frontend

```bash
cd frontend

# Installa dipendenze
npm ci

# Build per produzione
npm run build

# I file statici sono in frontend/dist/
```

### Variabili d'ambiente frontend

Creare un file `.env.production` nella directory `frontend/`:

```env
VITE_API_BASE_URL=https://titoliengine.example.com/api/v1
```

---

## 8. Avvio Backend

### Diretto con uvicorn

```bash
cd backend

# Produzione: workers multipli, binding su socket
uvicorn app.main:app \
  --host 0.0.0.0 \
  --port 8000 \
  --workers 4 \
  --loop uvloop \
  --http httptools \
  --access-log \
  --log-level warning
```

### Con systemd

Creare `/etc/systemd/system/titoliengine.service`:

```ini
[Unit]
Description=TitoliEngine Backend
After=network.target postgresql.service redis.service
Wants=postgresql.service redis.service

[Service]
Type=exec
User=titoliengine
Group=titoliengine
WorkingDirectory=/opt/titoliengine/backend
EnvironmentFile=/opt/titoliengine/backend/.env
ExecStart=/opt/titoliengine/venv/bin/uvicorn app.main:app \
  --host 127.0.0.1 \
  --port 8000 \
  --workers 4 \
  --loop uvloop \
  --http httptools \
  --access-log \
  --log-level warning
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable titoliengine
sudo systemctl start titoliengine
sudo systemctl status titoliengine
```

---

## 9. NGINX Reverse Proxy

Configurazione NGINX per servire frontend statico e proxy API al backend.

Creare `/etc/nginx/sites-available/titoliengine`:

```nginx
upstream titoliengine_backend {
    server 127.0.0.1:8000;
    keepalive 32;
}

server {
    listen 80;
    server_name titoliengine.example.com;

    # Redirect HTTP -> HTTPS
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name titoliengine.example.com;

    # SSL (vedi sezione Let's Encrypt)
    ssl_certificate /etc/letsencrypt/live/titoliengine.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/titoliengine.example.com/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Content-Security-Policy "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'" always;

    # Frontend (file statici)
    root /opt/titoliengine/frontend/dist;
    index index.html;

    # API proxy
    location /api/ {
        proxy_pass http://titoliengine_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_http_version 1.1;
        proxy_set_header Connection "";

        # Timeout per operazioni pesanti (generazione scritture, valutazione)
        proxy_read_timeout 120s;
        proxy_send_timeout 120s;
    }

    # Health check
    location /health {
        proxy_pass http://titoliengine_backend;
        proxy_set_header Host $host;
    }

    # Upload: limite dimensione file
    location /api/v1/documents/upload {
        proxy_pass http://titoliengine_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        client_max_body_size 50M;
    }

    # SPA fallback: tutte le route al frontend
    location / {
        try_files $uri $uri/ /index.html;
    }

    # Cache file statici
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2)$ {
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/titoliengine /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

---

## 10. SSL con Let's Encrypt

```bash
# Installa certbot
sudo apt install certbot python3-certbot-nginx

# Ottieni certificato
sudo certbot --nginx -d titoliengine.example.com

# Il rinnovo automatico e' gia' configurato in:
# /etc/systemd/timers/certbot.timer
# oppure /etc/cron.d/certbot

# Verifica rinnovo
sudo certbot renew --dry-run
```

---

## 11. Monitoraggio

### Health check

L'endpoint `/health` restituisce lo stato dell'applicazione:

```bash
curl -s https://titoliengine.example.com/health | jq .
# {"status": "ok", "version": "1.0.0"}
```

Configurare un check periodico con cron o il monitoring tool preferito:

```bash
# Esempio cron: check ogni 5 minuti
*/5 * * * * curl -sf https://titoliengine.example.com/health || echo "TitoliEngine DOWN" | mail -s "ALERT" admin@studio.it
```

### Monitoraggio con systemd

```bash
# Stato del servizio
sudo systemctl status titoliengine

# Log in tempo reale
sudo journalctl -u titoliengine -f

# Log errori recenti
sudo journalctl -u titoliengine --since "1 hour ago" -p err
```

### Metriche da monitorare

| Metrica | Fonte | Soglia alert |
|---------|-------|--------------|
| HTTP status 5xx | NGINX access log | > 5 in 5 min |
| Response time p95 | Header `X-Process-Time` | > 2s |
| PostgreSQL connessioni attive | `pg_stat_activity` | > 80% pool |
| Redis memoria | `redis-cli info memory` | > 80% maxmemory |
| Disco (uploads) | `df` | > 85% |
| CPU / RAM backend | systemd / htop | > 80% sustained |

---

## 12. Backup

### PostgreSQL

```bash
# Backup completo
pg_dump -U titoliengine -h localhost -Fc titoliengine_prod > backup_$(date +%Y%m%d_%H%M%S).dump

# Restore
pg_restore -U titoliengine -h localhost -d titoliengine_prod --clean backup_20250115_120000.dump
```

### Script di backup automatico

Creare `/opt/titoliengine/scripts/backup.sh`:

```bash
#!/bin/bash
set -euo pipefail

BACKUP_DIR="/opt/titoliengine/backups"
RETENTION_DAYS=30
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

mkdir -p "$BACKUP_DIR"

# Backup database
pg_dump -U titoliengine -h localhost -Fc titoliengine_prod \
  > "$BACKUP_DIR/db_$TIMESTAMP.dump"

# Backup documenti uploadati
tar czf "$BACKUP_DIR/uploads_$TIMESTAMP.tar.gz" \
  /var/lib/titoliengine/uploads/

# Backup .env (senza stamparla nei log)
cp /opt/titoliengine/backend/.env "$BACKUP_DIR/env_$TIMESTAMP.bak"
chmod 600 "$BACKUP_DIR/env_$TIMESTAMP.bak"

# Pulizia backup vecchi
find "$BACKUP_DIR" -type f -mtime +$RETENTION_DAYS -delete

echo "Backup completato: $TIMESTAMP"
```

```bash
chmod +x /opt/titoliengine/scripts/backup.sh

# Cron: backup giornaliero alle 02:00
echo "0 2 * * * /opt/titoliengine/scripts/backup.sh >> /var/log/titoliengine-backup.log 2>&1" | sudo crontab -
```

### Documenti

I documenti caricati sono criptati at-rest. Il backup deve includere:
1. I file nella directory `uploads/`
2. La chiave `TE_SECRET_KEY` (senza la quale i file non sono decriptabili)

---

## 13. Sicurezza

### Checklist pre-produzione

- [ ] **`TE_SECRET_KEY`**: generata con `secrets.token_urlsafe(48)`, unica per ambiente
- [ ] **`TE_DEBUG=false`**: Swagger UI disabilitato in produzione
- [ ] **`TE_CORS_ORIGINS`**: solo il dominio di produzione, non `*`
- [ ] **Password PostgreSQL**: forte, non quella di default
- [ ] **Redis**: protetto con password o binding solo su localhost/rete interna
- [ ] **NGINX**: HTTPS obbligatorio, redirect HTTP -> HTTPS
- [ ] **Security headers**: X-Frame-Options, CSP, HSTS configurati
- [ ] **Rate limiting**: attivo (100 req/min API, 20 req/min auth)
- [ ] **File upload**: limite dimensione (50MB in NGINX)
- [ ] **Firewall**: porte 5432 e 6379 non esposte pubblicamente
- [ ] **Backup**: script automatico configurato e testato
- [ ] **Log rotation**: configurata per evitare riempimento disco
- [ ] **Utente sistema dedicato**: il backend non gira come root
- [ ] **Aggiornamenti**: piano per aggiornamenti di sicurezza OS e dipendenze

### Middleware di sicurezza integrati

TitoliEngine include middleware di sicurezza attivi di default:

1. **SecurityHeadersMiddleware**: aggiunge Helmet-equivalent headers
2. **InputSanitizationMiddleware**: sanitizza input per prevenire injection
3. **RateLimitMiddleware**: rate limiting per IP (100 req/min, 20 per auth)
4. **CORS**: configurazione restrittiva (solo origini specificate)
5. **Encryption at-rest**: documenti criptati con la secret key

### Encryption documenti

I documenti PDF caricati sono criptati prima del salvataggio su disco usando la `TE_SECRET_KEY`. La deduplicazione avviene tramite hash SHA-256 calcolato sul contenuto originale (prima della cifratura).

---

## 14. Troubleshooting

### Il backend non parte

```bash
# Verifica log
sudo journalctl -u titoliengine -n 50

# Verifica connessione DB
python -c "import asyncpg; import asyncio; asyncio.run(asyncpg.connect('postgresql://...'))"

# Verifica connessione Redis
redis-cli -u redis://localhost:6379/0 ping
```

### Errori di migrazione

```bash
# Verifica stato attuale
cd backend && alembic current

# Se il DB e' in stato inconsistente
alembic stamp head  # ATTENZIONE: marca come migrato senza eseguire
```

### Performance lente

```bash
# Verifica pool connessioni
# Nel log PostgreSQL, cercare "connection pool exhausted"

# Aumentare pool size in .env
TE_DATABASE_POOL_SIZE=20
TE_DATABASE_MAX_OVERFLOW=40

# Verifica indici mancanti
# Le query lente appaiono nel log con TE_DATABASE_ECHO=true
```

### Upload fallisce

```bash
# Verifica permessi directory upload
ls -la /var/lib/titoliengine/uploads/

# Verifica limite NGINX
# client_max_body_size in /etc/nginx/sites-available/titoliengine

# Verifica spazio disco
df -h /var/lib/titoliengine/
```
