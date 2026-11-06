param([switch]$NoBrowser, [switch]$PrepareOnly, [switch]$SmokeTest)
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'app/scripts/environment.ps1')
Push-Location $ProjectRoot
try {
    Initialize-Tools
    $runtime = Initialize-Runtime
    $python = Join-Path $ProjectRoot '.venv/Scripts/python.exe'
    Invoke-Checked $python @('-m', 'alembic', 'upgrade', 'head')
    Push-Location (Join-Path $ProjectRoot 'app/frontend')
    try {
        $stamp = '.dependency-lock.sha256'
        $digest = (Get-FileHash -LiteralPath 'package-lock.json' -Algorithm SHA256).Hash
        if (!(Test-Path 'node_modules/.dependency-lock.sha256') -or (Get-Content 'node_modules/.dependency-lock.sha256' -Raw).Trim() -ne $digest) {
            Invoke-Npm @('ci', '--no-audit', '--no-fund')
            Set-Content -LiteralPath "node_modules/$stamp" -Value $digest -Encoding ASCII
        }
        Invoke-Npm @('run', 'build')
    } finally { Pop-Location }
    if ($PrepareOnly) { Write-Host 'Preparation complete; no server started.'; return }
    # Check availability before starting so an unrelated process is never reused.
    $probe = New-Object Net.Sockets.TcpListener([Net.IPAddress]::Parse('127.0.0.1'),8765)
    try { $probe.Start() } finally { $probe.Stop() }
    $stdout = Join-Path $runtime 'logs/server.stdout.log'
    $stderr = Join-Path $runtime 'logs/server.stderr.log'
    $stopFile = Join-Path $runtime ('stop-' + [guid]::NewGuid().ToString() + '.flag')
    $server = Start-Process -FilePath $python -ArgumentList @('-m','app.backend.serve','--stop-file', ('"{0}"' -f $stopFile)) -WorkingDirectory $ProjectRoot -WindowStyle Hidden -RedirectStandardOutput $stdout -RedirectStandardError $stderr -PassThru
    try {
        $ready = $false
        for ($attempt=0; $attempt -lt 40; $attempt++) {
            if ($server.HasExited) { throw "Server exited. See $stderr" }
            try {
                $health = Invoke-RestMethod 'http://127.0.0.1:8765/api/health' -TimeoutSec 1
                if ($health.status -eq 'ok') { $ready=$true; break }
            } catch { Start-Sleep -Milliseconds 250 }
        }
        if (!$ready) { throw "Health check failed. See $stderr" }
        Write-Host 'CommerceVideoHub: http://127.0.0.1:8765'
        Write-Host 'G1 scaffold; publishing disabled. Press Ctrl+C to stop.'
        if ($SmokeTest) {
            $page = Invoke-WebRequest 'http://127.0.0.1:8765/' -UseBasicParsing
            if ($page.StatusCode -ne 200 -or !$page.Content.Contains('CommerceVideoHub')) { throw 'Frontend smoke failed' }
            $listeners = @(Get-NetTCPConnection -State Listen -LocalPort 8765 -ErrorAction Stop)
            if (!$listeners.Count -or @($listeners | Where-Object LocalAddress -ne '127.0.0.1').Count) { throw 'Unexpected network binding' }
            Write-Host 'STARTUP SMOKE PASSED: HTTP 200, database healthy, listener 127.0.0.1:8765 only.'
            return
        }
        if (!$NoBrowser) { Start-Process 'http://127.0.0.1:8765' }
        while (!$server.HasExited) { Start-Sleep -Milliseconds 500 }
        if ($server.ExitCode -ne 0) { throw "Server exited with code $($server.ExitCode)" }
    } finally {
        if (!$server.HasExited) {
            New-Item -ItemType File -Path $stopFile -Force | Out-Null
            if (!$server.WaitForExit(10000)) { & taskkill.exe /PID $server.Id /T /F | Out-Null }
        }
        Remove-Item -LiteralPath $stopFile -Force -ErrorAction SilentlyContinue
    }
} finally { Pop-Location }
