# Attendance Punch Root-Cause and Integrity Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reproduce the fresh punch failure deterministically, repair the evidenced cause at the correct layer, and close the already-confirmed legacy `OPEN` attendance integrity gap without creating real attendance records during diagnosis.

**Architecture:** A disposable PostgreSQL schema and focused service tests exercise the same resolver-to-service-to-transaction path as the UI, with and without GPS. Structured error IDs identify the failing stage without exposing employee or location data. A separate Liquibase migration quarantines legacy invalid `OPEN` rows and strengthens the database invariant. The production repair is selected only from captured evidence, not from the generic UI message.

**Tech Stack:** Rust, SeaORM, async-graphql, PostgreSQL advisory locks, Liquibase XML, PowerShell migration checks, React, TypeScript, Vitest.

**Spec:** `docs/superpowers/specs/2026-08-26-canonical-rbac-authorization-design.md` (attendance diagnosis boundary)

## Global Constraints

- Do not create, update, or delete live attendance records without explicit user approval.
- Do not treat the generic React message as a diagnosis. Capture GraphQL `extensions.code` and `errorId`, then correlate the server-side error.
- Do not log JWTs, usernames, employee IDs, names, coordinates, IP addresses, database URLs, or raw SQL parameter values.
- Keep authorization remediation in the canonical RBAC plan. `attendance:punch_self` is already present for the affected user and is not the confirmed cause of the fresh punch failure.
- Do not commit or alter unrelated dirty files.
- The root-cause repair task must be written against the observed failing test before implementation proceeds past the evidence checkpoint.

---

## Task 1: Add disposable-schema tests for a truly fresh punch

**Files:**

- Modify: `hrms-svc/crates/kabipay-attendance/tests/attendance_management_postgres.rs`
- Reference: `hrms-svc/crates/kabipay-attendance/src/services/attendance_service.rs`
- Reference: `hrms-svc/crates/kabipay-attendance/src/services/attendance_regularization_service.rs`

- [ ] Extend the existing explicitly ignored PostgreSQL harness to create the complete minimum attendance schema needed by `punch_today`, including policy lookup, attendance instant columns, indexes, constraints, and advisory-lock behavior.
- [ ] Add `fresh_first_punch_without_gps_creates_one_open_segment`: no prior rows for the employee; assert one `OPEN` row with matching tenant/employee, business work date, non-null `check_in_time` and `check_in_at`, null checkout fields, and source `WEB`.
- [ ] Add `fresh_first_punch_with_gps_creates_one_open_segment`: use boundary-safe WGS84 values with more than seven fractional digits; assert persisted values are valid for `NUMERIC(10,7)` and source `WEB+GPS`.
- [ ] Add `fresh_punch_rolls_back_when_any_stage_fails`: inject or provoke each database stage failure and assert no partial attendance row remains.
- [ ] Add `concurrent_fresh_punches_leave_one_open_segment`: start two calls for the same employee/date and assert the lock serializes them into one check-in followed by one check-out, or into the explicitly documented outcome.
- [ ] Run only these ignored tests against an explicitly approved disposable PostgreSQL database:

```powershell
cargo test -p kabipay-attendance --test attendance_management_postgres fresh_first_punch -- --ignored --nocapture
cargo test -p kabipay-attendance --test attendance_management_postgres concurrent_fresh_punches -- --ignored --nocapture
```

Run from: `hrms-svc`

## Task 2: Make the punch failure diagnosable without exposing sensitive data

**Files:**

- Modify: `hrms-svc/crates/kabipay-attendance/src/resolvers/mutation.rs`
- Modify: `hrms-svc/crates/kabipay-attendance/src/services/attendance_service.rs`
- Modify: focused Rust tests in the same modules

- [ ] Add a test that an internal/database punch failure returns a stable public code and `errorId` while the response omits raw database and location details.
- [ ] Add a small internal `PunchStage` enum covering policy load, policy validation, transaction begin, employee/date lock, open-row lookup, insert/update, commit, and post-commit reload.
- [ ] Add structured tracing at the resolver/service boundary containing only operation `attendance.punch_today`, tenant ID, request/error ID, stage, and stable error category.
- [ ] Preserve the original `KabiPayError` source so `DATABASE_ERROR`, `VALIDATION_ERROR`, and `FORBIDDEN` remain distinguishable; do not convert everything to `INTERNAL_ERROR`.
- [ ] Ensure success logs do not include coordinates or IP addresses.
- [ ] Run focused tests:

```powershell
cargo test -p kabipay-attendance punch
cargo test -p kabipay-common error::tests
```

Run from: `hrms-svc`

## Task 3: Capture the exact failing branch without writing live attendance

**Files:**

- No source modification required unless Task 2 instrumentation is not yet present.

- [ ] Reproduce through the disposable integration test using the affected tenant's schema shape, timezone, policy shape, and coordinate precision, but generated tenant/user/employee IDs.
- [ ] Compare GPS-on and GPS-off results to isolate location parsing/storage from the core transaction.
- [ ] Capture the failing test name, `extensions.code`, `errorId`, `PunchStage`, PostgreSQL SQLSTATE, and constraint name when present.
- [ ] Confirm the schema has run migrations 0065 and 0066 and compare actual attendance column types, constraints, and indexes to the changelog.
- [ ] At this checkpoint, write the exact failing assertion and evidenced cause into this plan's Task 4 before changing production logic. Do not proceed with a speculative repair.

