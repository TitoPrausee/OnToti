#!/usr/bin/env bash
set -euo pipefail

REPO="${1:-TitoPrausee/OnToti}"

create_issue() {
  local title="$1"
  local body="$2"
  gh issue create --repo "$REPO" --title "$title" --body "$body"
}

create_issue "[Roadmap] Tailscale Netzwerk-Hardening" "Implementiere Tailnet-only Zugriff, Node-ID Allowlist und Tailscale Serve/Funnel Setup."
create_issue "[Roadmap] Daemon/Service Installation" "Service-Installationen fuer systemd, launchd und Windows Service bereitstellen."
create_issue "[Roadmap] Multi-Agent Message Bus" "Redis Streams mit standardisiertem Nachrichtenschema und Loop-Erkennung integrieren."
create_issue "[Roadmap] Pipeline Engine fuer Agenten" "Deklarative Pipeline mit Parallelisierung, Retry/Timeout und Fehlerpfaden umsetzen."
create_issue "[Roadmap] Agenten-Topologie im UI" "Live-Graph fuer Agentenbeziehungen, Status und Token-Verbrauch implementieren."
create_issue "[Roadmap] Scheduler + Trigger" "Cron (Sekundenfeld), Stagger und Event-Trigger (Webhook/File/API) integrieren."
create_issue "[Roadmap] Heartbeat Nachrichten" "Proaktive Statusmeldungen kanalweise konfigurierbar machen."
create_issue "[Roadmap] Tool-Sandbox & Policy Engine" "Datei/Shell Policy-Checks zentral durchsetzen und Verstoesse blockieren."
create_issue "[Roadmap] Unveraenderliches Audit Log" "Append-only Audit-Store mit Suche/Filter/Export im UI umsetzen."
create_issue "[Roadmap] Secret Management Hardening" "Secrets auf age/pass/keychain migrieren und Rotationflows definieren."
create_issue "[Roadmap] MCP Integration" "MCP Client Layer und erste MCP Tool-Adapter integrieren."
create_issue "[Roadmap] Skill Hot-Reload" "Skill Reload zur Laufzeit inkl. Versionierung und Rollback implementieren."
create_issue "[Roadmap] Messaging Adapter Framework" "Channel Adapter Interface mit Telegram/Discord als erste Adapter."
create_issue "[Roadmap] Multi-User Session Management" "Benannte Sessions mit isoliertem Kontext im UI umsetzen."
create_issue "[Roadmap] Provider-Abstraktion erweitern" "Adapter fuer Claude, Gemini und LM Studio finalisieren."
create_issue "[Roadmap] Vollstaendiger Offline-Betrieb" "Cloud-unabhaengigen Betrieb fuer lokale Modelle robust machen."
create_issue "[Roadmap] Browser Automation Skill" "Playwright Skill fuer Web-Interaktion, Screenshot und DOM-Extraktion."
create_issue "[Roadmap] Plugin/Webhook Framework" "Plugin Lifecycle und Webhook Routing fuer externe Systeme bauen."
create_issue "[Roadmap] Container Production Setup" "Multi-stage Docker Build, Chromium optional, Compose-Profile."
create_issue "[Roadmap] Test- und QA-Strategie" "Unit/Integration/e2e Tests plus CI Pipeline etablieren."

echo "Issues erstellt in $REPO"
