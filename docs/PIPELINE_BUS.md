# Pipeline + Message Bus (Issues #3, #4, #5)

## Umgesetzt
- Interner Message-Bus mit Local Backend und optionalem Redis Streams Backend.
- Pipeline-Ausfuehrung im Orchestrator (`sequential` oder `parallel`) mit Retry-Logik.
- Zyklische Abhaengigkeiten in Pipeline-Graphen werden erkannt und blockiert.
- Neue Endpunkte:
  - `GET /bus/messages`
  - `GET /topology`
- UI-Erweiterung:
  - Tab `Topologie` mit grafischer Darstellung der Agentenstruktur
  - Tab `Bus` mit Live-Nachrichten

## Konfiguration

```json
"pipelines": {
  "mode": "sequential",
  "max_retries": 1
},
"bus": {
  "backend": "local",
  "redis_url": "redis://localhost:6379/0",
  "stream_key": "ontoti:bus",
  "max_messages": 1000
}
```

## Hinweise
- Bei `bus.backend=redis` wird `redis` nur genutzt, wenn das Python-Paket verfuegbar ist.
- Ohne Redis faellt der Bus automatisch auf in-memory zurueck.
