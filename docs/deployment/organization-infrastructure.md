# Organization infrastructure ownership and release

Approved local restructuring: 2026-10-19. No live rollout, data move, identity backfill or legacy retirement is implied by source changes/tests.

## Repositories and VPS layout

| Owner | Independently operated responsibility | VPS example |
| --- | --- | --- |
| `hrms-database` | PostgreSQL Liquibase schema + `provisioning/organization` roles/grants/publications/RLS | operator migration checkout; never service image startup |
| `hrms-clickhouse` | ClickHouse install/config + version/checksum/lock migration CLI + grants | `/opt/apps/clickhouse` with explicit existing storage/secrets |
| `hrms-kafka` | Broker, one isolated Connect + read-only capture proxy per company, optional metadata Connect, topics/ACL/connector maintenance | `/opt/apps/kafka` with explicit existing storage/secrets |
| `hrms-svc` | Business services, versioned events, independent consumers, source exporter, archives and accepted-policy retention | application images only |
| `hrms-documentation` | Shared platform and HRMS deployment orchestration, Caddy, backup/image archives and release evidence | shared `/opt/apps`; app `/opt/apps/hrms` |

```
/opt/apps/
  .env                         # operator platform settings; DB containers receive only their own variables
  compose.platform.yaml        # Caddy/PostgreSQL/Mongo only
  Caddyfile                    # shared Finance/RMS + imported HRMS fragments
  certs/cloudflare/
  data/postgres/               # existing root storage, never automatically moved
  data/mongo/
  kafka/                       # independently installed hrms-kafka project
  clickhouse/                  # independently installed hrms-clickhouse project
  hrms/
    compose.json               # generated application-only release
    release.json               # explicit artifact/service inventory
    config/                    # public keys, trusted endpoint/topic bindings, UI config, CA roots
    caddy/                     # generated public/private HRMS routes
    env/                       # manually provisioned restricted per-role/per-company files
    secrets/                   # separate per-company/per-service/private archive keys
    data/                      # explicitly mapped existing files/archive state
    images/archive/<release>/  # only four HRMS image families
    backups/                   # independent backup runner, its own env/backup.env
```

The two new projects are standalone local Git projects on `feat/organization-cross-company-management`; no remote repositories/publishing/commits were created. Application event code remains in svc because it enforces HRMS contracts; it is not Kafka installation logic. `TenantId` and `WithWorker` deployment switches were removed: company IDs come from the manifest and required source/event workers are part of the rendered release.

## Fixed routing and employee flow

1. A company UI hostname serves its own runtime configuration and uses that same hostname for Auth/GraphQL/files/prejoining. One shared Auth process is `client` plane only and selects a distinct company RSA signer and database binding. One shared gateway uses the complete deployment-owned service endpoint map; no event/header supplies a URL.
2. A manager/HR logs in to their employing company. The organization workspace sends their verified login-company selector and bearer token through that gateway to the central organization GraphQL service. HR needs a separate scoped organization grant; their old HR role remains local to its company.
3. Company membership, grants, principals/employment links and reporting relationships are managed in the organization module. A relationship is employee-to-manager, not a company parent hierarchy: people in A may report to a manager employed in B and people in B may report to another manager in A. Cycle/self-approval, capability and employee-scope rules remain enforced.
4. Source transaction writes business state plus the small transactional outbox atomically. Its separately bound CDC role reads only the exact publication tables; company Connect emits a versioned company event into its fixed Kafka topic.
5. Independent inbox/history/reporting groups validate provenance and idempotency, each commit their own progress. Inbox stays usable during history/reporting failure; APIs distinguish PARTIAL/unreconciled capture from a valid zero. ClickHouse keeps business, reporting and restricted control history; diagnostics are redacted and exported separately through the configured OTel backend.
6. Manager sees source-company-labelled requests and history in the organization workspace under their existing home-company session. A decision calls the fixed HTTPS source service endpoint with short-lived scoped delegation + audience/body-bound service proof. The source checks live identity, installed membership/grant/relationship, expected version and idempotency before updating its own database/receipt atomically. The resulting event updates shared views; no organization process connects to a tenant database.
7. Payroll remains a source-owned durable job with fresh authorization at commit and a separate accepted receipt/job status. Owner reporting uses authorized company scopes and the ClickHouse projections; source reconciliation/capture barriers fence completeness.

Public Caddy denies `/internal*`, `/auth/internal*` and the organization identity bridge. Source commands, policy callbacks, Connect, Kafka, ClickHouse and archive remain private. Private source/policy TLS uses explicit CA trust plus hostname checks; service proof is still required behind TLS. Capture workers receive only the narrow read-only per-company proxy client, never Connect administrator credentials. Archive has mTLS and a separate encryption key.

