<# Shared platform preparation; HRMS application release is deploy-on-vps.ps1. #>
[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][string]$VpsHost,[string]$VpsUser='deploy',
    [int]$SshPort=22,[string]$SshIdentityFile,[string]$PlatformDir='/opt/apps',
    [string]$HrmsDir='/opt/apps/hrms',[switch]$StageCaddy,[switch]$Up,[switch]$ReloadCaddy
)
$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot 'deploy/Remote.ps1')
Assert-RemoteValue $PlatformDir 'PlatformDir'; Assert-RemoteValue $HrmsDir 'HrmsDir'
if (-not $PlatformDir.StartsWith('/') -or -not $HrmsDir.StartsWith("$PlatformDir/")) { throw 'Use explicit platform/HRMS absolute paths.' }
Initialize-Remote $VpsHost $VpsUser $SshPort $SshIdentityFile
$documentation=Split-Path -Parent $PSScriptRoot
Invoke-Remote "set -eu; umask 077; mkdir -p '$PlatformDir' '$HrmsDir/scripts'"
Copy-Remote (Join-Path $documentation 'deploy/platform/compose.yaml') "$PlatformDir/compose.platform.yaml"
Copy-Remote (Join-Path $PSScriptRoot 'deploy/platform.sh') "$HrmsDir/scripts/platform.sh"
if ($StageCaddy) {
    Copy-Remote (Join-Path $documentation 'deploy/Caddyfile.example') "$PlatformDir/Caddyfile.candidate"
    Write-Host 'Review Caddyfile.candidate against current shared routes/certificates. Existing Caddyfile was not overwritten.'
}
$operation=if($Up){'up'}elseif($ReloadCaddy){'reload-caddy'}else{'validate'}
Invoke-Remote "set -eu; bash '$HrmsDir/scripts/platform.sh' '$PlatformDir' '$HrmsDir' '$operation'"
