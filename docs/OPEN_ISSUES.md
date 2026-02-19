# Offene Planung als Issues

## 1. Tailscale Netzwerk-Hardening
- Tailnet-only Zugriff auf UI/API
- Node-ID Allowlist
- Tailscale Serve/Funnel Dokumentation

## 2. Daemon/Service Installation
- systemd Service Unit
- launchd plist
- Windows Service Wrapper

## 3. Multi-Agent Message Bus
- Redis Streams Integration
- Nachrichten-Schema (sender, empfaenger, task, prioritaet)
- Loop-Erkennung gegen zirkulaere Abhaengigkeiten

## 4. Pipeline Engine fuer Agenten
- Deklarative Pipeline-Definition
- Parallelisierung + Retry/Timeout Regeln
- Fehlerbehandlung je Pipeline-Stufe

## 5. Agenten-Topologie Live-Visualisierung
- Echtzeit-Graph im UI
- Eltern-Kind Beziehungen
- Token-Nutzung je Agent

## 6. Scheduler + Trigger System
- Cron mit Sekundenfeld
- Stagger/Jitter pro Job
- Trigger: Webhook, File Watcher, API Status

## 7. Heartbeat & Proaktive Nachrichten
- Regelbasierte Statuszusammenfassungen
- Kanalweise Aktivierung/Deaktivierung

## 8. Tool-Sandbox und Policy Engine
- Dateisystem-Whitelist Enforcer
- Shell Policy (sandboxed/direct)
- Blockliste fuer destruktive Kommandos

## 9. Unveraenderliches Audit Log
- Append-only Event-Store
- Filter/Search im UI
- Export als JSONL/CSV

## 10. Secret Management Hardening
- Migration auf age/pass/system keychain
- Secret Rotation Flows
- Keine Klartext-Secrets in Config

## 11. MCP Server Integration
- MCP Client Layer
- Tool Discovery + Healthchecks
- Erste Referenz-Adapter

## 12. Skill-Hot-Reload + Versionierung
- Runtime Reload ohne Neustart
- Skill Registry Version Lock
- Rollback auf vorherige Skill-Version

## 13. Messaging Adapter Framework
- Einheitliches Channel Adapter Interface
- Startadapter: Telegram + Discord
- Allowlist + Pairing Flow

## 14. Multi-User Session Management
- Benannte Sessions im UI
- Kontextwechsel ohne Verlust
- Session-spezifische Agenten-Kontexte

## 15. Provider-Abstraktion erweitern
- Anthropic Claude Adapter
- Gemini Adapter
- LM Studio OpenAI-kompatibel finalisieren

## 16. Offline-Betrieb Vollstaendig
- Cloud-freie Pfade fuer Ollama/LM Studio
- Offline Healthchecks + Warnhinweise

## 17. Browser Automation Skill
- Playwright Worker + Screenshot Pipeline
- DOM-Extraktion fuer Agenteninput

## 18. Plugin/Webhook Framework
- Eingehende Webhooks mit Routing
- Plugin Lebenszyklus (install/update/remove)

## 19. Container Production Setup
- Multi-stage Docker Build
- Optionaler Chromium Container
- Compose Profiles (dev/prod)

## 20. Test- und QA-Strategie
- Unit + Integration + e2e Tests
- API Contract Tests
- CI Pipeline fuer Lint/Test/Build
