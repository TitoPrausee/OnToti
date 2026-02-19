#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

if [[ -f .venv/bin/activate ]]; then
  # shellcheck source=/dev/null
  source .venv/bin/activate
fi

PYTHONPYCACHEPREFIX="$ROOT_DIR/.pycache" python -m py_compile app/main.py app/provider.py app/orchestrator.py app/config_manager.py app/security.py
python -m unittest discover -s tests -p "test_*.py" -v
