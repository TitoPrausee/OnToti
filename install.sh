#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT_DIR"

INSTALL_SERVICE="${INSTALL_SERVICE:-1}"
HOST="${ONTOTI_HOST:-127.0.0.1}"
PORT="${ONTOTI_PORT:-8000}"

choose_python() {
  if command -v python3.12 >/dev/null 2>&1; then echo "python3.12"; return; fi
  if command -v python3.11 >/dev/null 2>&1; then echo "python3.11"; return; fi
  if command -v python3 >/dev/null 2>&1; then echo "python3"; return; fi
  echo ""
}

PY_BIN="$(choose_python)"
if [[ -z "$PY_BIN" ]]; then
  echo "Kein Python gefunden. Bitte Python 3.11+ installieren."
  exit 1
fi

echo "[1/8] Python: $PY_BIN"
if [[ ! -d .venv ]]; then
  "$PY_BIN" -m venv .venv
fi

# shellcheck source=/dev/null
source .venv/bin/activate

echo "[2/8] Abhaengigkeiten installieren"
python -m pip install --upgrade pip
pip install -r requirements.txt

echo "[3/8] Verzeichnisse initialisieren"
mkdir -p data logs skills
[[ -f data/secrets.json ]] || echo '{}' > data/secrets.json
chmod 600 data/secrets.json 2>/dev/null || true

echo "[4/8] Konfigurationsdatei pruefen"
python - <<'PY'
from app.config_manager import ConfigManager
cm = ConfigManager(__import__('pathlib').Path('config.json'))
ok, msg = cm.validate(cm.load())
if not ok:
    raise SystemExit(f"config invalid: {msg}")
print("config ok")
PY

echo "[5/8] Tests ausfuehren"
./scripts/run_tests.sh

echo "[6/8] Smoke-Test"
./scripts/smoke_test.sh

echo "[7/8] Service-Setup"
if [[ "$INSTALL_SERVICE" == "1" ]]; then
  OS="$(uname -s)"
  if [[ "$OS" == "Linux" ]]; then
    mkdir -p "$HOME/.config/systemd/user"
    cat > "$HOME/.config/systemd/user/ontoti.service" <<UNIT
[Unit]
Description=OnToti AI Assistant (User)
After=network.target

[Service]
Type=simple
WorkingDirectory=$ROOT_DIR
ExecStart=$ROOT_DIR/.venv/bin/python -m uvicorn app.main:app --host $HOST --port $PORT
Restart=always
RestartSec=3
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=default.target
UNIT
    systemctl --user daemon-reload || true
    systemctl --user enable --now ontoti.service || true
  elif [[ "$OS" == "Darwin" ]]; then
    mkdir -p "$HOME/Library/LaunchAgents"
    cat > "$HOME/Library/LaunchAgents/com.ontoti.bot.plist" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>Label</key><string>com.ontoti.bot</string>
  <key>ProgramArguments</key><array>
    <string>$ROOT_DIR/.venv/bin/python</string>
    <string>-m</string><string>uvicorn</string><string>app.main:app</string>
    <string>--host</string><string>$HOST</string><string>--port</string><string>$PORT</string>
  </array>
  <key>WorkingDirectory</key><string>$ROOT_DIR</string>
  <key>RunAtLoad</key><true/>
  <key>KeepAlive</key><true/>
  <key>StandardOutPath</key><string>$ROOT_DIR/logs/ontoti.out.log</string>
  <key>StandardErrorPath</key><string>$ROOT_DIR/logs/ontoti.err.log</string>
</dict></plist>
PLIST
    launchctl unload "$HOME/Library/LaunchAgents/com.ontoti.bot.plist" 2>/dev/null || true
    launchctl load "$HOME/Library/LaunchAgents/com.ontoti.bot.plist" || true
  else
    echo "Service-Autoinstall fuer dieses OS nicht implementiert."
  fi
else
  echo "Service-Setup uebersprungen (INSTALL_SERVICE=0)."
fi

echo "[8/8] Fertig"
cat <<MSG

OnToti ist installiert.

Start manuell:
  source .venv/bin/activate
  python -m uvicorn app.main:app --host $HOST --port $PORT

Web UI:
  http://$HOST:$PORT/

MSG
