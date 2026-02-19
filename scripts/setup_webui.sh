#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

choose_python() {
  if command -v python3.12 >/dev/null 2>&1; then
    echo "python3.12"
    return
  fi
  if command -v python3.11 >/dev/null 2>&1; then
    echo "python3.11"
    return
  fi
  if command -v python3 >/dev/null 2>&1; then
    echo "python3"
    return
  fi
  echo "" 
}

PY_BIN="$(choose_python)"
if [[ -z "$PY_BIN" ]]; then
  echo "Kein Python gefunden. Installiere Python 3.12 oder 3.11."
  exit 1
fi

echo "[1/5] Nutze Python: $PY_BIN"

if [[ -d .venv ]]; then
  echo "[2/5] Vorhandene .venv wird weiterverwendet"
else
  echo "[2/5] Erzeuge virtuelle Umgebung"
  "$PY_BIN" -m venv .venv
fi

# shellcheck source=/dev/null
source .venv/bin/activate

echo "[3/5] Upgrade pip"
python -m pip install --upgrade pip

echo "[4/5] Installiere Dependencies"
pip install -r requirements.txt

echo "[5/5] Prüfe Kernmodule"
PYTHONPYCACHEPREFIX="$ROOT_DIR/.pycache" python -m py_compile app/main.py app/provider.py app/orchestrator.py

cat <<MSG

Setup abgeschlossen.

Start:
  source .venv/bin/activate
  python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

Öffnen:
  http://127.0.0.1:8000/

MSG
