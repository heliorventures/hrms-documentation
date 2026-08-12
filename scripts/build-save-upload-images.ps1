<#
.SYNOPSIS
    Build KabiPay Docker images locally, save them as tar archives, and upload them to a VPS.

.DESCRIPTION
    This script builds Docker images on the local machine only.
    It does not upload source code to the VPS.
    It saves images as .tar archives and uploads them using SCP.
    Source directories are auto-detected from the workspace root. The current
    HRMS repository names (hrms-svc, hrms-gateway, hrms-ui) and the older
    KabiPay repository names (kabipay-svc, kabipay-gateway, kabipay-ui) are
    both supported. Use -SvcDir, -GatewayDir, or -UiDir when a custom checkout
    layout is required.

.EXAMPLE
    .\scripts\build-save-upload-images.ps1 -Tag helior-001 -VpsHost 159.198.70.19 -VpsUser deploy

.EXAMPLE
    .\scripts\build-save-upload-images.ps1 -Tag helior-001 -VpsHost 159.198.70.19 -VpsUser deploy -PublicBaseUrl https://heliorsoft.com -ApiBaseUrl https://api.heliorsoft.com -TenantId e6d4fc13-feb8-52a0-93bd-f66c795969b1 -DeployAfterUpload

.EXAMPLE
    .\scripts\build-save-upload-images.ps1 -Tag helior-001 -VpsHost 159.198.70.19 -VpsUser deploy -SshPort 22 -RemoteDir /opt/apps/images

.EXAMPLE
    .\scripts\build-save-upload-images.ps1 -Tag helior-001 -SkipUpload
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidatePattern('^[a-zA-Z0-9_.-]+$')]
    [string]$Tag,

    [string]$VpsHost,

    [string]$VpsUser = 'deploy',

    [int]$SshPort = 22,

    [string]$SshIdentityFile,

    [string]$RemoteDir = '/opt/apps/images',

    [string]$OutputDir = 'dist-images',

    [string]$SourceRoot,

    [string]$SvcDir,

    [string]$GatewayDir,

    [string]$UiDir,

    [string]$PublicBaseUrl,

    [string]$ApiBaseUrl,

    [string]$TenantId,

    [string]$CaddySiteAddress,

    [switch]$DeployAfterUpload,

    [switch]$WithWorker,

    [switch]$SkipDeploymentValidation,

    [switch]$SkipUpload
)

$ErrorActionPreference = 'Stop'

$ProjectDocumentationDir = Split-Path -Parent $PSScriptRoot
$Root = Split-Path -Parent $ProjectDocumentationDir

$OutDir = Join-Path $Root $OutputDir

$SvcImage = "kabipay-svc:$Tag"
$GatewayImage = "kabipay-gateway:$Tag"
$UiImage = "kabipay-ui:$Tag"

$SvcTarName = "kabipay-svc-$Tag.tar"
$GatewayTarName = "kabipay-gateway-$Tag.tar"
$UiTarName = "kabipay-ui-$Tag.tar"

$SvcTar = Join-Path $OutDir $SvcTarName
$GatewayTar = Join-Path $OutDir $GatewayTarName
$UiTar = Join-Path $OutDir $UiTarName
$DeployScript = Join-Path $PSScriptRoot 'deploy-on-vps.ps1'

function Require-Command {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Name
    )

    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        throw "$Name is required but was not found on PATH"
    }
}

function Resolve-FullPath {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path
    )

    if ([System.IO.Path]::IsPathRooted($Path)) {
        return [System.IO.Path]::GetFullPath($Path)
    }

    return [System.IO.Path]::GetFullPath((Join-Path (Get-Location).Path $Path))
}

