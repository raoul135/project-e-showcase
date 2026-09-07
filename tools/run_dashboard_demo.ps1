[CmdletBinding()]
param(
    [int]$Port = 8501
)

$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot
$venvRoot = Join-Path $repoRoot '.venv'
$venvPython = Join-Path $venvRoot 'Scripts\python.exe'
$requirements = Join-Path $repoRoot 'dashboard\requirements.txt'
$requirementsMarker = Join-Path $venvRoot '.project-e-dashboard-requirements.sha256'

function Find-SystemPython {
    $candidates = @(
        @{ Command = 'py'; Arguments = @('-3') },
        @{ Command = 'python'; Arguments = @() },
        @{ Command = 'python3'; Arguments = @() }
    )

    foreach ($candidate in $candidates) {
        $command = Get-Command $candidate.Command -ErrorAction SilentlyContinue
        if ($null -eq $command) { continue }
        try {
            & $command.Source @($candidate.Arguments) -c 'import sys; print(sys.executable)' 2>$null | Out-Null
            if ($LASTEXITCODE -eq 0) {
                return $candidate
            }
        }
        catch {
            # Try the next interpreter name.
        }
    }
    return $null
}

function Invoke-Python {
    param(
        [Parameter(Mandatory)] [string]$Executable,
        [Parameter(Mandatory)] [string[]]$Arguments
    )
    & $Executable @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Python command failed with exit code ${LASTEXITCODE}: $Executable $($Arguments -join ' ')"
    }
}

if (-not (Test-Path -LiteralPath $requirements -PathType Leaf)) {
    throw "Dashboard requirements file was not found at $requirements."
}

if (-not (Test-Path -LiteralPath $venvPython -PathType Leaf)) {
    $systemPython = Find-SystemPython
    if ($null -eq $systemPython) {
        throw "Python 3 is required to run the Project-E demo. Install Python 3 from https://www.python.org/downloads/ and run this script again."
    }

    Write-Host "Creating the Project-E demo virtual environment..."
    & $systemPython.Command @($systemPython.Arguments) -m venv $venvRoot
    if ($LASTEXITCODE -ne 0 -or -not (Test-Path -LiteralPath $venvPython -PathType Leaf)) {
        throw "Python was found, but creating the demo virtual environment failed at $venvRoot."
    }
}

$requirementsHash = (Get-FileHash -LiteralPath $requirements -Algorithm SHA256).Hash
$installedHash = if (Test-Path -LiteralPath $requirementsMarker -PathType Leaf) {
    (Get-Content -LiteralPath $requirementsMarker -Raw).Trim()
} else { '' }

if ($requirementsHash -ne $installedHash) {
    Write-Host "Preparing the Project-E demo dependencies (first run or requirements changed)..."
    Invoke-Python -Executable $venvPython -Arguments @('-m', 'pip', 'install', '--upgrade', 'pip')
    Invoke-Python -Executable $venvPython -Arguments @('-m', 'pip', 'install', '--requirement', $requirements)
    Set-Content -LiteralPath $requirementsMarker -Value $requirementsHash -Encoding ASCII
}

Write-Host "Starting the privacy-safe Project-E dashboard demo on port $Port..."
$env:PROJECT_E_DASHBOARD_MODE = 'demo'
Invoke-Python -Executable $venvPython -Arguments @('-m', 'streamlit', 'run', (Join-Path $repoRoot 'dashboard\app.py'), '--server.port', "$Port", '--server.headless', 'true')
