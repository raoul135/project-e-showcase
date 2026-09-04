[CmdletBinding()]
param(
    [int]$Port = 8501
)

$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot
$python = Join-Path $repoRoot '.venv\Scripts\python.exe'

if (-not (Test-Path -LiteralPath $python)) {
    throw "Expected virtual environment Python at $python. Create it and install the dashboard requirements first."
}

$env:PROJECT_E_DASHBOARD_MODE = 'demo'
& $python -m streamlit run (Join-Path $repoRoot 'dashboard\app.py') --server.port $Port --server.headless true
