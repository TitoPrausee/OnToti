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
