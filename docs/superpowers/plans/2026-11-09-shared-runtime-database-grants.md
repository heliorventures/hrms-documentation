# Shared runtime database grants implementation plan

> **For agentic workers:** Use superpowers:executing-plans. User approved this focused implementation and local checks. No commits, production changes or .env inspection.

**Goal:** Permit a stable business-service login to bootstrap private-event permissions in multiple explicitly approved company databases without admitting unrelated databases or weakening private-event grants.

**Architecture:** Add optional `-CompanyDatabases` to the existing company provisioner. Validate the exact reviewed list against central metadata on the fixed host, then validate actual effective CONNECT privileges on the source server. Empty/omitted lists retain the existing isolated behavior; operator sources reject shared lists. Each invocation grants only the current source database/schema and its existing protected columns. Metadata inventory remains frozen throughout provisioning because the registry and source transactions are separate.

**Tech stack:** PowerShell, psql/PostgreSQL, Node test runner and an owned native PostgreSQL fixture.

**Spec:** Approved separate company database/shared service design; `2026-11-09-registry-company-databases.md`, plus blocker inventory in `../../runbooks/company-database-split.md`.

## Review focus and constraints

- Reject malformed, duplicate, missing-target, nonexistent, system and registry database entries.
- Every listed database must have exactly one active mapping, owned by a non-deleted ACTIVE/SUSPENDED company with exactly one active mapping; host/type/schema must be valid.
- Reject operator shared lists and effective CONNECT outside the reviewed list, including PUBLIC/inherited grants; keep the existing no-membership/no-owner/elevated-role restrictions.
- Preserve protected columns, generation/state authority, business grants and single-database default behavior.
- Never grant other companies from one invocation or silently revoke privileges used by another product.

## Tasks

- [x] Add failing wrapper tests for shared list propagation and rejected inputs.
- [x] Add real SQL regression tests with two company databases, one shared role and a forbidden third database; cover registry validation and protected grants.
- [x] Implement reviewed-list parsing, registry validation and source effective-CONNECT checks.
- [x] Run focused tests, independent review, and update provisioning/runbook usage and evidence.

## Execution record

Source inspection confirmed the old `runtime-bootstrap.sql` compares every CONNECT privilege to `current_database()`, causing the second company bootstrap to reject a stable shared-service login. The registration check is a separate fixed-TLS operator connection, followed by a transaction in the source. Private-worker/CDC provisioning is separate and remains unchanged.

Docker is unavailable locally. Use a disposable native PostgreSQL 17 cluster for SQL checks; PostgreSQL 16 production rehearsal and verified-TLS transport remain separate acceptance gates.

The initial wrapper regression failed because CompanyDatabases did not exist. The real SQL regression failed on the old cross-database CONNECT rejection. Both passed after the focused fix. A direct Windows PowerShell native-argv probe then demonstrated JSON quote loss; the list now uses base64 JSON transport, independently decoded and validated by SQL. This transport change is covered by the wrapper regression and a native argument probe; final SQL and legacy-path regressions follow.

Final verification on 2026-11-09:

- `provisioning/private-events/tests/provision.test.ps1`: PASS with psql mocked, covering argument transport, shared-list validation and stop-on-registry-error behavior.
- `PRIVATE_TEST_PG_BIN=C:/Program Files/PostgreSQL/17/bin` with `node --experimental-test-isolation=none --test provisioning/private-events/tests/shared-runtime.test.cjs`: PASS (1 integration test, 0 failures). Real SQL verifies two shared company sources, actual role connections, idempotence, business grants retained, protected column rejection, advanced authority rejection, malformed/missing/unavailable lists, unrelated database denial, PUBLIC leakage, role membership, registry host/deleted/duplicate rejection, and successful isolated-company/operator defaults.
- Node syntax checks and scoped `git diff --check`: PASS. Independent source review reported no actionable security/correctness findings.
- One intermediate expanded fixture run lost PG_VERSION/postmaster.pid in the OS temporary directory. The harness now creates its unique owned fixture under workspace `.codex-tmp`; the complete rerun passed and stopped its server. Synthetic files remain for diagnosis; no existing PostgreSQL service was stopped.

No .env inspection, production connection, production grants, deployment or commits occurred in this task. PostgreSQL 16 and verified-TLS transport, actual production role grants and full migration/runtime acceptance remain unverified. Catalog/helper dependencies and migration rehearsal remain the next workstream.