function Resolve-SourceDirectory {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Role,

        [AllowEmptyString()]
        [string]$ProvidedPath,

        [Parameter(Mandatory = $true)]
        [string]$SourceRootPath,

        [Parameter(Mandatory = $true)]
        [string[]]$Candidates,

        [Parameter(Mandatory = $true)]
        [string]$OverrideParameterName
    )

    $CheckedPaths = @()

    if (-not [string]::IsNullOrWhiteSpace($ProvidedPath)) {
        $ResolvedPath = Resolve-FullPath $ProvidedPath
        $CheckedPaths += $ResolvedPath

        if (Test-Path (Join-Path $ResolvedPath 'Dockerfile')) {
            return $ResolvedPath
        }

        throw "$Role source directory does not contain a Dockerfile: $ResolvedPath"
    }

    foreach ($Candidate in $Candidates) {
        $CandidatePath = Join-Path $SourceRootPath $Candidate
        $CheckedPaths += $CandidatePath

        if (Test-Path (Join-Path $CandidatePath 'Dockerfile')) {
            return $CandidatePath
        }
    }

    throw "$Role source directory was not found. Checked: $($CheckedPaths -join ', '). Use $OverrideParameterName to provide the directory explicitly."
}

function Run-Command {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Description,

        [Parameter(Mandatory = $true)]
        [scriptblock]$Command
    )

    Write-Host "==> $Description" -ForegroundColor Cyan

    & $Command

    if ($LASTEXITCODE -ne 0) {
        throw "$Description failed with exit code $LASTEXITCODE"
    }
}

Require-Command docker

if (-not $SkipUpload) {
    Require-Command ssh
    Require-Command scp

    if ([string]::IsNullOrWhiteSpace($VpsHost)) {
        throw "VpsHost is required unless -SkipUpload is set"
    }

    if ([string]::IsNullOrWhiteSpace($VpsUser)) {
        throw "VpsUser is required unless -SkipUpload is set"
    }
}

if ($SkipUpload -and $DeployAfterUpload) {
    throw "DeployAfterUpload cannot be used with SkipUpload"
}

if ($DeployAfterUpload) {
    if ([string]::IsNullOrWhiteSpace($PublicBaseUrl)) {
        throw "PublicBaseUrl is required when DeployAfterUpload is set"
    }

    if ([string]::IsNullOrWhiteSpace($TenantId)) {
        throw "TenantId is required when DeployAfterUpload is set"
    }

    if (-not (Test-Path $DeployScript)) {
        throw "Missing deploy script: $DeployScript"
    }
}

$SshArgs = @('-p', $SshPort)
$ScpArgs = @('-P', $SshPort)

if (-not [string]::IsNullOrWhiteSpace($SshIdentityFile)) {
    if (-not (Test-Path $SshIdentityFile)) {
        throw "SSH identity file does not exist: $SshIdentityFile"
    }

    $SshArgs += @('-i', $SshIdentityFile)
    $ScpArgs += @('-i', $SshIdentityFile)
}

if ([string]::IsNullOrWhiteSpace($SourceRoot)) {
    $ResolvedSourceRoot = Resolve-FullPath $Root
} else {
    $ResolvedSourceRoot = Resolve-FullPath $SourceRoot
}

if (-not (Test-Path $ResolvedSourceRoot)) {
    throw "SourceRoot does not exist: $ResolvedSourceRoot"
}

$SvcDir = Resolve-SourceDirectory `
    -Role 'Service' `
    -ProvidedPath $SvcDir `
    -SourceRootPath $ResolvedSourceRoot `
    -Candidates @('hrms-svc', 'kabipay-svc') `
    -OverrideParameterName '-SvcDir'

$GatewayDir = Resolve-SourceDirectory `
    -Role 'Gateway' `
    -ProvidedPath $GatewayDir `
    -SourceRootPath $ResolvedSourceRoot `
    -Candidates @('hrms-gateway', 'kabipay-gateway') `
    -OverrideParameterName '-GatewayDir'