## Task 4: Implement the evidenced fresh-punch repair

**Files:**

- Modify only the source/migration files implicated by Task 3 evidence.
- Test first in `hrms-svc/crates/kabipay-attendance/tests/attendance_management_postgres.rs` or the closest unit-test module.

- [ ] Convert the Task 3 reproduction into a permanent failing regression test that asserts the required user-visible and database outcome.
- [ ] Record the exact root cause, failing stage, SQLSTATE/constraint or Rust error variant, and chosen invariant in this task before implementation.
- [ ] Implement the repair at the owning layer: input normalization for invalid external values, service transaction logic for ordering/concurrency faults, Liquibase for schema/data invariants, or deployment configuration for schema drift. Do not add bypasses around permission checks, constraints, or transactions.
- [ ] Verify the main path and the rare branch that exposed the failure.
- [ ] Run the new regression test twice: once alone and once with the full `kabipay-attendance` suite.

```powershell
cargo test -p kabipay-attendance --test attendance_management_postgres fresh_first_punch_with_gps_matches_deployed_schema_contract -- --ignored --nocapture
cargo test -p kabipay-attendance
```

Run from: `hrms-svc`

## Task 5: Quarantine invalid legacy `OPEN` rows and strengthen the invariant

**Files:**

- Create: `hrms-database/changelog/migrations/0068_attendance_open_integrity/attendance_open_integrity.xml`
- Modify: `hrms-database/changelog/tenant.changelog-master.xml`
- Create: `hrms-database/scripts/test-attendance-open-integrity-migration.ps1`
- Modify: `hrms-svc/crates/kabipay-attendance/tests/attendance_management_postgres.rs`

- [ ] Add a failing static migration test requiring singleton legacy rows with `status='OPEN'` and missing `check_in_at` or `check_in_time` to be audited and changed to `INCOMPLETE`.
- [ ] Add an integration test proving an old malformed open row cannot block a new valid punch after migration 0068.
- [ ] In migration 0068, write affected row IDs and reason codes to `attendance_instant_backfill_audit` before changing status.
- [ ] Quarantine malformed `OPEN` rows as `INCOMPLETE`; do not invent punch instants.
- [ ] Replace `uq_attendance_one_open` with a predicate that represents a valid open segment: `status='OPEN'`, both check-in representations present, and both checkout representations absent.
- [ ] Add a check constraint requiring every future `OPEN` row to contain `check_in_time` and `check_in_at`, and no checkout value.
- [ ] Include migration 0068 after canonical RBAC migration 0067. Keep the migrations separate so RBAC deployment and attendance integrity are independently auditable.
- [ ] Run migration checks:

```powershell
pwsh -NoProfile -File .\scripts\test-attendance-time-migration.ps1
pwsh -NoProfile -File .\scripts\test-attendance-open-integrity-migration.ps1
```

Run from: `hrms-database`

## Task 6: Give the UI actionable punch feedback while retaining loaded state

**Files:**

- Modify: `hrms-ui/src/utils/graphqlUserMessage.ts`
- Modify: `hrms-ui/src/utils/graphqlUserMessage.test.ts`
- Modify: `hrms-ui/src/modules/dashboard/components/PunchInOut.tsx`
- Modify: `hrms-ui/src/modules/dashboard/components/PunchInOut.test.tsx`

- [ ] Add tests for every stable public code produced by the evidenced repair, including conflict, validation, permission, tenant database unavailable, and unknown internal failure.
- [ ] Map stable codes to domain guidance: retry a transient conflict, correct invalid location/policy input, contact HR for missing punch permission, and retry later for tenant-database unavailability.
- [ ] Display `errorId` for internal/database failures so support can correlate logs, without displaying raw server details.
- [ ] Preserve the last loaded attendance summary after mutation or refresh failure and keep duplicate punch submission disabled while a mutation is pending.
- [ ] Ensure permission-gated rendering from the RBAC plan suppresses the punch mutation entirely when `attendance:punch_self` is absent.
- [ ] Run focused UI tests:

```powershell
npm test -- src/utils/graphqlUserMessage.test.ts src/modules/dashboard/components/PunchInOut.test.tsx
```

Run from: `hrms-ui`

## Task 7: Final verification without touching live data

**Files:**

- No additional source files expected.

- [ ] Run Rust formatting/checks and attendance tests:

```powershell
cargo fmt --all -- --check
cargo test -p kabipay-attendance
```

- [ ] Run database static migration checks and UI focused tests from Tasks 5 and 6.
- [ ] Apply migrations to a disposable tenant and verify first punch, checkout, second punch, GPS on/off, timezone boundary, malformed legacy row, and concurrent calls.
- [ ] Confirm no live tenant attendance row was created during diagnosis.
- [ ] Request separate approval before applying migrations or retesting a real punch against the Helior Prd tenant.
- [ ] Inspect uncommitted/staged changes separately and do not commit:

```powershell
git diff --check
git diff --stat
git diff --cached --stat
git status --short
```

Run in each modified repository.
