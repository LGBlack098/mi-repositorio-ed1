param([int]$Port = 8000, [string]$BindAddress = '127.0.0.1')
$ErrorActionPreference = 'Stop'
$projectPython = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
Push-Location -LiteralPath $PSScriptRoot
try {
    & $projectPython main.py --web --sin-abrir --host $BindAddress --port $Port
} finally {
    Pop-Location
}