$UiDir = Resolve-SourceDirectory `
    -Role 'UI' `
    -ProvidedPath $UiDir `
    -SourceRootPath $ResolvedSourceRoot `
    -Candidates @('hrms-ui', 'kabipay-ui') `
    -OverrideParameterName '-UiDir'

if ($RemoteDir.Contains("'")) {
    throw "RemoteDir cannot contain a single quote"
}

Write-Host "==> Source directories" -ForegroundColor Cyan
Write-Host "  Service: $SvcDir"
Write-Host "  Gateway: $GatewayDir"
Write-Host "  UI:      $UiDir"

New-Item -ItemType Directory -Path $OutDir -Force | Out-Null

Run-Command "Building $SvcImage" {
    docker build -t $SvcImage $SvcDir
}

Run-Command "Building $GatewayImage" {
    docker build -t $GatewayImage $GatewayDir
}

Run-Command "Building $UiImage" {
    docker build -t $UiImage $UiDir
}

Run-Command "Saving $SvcImage to $SvcTar" {
    docker save $SvcImage -o $SvcTar
}

Run-Command "Saving $GatewayImage to $GatewayTar" {
    docker save $GatewayImage -o $GatewayTar
}

Run-Command "Saving $UiImage to $UiTar" {
    docker save $UiImage -o $UiTar
}

if ($SkipUpload) {
    Write-Host ""
    Write-Host "Upload skipped. Image archives are ready:" -ForegroundColor Green
    Write-Host "  $SvcTar"
    Write-Host "  $GatewayTar"
    Write-Host "  $UiTar"
    exit 0
}

$Remote = "${VpsUser}@${VpsHost}"
$DeploymentStamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$RemoteArchiveDir = "$RemoteDir/archive/$DeploymentStamp"
$RemotePrepareCommand = "set -eu; mkdir -p '$RemoteDir' '$RemoteDir/archive'; if ls '$RemoteDir'/kabipay-*.tar >/dev/null 2>&1; then mkdir -p '$RemoteArchiveDir'; mv '$RemoteDir'/kabipay-*.tar '$RemoteArchiveDir'/; fi"

Run-Command "Preparing remote image directory and archive on $Remote" {
    ssh @SshArgs $Remote $RemotePrepareCommand
}

Run-Command "Uploading image archives to ${Remote}:$RemoteDir" {
    scp @ScpArgs $SvcTar $GatewayTar $UiTar "${Remote}:$RemoteDir/"
}

if ($DeployAfterUpload) {
    $DeployArgs = @(
        '-Tag', $Tag,
        '-VpsHost', $VpsHost,
        '-VpsUser', $VpsUser,
        '-SshPort', $SshPort,
        '-PublicBaseUrl', $PublicBaseUrl,
        '-TenantId', $TenantId,
        '-Deploy'
    )

    if (-not [string]::IsNullOrWhiteSpace($ApiBaseUrl)) {
        $DeployArgs += @('-ApiBaseUrl', $ApiBaseUrl)
    }

    if (-not [string]::IsNullOrWhiteSpace($SshIdentityFile)) {
        $DeployArgs += @('-SshIdentityFile', $SshIdentityFile)
    }

    if (-not [string]::IsNullOrWhiteSpace($CaddySiteAddress)) {
        $DeployArgs += @('-CaddySiteAddress', $CaddySiteAddress)
    }

    if ($WithWorker) {
        $DeployArgs += '-WithWorker'
    }

    if ($SkipDeploymentValidation) {
        $DeployArgs += '-SkipValidation'
    }

    Run-Command "Deploying uploaded images on $Remote" {
        & $DeployScript @DeployArgs
    }

    exit 0
}

Write-Host ""
Write-Host "Done. Image archives uploaded successfully." -ForegroundColor Green
Write-Host ""
Write-Host "Next deployment command:" -ForegroundColor Yellow
Write-Host "  .\scripts\deploy-on-vps.ps1 -Tag $Tag -VpsHost $VpsHost -VpsUser $VpsUser -PublicBaseUrl https://heliorsoft.com -ApiBaseUrl https://api.heliorsoft.com -TenantId <tenant-id> -Deploy"
