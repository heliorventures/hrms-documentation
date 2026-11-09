# Exercise release orchestration with synthetic sources and a fake Docker command.
# No image is built and no registry or VPS is contacted.
$ErrorActionPreference = 'Stop'
$entry = Join-Path (Split-Path -Parent $PSScriptRoot) 'build-save-upload-images.ps1'
$temporary = Join-Path ([System.IO.Path]::GetTempPath()) ('hrms-build-security-' + [guid]::NewGuid().ToString('N'))
$global:SecurityGateCalls = [System.Collections.Generic.List[object]]::new()
$global:SecurityGateFailureAt = 0
function docker {
    $global:SecurityGateCalls.Add(@($args))
    if ($args[0] -eq 'run') {
        $runs = @($global:SecurityGateCalls | Where-Object { $_[0] -eq 'run' }).Count
        $global:LASTEXITCODE = if ($runs -eq $global:SecurityGateFailureAt) { 1 } else { 0 }
    } else { $global:LASTEXITCODE = 0 }
}
function Assert-Test([bool]$Condition, [string]$Message) { if (-not $Condition) { throw $Message } }
try {
    foreach ($relative in @('hrms-svc', 'hrms-gateway', 'hrms-ui', 'hrms-svc/integrations/organization-events')) {
        $directory = Join-Path $temporary $relative
        New-Item -ItemType Directory -Path $directory -Force | Out-Null
        Set-Content -LiteralPath (Join-Path $directory 'Dockerfile') -Value 'FROM scratch'
        Set-Content -LiteralPath (Join-Path $directory 'package.json') -Value '{"name":"synthetic","version":"1.0.0"}'
        Set-Content -LiteralPath (Join-Path $directory 'package-lock.json') -Value '{"lockfileVersion":3}'
    }
    foreach ($failureAt in @(1, 2, 3)) {
        $global:SecurityGateCalls.Clear()
        $global:SecurityGateFailureAt = $failureAt
        $rejected = $false
        try { & $entry -Tag security-test -SourceRoot $temporary -OutputDir (Join-Path $temporary 'out') -SkipUpload }
        catch { $rejected = $true }
        Assert-Test $rejected "Audit failure $failureAt did not block release"
        Assert-Test (@($global:SecurityGateCalls | Where-Object { $_[0] -in @('build', 'save') }).Count -eq 0) 'Audit failure reached build/save'
    }
    $global:SecurityGateCalls.Clear()
    $global:SecurityGateFailureAt = 0
    & $entry -Tag security-test -SourceRoot $temporary -OutputDir (Join-Path $temporary 'out') -SkipUpload
    $audits = @($global:SecurityGateCalls | Where-Object { $_[0] -eq 'run' })
    Assert-Test ($audits.Count -eq 3) 'Expected fresh audits of gateway, UI and event-worker lockfiles'
    foreach ($audit in $audits) {
        $arguments = $audit -join ' '
        Assert-Test ($arguments.Contains('--audit-level=low')) 'Audit threshold weakened'
        Assert-Test ($arguments.Contains('--package-lock-only')) 'Audit did not use lockfile'
        Assert-Test ($arguments.Contains('--include=dev')) 'Development tools excluded from audit'
        Assert-Test (-not $arguments.Contains('--omit')) 'Audit omitted dependencies'
        Assert-Test ($arguments.Contains('target=/app/package.json,readonly')) 'Manifest mount not read-only'
        Assert-Test ($arguments.Contains('target=/app/package-lock.json,readonly')) 'Lockfile mount not read-only'
        Assert-Test (-not $arguments.Contains('.env')) 'Secret file included in audit mounts'
    }
    Assert-Test ($global:SecurityGateCalls[0][0] -eq 'run' -and $global:SecurityGateCalls[2][0] -eq 'run') 'Audits must precede builds'
    Assert-Test (@($global:SecurityGateCalls | Where-Object { $_[0] -eq 'build' }).Count -eq 4) 'Successful audit changed build inventory'
    # A missing lockfile must fail before any image builds.
    Remove-Item -LiteralPath (Join-Path $temporary 'hrms-ui/package-lock.json')
    $global:SecurityGateCalls.Clear()
    $rejected = $false
    try { & $entry -Tag security-test -SourceRoot $temporary -OutputDir (Join-Path $temporary 'out') -SkipUpload }
    catch { $rejected = $true }
    Assert-Test $rejected 'Missing lockfile accepted'
    Assert-Test (@($global:SecurityGateCalls | Where-Object { $_[0] -in @('build', 'save') }).Count -eq 0) 'Missing lockfile reached build/save'
    Write-Host 'PASS: audit failures and missing lockfiles block releases; all dependency trees audited before builds.'
} finally {
    $resolved = [System.IO.Path]::GetFullPath($temporary)
    $parent = [System.IO.Path]::GetFullPath([System.IO.Path]::GetTempPath()).TrimEnd('\')
    if ((Split-Path -Parent $resolved) -ne $parent -or (Split-Path -Leaf $resolved) -notlike 'hrms-build-security-*') { throw 'Unsafe test cleanup path' }
    Remove-Item -LiteralPath $resolved -Recurse -Force
    Remove-Variable SecurityGateCalls,SecurityGateFailureAt -Scope Global
}
