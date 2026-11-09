# Registry company databases implementation plan

**Goal:** Keep one stable, restricted company-database login per application service. Manage company database/schema mappings in `kabipay_ops.tenant_database`, with no per-company passwords in service configuration.

**Approved direction:** The user approved stable application credentials and centrally managed tenant mappings after discussing the shared PostgreSQL connection limit. This continues the shared-services implementation. No production operation or commit is authorized.

**Design:** Version 2 company catalogues contain deployment inventory, origins and secret references only. The renderer generates all catalogues from one onboarding manifest. Each service mounts its own fixed `service/database.json` with a verified-TLS server URL and a required company database-name prefix. Registry rows may select a database/schema on that fixed server but cannot select host, port, user, password or TLS settings. Reject unknown companies, inactive/deleted tenants, ambiguous mappings, shared company databases, reserved/unsafe identifiers and mappings outside the prefix. Pin each accepted registry mapping for the process lifetime; changing a live mapping requires a reviewed restart after write freeze and CDC handoff. This avoids silently switching an in-flight business workflow to another database.

**Onboarding boundary:** Add the company once to the deployment manifest, create/migrate its database, grant the existing application roles access, and register its mapping centrally. Provision company cryptographic keys, TLS hostnames and file directories, then render the complete fleet and perform the existing reviewed rollout. No per-service credential file changes are needed for a new company. This is automatic catalogue generation and registry database discovery, not zero-provisioning tenant activation. Version 1 static company DSNs remain explicitly supported for existing non-rendered deployments; the new renderer uses version 2.

**Alternatives:** A single administrator login across all services was rejected because business services do not need provisioning privileges. Separate tenant passwords remain available in version 1 but do not meet the user's onboarding preference. Service-specific restricted logins preserve purpose boundaries while allowing each service's login to be granted access to new company databases.

**Constraints:** Preserve the existing staged service snapshot; new edits stay unstaged. Native commands only, no Dart/Flutter, commits or VPS changes. Continue the approved focused local verification. Keep separate company data and existing signed authorization checks. Metadata credentials remain separate from company-runtime credentials. Existing connection budgets remain enforced.

## Tasks

- [x] Add a focused registry connection module with bounded protected configuration, fixed-server TLS options, identifier/prefix checks, unique registry mapping validation and process-lifetime binding pins.
- [x] Extend shared configuration to version 2 and integrate startup/request validation without weakening version 1 or allowing fallback.
- [x] Generate non-secret per-service catalogues from the central manifest; update mounts, configuration preflight and examples. Keep database credentials outside generated/uploaded artifacts.
- [x] Add focused tests for stable login reuse, malicious registry targets, duplicate mappings, remapping after cache creation, generated onboarding and missing/insecure credentials. Run approved local Rust and deployment checks.
- [x] Update the onboarding/environment documentation and current architecture mirrors, explicitly distinguishing database discovery from key/host provisioning and production rehearsal.

## Review focus

Registry values must never redirect shared credentials to another server. A company mapping must not point at another company's active database. Cached connections must not bypass suspension or remapping checks. Registry/database failures must not activate legacy fallback. Newly rendered tenants must not require manual edits to every service's credentials/catalogue. No code may claim that separate databases or shared credentials multiply PostgreSQL's server-wide connection capacity.

## Verification and review — 2026-11-09

- `cargo test --locked -p kabipay-common --lib -- --test-threads=1`: 121 passed, 2 ignored PostgreSQL fixtures. Six new registry tests cover stable service login reuse, untrusted/unsafe target rejection, insecure service configuration, ambiguous/shared mappings, cached binding pins and version/configuration mismatch.
- `cargo check --locked -p kabipay-common -p kabipay-auth -p kabipay-employee -p kabipay-payroll -p kabipay-tenant-maintenance -p kabipay-organization --all-targets`: passed. Existing unused/example warnings and the `proc-macro-error2` future-compatibility warning remain.
- `node --experimental-test-isolation=none --test scripts/deploy/render.test.mjs scripts/deploy/private-events.test.mjs scripts/deploy/compose.test.mjs scripts/deploy/caddy.test.mjs scripts/deploy/inventory.test.mjs scripts/deploy/shared-config.test.mjs scripts/deploy/document-links.test.mjs`: 27 passed after the final fix. Used local Caddy 2.10.2 through `CADDY_BINARY`; Compose parsed configuration without starting containers.
- `& scripts/deploy/deploy.test.ps1`: passed with mocked SSH/SCP, verifying generated artifact upload and preservation of operator-owned secrets. No VPS was contacted.
- `git diff --check`: passed in the two changed repositories.
- A GPT 6.1 sol summarizer prepared a narrow brief for the independent Astra source review. The review identified one provisioning-contract mismatch: generated history TLS filenames differed from the documented `client.crt` / `client.key`. Generated references were aligned with the established names and a regression test added. No additional confirmed routing defect was reported in the inspected scope.

## Production acceptance still required

Local proxy tests do not prove real database grants, certificate trust, schema migration, in-flight connection draining, application startup or tenant workflows. Build the new images and rehearse two separate company databases with the stable service roles before rollout. Verify that runtime roles cannot provision databases/roles, alter metadata mappings, or access other products. Preserve the earlier migration prerequisites, write freeze, CDC handoff, backup/restore and rollback gates. Tenant cryptographic keys, public trust entries, hostnames and file directories still require provisioning. No production changes, migrations or commits were performed by this task.
