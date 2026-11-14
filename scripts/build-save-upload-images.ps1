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
    layout is required. Organization event workers are built from the service
    checkout's integrations/organization-events folder; use -EventsDir to override.
    Shared platform, Caddy and database configuration use separate operator steps.
    Use -InteractiveSsh from a terminal to allow native SSH/SCP password or key
    passphrase prompts. The default is noninteractive for automation.

.EXAMPLE
    .\scripts\build-save-upload-images.ps1 -Tag helior-001 -VpsHost 159.198.70.19 -VpsUser deploy

.EXAMPLE
    .\scripts\build-save-upload-images.ps1 -Tag helior-001 -VpsHost 159.198.70.19 -VpsUser deploy -Manifest .\deploy\hrms\manifest.json -DeployAfterUpload

.EXAMPLE
    .\scripts\build-save-upload-images.ps1 -Tag helior-001 -VpsHost 159.198.70.19 -VpsUser deploy -SshPort 22 -RemoteDir /opt/apps/hrms/images

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

    [switch]$InteractiveSsh,

    [string]$RemoteDir = '/opt/apps/hrms/images',

    [string]$AppDir = '/opt/apps/hrms',

    [string]$Manifest,

    [string]$InventoryReport,

    [string]$InventoryService,

    [string]$InventoryDatabase,

    [string]$ReleaseOutputDir,

    # Reuse reviewed archives and SHA256SUMS from OutputDir; no local build.
    [switch]$SkipBuild,

    [string]$OutputDir = 'dist-images',

    [string]$SourceRoot,

    [string]$SvcDir,

    [string]$GatewayDir,

    [string]$UiDir,

    [string]$EventsDir,

    # Compile the existing organization workspace into the browser bundle.
    [switch]$EnableOrganizationWorkspace,

    [string]$PublicBaseUrl,

    [string]$ApiBaseUrl,

    [string]$CaddySiteAddress,

    [switch]$DeployAfterUpload,

    [switch]$SkipDeploymentValidation,

    [switch]$SkipUpload
)

$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'deploy/Remote.ps1')
. (Join-Path $PSScriptRoot 'deploy/DependencySecurity.ps1')
if ($CaddySiteAddress) { throw 'CaddySiteAddress is deprecated: shared Caddy configuration uses the separate reviewed platform procedure, not HRMS image upload/deployment.' }
Assert-RemoteValue $RemoteDir 'RemoteDir'
Assert-RemoteValue $AppDir 'AppDir'
if (-not $RemoteDir.StartsWith('/') -or $RemoteDir -eq '/') { throw 'RemoteDir must be an absolute HRMS image directory.' }
if ($DeployAfterUpload -and -not $RemoteDir.StartsWith("$AppDir/")) { throw 'RemoteDir must be within AppDir for an HRMS application release.' }
if ($Manifest -and -not (Test-Path -LiteralPath $Manifest -PathType Leaf)) { throw 'Manifest file does not exist.' }
$UiOrganizationEnabled = $EnableOrganizationWorkspace.IsPresent
if ($Manifest) {
    $BuildManifest = Get-Content -LiteralPath $Manifest -Raw | ConvertFrom-Json
    if ($BuildManifest.mode -eq 'organization') {
        if ($PSBoundParameters.ContainsKey('EnableOrganizationWorkspace') -and -not $EnableOrganizationWorkspace) {
            throw 'An organization manifest requires the organization workspace in its UI image.'
        }
        $UiOrganizationEnabled = $true
    }
}

$ProjectDocumentationDir = Split-Path -Parent $PSScriptRoot
$Root = Split-Path -Parent $ProjectDocumentationDir

$OutDir = if ([System.IO.Path]::IsPathRooted($OutputDir)) { $OutputDir } else { Join-Path $Root $OutputDir }

$SvcImage = "kabipay-svc:$Tag"
$GatewayImage = "kabipay-gateway:$Tag"
$UiImage = "kabipay-ui:$Tag"
$EventsImage = "kabipay-organization-events:$Tag"

$SvcTarName = "kabipay-svc-$Tag.tar"
$GatewayTarName = "kabipay-gateway-$Tag.tar"
$UiTarName = "kabipay-ui-$Tag.tar"
$EventsTarName = "kabipay-organization-events-$Tag.tar"