Organization mode has **no public unbound tenant/HMAC fleet**: the old global Auth/gateway are operator-only and the old subgraph bundle becomes ops-only. All active tenants on that fleet must be inventoried and provisioned before enabling the mode. The release accepts only the shared application organization manifest and omits the retired `kabipay-outbox-worker` executable. Shared `kabipay-tenant-maintenance` preserves scheduled business work; separate private delivery workers own durable broker retries and call the fixed source Employee adapter using mTLS plus scoped proof. Finance calls use the source HTTPS proxy on ports8451/8452. Reconcile pending and uncertain legacy work and complete history export/restore/reader migration before manually retiring an old worker; deployment inventories running `apps` project commands/entrypoints and refuses any retired delivery binary, including renamed company workers and shell launches. The old service label and exact global container name remain guarded; failed inventory/inspection blocks rollout and no container is stopped automatically. Provision every private worker, history client/server, key, certificate and database/topic scope from [the environment contract](../../deploy/hrms/environment.md#private-audit-delivery-and-history).

## Review/render without a VPS

```powershell
node hrms-documentation/scripts/deploy/render.mjs hrms-documentation/deploy/hrms/manifest.example.json .codex-tmp/hrms-release
& hrms-documentation/scripts/deploy-on-vps.ps1 -Tag helior-organization-001 -Manifest hrms-documentation/deploy/hrms/manifest.example.json -OutputDir .codex-tmp/hrms-release -RenderOnly
```

Replace example identifiers/hosts and map each existing company private-file directory explicitly. Review every output and [environment boundary](../../deploy/hrms/environment.md). The manifest contains no credentials. Release uploads only the explicit generated artifact allowlist, never every file in a reused output directory.

### Required inventory before application startup

The current deployment uses one shared ops registry/fleet. Render the exact tag, manifest and output directory with -RenderOnly. A separate database operator must run [the read-only inventory tool](../../../hrms-database/provisioning/organization/README.md#shared-fleet-cutover-inventory) against that release using a restricted libpq service/passfile:

```powershell
node hrms-database/provisioning/organization/check-rollout.cjs --release-dir D:/review/hrms-release --service hrms_ops_readonly --database ops_database --output D:/review/cutover-inventory.txt
& hrms-documentation/scripts/deploy-on-vps.ps1 -Tag reviewed-tag -Manifest D:/review/manifest.json -OutputDir D:/review/hrms-release -VpsHost reviewed-host -Deploy -InventoryReport D:/review/cutover-inventory.txt
```

These are operator examples, not commands already executed. Use the same reviewed tag/manifest/output directory for render and deployment. ACTIVE and SUSPENDED tenant IDs and current subdomains must match the release exactly. Provisioning, status/subdomain changes and file edits remain frozen through the application/Caddy cutover. A changed release or a window exceeding fifteen minutes needs a fresh query/receipt. The receipt is trusted operator evidence against omissions; it does not replace authorization or prove production acceptance.

The remote guard validates the receipt, tag, tenant set, expiry and SHA256 of every rendered artifact before loading images and again immediately before startup. -SkipValidation does not bypass it. Node/database credentials stay with the operator; application containers never receive the inventory-query credentials. RenderOnly, image-only preparation and status validation do not start services and do not require a receipt. Retired global/company worker guards remain mandatory.

## Existing VPS cutover: separate operator steps

1. Inventory live Compose project names, external Finance/RMS network, Caddy state volumes, all mounts, image versions and active HRMS tenants/workers. Back up config, databases, history, archive manifests/keys and broker metadata using supported procedures. Keep the existing root storage/project/network names. Default compatibility identity is `apps`, `apps_app-network`, `apps_caddy_data` and `apps_caddy_config`; a mismatch must stop the release and be reviewed, not create empty replacement state.
2. Render/review an application manifest; provision all env/cert/key/data directories with correct ownership (Node worker/archive image is non-root). Follow the separate DB/ClickHouse/Kafka READMEs. Infrastructure installation must never be triggered by `deploy-on-vps.ps1 -Deploy`.
3. Stage `deploy/platform/compose.yaml` as `/opt/apps/compose.platform.yaml` and the canonical Caddy example as a **candidate**, reconcile existing Finance/RMS/domain/cert routes, then validate before replacing/reloading. `scripts/deploy-platform.ps1 -StageCaddy` stages only a candidate. `platform.sh` checks existing PG/Mongo mounts/Caddy volume identities, explicit root env file, private networks and complete Caddy configuration; it never moves data. Existing app network and Caddy state volumes must exist. Fresh installs explicitly create them before setup; never apply fresh-install commands to an existing VPS.
4. Install Kafka broker once, each company Connect/proxy independently, metadata Connect independently and ClickHouse independently at root-level project directories. Retain exact existing storage/cluster IDs; never mount one Kafka/ClickHouse data directory into old and new containers concurrently. The earlier mixed service Compose file is removed from source; archive the old VPS manifest only after cutover review. PostgreSQL logical replication/WAL settings are an explicit source DBA operation; slot monitoring must precede CDC enablement.
5. Apply approved ops/tenant migrations through `hrms-database`; provision least-privilege source/control/worker roles/grants/publications there. Rehearse existing-company 0125 on representative data: it retains necessary write locks, uses one survey/audit pass and aborts atomically after a five-second lock wait or sixty-second statement limit. Schedule a measured maintenance window; do not disable the limits or repeatedly retry into traffic. Preserve 0115's durable-evidence rollback guard and agree the forward recovery/restore boundary before enablement. Apply ClickHouse schemas/grants through its own CLI; unresolved migration intent/lock requires DBA reconciliation and is never automatically replayed. Independently provision exact Kafka topics/ACLs/connectors using its admin CLI. No server starts with automatic business schema migration or destructive cleanup.
6. Complete the source retirement gates and reviewed retirement handoff for every global/company legacy delivery worker, preserving pending/uncertain destination outcomes and accepted history/restore evidence. Provision the shared runtimes with explicit per-company configuration, maintenance process, private audit/delivery workers, operator audit worker and purpose-separated mTLS history servers using the environment contract. First organization creation is a separate authorized `bootstrap_organization <company-uuid> <organization-name>` operation with a securely supplied `KABIPAY_ORGANIZATION_BOOTSTRAP_TOKEN`; follow [organization bootstrap and administration](../runbooks/organization-service.md#first-organization-and-subsequent-administration). Start shared runtimes/central workers. Build/upload the four application images with `build-save-upload-images.ps1`, using `-Manifest` on deployment. Run application release, then explicit Caddy validate/reload. Root setup, schema operations and application rollout are separate commands; deprecated combined Caddy/env/tenant-map switches fail with the replacement operation.
7. Run company login/refresh and token-mismatch negatives, real HR/manager/owner UI approval/reporting, grant/relation/membership revocation, payroll execution/crash recovery, capture for every source/partition/role, retry/quarantine, independent sink failure/restart, source reconciliation and encrypted archive restore. Confirm public private-path denials and restricted Kafka/Connect/CH/DB access. Live browser, HA/failover and off-host restore need recorded acceptance; static/config/unit checks cannot supply it.
8. Only after accepted retention and verified equivalents, independently authorize each old poller/retry writer/log store/history read path/data deletion for retirement. Keep business data, receipts/jobs and transactional outbox safety. A retry queue or diagnostic log is not a permanent business ledger.

On an existing host run platform helper from a restricted shell with its explicit paths. Do not use `docker compose down -v`, `--remove-orphans`, bulk prune, a new unreviewed project name or recursive data moves during this cutover.

## Validation and outstanding gates

See [phase/cleanup audit](organization-phase-cleanup-audit.md) and the dated infrastructure workstream ledgers. After the approved Docker recovery, current two-company PostgreSQL16.15 TLS/ACL/CDC/private-proxy checks, fresh ClickHouse schema/grant/lock/timeout checks and all six event lifecycle fixtures passed. The earlier infrastructure unit baseline recorded 20 files / 55 tests; current retirement verification is recorded in the dated retirement reports. All four application images are built and inspected. Final Rust export excludes stale cached executables and the checked runtime libraries resolve. Renderer/Caddy/PowerShell/Compose checks do not prove full application startup, company egress/business delivery, optional metadata Connect TLS delivery, live browser behavior or production rollout. Backup/off-host restore, existing-data reconciliation and legacy retirement remain explicit acceptance gates.

## Shared application rollout revision — 2026-11-09

For existing tenants sharing a database, start with the [company database split preflight and staged runbook](../runbooks/company-database-split.md). Creating empty databases and deploying images is insufficient: shared catalog/helper dependencies, pending migrations, service-role grants and final-copy reconciliation must be resolved first.

Use `applicationLayout=shared` and the [shared environment contract](../../deploy/hrms/environment.md#shared-application-services). There are 18 business processes for the fleet, with shared client Auth/gateway/UI/maintenance; database count does not determine application replica count. The process trust boundary now includes its configured companies, while each database, credential, private key, authorization decision and CDC publication remains explicitly scoped. Existing Kafka/ClickHouse installation work is retained.

Before application rollout, render the company catalogues from the central manifest, provision each service's stable `database.json`, and verify the PostgreSQL connection allocation. Database/schema mappings come from the main metadata registry; no per-company database passwords are added to service files. Five company pools per 20 processes at one connection each, plus one metadata connection per process, reserve 120 connections before central services, CDC and other products. The live PostgreSQL limit must be measured and sized explicitly; startup configuration is not a measurement. Sharing a login does not combine PostgreSQL connections across databases.

For an upgrade from a previous bound application fleet, freeze company writes and scheduled jobs, retain rollback artifacts and stop the reviewed old company application containers before starting shared services. The release refuses old company application labels because Compose would retain them as running orphans. Never use `--remove-orphans` on the shared `apps` project: it also contains platform services. Existing global outbox retirement checks remain mandatory. For the current legacy production fleet, complete the separate database migration and delivery cutover plan first.

This revision does not move any tenant data, change registry targets, restart PostgreSQL or deploy to the VPS. Old two-company image/runtime acceptance records predate this code and do not certify the shared layout.

For subsequent onboarding, follow [Adding a company](../../deploy/hrms/environment.md#adding-a-company). Grant the existing service roles access to the newly migrated database, register its exact mapping, add its inventory/key ID once to the central manifest, and render the fleet. Keys, certificates, trust lists, file directories and CDC remain provisioned per company. Changing an accepted database/schema mapping is a reviewed write-freeze/CDC-handoff/restart operation, not a hot database switch. Newly registered companies require the generated inventory rollout before access is admitted.
