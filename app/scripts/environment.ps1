$ErrorActionPreference = 'Stop'
$ProjectRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
$env:PYTHONUTF8 = '1'

function Invoke-Checked {
    param([string]$Exe, [string[]]$Arguments)
    & $Exe @Arguments
    if ($LASTEXITCODE -ne 0) { throw "Command failed ($LASTEXITCODE): $Exe $($Arguments -join ' ')" }
}

function Find-Node {
    $candidates = @(
        (Join-Path $ProjectRoot '.tools/node/node.exe'),
        (Join-Path $env:USERPROFILE '.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe')
    )
    $installed = Get-Command node.exe -ErrorAction SilentlyContinue
    if ($installed) { $candidates = @($installed.Source) + $candidates }
    foreach ($candidate in $candidates) {
        if (Test-Path -LiteralPath $candidate) {
            $version = & $candidate -p 'process.versions.node'
            if ([version]$version -ge [version]'22.12.0') { return $candidate }
        }
    }
    throw 'Node.js >=22.12 is required. Install Node.js LTS and reopen PowerShell.'
}

function Invoke-Npm {
    param([string[]]$Arguments)
    $npmCommand = Get-Command npm.cmd -ErrorAction SilentlyContinue
    if ($npmCommand) { Invoke-Checked $npmCommand.Source $Arguments; return }
    $npmCli = Join-Path $ProjectRoot '.tools/package/bin/npm-cli.js'
    if (!(Test-Path -LiteralPath $npmCli)) { throw 'npm is missing. Install Node.js with npm.' }
    Invoke-Checked $script:NodePath (@($npmCli) + $Arguments)
}

function Initialize-Tools {
    if (!(Get-Command uv.exe -ErrorAction SilentlyContinue)) { throw 'uv is required. See README.md.' }
    $script:NodePath = Find-Node
    $env:PATH = (Split-Path $script:NodePath) + ';' + $env:PATH
    Invoke-Checked 'uv' @('sync', '--frozen')
}

function Initialize-Runtime {
    if ($env:CVH_RUNTIME_DIR) { $directory = [IO.Path]::GetFullPath($env:CVH_RUNTIME_DIR) }
    else { $directory = Join-Path $ProjectRoot 'runtime' }
    New-Item -ItemType Directory -Force -Path $directory | Out-Null
    # Protect only this application's directory. Never alter parent ACLs.
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent().User
    $acl = New-Object Security.AccessControl.DirectorySecurity
    $acl.SetOwner($identity)
    $acl.SetAccessRuleProtection($true, $false)
    foreach ($sid in @($identity, (New-Object Security.Principal.SecurityIdentifier('S-1-5-18')))) {
        $rule = New-Object Security.AccessControl.FileSystemAccessRule($sid, 'FullControl', 'ContainerInherit,ObjectInherit', 'None', 'Allow')
        $acl.AddAccessRule($rule)
    }
    Set-Acl -LiteralPath $directory -AclObject $acl
    foreach ($child in @('logs','profiles','media','thumbnails')) {
        New-Item -ItemType Directory -Force -Path (Join-Path $directory $child) | Out-Null
    }
    return $directory
}
