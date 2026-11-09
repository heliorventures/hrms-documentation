# Split existing tenant databases before shared-service rollout

Status: preparation; **not cleared for production cutover**. Production facts are recorded inventory snapshots; a local backup rehearsal does not establish current production readiness.

The intended layout is one PostgreSQL server, one database per company, shared application services and a central metadata registry. Keep existing tenant UUIDs and schema names. `helior` remains the metadata database unless a separate metadata migration is explicitly reviewed. Separate databases still share PostgreSQL's instance-wide connection limit.

## 1. Collect the current source inventory (read-only)

### From your computer through an existing SSH tunnel

Use `hrms-database/.env` for `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DB`, `POSTGRES_USER` and `POSTGRES_PASSWORD`. The local runner reads this exact file without modifying it or importing credentials into the parent process environment. It permits only a loopback host and requires the database to match the explicit `--expected-database` argument. The tunnel must already forward this local port to the intended production PostgreSQL server; matching a database name alone does not establish server identity.

From `D:/work/heliorventures/hrms-database` in PowerShell:

```powershell
$report = Join-Path (Resolve-Path '../.codex-tmp').Path ('company-db-preflight-' + [guid]::NewGuid().ToString('N') + '.jsonl')
node provisioning/company-databases/run-local.cjs --expected-database helior --psql 'C:/Program Files/PostgreSQL/17/bin/psql.exe' --output $report
```

Use an existing protected output directory and your installed psql path. The runner passes credentials only in the psql child environment, ignores ambient libpq connection overrides, starts the connection with default read-only transactions, and runs the same SQL below. It refuses an existing output path and only writes a report after checking the read-only inventory and completion marker. A failed attempt can leave an empty output file; choose a new filename for a retry. It does not print raw database errors or credentials.

`POSTGRES_SSLMODE` and `POSTGRES_SSLROOTCERT` can configure PostgreSQL TLS explicitly; the default libpq mode is `prefer`, inside the authenticated SSH tunnel. This runner neither opens nor verifies the tunnel's remote destination. The VPS method below remains available when a tunnel is not in use.

### Directly on the VPS

Upload `hrms-database/provisioning/company-databases/preflight.sql` to `/root/hrms-db-preflight.sql` on the VPS. Use the checked-out file, not a partially pasted terminal fragment. From Windows PowerShell, substitute your actual VPS SSH destination:

```powershell
scp D:/work/heliorventures/hrms-database/provisioning/company-databases/preflight.sql root@<VPS_IP>:/root/hrms-db-preflight.sql
```

Run the following **on the VPS in Bash**. This uses the existing PostgreSQL container's local socket and configured login. No passwords are printed and no Docker restart is performed. If local authentication fails, stop and configure an operator-owned passfile; do not paste passwords into chat or commands.

```bash
(
  set -eu
  umask 077
  test -s /root/hrms-db-preflight.sql
  report=$(mktemp /root/hrms-db-preflight.XXXXXXXX.jsonl)
  if docker exec -i postgres sh -c \
    'exec psql -X -qAt --no-password -U "${POSTGRES_USER:-postgres}" -d helior -v ON_ERROR_STOP=1 -v expected_database=helior' \
    < /root/hrms-db-preflight.sql > "$report"; then
    printf 'Completed inventory: %s\n' "$report"
    tail -n 1 "$report"
  else
    printf 'FAILED: incomplete report at %s; do not use it for migration.\n' "$report" >&2
    exit 1
  fi
)
```

Attach the resulting `.jsonl` file for review. It contains schema names, registry identifiers, object names, migration IDs and capacity metadata; it contains no passwords or business rows. A final `section: complete` means collection succeeded, **not** that migration is safe. Missing/duplicate mappings and locked migration tables are reported for review, not repaired. Estimated row counts are not reconciliation evidence.

The script uses one read-only repeatable-read transaction with statement and lock timeouts. It includes ACTIVE/SUSPENDED tenants, incomplete mappings, tenant schemas, cross-schema foreign keys in both directions, external trigger functions, catalog-recorded dependencies, extensions, large objects, migration history, slots and current connection counts. Catalog inspection cannot discover every dynamic SQL reference, application dependency or external file reference.

## 2. Resolve the demonstrated blockers

