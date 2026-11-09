# Company database split preflight implementation plan

> **For agentic workers:** Use superpowers:executing-plans for this scoped preparation. No commits or production execution.

**Goal:** Obtain a reproducible, read-only inventory before moving existing tenant schemas into separate databases with shared services.

**Architecture:** Run a fixed psql script in one read-only repeatable-read transaction against the explicitly named source database. Report metadata only, never credentials or business rows. A staged runbook keeps rehearsal, dependency corrections, final copy, registry cutover and application rollout separate.

**Tech Stack:** PostgreSQL 16 SQL, psql, Node native test runner; optional owned local PostgreSQL fixture.

**Spec:** Approved separate-company-database/shared-service design in `2026-11-09-registry-company-databases.md`; current production evidence supplied in conversation.

## Constraints and review focus

- Preserve tenant UUIDs, schema names, business data and Liquibase history.
- Never change live mappings, restart PostgreSQL, create databases or grant permissions in preflight.
- Inventory every ACTIVE/SUSPENDED tenant, including missing/duplicate mappings; do not hardcode five companies in executable code.
- Detect dependencies in both directions and report uninspected dynamic SQL as a limitation.
- Missing history/locked migrations and shared runtime role restrictions must remain explicit rollout gates.
- No secrets, query text or business rows in the report. Never overwrite an existing report.
- Source metadata inspection is not restore, migration, application or production acceptance.

## Tasks

- [x] Add `hrms-database/provisioning/company-databases/tests/preflight.test.cjs`: owned local fixture verifies target mismatch, all tenants including incomplete bindings, dependency evidence, history/locks, and unchanged source state.
- [x] Add `hrms-database/provisioning/company-databases/preflight.sql`: fixed read-only metadata queries, bounded timeouts and completion marker.
- [x] Add `hrms-documentation/docs/runbooks/company-database-split.md`: exact first VPS command; dependency decisions and staged acceptance/rollback gates.
- [x] Run focused local checks, record limitations and link from infrastructure deployment guidance.

## Execution record

Ruling: start with evidence collection, not a generic copy command. Source inspection confirmed that migration 0110 requires central catalog tables, the integration FK crosses schemas, and the private runtime bootstrap rejects multi-database CONNECT. Copying now would conceal unresolved production dependencies. This stage prepares the next operator action; it does not claim the split is ready to deploy.

Local Docker engine was unavailable at initial inspection. Native PostgreSQL 17 binaries are installed; a disposable loopback-only fixture can validate the inventory script, but cannot establish PostgreSQL 16 migration/runtime acceptance.

Verification: the native PostgreSQL fixture test passed (1 test, 0 failures) using `PREFLIGHT_TEST_PG_BIN=C:/Program Files/PostgreSQL/17/bin` and `node --experimental-test-isolation=none --test hrms-database/provisioning/company-databases/tests/preflight.test.cjs`. This exercises real SQL, including wrong database, absent registry, missing/duplicate bindings, external FK/trigger/incoming view, missing history, lock state and source registry preservation. It does not run tenant migrations, restore production data, exercise service grants or verify live readiness.

The initial Windows fixture timeout occurred after pg_ctl started the temporary server but inherited captured handles remained open. The fixture was stopped explicitly; the harness now avoids captured pg_ctl handles and checks its owned postmaster.pid during cleanup. The successful run stopped its server normally and retained only synthetic fixture files for diagnosis.

Independent source review found one runbook sequencing issue: final migration exports must follow successful colocated migrations, with a separate rollback backup taken first. Corrected that ordering. The reviewer reported no additional SQL/test correctness or safety findings; this was source review, not production verification.

User-directed follow-up: added `run-local.cjs` to read the existing `hrms-database/.env` and collect the same inventory through an already-open loopback tunnel. Explicit expected-database validation, isolated libpq environment, read-only connection default, exclusive report creation and completion validation are covered by three passing local runner tests. The SQL remains unchanged. No credentials are logged or written into the report. Tunnel forwarding/host identity is supplied by the operator, not independently attested by this wrapper.
