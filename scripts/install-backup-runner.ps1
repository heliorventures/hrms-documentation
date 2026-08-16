<#
.SYNOPSIS
    Upload the backup runner files to the VPS and optionally sync docker-compose.yml.

.DESCRIPTION
    This script prepares /opt/apps/backup-runner on the VPS. It does not write
    secrets into /opt/apps/.env. Configure BACKUP_* values manually on the VPS
    before starting the backup profile.

.EXAMPLE
    .\scripts\install-backup-runner.ps1 -VpsHost 159.198.70.19 -VpsUser deploy -SyncCompose
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$VpsHost,

    [string]$VpsUser = 'deploy',

    [int]$SshPort = 22,

    [string]$SshIdentityFile,

    [string]$AppDir = '/opt/apps',

    [switch]$SyncCompose
)

$ErrorActionPreference = 'Stop'

$ProjectDocumentationDir = Split-Path -Parent $PSScriptRoot
$BackupRunnerDir = Join-Path $ProjectDocumentationDir 'deploy/backup-runner'
$ComposeTemplate = Join-Path $ProjectDocumentationDir 'deploy/docker-compose.prod.yml'

if (-not (Test-Path $BackupRunnerDir)) {
    throw "Missing backup runner directory: $BackupRunnerDir"
}
if ($SyncCompose -and -not (Test-Path $ComposeTemplate)) {
    throw "Missing compose template: $ComposeTemplate"
}

foreach ($command in @('ssh', 'scp')) {
    if (-not (Get-Command $command -ErrorAction SilentlyContinue)) {
        throw "$command is required but was not found on PATH"
    }
}

$Remote = "${VpsUser}@${VpsHost}"
$SshArgs = @('-p', $SshPort)
$ScpArgs = @('-P', $SshPort)

if (-not [string]::IsNullOrWhiteSpace($SshIdentityFile)) {
    if (-not (Test-Path $SshIdentityFile)) {
        throw "SSH identity file does not exist: $SshIdentityFile"
    }
    $SshArgs += @('-i', $SshIdentityFile)
    $ScpArgs += @('-i', $SshIdentityFile)
}

function Run-Command {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Description,

        [Parameter(Mandatory = $true)]
        [scriptblock]$Action
    )

    Write-Host "==> $Description" -ForegroundColor Cyan
    & $Action
    if ($LASTEXITCODE -ne 0) {
        throw "$Description failed with exit code $LASTEXITCODE"
    }
}

if ($AppDir.Contains("'")) {
    throw 'AppDir cannot contain a single quote'
}

$RemoteBackupDir = "$AppDir/backup-runner"

Run-Command "Creating remote backup runner directory on $Remote" {
    ssh @SshArgs $Remote "mkdir -p '$RemoteBackupDir' '$AppDir/backups'"
}

Run-Command "Uploading backup runner files to ${Remote}:$RemoteBackupDir" {
    scp @ScpArgs (Join-Path $BackupRunnerDir 'Dockerfile') "${Remote}:$RemoteBackupDir/"
    scp @ScpArgs (Join-Path $BackupRunnerDir 'backup-entrypoint.sh') "${Remote}:$RemoteBackupDir/"
    scp @ScpArgs (Join-Path $BackupRunnerDir 'backup-now.sh') "${Remote}:$RemoteBackupDir/"
}

if ($SyncCompose) {
    Run-Command "Uploading docker-compose.yml to ${Remote}:$AppDir" {
        scp @ScpArgs $ComposeTemplate "${Remote}:$AppDir/docker-compose.yml"
    }
}

Write-Host ""
Write-Host "Backup runner files uploaded." -ForegroundColor Green
Write-Host "Next steps on VPS:" -ForegroundColor Yellow
Write-Host "  1. Edit $AppDir/.env and set BACKUP_* values."
Write-Host "  2. Build: docker compose --profile backup build backup-runner"
Write-Host "  3. Start: docker compose --profile backup up -d backup-runner"
Write-Host "  4. Check logs: docker logs -f backup-runner"
