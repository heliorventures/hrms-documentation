# Company database dependency removal implementation plan

> **For agentic workers:** Use superpowers:executing-plans. Continue the approved local implementation and focused checks. Preserve preceding uncommitted work; no commits, .env access or production execution.

**Goal:** Remove tenant integration and timestamp-trigger dependencies on the colocated ops schema, and demonstrate a synthetic schema export/restore into separate company databases.

**Architecture:** Keep one authoritative integration catalog in metadata. New ops migration 0128 makes connector UUIDs durable (soft-disable instead of delete/truncate/ID mutation). New tenant migration 0129 seeds only existing connector IDs into a local reference table, preserves a local FK, and moves timestamp triggers to a reviewed tenant-local helper. Analytics validates active connectors against metadata before atomically adding the local reference and connecting/reconnecting in the company database. No mutable catalog replica is introduced.

**Tech stack:** PostgreSQL forward Liquibase migrations, Rust/SeaORM, Node native PostgreSQL fixture, pg_dump/pg_restore.

**Spec:** Approved separate company databases with shared services; `../../runbooks/company-database-split.md`.

## Constraints and decisions

- Retain IDs, integration credentials/configuration, migration history and trigger semantics. Never rewrite applied changesets.
- Apply ops 0128 and tenant migrations through 0129 while metadata and source tenant schemas are colocated; pending 0110 still requires that layout. Freeze writers until new application code is deployed. Existing old binaries do not populate local connector references.
- Resolve unknown/inactive connectors and metadata failures before company writes. Catalog activation is checked at admission; this is not a distributed transaction or a promise to disconnect existing integrations on catalog deactivation.
- Local references contain only stable IDs, not mutable catalog names/status/configuration. Raw SQL/privileged maintenance must follow the same authoritative validation contract; runtime grants restrict reference-table mutation to required SELECT/INSERT.
- Reject unknown helper behavior and unsupported trigger forms rather than changing their behavior silently. Preserve trigger names, conditions, enable modes and comments.
- This phase proves synthetic dependency removal/export/restore only. Full production-backup restore, Liquibase history/checksum acceptance, remaining migrations, TLS/CDC and business workflows remain later gates.

## Tasks

- [x] Write failing native SQL/export/restore regressions for catalog identity, preserved data, local FK rejection, timestamp behavior and absence of ops dependencies after restore.
- [x] Implement 0128/0129 forward migrations and register them in the ops/tenant master changelogs.
- [x] Write failing Rust tests for unknown/inactive/unavailable metadata, correct ops-versus-company routing, atomic reconnect/upsert and preserved secret/config fields; implement the Analytics write path in a focused module.
- [x] Run focused Rust and native SQL checks, independent source review and update the runbook with rollout order, grants and precise acceptance limits.

## Review focus

Catalog IDs must survive central deletion attempts; historical inactive connectors must survive migration. Concurrent connects must not duplicate tenant integrations or overwrite credentials/configuration. Metadata failures must not fall back to locally cached IDs. Trigger reconstruction must preserve disabled/replica/always modes and comments and reject unsupported/custom helpers. New future tenant migrations must use the local helper. An isolated restored company schema must work without kabipay_ops tables/functions.

## Execution record

Analytics currently lists the central catalog through ops_db, but its connect mutation passes only tenant_db and relies on the cross-schema FK. This is the application caller that must change. Current helper migration defines the same NOW()/NEW.updated_at behavior supplied in the production evidence. Existing tenant migration history ends at 0109; the upcoming dependency migration will be appended after 0125, with ops 0128 first. Separate retirement changelogs 0126/0127 remain separate.

Implemented the forward migrations, updated the sole connect resolver caller and removed the superseded service function. Added SeaORM proxy tests and the owned-cluster PostgreSQL rehearsal. Initial RED checks demonstrated missing migration files and the missing Rust implementation before implementation. Test assertions were corrected for PostgreSQL's FK-before-TRUNCATE guard, internal char casting and the actual missing GiST operator-class diagnostic.

Verification: `cargo test -p kabipay-analytics --bin kabipay-analytics` passed 22 tests, including a final rerun. Native `dependencies.test.cjs` passed on PostgreSQL 17 initially in 61 seconds and after review fixes in 70 seconds; final retained stopped fixture `D:/work/heliorventures/.codex-tmp/hrms-shared-grants-NRwroN`. Both master changelogs and both new XML files parsed successfully. `git diff --check` passed in database, service and documentation repositories. No .env, production connection, full Liquibase run, release-image build/deploy or commit was performed in this phase.

Independent source review followed a dedicated GPT 6.1 sol summary. All three P2 findings were reproduced together (all three regression flags false) before fixing them; the final native rehearsal passed with all three true:

- Final: fixed session-dependent trigger deparsing by setting transaction-local `search_path=pg_catalog`; a caller with `kabipay_ops` visible now migrates successfully.
- Final: fixed alteration of matching text inside trigger conditions by replacing only the terminal function invocation; the regression preserves an identical string literal through migration and restore.
- Final: fixed acceptance of unreviewed helper settings by requiring `proconfig IS NULL`; configured helpers now stop for review instead of silently changing behavior.

No unresolved source findings remain from the scoped review. Actual PostgreSQL 16/Liquibase/full-backup acceptance, new empty company bootstrap, capacity/TLS and CDC/private-history handoff remain rollout gates rather than claims established by this synthetic fixture.
