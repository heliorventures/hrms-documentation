# Company database and application deployment commands

These commands use the existing deployment entry points. Application release and database operations remain separate. Do not run the examples unchanged: paths, tenant IDs, hosts, roles and configuration must match the reviewed environment. No command below automatically stops writers, switches the registry, changes PostgreSQL server settings or installs Kafka/ClickHouse.

## PostgreSQL private network persistence

Company CDC uses a separate private source network per company. The shared
PostgreSQL container must retain its existing application networks and its
reviewed metadata, shared-source and company CDC networks. Attaching those
networks does not require a PostgreSQL restart.

When recreating PostgreSQL later, include the operator-generated
`config/postgres-networks.override.json` alongside the platform Compose file.
Review the merged configuration privately before recreation; it can contain
credentials. Confirm that the existing PostgreSQL storage, command, environment
and original networks are preserved, with the expected source addresses and
`postgres` aliases. Do not recreate PostgreSQL from the platform file alone after
this network setup. Application image deployment remains a separate operation
and must not recreate the shared database container.

## 1. Build once, or reuse the saved release

Run from the workspace root in PowerShell. A new release can be built and saved with:

```powershell
& .\hrms-documentation\scripts\build-save-upload-images.ps1 `
  -Tag YOUR_NEW_RELEASE_TAG -OutputDir D:\protected\release-images -SkipUpload
```

For the already built `helior-org-20261109-002`, **do not rebuild**. Upload its archives using:

```powershell
& .\hrms-documentation\scripts\build-save-upload-images.ps1 `
  -Tag helior-org-20261109-002 `
  -SkipBuild `
  -OutputDir D:\work\heliorventures\.codex-tmp\hrms-release-20261109-002\archives `
  -VpsHost YOUR_SSH_HOST -VpsUser root `
  -RemoteDir /opt/apps/hrms/images/helior-org-20261109-002
```

`-SkipBuild` requires the original four archives and `SHA256SUMS`. It verifies the archives without regenerating their hashes. Upload verifies checksums again on the VPS. It never uploads `.env` or service credentials. Use a fresh release tag for changed images. The VPS requires Docker Compose, Bash, `sha256sum`, `awk`, and **Python 3.9 or later** for archive identity checks. Verify `python3 --version` before the maintenance window.

## 2. Render the actual production manifest

The example manifest contains fictional tenants. Prepare the actual manifest with every ACTIVE/SUSPENDED tenant, domain, existing client key ID, private-file path and connection budget. Provision the required files according to [the environment contract](../../deploy/hrms/environment.md).

Set `privateHistoryCompanyIds` explicitly to the company UUIDs whose private
source consumers are ready. Keep all companies in `companies`, including those
whose private consumers are not active yet. Review the resulting
`release.activeServices`, `startup-services.txt` and `compose-active.json`;
startup and readiness use that exact selection. Worker activation does not
grant organization membership or replace source/CDC permission preparation.
Never substitute an unscoped `docker compose up` command. Re-rendering these
artifacts invalidates the inventory receipt and requires a fresh preflight.

For password-based SSH use `-InteractiveSsh` on the upload/deployment commands
and run them in your normal PowerShell window. The native SSH/sudo prompts
collect passwords privately; never put passwords in command arguments.

```powershell
$Manifest = 'D:\protected\hrms-production-manifest.json'
$Rendered = 'D:\protected\hrms-rendered-20261109-002'

& .\hrms-documentation\scripts\deploy-on-vps.ps1 `
  -Tag helior-org-20261109-002 -Manifest $Manifest `
  -OutputDir $Rendered -RenderOnly
```

To stage generated configuration and load images without starting services:

```powershell
& .\hrms-documentation\scripts\deploy-on-vps.ps1 `
  -Tag helior-org-20261109-002 -Manifest $Manifest -OutputDir $Rendered `
  -VpsHost YOUR_SSH_HOST -VpsUser root `
  -ImageDir /opt/apps/hrms/images/helior-org-20261109-002 `
  -SyncCompose -LoadImages
```

Image loading checks all four archive tags/config digests/platforms before loading any and compares the resulting image IDs. Existing images with the requested tag cannot conceal the wrong archive. The old worker may remain running during image-only preparation; startup still requires its reviewed handoff. Staging configuration changes files under `/opt/apps/hrms`; do not stage over an active reviewed release without preserving its artifacts.

## 3. Deploy central migrations

