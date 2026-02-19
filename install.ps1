$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
  Write-Error "Python nicht gefunden. Bitte Python 3.11+ installieren."
}

if (-not (Test-Path ".venv")) {
  python -m venv .venv
}

.\.venv\Scripts\python -m pip install --upgrade pip
.\.venv\Scripts\pip install -r requirements.txt

if (-not (Test-Path "data")) { New-Item -ItemType Directory -Path data | Out-Null }
if (-not (Test-Path "logs")) { New-Item -ItemType Directory -Path logs | Out-Null }
if (-not (Test-Path "skills")) { New-Item -ItemType Directory -Path skills | Out-Null }
if (-not (Test-Path "data\secrets.json")) { '{}' | Out-File -Encoding utf8 "data\secrets.json" }

.\.venv\Scripts\python -m unittest discover -s tests -p "test_*.py" -v

Write-Host "Installation abgeschlossen."
Write-Host "Start: .\.venv\Scripts\python -m uvicorn app.main:app --host 127.0.0.1 --port 8000"
