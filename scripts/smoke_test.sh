#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

# shellcheck source=/dev/null
source .venv/bin/activate

PORT="${ONTOTI_SMOKE_PORT:-8099}"
LOG="/tmp/ontoti-smoke.log"

python -m uvicorn app.main:app --host 127.0.0.1 --port "$PORT" >"$LOG" 2>&1 &
PID=$!
trap 'kill $PID 2>/dev/null || true' EXIT

sleep 2

curl -fsS "http://127.0.0.1:$PORT/health" >/dev/null
curl -fsS "http://127.0.0.1:$PORT/ready" >/dev/null
curl -fsS "http://127.0.0.1:$PORT/setup/state" >/dev/null
curl -fsS "http://127.0.0.1:$PORT/sessions" >/dev/null
curl -fsS "http://127.0.0.1:$PORT/jobs" >/dev/null
curl -fsS "http://127.0.0.1:$PORT/policy/status" >/dev/null
curl -fsS "http://127.0.0.1:$PORT/topology" >/dev/null
curl -fsS "http://127.0.0.1:$PORT/bus/messages" >/dev/null

curl -fsS -X POST "http://127.0.0.1:$PORT/chat" \
  -H 'content-type: application/json' \
  -d '{"session_id":"smoke","text":"Bitte teste die Runtime."}' >/dev/null

curl -fsS "http://127.0.0.1:$PORT/audit/verify" >/dev/null

echo "smoke ok"
