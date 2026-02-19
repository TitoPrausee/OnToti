#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

if [[ ! -f .venv/bin/activate ]]; then
  echo "Fehlt: .venv. Bitte zuerst scripts/setup_webui.sh ausführen."
  exit 1
fi

# shellcheck source=/dev/null
source .venv/bin/activate
exec python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
