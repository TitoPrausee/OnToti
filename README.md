# OnToti

OnToti ist ein selbst gehosteter KI-Assistent mit:
- Web-UI fuer komplette Einrichtung und Betrieb
- adaptiver Persona und persistentem Speicher
- Multi-Agent-Orchestrierung mit Pipeline-Modus
- Message-Bus (local oder redis)
- Scheduler (Cron mit Sekundenfeld) + Heartbeat/Jobs
- Tailscale-Hardening (tailnet-only, CIDRs, Node-Allowlist)
- Audit-Log mit Hash-Chain-Integritaet

## One-Command Installation

### macOS / Linux

```bash
cd /Users/tito1/Desktop/Test
./install.sh
```

### Windows

```powershell
cd C:\OnToti
.\install.ps1
```

Details: `/Users/tito1/Desktop/Test/docs/INSTALL.md`

## Start

```bash
cd /Users/tito1/Desktop/Test
source .venv/bin/activate
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Web UI: `http://127.0.0.1:8000/`

## Web-UI Bereiche

- `Chat`: Multi-Session Chat
- `Topologie`: Agentenstruktur mit Tokenverbrauch
- `Agents`: Rohstatus der Agenten
- `Bus`: Nachrichtenfluss zwischen Agenten
- `Operations`: Sessions, Scheduler, Webhooks, Policy, Audit
- `Setup`: Provider/Sicherheit/Pipeline/Bus/Copilot
- `Raw Config`: direkter JSON-Editor

## API Highlights

- Runtime: `GET /health`, `GET /ready`, `GET /diagnostics`
- Setup: `GET /setup/state`, `POST /setup/apply`
- Sessions: `GET /sessions`, `POST /sessions`, `DELETE /sessions/{id}`
- Scheduler: `GET /jobs`, `POST /jobs`, `PUT /jobs/{id}`, `POST /jobs/{id}/pause`, `POST /jobs/{id}/resume`
- Pipeline/Bus: `GET /topology`, `GET /bus/messages`
- Webhooks: `POST /webhooks/{source}`, `GET /webhooks`
- Policy: `GET /policy/status`, `POST /policy/file-check`, `POST /policy/shell-check`
- Audit: `GET /audit`, `GET /audit/verify`

## Tests

```bash
cd /Users/tito1/Desktop/Test
./scripts/run_tests.sh
./scripts/smoke_test.sh
```

## Relevante Dateien

- Config: `/Users/tito1/Desktop/Test/config.json`
- Secrets: `/Users/tito1/Desktop/Test/data/secrets.json`
- DB: `/Users/tito1/Desktop/Test/data/memory.db`
- Installer: `/Users/tito1/Desktop/Test/install.sh`, `/Users/tito1/Desktop/Test/install.ps1`