The database tools load operator credentials internally from `hrms-database/.env`. Do not paste its contents into a terminal or chat. The file's database must remain the central database. Use `verify-full` plus `POSTGRES_SSLROOTCERT` where needed. For an authenticated, already-open loopback SSH tunnel, `POSTGRES_SSLMODE=disable` is accepted explicitly; plaintext to non-loopback hosts is rejected. This operator tunnel exception does not weaken application TLS requirements.

```powershell
Set-Location D:\work\heliorventures\hrms-database
node migrate-ops.cjs --expected-database helior --command validate
if ($LASTEXITCODE -ne 0) { throw 'Ops validation failed' }
node migrate-ops.cjs --expected-database helior --command update
if ($LASTEXITCODE -ne 0) { throw 'Ops migration failed' }
```

This deploys the ops master only, using the existing metadata registry and public Liquibase history. It refuses `company_*` targets and an unexpected central database. It is not an initial empty metadata-database provisioner.

## 4. One-time transfer of an existing tenant

Follow [the database split runbook](company-database-split.md) for the maintenance freeze, final backup, history/delivery handoff and rollback boundary. Stop **all** source-database application connections, including idle pools, scheduled jobs, imports and old workers. Preserve and restore-test the final backup before source migrations.

First apply the pending tenant migrations while the schema is still colocated with `kabipay_ops`. The existing schema-mode command remains available for that stage:

```powershell
& .\scripts\reusable\migrations\update-tenant-liquibase.ps1 `
  -Schema tenant_REPLACE_WITH_VERIFIED_SCHEMA -DbName helior
```

Ops 0128 must precede tenant 0129. Do not edit Liquibase history or mark changesets applied. Fresh standalone company databases cannot run these old cross-schema migrations directly.

Prepare a protected copy of [transfer-plan.example.json](../../../hrms-database/provisioning/company-databases/transfer-plan.example.json). Replace **all** examples with reviewed values. The file contains identifiers and grants, no passwords. Specify:

- Actual `systemIdentifier` from `SELECT system_identifier::text FROM pg_control_system()` on the intended PostgreSQL server.
- Exact source tenant UUID/schema/runtime host and destination database/owner.
- Required tenant extensions with their actual version/schema. Catalog-recorded tenant dependencies must be included; central-only extensions are not copied. Unsupported extension locations stop transfer.
- All approved company database names for the stable service logins.
- Pre-existing restricted LOGIN roles and explicit business table/column/sequence permissions. This list is an upper bound on effective access; surplus grants cause failure. The example reader is **not** a full production service permission policy.
- Optional `preservedFunctions` per role: existing executable routines approved by exact `name`, `identityArguments` and `definitionSha256`. Use `pg_get_function_identity_arguments(oid)` and `encode(sha256(convert_to(pg_get_functiondef(oid),'UTF8')),'hex')` from the source catalog. Review each routine body and its authorization before listing it. This acknowledges preserved access; the transfer never grants routine execution. Private operator routines and grant options are refused. An omitted, changed or unavailable routine stops the copy.

The destination must already exist, be empty and closed (`ALLOW_CONNECTIONS=false`), have a restricted NOLOGIN owner, no owner memberships and no unapproved database grants. The script does not create roles/passwords or revoke access on other products' databases. Correct those prerequisites through separately reviewed provisioning.

Preview, from `hrms-database`:

```powershell
node provisioning/company-databases/transfer-tenant-temporary.cjs `
  --plan D:\protected\company-transfer.json `
  --pg-bin 'C:\Program Files\PostgreSQL\16\bin' `
  --output D:\protected\company-transfer-preview-001
```

Planning reads source prerequisites and closed-destination metadata. It does **not** open the destination or certify its contents. Use installed matching PostgreSQL tools; the above bin path is an example.

After reviewing the plan, freezing writers and verifying the backup:

```powershell
node provisioning/company-databases/transfer-tenant-temporary.cjs `
  --plan D:\protected\company-transfer.json `
  --pg-bin 'C:\Program Files\PostgreSQL\16\bin' `
  --output D:\protected\company-transfer-copy-001 `
  --execute --writers-stopped
```

Each output directory must be new and have a protected existing parent. Windows operators must protect it with NTFS ACLs; POSIX mode bits alone do not configure Windows access. It contains a tenant dump, schema/ACL definitions, fingerprints, grants and a receipt. Retain it as sensitive backup evidence.

