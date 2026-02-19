# OnToti (Web-Setup Ready)

OnToti ist ein selbst gehosteter KI-Assistent mit Web-Setup, adaptiver Persona, Multi-Agent-Basis und Copilot-Integration.

## Quickstart

```bash
cd /Users/tito1/Desktop/Test
./scripts/setup_webui.sh
./scripts/run_webui.sh
```

Oeffnen: `http://127.0.0.1:8000/`

## Web-Setup Features

Im Tab `Setup` kannst du konfigurieren:
- Bot-Identity (Name/Ton)
- Provider (github_models/openai/ollama/lmstudio)
- API-Key-ENV + API-Key-Wert (lokal in `data/secrets.json`)
- Security: Sandbox, Tailnet-only, Tailscale CIDRs, Node-Allowlist
- Agenten-Limit, Pipeline-Modus und Retries
- Message-Bus Backend (local/redis)
- Copilot Quick Setup (Token pruefen + aktivieren)

## Umgesetzte Roadmap-Issues

- `#1` Tailscale Hardening Basis
- `#2` Service-Templates fuer systemd/launchd/Windows
- `#3` Multi-Agent Message Bus (local + optional redis)
- `#4` Pipeline Engine (sequential/parallel + Retry + Zykluscheck)
- `#5` Agenten-Topologie im UI
- `#19` Container Production Setup
- `#20` Test- und QA-Grundlage (CI + Unit Tests)

## Neue Endpunkte

- `GET /topology`
- `GET /bus/messages`
- `GET /security/status`

## Doku

- Web-UI Setup: `/Users/tito1/Desktop/Test/docs/WEBUI_SETUP.md`
- Tailscale Hardening: `/Users/tito1/Desktop/Test/docs/TAILSCALE_HARDENING.md`
- Service Setup: `/Users/tito1/Desktop/Test/docs/SERVICE_SETUP.md`
- Pipeline + Bus: `/Users/tito1/Desktop/Test/docs/PIPELINE_BUS.md`
- QA Strategie: `/Users/tito1/Desktop/Test/docs/QA_STRATEGY.md`
- Offene Planung: `/Users/tito1/Desktop/Test/docs/OPEN_ISSUES.md`

## Service/Container Dateien

- systemd: `/Users/tito1/Desktop/Test/deployment/services/ontoti.service`
- launchd: `/Users/tito1/Desktop/Test/deployment/services/com.ontoti.bot.plist`
- Windows: `/Users/tito1/Desktop/Test/deployment/services/install-windows-service.ps1`
- Docker: `/Users/tito1/Desktop/Test/Dockerfile`
- Compose: `/Users/tito1/Desktop/Test/docker-compose.yml`
- Compose Prod: `/Users/tito1/Desktop/Test/docker-compose.prod.yml`

## Tests

```bash
cd /Users/tito1/Desktop/Test
./scripts/run_tests.sh
```
