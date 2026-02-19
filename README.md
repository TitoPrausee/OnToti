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
- Maximal aktive Agenten
- Copilot Quick Setup (Token pruefen + aktivieren)

## Neue Umsetzungen aus offenen Issues

- Issue #1: Tailscale Hardening Basis (`tailnet_only`, CIDRs, Node-Allowlist)
- Issue #2: Service-Templates fuer systemd/launchd/Windows
- Issue #19: Multi-stage Docker + Production Compose + optionales Chromium Profil
- Issue #20: Unit-Tests + CI Workflow

## Doku

- Web-UI Setup: `/Users/tito1/Desktop/Test/docs/WEBUI_SETUP.md`
- Tailscale Hardening: `/Users/tito1/Desktop/Test/docs/TAILSCALE_HARDENING.md`
- Service Setup: `/Users/tito1/Desktop/Test/docs/SERVICE_SETUP.md`
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
