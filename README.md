# Soul Bot Prototype (Web-Setup Ready)

Dieses Projekt ist ein erster finalisierter Prototyp mit Fokus auf:
- Self-hosted Bot Runtime
- Adaptive Persona + Stil-Lernen
- Multi-Agent-Basis (Orchestrator + Sub-Agents)
- Voller Setup-Flow im Web-UI
- Copilot-Anbindung per Klick im Setup-Tab

## Quickstart

```bash
cd /Users/tito1/Desktop/Test
./scripts/setup_webui.sh
./scripts/run_webui.sh
```

Öffne dann: `http://127.0.0.1:8000/`

## Konfiguration über Web-UI

Im Tab `Setup` kannst du konfigurieren:
- Bot-Identity (Name/Ton)
- Provider (github_models/openai/ollama/lmstudio)
- API-Key-ENV + API-Key-Wert
- Security-Optionen (Sandbox, Allow Paths)
- Maximal aktive Agenten
- Optional: Copilot Quick Setup (Token prüfen + aktivieren)

## Wichtige Dateien

- `/Users/tito1/Desktop/Test/config.json`
- `/Users/tito1/Desktop/Test/data/persona.json`
- `/Users/tito1/Desktop/Test/data/style_profile.json`
- `/Users/tito1/Desktop/Test/data/secrets.json`
- `/Users/tito1/Desktop/Test/data/memory.db`

## Setup-Skript + Doku

- Setup Script: `/Users/tito1/Desktop/Test/scripts/setup_webui.sh`
- Start Script: `/Users/tito1/Desktop/Test/scripts/run_webui.sh`
- Anleitung: `/Users/tito1/Desktop/Test/docs/WEBUI_SETUP.md`

## API (Auszug)

- `GET /setup/state`
- `POST /setup/apply`
- `POST /provider/test`
- `POST /copilot/setup`
- `GET /config`
- `PUT /config`
- `POST /chat`
- `GET /agents`
- `GET /audit`

## Hinweis

Secrets werden lokal in `data/secrets.json` gespeichert (Dateirechte werden auf restriktiv gesetzt, sofern vom OS erlaubt).

## Offene Planung (Roadmap)

Die folgenden Punkte sind als naechste Ausbaustufen geplant und werden als einzelne GitHub-Issues verfolgt:

1. Tailscale Netzwerk-Hardening (Tailnet-only, Allowlist, Serve/Funnel)
2. Daemon/Service Installation (systemd, launchd, Windows Service)
3. Multi-Agent Message Bus (Redis Streams + Loop-Erkennung)
4. Pipeline Engine fuer Agenten (deklarativ, retry/timeout)
5. Agenten-Topologie Live-Visualisierung im UI
6. Scheduler + Trigger (Cron Sekundenfeld, Webhook/File/API)
7. Heartbeat und proaktive Nachrichten
8. Tool-Sandbox und zentrale Policy Engine
9. Unveraenderliches Audit Log mit Suche/Export
10. Secret Management Hardening (age/pass/keychain)
11. MCP Server Integration
12. Skill Hot-Reload + Versionierung + Rollback
13. Messaging Adapter Framework (Telegram/Discord zuerst)
14. Multi-User Session Management
15. Provider-Abstraktion erweitern (Claude/Gemini/LM Studio)
16. Vollstaendiger Offline-Betrieb fuer lokale Modelle
17. Browser Automation Skill (Playwright)
18. Plugin/Webhook Framework
19. Container Production Setup (multi-stage/profiles)
20. Test- und QA-Strategie mit CI

Details und Issue-Texte: `/Users/tito1/Desktop/Test/docs/OPEN_ISSUES.md`

Automatische Erstellung der Issues:

```bash
cd /Users/tito1/Desktop/Test
./scripts/create_github_issues.sh TitoPrausee/OnToti
```
