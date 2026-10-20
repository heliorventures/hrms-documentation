<#
.SYNOPSIS
Upload the independent HRMS backup runner and optionally its own Compose manifest.
.DESCRIPTION
Prepares only /opt/apps/hrms/backup-runner, backups, images and env directories.
Configure env/backup.env locally on the VPS; no secrets or root platform Compose
are copied. PostgreSQL already exists on the configured external application network.
.EXAMPLE
.\scripts\install-backup-runner.ps1 -VpsHost example.invalid -VpsUser deploy -SyncCompose
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][string]$VpsHost,
    [string]$VpsUser='deploy',
    [int]$SshPort=22,
    [string]$SshIdentityFile,
    [string]$AppDir='/opt/apps/hrms',
    [switch]$SyncCompose
)
$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot 'deploy/Remote.ps1')
Assert-RemoteValue $AppDir 'AppDir'
if (-not $AppDir.StartsWith('/') -or $AppDir -in @('/','/opt','/opt/apps') -or $AppDir.EndsWith('/')) { throw 'AppDir must be a dedicated absolute HRMS application directory.' }
if ($SshIdentityFile -and -not (Test-Path -LiteralPath $SshIdentityFile -PathType Leaf)) { throw 'SSH identity file does not exist.' }
$ProjectDocumentationDir=Split-Path -Parent $PSScriptRoot
$BackupRunnerDir=Join-Path $ProjectDocumentationDir 'deploy/hrms/backup-runner'
$ComposeTemplate=Join-Path $ProjectDocumentationDir 'deploy/hrms/backup.compose.yaml'
$RunnerFiles=@('Dockerfile','backup-entrypoint.sh','backup-now.sh')
foreach ($name in $RunnerFiles) {
    if (-not (Test-Path -LiteralPath (Join-Path $BackupRunnerDir $name) -PathType Leaf)) { throw "Missing backup runner file: $name" }
}
if ($SyncCompose -and -not (Test-Path -LiteralPath $ComposeTemplate -PathType Leaf)) { throw 'Missing independent backup Compose template.' }
foreach ($command in @('ssh','scp')) {
    if (-not (Get-Command $command -ErrorAction SilentlyContinue)) { throw "$command is required but was not found on PATH" }
}
Initialize-Remote $VpsHost $VpsUser $SshPort $SshIdentityFile
Invoke-Remote "set -eu; umask 077; mkdir -p '$AppDir/backup-runner' '$AppDir/backups' '$AppDir/images' '$AppDir/env'"
foreach ($name in $RunnerFiles) { Copy-Remote (Join-Path $BackupRunnerDir $name) "$AppDir/backup-runner/$name" }
if ($SyncCompose) { Copy-Remote $ComposeTemplate "$AppDir/backup.compose.yaml" }
Write-Host 'HRMS backup files uploaded; no containers or backup schedules were started.'
Write-Host "Configure $AppDir/env/backup.env with the existing BACKUP_* and POSTGRES_* variable names."
Write-Host 'Verify existing schedules and backup/restore coverage before explicitly enabling this independent runner.'
Write-Host "Build: docker compose -f '$AppDir/backup.compose.yaml' --profile backup build backup-runner"
Write-Host "Start: docker compose -f '$AppDir/backup.compose.yaml' --profile backup up -d backup-runner"
Write-Host "Logs: docker compose -f '$AppDir/backup.compose.yaml' --profile backup logs -f backup-runner"