$SvcTar = Join-Path $OutDir $SvcTarName
$GatewayTar = Join-Path $OutDir $GatewayTarName
$UiTar = Join-Path $OutDir $UiTarName
$EventsTar = Join-Path $OutDir $EventsTarName
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

if (-not $SkipBuild) { Require-Command docker }

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
    if (-not $Manifest -or -not $ReleaseOutputDir -or ((-not $InventoryReport) -and (-not $InventoryService -or -not $InventoryDatabase))) {
        throw 'DeployAfterUpload requires Manifest, ReleaseOutputDir and either InventoryReport or InventoryService plus InventoryDatabase to issue a fresh receipt after upload.'
    }
    if ($InventoryReport -and ($InventoryService -or $InventoryDatabase)) { throw 'Choose an existing inventory receipt or fresh inventory service, not both.' }
    if ($InventoryReport -and -not (Test-Path -LiteralPath $InventoryReport -PathType Leaf)) { throw 'Inventory report does not exist.' }
    if ($InventoryService -and ($InventoryService -cnotmatch '^[a-z][a-z0-9_.-]*$' -or $InventoryDatabase -cnotmatch '^[a-z][a-z0-9_]{0,62}$')) { throw 'Invalid read-only inventory service/database.' }

    if (-not (Test-Path $DeployScript)) {
        throw "Missing deploy script: $DeployScript"
    }
}

if (-not $SkipUpload) {
    if ($SshIdentityFile -and -not (Test-Path -LiteralPath $SshIdentityFile -PathType Leaf)) { throw 'SSH identity file does not exist.' }
    Initialize-Remote $VpsHost $VpsUser $SshPort $SshIdentityFile -InteractiveSsh:$InteractiveSsh
}