| Blocker | Required resolution before deployment |
| --- | --- |
| `tenant_integration` references `kabipay_ops.integration_connector` | Source implementation: ops 0128 retains catalog identities; tenant 0129 replaces the cross-schema FK with a local ID reference FK. Updated Analytics validates every connect/reconnect against the authoritative active ops catalog before its company transaction. Rehearse the coordinated migrations, grants and application release on PostgreSQL 16. |
| Tenant update triggers call `kabipay_ops.set_updated_at()` | Source implementation: tenant 0129 creates a tenant-local helper and retargets timestamp triggers, preserving conditions, enable modes and comments. Unknown helper behavior or unsupported trigger forms stop migration. Inventory and resolve all other function, type, extension, view and default dependencies. |
| Pending migration 0110 reads/locks `kabipay_ops.tenant_database` and `kabipay_ops.module` | Rehearse applying it while source schemas and metadata are colocated in an isolated restored clone, then preserve its real Liquibase history during export. Review the production sequence and every later pending migration before execution. Do not mark it applied manually or edit an applied migration. |
| Shared company-service role provisioning | The source fix adds explicit `-CompanyDatabases` to the private-source provisioner, with registry ownership checks and rejection of CONNECT outside that list. Use the [provisioning instructions](../../../hrms-database/provisioning/private-events/README.md#shared-company-business-service-logins), repeat per company/service role, and freeze registry changes during the sequence. Actual production grants and PostgreSQL 16/TLS acceptance still require rehearsal; operator/CDC/private-worker isolation remains. |
| PostgreSQL was reported at `wal_level=replica`; connection capacity is unmeasured | Size WAL/slot/connection limits using all applications on this instance. Five companies currently allocate up to 120 application connections before central workers, CDC, Finance, RMS and operator headroom. Plan any required restart in an agreed maintenance window. Unlimited retained slot WAL must not become an unnoticed disk-exhaustion condition. |
| Old delivery worker was reported running | Complete existing private-history export, pending/uncertain delivery ownership, reader switch and retirement gates. Do not simply stop the old worker to bypass deployment checks. |

The preflight itself does not fix these blockers. The shared-role and dependency source changes require rehearsal together before production database creation/copy/cutover.

### Integration catalog and timestamp dependency contract

Apply pending ops migrations through **0128 first**, then pending tenant migrations through **0129**, while source tenant schemas and metadata are still colocated. Migration 0110 requires that layout. Freeze all writers for this coordinated sequence and export only after migration succeeds. Keep the real Liquibase records; do not mark changesets applied manually. The new migrations deliberately reject automatic rollback because company databases may already retain these identities.

Ops remains the only mutable integration catalog. Connector IDs cannot be changed, hard-deleted or truncated after 0128; disable a connector with `is_active=false`. Tenant 0129 backfills only IDs already used by integrations, including historical inactive connectors, into `integration_connector_ref`. It retains the FK name and delete restriction. It does not copy catalog names, status or configuration.

The new Analytics image checks the central catalog on every connect/reconnect, then inserts the local ID and upserts the integration in one company transaction. Unknown/inactive connectors and metadata failures reject admission. Reconnection preserves the integration ID, encrypted credentials, configuration and creation time. Concurrent requests converge on the existing unique tenant/connector row. Catalog activation is checked at admission; disabling the catalog entry does not automatically disconnect existing integrations or constitute a distributed transaction.

For the stable Analytics company login, grant schema USAGE plus SELECT/INSERT on `integration_connector_ref`; do not grant UPDATE, DELETE or TRUNCATE on that table. Its connection write needs SELECT/INSERT on `tenant_integration` and UPDATE of `is_active`, `connected_at`, `updated_at`. Retain separately reviewed permissions needed by other Analytics operations and central catalog SELECT. Use the provisioning allowlist contract for effective database access. Privileged imports/maintenance must validate against the authoritative catalog before adding IDs; the local reference table is not an admission authority.

Deploy the updated Analytics code together with these migrations. Old binaries do not create local references for newly selected connectors. Future tenant migrations must use the tenant-local `"${schema}".set_updated_at()` helper. A new empty company database still needs a reviewed bootstrap sequence for historical migrations that reference ops; applying the historical tenant master directly to an empty standalone database is not yet demonstrated.

Local evidence (2026-11-09): all 22 Analytics binary tests passed, including missing/inactive/unavailable catalog and transaction behavior. A synthetic native PostgreSQL 17 rehearsal applied the actual forward SQL, exported/restored two tenant schemas into separate databases without `kabipay_ops`, preserved integration values, a migration-history marker, trigger modes/conditions/comments and sequence state, and exercised the actual application SQL under restricted grants with concurrent requests. It also proved a missing extension causes a single-transaction restore to roll back, followed by successful restore after provisioning that extension. Independent review found three migration issues; regressions reproduced them and passed after fixes for session-dependent deparsing, preservation of condition text and rejection of unreviewed helper settings. This is not a full Liquibase-engine run, real backup reconciliation or production PostgreSQL 16 acceptance. No `.env` or production connection was used for this phase.

Reproduce the isolated synthetic rehearsal from `hrms-database` (uses only a newly created local cluster):

```powershell
$env:PRIVATE_TEST_PG_BIN='C:/Program Files/PostgreSQL/17/bin'
node --experimental-test-isolation=none --test provisioning/company-databases/tests/dependencies.test.cjs
```

### Production-backup rehearsal completed locally, 2026-11-09

A fresh read-only inventory and database-only backup of `helior` were taken through the existing SSH tunnel. Credentials were loaded internally without being displayed. The archive is 4,991,404 bytes, SHA-256 `8c13a7224d1255f998a37e730152d2ed3508c628afd451100cb974a86ccf3a1f`; it restored successfully into an isolated PostgreSQL 16.14 Alpine container with matching UTF8/en_US.utf8 encoding and locale.

Actual Liquibase 4.28.0 validation/update ran from 161 frozen migration files. Central history advanced from 34 to 42 changesets; each of five tenants advanced from 259 to 268. All historical checksums were preserved and the main ops/tenant changelogs reported zero pending changes. Separate retirement gates remain.

All five schemas were then exported into separate local company databases. Across 1,385 tables, row counts and sorted SHA-256 row digests matched; sequence state and the compared column/default, relation, view, policy, sequence, type, constraint, index, trigger and function definitions matched. PostgreSQL reparsed two known CHECK expressions into an equivalent distributed varchar-to-text cast form; comparison accepts only those exact equivalent spellings and retains the raw definitions. All tables with a `tenant_id` column were checked for other tenants' rows; none were found. Each destination contains one tenant schema, no `kabipay_ops`, no cross-schema FK and no external tenant trigger helper.

Evidence is retained in the access-restricted workspace directory `.codex-tmp/helior-rehearsal-20261109-152835-e9643037`, including `SUMMARY.md`, `rehearsal-receipt.json`, the original archive, per-company archives and before/after fingerprints. The local database container is stopped and its data volume is retained. Production data, registry mappings and services were not changed.

Limits: this copy excludes cluster-wide roles/password hashes, external tenant files, VPS configuration, Kafka and ClickHouse. Restore used a synthetic local owner without source ACLs. Local registry mappings have not yet been switched, and shared application runtime, production grants/TLS, CDC and private-history/delivery handoff have not been accepted against this restored snapshot. These remain prerequisites for production cutover. A final frozen production backup is still required during the maintenance window.

### Empty production destinations created, 2026-11-09

All five `company_*` destinations listed below were created on the existing VPS PostgreSQL cluster from `template0`. Each has a dedicated restricted NOLOGIN owner, `ALLOW_CONNECTIONS=false`, and no PUBLIC database privileges. Readback verified these settings and the unchanged five `helior` registry mappings. No source migration, data copy, application deployment or PostgreSQL restart occurred. Evidence: `vps-empty-databases-receipt.json` in the protected rehearsal directory.

Enable each destination only during the reviewed migration sequence. Database creation does not satisfy release, permissions, backup or cutover gates. The existing `helior` source remains authoritative.

### Preserve permission restrictions during schema transfer

The next local rehearsal demonstrated that `pg_dump`/`pg_restore --no-acl` discards explicit REVOKEs as well as grants. Restored private operator functions consequently regained default PUBLIC EXECUTE. The runtime provisioning SQL templates rejected this state with `Private runtime can execute operator evidence/capture/retirement functions` before committing the bootstrap transaction.

Before admitting service logins, capture and reconcile effective ACLs from the frozen, migrated source against each destination. This includes PUBLIC routine EXECUTE restrictions, schema/table/column/sequence privileges, owner mapping and default privileges. Do not assume that a successful data/schema comparison proves permission equivalence, grant all functions/tables, or bypass the provisioner's rejection. When source role ACLs cannot be restored directly, use an explicit reviewed role/owner mapping and permission transfer plan. Preserve the source ACL inventory and destination readback with the migration receipt.

The local recovery used the migrated clone's routine signatures and PUBLIC EXECUTE baseline to restore exactly those routine restrictions. Actual shared-role templates then passed for all five company databases on PostgreSQL 16.14, including a second idempotent invocation, local-socket reads as the restricted database role, denied protected authority updates, and effective CONNECT only to the five approved destinations. Local metadata mappings were switched in one guarded transaction. The PowerShell provisioning wrapper was not exercised in this rehearsal. The clone was stopped after verification; evidence is in `shared-grants-1794222661085/receipt.json` inside the protected rehearsal directory. This supersedes the earlier snapshot's statement that local mappings had not been switched.

That scoped check does not establish full production ACL equivalence, password/TLS authentication or application acceptance. Production revocation of PUBLIC CONNECT on other databases must separately preserve the existing Finance/RMS and other approved users; the isolated clone's blanket revocation is not a production command.

### Live readiness refresh, 2026-11-09

A new read-only report verified the recorded cluster identity and unchanged `helior` mappings. PostgreSQL remains 16.14 with `max_connections=100`, three superuser reserved connections, `wal_level=replica`, `ssl=off`, ten replication slots allowed, no existing slots, and unlimited `max_slot_wal_keep_size=-1`. It observed 19 `helior`, two Finance and one `appdb` client connections; these are a point-in-time count, not peak-load sizing. The planned 120 application allocation alone exceeds the current limit.

Source history remains at 34 ops changesets and 259 per tenant; no tenant migration locks were set. Aggregate legacy counts were 111 audit rows and 16 outbox rows, with zero webhook delivery and employee finance outbox rows. These counts do not classify pending/uncertain outcomes or establish retirement acceptance. All five destination databases remain closed. Evidence: `live-readiness-1794222932573.json` in the protected rehearsal directory. Capacity, PostgreSQL TLS, WAL/CDC preparation and legacy handoff remain live cutover gates.

## 3. Back up and rehearse

1. Take an access-controlled full `helior` backup, required global role/grant definitions, configuration and tenant file backups. Keep an off-host copy and its checksum. Restore-test the backup before scheduling cutover.
2. Restore to an isolated PostgreSQL 16 rehearsal server with application egress/delivery disabled. Preserve the original backup; never point rehearsal workers at production Kafka, ClickHouse, email, payroll integrations or file stores.
3. Rehearse pending ops migrations through 0128, then tenant migrations through 0129, while colocated and with writers frozen. Keep the existing public and per-tenant Liquibase history; stop on any lock, missing prerequisite or checksum error. Repeat the dependency inventory after migration.
4. Create empty rehearsal company databases under a non-login migration owner. Provision reviewed extensions, versions and schemas before restoring one company's schema into each. A schema-only selection does not include extension-owned operator classes such as those supplied by `btree_gist`. Use `pg_restore --exit-on-error --single-transaction` for each empty target. Do not use `pg_restore --create` for a renamed target: it uses the archived database name. Do not use `--clean` against an existing destination.
5. Preserve IDs, credentials/hashes, sequences, constraints, indexes, tenant data, protected/private legacy state, migration history and file references. Compare exact counts and stable content digests from a consistent snapshot, plus sequence state and schema objects. Validate FKs, trigger behavior and absence of other tenants' owned rows.
6. Transfer and verify the reviewed permission restrictions, including the PUBLIC routine restrictions described above, before applying grants to stable service-specific logins. Verify actual effective permissions, including PUBLIC, column grants, default privileges, owners and role memberships. Shared business-service logins may reach approved company databases; metadata credentials remain separate. Never grant all tables indiscriminately because protected event tables use column-level permissions.
7. Run two company databases concurrently through shared services using the real release configuration. Verify sign-in, tenant isolation, employee changes, payroll/loans, integrations, jobs, files, audit/history and failed-access cases. Verify suspension/remapping fails closed and the pool allocation fits the server.
8. Rehearse CDC bootstrap and private-event handoff with new source database identities and the accepted history baseline. Do not copy or reuse old logical slots across databases, reset authority records, or silently skip legacy delivery/history reconciliation.

PostgreSQL schema-filtered dumps do not automatically include external dependencies; large objects and global roles also need explicit handling. Use error-stopping restore behavior and preserve failed-run evidence. See the PostgreSQL 16 [pg_dump](https://www.postgresql.org/docs/16/app-pgdump.html) and [pg_restore](https://www.postgresql.org/docs/16/app-pgrestore.html) documentation.

## 4. Prepare the production release

Proposed database names (review against the final service credential prefix before creating):

| Company | Proposed database | Retained schema |
| --- | --- | --- |
| heliorprd | `company_heliorprd` | `tenant_e6d4fc13` |
| solvianbuildcon | `company_solvianbuildcon` | `tenant_f06f9f79` |
| solvianconsultancy | `company_solvianconsultancy` | `tenant_a50902ed` |
| solvianinfra | `company_solvianinfra` | `tenant_12f0a2cd` |
| venketeshwarabio | `company_venketeshwarabio` | `tenant_c107de74` |

After rehearsal passes, prepare and review the complete release manifest and four images using the existing build/upload tooling. Provision keys/certificates, stable service credential files, trust lists, file directories and company-scoped CDC/private workers. Verify shared-service PostgreSQL TLS and actual grants. Retain the existing Kafka/ClickHouse installations, data, certificates and cluster identities; installation success does not prove application ingestion or history acceptance.

Do not deploy the new shared runtime against five registry mappings that still point to `helior`: it deliberately rejects multiple active companies sharing a database name.

## 5. Perform the approved maintenance cutover

Only proceed with reviewed commands, successful rehearsal evidence, verified backups, adequate capacity and an agreed maintenance window:

1. Freeze tenant onboarding/mapping changes and all company writers: API traffic, scheduled jobs, imports, integrations and old workers. Reconcile in-flight and uncertain delivery outcomes using the retirement runbook.
2. While writes remain fenced, retain a pre-migration rollback backup. Apply reviewed ops migrations through 0128 and tenant migrations through 0129, including the colocated prerequisites of 0110, before producing the final migration exports. Capture those exports only after the migrations succeed; provision required extensions, restore into verified empty destinations and repeat reconciliation. An earlier rehearsal/live backup is not the final data copy.
3. Update all reviewed company mappings in one guarded metadata transaction with assertions on tenant UUID, original mapping and destination. Preserve an audit receipt containing old/new mappings and backup/reconciliation references. Keep writers stopped.
4. Complete private-source authority and CDC provisioning in the dependency order demonstrated by rehearsal. Registration-dependent tools must see the new mappings before they run. Keep writers stopped throughout this stage.
5. Start the reviewed shared-service release and required workers, then validate/reload Caddy through the existing deployment tooling. Use fresh processes: accepted database/schema mappings are pinned for each process lifetime.
6. Validate all five tenants and tenant isolation before reopening writes. Monitor errors, connections, slot lag/WAL retention, outbox backlog, duplicate delivery and ClickHouse ingestion.

Steps 3–4 are one reviewed sequence. Never enable traffic between the mapping transaction and successful provisioning.

## Rollback boundary

Before any new-database writes, rollback must account for migrations already applied to the source. A mapping/image rollback alone is insufficient: old Analytics binaries cannot add new connector references after 0129. Rehearse either restoring the pre-migration source backup with the compatible old release or retaining a release compatible with the migrated source. Confirm source data and worker ownership before reopening writes. Keep source schemas and backups throughout acceptance.

After new writes or external deliveries, switching mappings back loses or forks state. Fence writers, reconcile/replay or reverse-migrate accepted changes, and obtain a reviewed recovery decision. Do not run both old and new writers, drop original schemas or delete slots as an automatic cleanup step.

## Evidence required to call this live

- Current source inventory reviewed; every blocker above resolved.
- PostgreSQL 16 restore/split/migration and two-company shared-service rehearsal passed.
- All five final destinations reconciled, with IDs, history and grants verified.
- Private history/delivery retirement and CDC acceptance completed.
- Coordinated images/configuration deployed and all tenant acceptance checks passed.
- Backup restore and rollback procedure demonstrated; capacity and disk monitoring active.

The recorded operations created empty, closed production destinations only. Tenant data and mappings have not been migrated, application images have not been deployed by this procedure, and production readiness is not certified.
