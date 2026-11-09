# Company deployment implementation plan

**Goal:** Deploy saved or newly built HRMS images through the existing entry points; target company migrations through the authoritative registry; provide a temporary, guarded same-server schema transfer command.

**Approved scope:** User approved implementation, focused local tests and migration rehearsal. No VPS operations, live data changes, commits or secret display.

**Architecture:** Keep application rollout separate from database operations. Preserve release/inventory checks and the shared service layout. Resolve database migration targets from the central registry with explicit expected target assertions. Copy into an empty destination using PostgreSQL tools with original ownership and ACLs, reconcile data and permissions, then apply explicit reviewed grants. Keep registry switching separate from copy and authority/CDC handoff.

**Stack:** Existing PowerShell entry points, Node CommonJS, PostgreSQL native tools and Liquibase.

## Tasks

- [x] Deployment regression: forward inventory/render inputs; deploy saved archives without rebuilding; verify local and remote checksums; never bypass startup guards.
- [x] Company migration regression: exact registry/database/schema/host binding, active or suspended tenant, separate ops target, no credential argv/logs, portable Liquibase runner.
- [x] Temporary transfer regression: explicit plan/execute modes and writer freeze; same-server identity; empty destination; dependency and migration prerequisites; ownership/ACL preservation; data/sequence reconciliation; explicit restricted service grants; durable receipt; no automatic mapping switch or destructive cleanup.
- [x] Run focused orchestration tests and native isolated PostgreSQL rehearsal, document exact commands and limitations.

## Review focus

- Stale inventory or changed rendered release must fail before startup.
- A tunnel address is a transport endpoint, not a replacement for the registry runtime host.
- Existing company history must be preserved; do not bootstrap historical migrations directly into an empty isolated database.
- PUBLIC privileges, column grants, default ACLs and function privileges must survive copying.
- Copy failures must leave evidence and must never reopen writers or change registry mappings.

The live capacity, TLS, CDC and private-history acceptance gates remain mandatory. No source/database/schema deletion is part of this implementation.

## Local verification

23 focused Node tests, six native Bash inventory cases, image-load orchestration, Python archive identity regression, four PowerShell suites and an isolated PostgreSQL permission/transfer test passed. The four saved release archives passed tag/platform/identity inspection without loading. A separate local saved-backup rehearsal applied actual ops/tenant Liquibase migrations, transferred one tenant (277 tables, 878 rows), reconciled it and applied the registry-selected company migration command. Production credentials/owners were not replicated into that fixture; synthetic roles were used. VPS deployment, all-company cutover and runtime acceptance remain unperformed. Exact operator commands are in [the release runbook](../../runbooks/company-release-commands.md).
