# Tailscale Hardening (Issue #1)

## Implementiert
- `security.tailnet_only` im Config-Setup
- `security.tailscale_cidrs` zur CIDR-Pruefung (Default `100.64.0.0/10`)
- `security.tailscale_node_allowlist` zur optionalen Node-ID-Beschraenkung
- Middleware-Block fuer alle Endpunkte (ausser `/health`, `/diagnostics`)

## Konfiguration
Im Web-UI unter `Setup`:
- `Tailnet-only Zugriff`
- `Tailscale CIDRs`
- `Tailscale Node Allowlist`

Oder direkt in `config.json`:

```json
"security": {
  "tailnet_only": true,
  "tailscale_cidrs": ["100.64.0.0/10"],
  "tailscale_node_allowlist": ["node-123"]
}
```

## Hinweis
Wenn eine Node-Allowlist gesetzt ist, muss der Reverse-Proxy den Header `X-Tailscale-Node` setzen.
