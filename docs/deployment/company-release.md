# Deploy shared applications and company database migrations

Use PowerShell from the workspace root. Substitute every placeholder. This workflow requires the reviewed production [manifest/environment contract](../../deploy/hrms/environment.md), existing company databases and service credentials. Preserve backups and use the maintenance sequence appropriate to each migration. Initial tenant-data transfer, registry switching and private-source/CDC handoffs are separate cutover operations; they must finish before first shared-runtime startup. Do not start against multiple company mappings still pointing to the same database.

## 1. Select the release

```powershell
Set-Location D:\work\heliorventures
$Tag = 'REPLACE_WITH_RELEASE_TAG'
$Vps = 'REPLACE_WITH_SSH_HOST'
$Manifest = 'D:\protected\hrms-production-manifest.json'
$Rendered = "D:\protected\hrms-rendered-$Tag"
$Archives = "D:\protected\hrms-images-$Tag"
$RemoteImages = "/opt/apps/hrms/images/$Tag"
```

The manifest must include every ACTIVE/SUSPENDED company and the reviewed connection budget. On the VPS, confirm `python3 --version` reports 3.9 or later. Docker Compose, Bash, `sha256sum` and `awk` are also required.

## 2. Build or reuse, then upload

For changed application code, build once:

```powershell
& .\hrms-documentation\scripts\build-save-upload-images.ps1 -Tag $Tag -OutputDir $Archives -SkipUpload
```

For an already built release, set `$Archives` to its existing archive directory and omit the build command. Upload with:

```powershell
& .\hrms-documentation\scripts\build-save-upload-images.ps1 `
  -Tag $Tag -OutputDir $Archives -SkipBuild `
  -VpsHost $Vps -VpsUser root -RemoteDir $RemoteImages
```

Exactly four matching archives plus the original `SHA256SUMS` are required. Upload rechecks hashes on the VPS. Credentials are not uploaded by this command.

For a password or encrypted-key login, add `-InteractiveSsh` to the upload and remote deployment commands and run them from an interactive PowerShell terminal. Native SSH/SCP prompts locally; passwords are never collected or saved by the scripts. Prompts may repeat because each SSH/SCP invocation opens a separate connection. Use `-SshIdentityFile <path>` when your login needs a specific key. Without `-InteractiveSsh`, authentication remains noninteractive for automation. The switch is forwarded automatically by `-DeployAfterUpload`; host-key verification remains unchanged.

## 3. Render and load without starting

```powershell
& .\hrms-documentation\scripts\deploy-on-vps.ps1 `
  -Tag $Tag -Manifest $Manifest -OutputDir $Rendered -RenderOnly

# Review the generated artifacts before staging them on the VPS.
& .\hrms-documentation\scripts\deploy-on-vps.ps1 `
  -Tag $Tag -Manifest $Manifest -OutputDir $Rendered `
  -VpsHost $Vps -VpsUser root -ImageDir $RemoteImages -SyncCompose -LoadImages
```

Loading verifies archive tags, platform and image identities. Staging overwrites release configuration under `/opt/apps/hrms`; preserve any previous release artifacts first. It does not stop/start application containers.

## 4. Apply reviewed database migrations

Database commands read operator credentials internally from `hrms-database/.env`. Its database remains the metadata database. Use verified TLS; an authenticated loopback tunnel may explicitly select `POSTGRES_SSLMODE=disable`. Do not display the file or put passwords in command arguments.

```powershell
Push-Location .\hrms-database
try {
  node migrate-ops.cjs --expected-database REPLACE_METADATA_DB --command validate
  if ($LASTEXITCODE -ne 0) { throw 'Ops validation failed' }
  node migrate-ops.cjs --expected-database REPLACE_METADATA_DB --command update
  if ($LASTEXITCODE -ne 0) { throw 'Ops migration failed' }

  # Repeat for each reviewed company after its registry mapping is cut over.
  & .\scripts\reusable\migrations\update-tenant-liquibase.ps1 `
    -TenantId 'REPLACE_COMPANY_UUID' -ExpectedMetadataDatabase REPLACE_METADATA_DB `
    -ExpectedDatabase company_REPLACE_NAME -RuntimeHost REPLACE_REGISTRY_HOST -Command update
} finally { Pop-Location }
```

The company command verifies the exact active registry mapping and existing 0129 baseline; it does not bootstrap an empty company database. Historical dependencies must be migrated while colocated before transferring existing data. For source preparation only, the existing `-Schema <verified-schema> -DbName <source-db>` parameter set remains available. Ops 0128 precedes tenant 0129. Do not edit applied history or mark migrations applied manually.

## 5. Issue fresh inventory and start

Only after database, role, TLS, capacity and worker-handoff requirements pass, issue a release-bound receipt using the configured restricted libpq service/passfile:

```powershell
$Inventory = Join-Path $Rendered ('inventory-' + [guid]::NewGuid().ToString('N') + '.txt')
node .\hrms-database\provisioning\organization\check-rollout.cjs `
  --release-dir $Rendered --service REPLACE_READONLY_LIBPQ_SERVICE `
  --database REPLACE_METADATA_DB --output $Inventory
if ($LASTEXITCODE -ne 0) { throw 'Fleet inventory failed' }

& .\hrms-documentation\scripts\deploy-on-vps.ps1 `
  -Tag $Tag -Manifest $Manifest -OutputDir $Rendered `
  -VpsHost $Vps -VpsUser root -ImageDir $RemoteImages `
  -Up -Validate -InventoryReport $Inventory
```

The receipt expires after 15 minutes. Freeze registry changes and do not change the rendered release after issuance. `-Deploy` combines configuration sync, loading, startup and validation when needed. The build/upload entry point can similarly use `-DeployAfterUpload -Manifest $Manifest -ReleaseOutputDir $Rendered -InventoryService <service> -InventoryDatabase <metadata-db>` to issue inventory after uploading.

Finally validate/reload the reviewed Caddy configuration and accept company login, isolation, writes, jobs, files and event/history flows before reopening traffic. Normal release commands do not restart shared infrastructure, migrate business data, delete source schemas or automatically roll back accepted writes.
