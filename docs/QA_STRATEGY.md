# QA Strategy (Issue #20)

## Aktueller Stand
- Unit-Tests in `tests/`
- CI Workflow in `.github/workflows/ci.yml`
- Syntax-Check + unittest bei jedem Push/PR

## Testumfang V1
- `tests/test_security.py`: Tailnet/CIDR/Allowlist Regeln
- `tests/test_config_manager.py`: Config-Validierung

## Nächste Schritte
- API Integration Tests fuer Setup-Endpoints
- End-to-End UI Tests (Playwright)
- Smoke-Test gegen aktive Provider in separatem, optionalem CI-Job
