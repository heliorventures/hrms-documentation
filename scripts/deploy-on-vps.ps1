<#
.SYNOPSIS
Render and release HRMS applications independently of the shared VPS platform.
.DESCRIPTION
Use -Manifest for company-bound organization deployments. Platform setup,
PostgreSQL provisioning, ClickHouse migration, Kafka and root Caddy have separate
operator steps. Use -RenderOnly for local review artifacts without SSH/SCP.
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][ValidatePattern('^[a-zA-Z0-9_.-]+$')][string]$Tag,
    [string]$VpsHost,[string]$VpsUser='deploy',[int]$SshPort=22,[string]$SshIdentityFile,
    [string]$AppDir='/opt/apps/hrms',[string]$ImageDir='/opt/apps/hrms/images',
    [string]$Manifest,[string]$OutputDir,[switch]$RenderOnly,[string]$InventoryReport,
    [string]$PublicBaseUrl,[string]$ApiBaseUrl,[string]$CaddySiteAddress,
    [switch]$Deploy,[switch]$SyncCompose,[switch]$LoadImages,[switch]$Up,[switch]$Validate,[switch]$SkipValidation,
    [switch]$SyncEnvExample,[switch]$SyncCaddyfile,[switch]$SyncTenantDatabaseTarget
)
$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot 'deploy/Remote.ps1')
Assert-RemoteValue $AppDir 'AppDir'; Assert-RemoteValue $ImageDir 'ImageDir'
if ($AppDir -eq '/opt/apps' -or -not $ImageDir.StartsWith("$AppDir/")) { throw 'Use an HRMS application subdirectory and its own images directory; platform root is separate.' }
if ($SyncCaddyfile -or $CaddySiteAddress) { throw 'Root Caddy is shared: use the reviewed platform setup/Caddy procedure, not an HRMS application release.' }
if ($SyncEnvExample) { throw 'Provision separate env files using deploy/hrms/environment.md. Fleet-wide deploy/.env is never copied into organization containers.' }
if ($SyncTenantDatabaseTarget) { throw 'PostgreSQL registration/provisioning belongs to hrms-database. Application deployment never rewrites company database mappings.' }
if (-not $OutputDir) { $OutputDir=Join-Path ([System.IO.Path]::GetTempPath()) ("hrms-release-"+[guid]::NewGuid().ToString('N')) }
New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null
$manifestPath=Join-Path $OutputDir 'manifest.json'
if ($Manifest) {
    $config=Get-Content -LiteralPath $Manifest -Raw | ConvertFrom-Json
    $config | Add-Member -NotePropertyName tag -NotePropertyValue $Tag -Force
    $config | Add-Member -NotePropertyName appDir -NotePropertyValue $AppDir -Force
} else { throw 'Supply -Manifest with the bound company layout. Rollback uses the previous reviewed release artifacts.' }
if ($PublicBaseUrl -or $ApiBaseUrl) { throw 'Configure public origins in the reviewed company manifest.' }
$json=$config | ConvertTo-Json -Depth 25
[System.IO.File]::WriteAllText($manifestPath,$json,[System.Text.UTF8Encoding]::new($false))
Invoke-Native 'node' @((Join-Path $PSScriptRoot 'deploy/render.mjs'),$manifestPath,$OutputDir)
if ($RenderOnly) { Write-Host "Review generated HRMS artifacts: $OutputDir"; return }
if (-not $VpsHost) { throw 'VpsHost required for remote actions.' }
if ($Deploy) { $SyncCompose=$true; $LoadImages=$true; $Up=$true; $Validate=$true }
if ($SkipValidation) { $Validate=$false }
if ($Up) {
    if (-not $InventoryReport) { throw 'Startup requires -InventoryReport from the read-only hrms-database shared-fleet preflight.' }
    $inventory=Get-Item -LiteralPath $InventoryReport
    if ($inventory.PSIsContainer -or ($inventory.Attributes -band [System.IO.FileAttributes]::ReparsePoint)) { throw 'Inventory report must be a regular file.' }
}
Initialize-Remote $VpsHost $VpsUser $SshPort $SshIdentityFile
Invoke-Remote "set -eu; umask 077; mkdir -p '$AppDir/config' '$AppDir/caddy' '$AppDir/images' '$AppDir/scripts'"
if ($SyncCompose) {
    $release=Get-Content -LiteralPath (Join-Path $OutputDir 'release.json') -Raw | ConvertFrom-Json
    foreach ($relative in $release.artifacts) {
        Assert-RemoteValue $relative 'artifact relative path'
        if ($relative.StartsWith('/') -or $relative.StartsWith('.')) { throw 'Invalid generated artifact path.' }
        $file=Get-Item -LiteralPath (Join-Path $OutputDir $relative)
        if ($file.Attributes -band [System.IO.FileAttributes]::ReparsePoint) { throw 'Generated artifacts cannot be symlinks.' }
        $destination="$AppDir/$relative"
        $parent=$destination.Substring(0,$destination.LastIndexOf('/'))
        Invoke-Remote "set -eu; umask 077; mkdir -p '$parent'"
        Copy-Remote $file.FullName $destination
    }
}
Copy-Remote (Join-Path $PSScriptRoot 'deploy/release.sh') "$AppDir/scripts/release.sh"
Copy-Remote (Join-Path $PSScriptRoot 'deploy/reconcile-env.sh') "$AppDir/scripts/reconcile-env.sh"
Copy-Remote (Join-Path $PSScriptRoot 'deploy/check-inventory.sh') "$AppDir/scripts/check-inventory.sh"
if ($Up) {
    Copy-Remote $inventory.FullName "$AppDir/cutover-inventory.txt"
    Invoke-Remote "set -eu; chmod 600 '$AppDir/cutover-inventory.txt'"
}
$loadFlag=if($LoadImages){'1'}else{'0'}; $upFlag=if($Up){'1'}else{'0'}; $validateFlag=if($Validate){'1'}else{'0'}
Invoke-Remote "set -eu; bash '$AppDir/scripts/release.sh' '$AppDir' '$ImageDir' '$Tag' '$loadFlag' '$upFlag' '$validateFlag' '$($config.mode)'"
if ($Up) { Write-Host 'HRMS rollout requested. Root Caddy reload and cross-company acceptance remain explicit release steps.' }
