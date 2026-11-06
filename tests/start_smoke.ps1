$ErrorActionPreference = 'Stop'
$root = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
for ($iteration=1; $iteration -le 2; $iteration++) {
    & powershell.exe -NoProfile -ExecutionPolicy Bypass -File (Join-Path $root 'start.ps1') -NoBrowser -SmokeTest
    if ($LASTEXITCODE -ne 0) { throw "Startup iteration $iteration failed" }
    $listener = @(Get-NetTCPConnection -State Listen -LocalPort 8765 -ErrorAction SilentlyContinue)
    if ($listener.Count) { throw 'Server left a listener after shutdown' }
    Write-Host "START/STOP ITERATION $iteration PASSED"
}
$acl = Get-Acl -LiteralPath (Join-Path $root 'runtime')
if (!$acl.AreAccessRulesProtected) { throw 'Runtime ACL inheritance was not disabled' }
$allowed = @([Security.Principal.WindowsIdentity]::GetCurrent().User.Value, 'S-1-5-18')
foreach ($rule in $acl.Access) {
    $sid = $rule.IdentityReference.Translate([Security.Principal.SecurityIdentifier]).Value
    if ($sid -notin $allowed) { throw "Unexpected runtime ACL principal: $sid" }
}
Write-Host 'RUNTIME ACL PASSED: current user and SYSTEM only.'
