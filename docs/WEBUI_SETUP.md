# Web-UI Setup Guide

## Ziel
Dieses Setup richtet den Bot so ein, dass nahezu alles im Web-UI konfiguriert wird:
- Bot-Identity (Name/Ton)
- Provider (Copilot/OpenAI/Ollama/LMStudio)
- API-Keys (lokal gespeichert in `data/secrets.json`)
- Security-Optionen
- Agenten-Limits

## 1. Einmaliges Setup

```bash
cd /Users/tito1/Desktop/Test
./scripts/setup_webui.sh
```

Falls `python3.12` nicht installiert ist, nutzt das Skript `python3.11` oder `python3`.

## 2. Start

```bash
cd /Users/tito1/Desktop/Test
./scripts/run_webui.sh
```

Dann öffnen:
- `http://127.0.0.1:8000/`

## 3. Setup in der UI

1. Tab `Setup` öffnen.
2. Identity setzen (`Bot Name`, `Ton`).
3. Provider setzen (`active`, `base_url`, `model`, `api key env`, `api key value`).
4. Optional `Copilot jetzt verbinden` aktivieren und GitHub Token eingeben.
5. Security + Agenten konfigurieren.
6. `Setup anwenden` klicken.
7. `Provider testen` klicken.

## 4. Persistenz

- Konfiguration: `config.json`
- Persona: `data/persona.json`
- Secrets: `data/secrets.json`
- Memory/Audit: `data/memory.db`

## 5. Diagnostics

- `GET /health`
- `GET /diagnostics`
- `GET /setup/state`
- `POST /provider/test`
