# OnToti Installation (One Command)

## macOS / Linux

```bash
cd /Users/tito1/Desktop/Test
./install.sh
```

Was der Installer erledigt:
1. Python-Venv erstellen/aktualisieren
2. Abhaengigkeiten installieren
3. Config/Secrets initialisieren
4. Tests ausfuehren
5. Smoke-Test gegen laufende API
6. Service als User-Dienst einrichten (launchd oder systemd --user)

### Start/Stop Service

- Linux (user service):
```bash
systemctl --user status ontoti.service
systemctl --user restart ontoti.service
```

- macOS (launchd):
```bash
launchctl list | grep com.ontoti.bot
launchctl kickstart -k gui/$(id -u)/com.ontoti.bot
```

## Windows

```powershell
cd C:\OnToti
.\install.ps1
```

Danach manuell starten:
```powershell
.\.venv\Scripts\python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

## Verifikation

- Health: `GET /health`
- Readiness: `GET /ready`
- Setup State: `GET /setup/state`
- UI: `http://127.0.0.1:8000/`
