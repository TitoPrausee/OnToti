param(
  [string]$ServiceName = "OnToti",
  [string]$ProjectRoot = "C:\OnToti"
)

$pythonExe = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
$binPath = '"' + $pythonExe + '" -m uvicorn app.main:app --host 0.0.0.0 --port 8000'

New-Service -Name $ServiceName -BinaryPathName $binPath -DisplayName "OnToti AI Assistant" -StartupType Automatic
Start-Service -Name $ServiceName
Write-Host "Service $ServiceName installiert und gestartet."