if (-not $SkipBuild) {
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

$EventsDir = Resolve-SourceDirectory -Role 'Organization events' -ProvidedPath $EventsDir -SourceRootPath $SvcDir -Candidates @('integrations/organization-events') -OverrideParameterName '-EventsDir'

Write-Host "==> Source directories" -ForegroundColor Cyan
Write-Host "  Service: $SvcDir"
Write-Host "  Gateway: $GatewayDir"
Write-Host "  UI:      $UiDir"
Write-Host "  Events:  $EventsDir"

New-Item -ItemType Directory -Path $OutDir -Force | Out-Null

Assert-DependencySecurity -SourceDirectory $GatewayDir -Role 'Gateway'
Assert-DependencySecurity -SourceDirectory $UiDir -Role 'UI'
Assert-DependencySecurity -SourceDirectory $EventsDir -Role 'Organization events'

Run-Command "Building $SvcImage" {
    docker build -t $SvcImage $SvcDir
}

Run-Command "Building $GatewayImage" {
    docker build -t $GatewayImage $GatewayDir
}

Run-Command "Building $UiImage" {
    $organizationFlag = if ($UiOrganizationEnabled) { 'true' } else { 'false' }
    docker build --build-arg "VITE_ORGANIZATION_ENABLED=$organizationFlag" -t $UiImage $UiDir
}

Run-Command "Building $EventsImage" {
    docker build -t $EventsImage $EventsDir
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

Run-Command "Saving $EventsImage to $EventsTar" {
    docker save $EventsImage -o $EventsTar
}

$checksumLines = @($SvcTar,$GatewayTar,$UiTar,$EventsTar) | ForEach-Object {
    (Get-FileHash -LiteralPath $_ -Algorithm SHA256).Hash.ToLowerInvariant() + '  ' + [IO.Path]::GetFileName($_)
}
[IO.File]::WriteAllText((Join-Path $OutDir 'SHA256SUMS'),(($checksumLines -join "`n")+"`n"),[Text.UTF8Encoding]::new($false))
}

# Never regenerate a checksum for reused archives: it would bless corruption.
$checksumPath=Join-Path $OutDir 'SHA256SUMS'
if (-not (Test-Path -LiteralPath $checksumPath -PathType Leaf)) { throw 'Missing SHA256SUMS for reviewed archives.' }
$expected=@{}
foreach($line in [IO.File]::ReadAllLines($checksumPath)) {
    if($line -notmatch '^([a-fA-F0-9]{64})  (kabipay-(?:svc|gateway|ui|organization-events)-[a-zA-Z0-9_.-]+\.tar)$' -or $expected.ContainsKey($Matches[2])) { throw 'Invalid or duplicate archive checksum entry.' }
    $expected[$Matches[2]]=$Matches[1]
}
if($expected.Count -ne 4){throw 'Exactly four release archive checksums required.'}
foreach($file in @($SvcTar,$GatewayTar,$UiTar,$EventsTar)) {
    $name=[IO.Path]::GetFileName($file)
    if(-not $expected.ContainsKey($name) -or -not (Test-Path -LiteralPath $file -PathType Leaf) -or (Get-FileHash -LiteralPath $file -Algorithm SHA256).Hash -ne $expected[$name]) { throw "Archive checksum mismatch: $name" }
}

if ($SkipUpload) {
    Write-Host ""
    Write-Host "Upload skipped. Image archives are ready:" -ForegroundColor Green
    Write-Host "  $SvcTar"
    Write-Host "  $GatewayTar"
    Write-Host "  $UiTar"
    Write-Host "  $EventsTar"
    return
}

$Remote = $script:RemoteTarget
$DeploymentStamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$RemoteArchiveDir = "$RemoteDir/archive/$DeploymentStamp"
$RemotePrepareCommand = @"
set -eu
umask 077
mkdir -p '$RemoteDir'
for image in '$RemoteDir'/kabipay-svc-*.tar '$RemoteDir'/kabipay-gateway-*.tar '$RemoteDir'/kabipay-ui-*.tar '$RemoteDir'/kabipay-organization-events-*.tar; do
    [ -f "`$image" ] || continue
    mkdir -p '$RemoteArchiveDir'
    mv -- "`$image" '$RemoteArchiveDir'/
done
"@

Run-Command "Preparing remote image directory and archive on $Remote" {
    Invoke-Remote $RemotePrepareCommand
}

Run-Command "Uploading image archives to ${Remote}:$RemoteDir" {
    Invoke-Native 'scp' ($script:ScpArguments + @($SvcTar,$GatewayTar,$UiTar,$EventsTar,$checksumPath,"${Remote}:$RemoteDir/"))
}

Invoke-Remote "set -eu; cd '$RemoteDir'; sha256sum --check SHA256SUMS"

if ($DeployAfterUpload) {
    if($InventoryService) {
        # A build/upload can take hours. Issue the fifteen-minute receipt only
        # after upload, against the exact reviewed manifest/tag/output.
        & $DeployScript -Tag $Tag -Manifest $Manifest -OutputDir $ReleaseOutputDir -AppDir $AppDir -ImageDir $RemoteDir -RenderOnly
        $InventoryReport=Join-Path $ReleaseOutputDir ('cutover-inventory-'+[guid]::NewGuid().ToString('N')+'.txt')
        Invoke-Native 'node' @((Join-Path $Root 'hrms-database/provisioning/organization/check-rollout.cjs'),'--release-dir',$ReleaseOutputDir,'--service',$InventoryService,'--database',$InventoryDatabase,'--output',$InventoryReport)
    }
    $DeployArgs = @{
        Tag = $Tag
        VpsHost = $VpsHost
        VpsUser = $VpsUser
        SshPort = $SshPort
        InteractiveSsh = $InteractiveSsh
        PublicBaseUrl = $PublicBaseUrl
        AppDir = $AppDir
        ImageDir = $RemoteDir
        Deploy = $true
        InventoryReport = $InventoryReport
        OutputDir = $ReleaseOutputDir
    }
    if ($Manifest) { $DeployArgs.Manifest = $Manifest }
    if ($ApiBaseUrl) { $DeployArgs.ApiBaseUrl = $ApiBaseUrl }
    if ($SshIdentityFile) { $DeployArgs.SshIdentityFile = $SshIdentityFile }
    if ($SkipDeploymentValidation) { $DeployArgs.SkipValidation = $true }
    Run-Command "Deploying uploaded images on $Remote" {
        & $DeployScript @DeployArgs
    }
    return
}

Write-Host ""
Write-Host "Done. Image archives uploaded successfully." -ForegroundColor Green
Write-Host ""
Write-Host "Next deployment command:" -ForegroundColor Yellow
$interactiveOption=if($InteractiveSsh){' -InteractiveSsh'}else{''}
Write-Host "  .\scripts\deploy-on-vps.ps1 -Tag $Tag -VpsHost $VpsHost -VpsUser $VpsUser -Manifest <reviewed-manifest.json> -OutputDir <reviewed-render-directory> -AppDir $AppDir -ImageDir $RemoteDir -Deploy -InventoryReport <fresh-inventory.txt>$interactiveOption"
