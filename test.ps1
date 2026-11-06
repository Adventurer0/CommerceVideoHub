param([switch]$SkipBrowser)
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'app/scripts/environment.ps1')
Push-Location $ProjectRoot
try {
    Initialize-Tools
    $python = Join-Path $ProjectRoot '.venv/Scripts/python.exe'
    Invoke-Checked $python @('-m', 'pytest', '-q')
    Invoke-Checked $python @('-m', 'mypy')
    Push-Location (Join-Path $ProjectRoot 'app/frontend')
    try {
        if (!(Test-Path 'node_modules')) { Invoke-Npm @('ci', '--no-audit', '--no-fund') }
        Invoke-Npm @('run', 'typecheck')
        Invoke-Npm @('run', 'build')
    } finally { Pop-Location }
    if (!$SkipBrowser) { Invoke-Checked $python @('tests/e2e.py') }
    Write-Host 'All requested checks passed.'
} finally { Pop-Location }
