# Service Setup (Issue #2)

Service-Templates liegen in `deployment/services/`:
- `ontoti.service` (systemd)
- `com.ontoti.bot.plist` (launchd)
- `install-windows-service.ps1` (Windows)

## systemd (Linux)

```bash
sudo cp deployment/services/ontoti.service /etc/systemd/system/ontoti.service
sudo systemctl daemon-reload
sudo systemctl enable --now ontoti
sudo systemctl status ontoti
```

## launchd (macOS)

1. In `deployment/services/com.ontoti.bot.plist` die Pfade `REPLACE_ME` ersetzen.
2. Dann laden:

```bash
cp deployment/services/com.ontoti.bot.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.ontoti.bot.plist
launchctl start com.ontoti.bot
```

## Windows Service (PowerShell als Admin)

```powershell
Set-ExecutionPolicy RemoteSigned -Scope Process
./deployment/services/install-windows-service.ps1 -ProjectRoot "C:\OnToti"
```