The script checks cluster/registry/locale/history/roles; rejects active clients, external FK/trigger dependencies, foreign tenant rows, unreviewed global default ACLs, large objects and unsupported relations; locks tables; exports a consistent snapshot; restores with original ownership and ACLs in one transaction; compares data, sequences and schema/ACL definitions; applies only reviewed grants; then closes the destination and checks for remaining sessions. It never drops a database/schema, resets source authority, switches mappings or terminates clients. Dynamic SQL dependencies still require the prior application/dependency review.

Schema comparison accepts only the two known equivalent PostgreSQL cast spellings for `management_assignment` status/relationship checks. Changed values, operators, ownership and grants still fail reconciliation.

**Success is `copied_verified_closed`, not live deployment.** Repeat per company. Then perform the guarded fleet mapping transaction and the canonical private-source/CDC/history provisioning in the reviewed cutover order. Protected authority/outbox grants are intentionally handled by [private-events provisioning](../../../hrms-database/provisioning/private-events/README.md), not generic table grants.

Failure leaves evidence and attempts to close the destination. A restored or extension-populated destination is not automatically cleared/reused; investigate the receipt and reconcile it. `destinationClosed=false` requires operator recovery before any further deployment. ALLOW_CONNECTIONS does not terminate existing sessions. Never reopen traffic solely because copy succeeded.

## 5. Future company-specific migration deployments

After the company registry points to its separate database and the 0129 baseline has been transferred:

```powershell
& .\scripts\reusable\migrations\update-tenant-liquibase.ps1 `
  -TenantId 'REPLACE_WITH_COMPANY_UUID' `
  -ExpectedMetadataDatabase helior `
  -ExpectedDatabase company_REPLACE_WITH_DATABASE `
  -RuntimeHost postgres `
  -Command update
```

Use `-Command validate` or `status` for the corresponding Liquibase operation. The command reads the authoritative mapping, verifies the expected database/runtime host and isolated schema, and preserves its existing tracking table. Operator transport may use a loopback tunnel; `RuntimeHost` must still match the Docker runtime registry host. No per-company password is added to service files. The operator's existing migration login must have the required rights on the selected database.

## 6. Issue a fresh inventory and deploy applications

After database/permission/worker/configuration prerequisites pass, return to the workspace root. Generate a new receipt using the configured restricted libpq service/passfile:

```powershell
Set-Location D:\work\heliorventures
$Inventory = Join-Path $Rendered ('inventory-' + [guid]::NewGuid().ToString('N') + '.txt')
node .\hrms-database\provisioning\organization\check-rollout.cjs `
  --release-dir $Rendered --service hrms_ops_readonly `
  --database helior --output $Inventory
if ($LASTEXITCODE -ne 0) { throw 'Fleet inventory failed' }

& .\hrms-documentation\scripts\deploy-on-vps.ps1 `
  -Tag helior-org-20261109-002 -Manifest $Manifest -OutputDir $Rendered `
  -VpsHost YOUR_SSH_HOST -VpsUser root `
  -ImageDir /opt/apps/hrms/images/helior-org-20261109-002 `
  -Deploy -InventoryReport $Inventory
```

The receipt expires after 15 minutes. Loading images early avoids consuming the window. If images/configuration have already been staged, use `-Up -Validate` instead of `-Deploy` with the same inputs. Never change the manifest/artifacts/tenant inventory after issuing the receipt.

The combined build/upload/deploy path can issue its receipt **after** build/upload, using the configured read-only libpq service:

```powershell
& .\hrms-documentation\scripts\build-save-upload-images.ps1 `
  -Tag YOUR_NEW_RELEASE_TAG -OutputDir D:\protected\release-images `
  -VpsHost YOUR_SSH_HOST -VpsUser root `
  -RemoteDir /opt/apps/hrms/images/YOUR_NEW_RELEASE_TAG `
  -DeployAfterUpload -Manifest $Manifest -ReleaseOutputDir $Rendered `
  -InventoryService hrms_ops_readonly -InventoryDatabase helior
```

Add `-SkipBuild` when reusing saved archives. Alternatively supply `-InventoryReport $Inventory` instead of the service/database pair, but only when upload fits the existing receipt window. All production database/worker/configuration gates must already be resolved. No bypass is provided for expired inventory.

Finally validate/reload the reviewed Caddy configuration and verify all company workflows, isolation, files, jobs and history/CDC before reopening traffic. Preserve original `helior` tenant schemas and backups during acceptance. No `docker compose down`, `--remove-orphans`, automatic infrastructure restart or destructive rollback is part of these commands.
