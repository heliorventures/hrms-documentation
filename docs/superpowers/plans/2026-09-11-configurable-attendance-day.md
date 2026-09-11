# Configurable Attendance Day Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task. Review each completed task before its dependent implementation.

**Goal:** Apply one tenant-configurable, future-effective attendance day consistently without changing history or inventing checkout time.

**Architecture:** An attendance-owned policy/window service resolves immutable UTC windows. Existing punch, adjustment, report and UI flows consume its work date and bounds; the generic tenant calendar remains unchanged. Worker cleanup persists expiry, while reads and mutations enforce the same cutoff even if that worker is late.

**Tech Stack:** Rust/SeaORM/GraphQL, Liquibase, React/TypeScript, Cargo offline tests and Vitest.

**Spec:** ../specs/2026-09-11-configurable-attendance-day-design.md (approved by user).

## Global Constraints

- Tenant-specific, admin-configurable attendance start time; default 05:00 in the tenant timezone.
- A normal day labelled D spans [D at the configured time, D+1 at that time).
- A punch still open at its day end is INCOMPLETE, not automatically punched out.
- Configuration changes apply only to future attendance days. Historical records and the active day's boundaries cannot be reinterpreted by a later setting change.
- Preserve unrelated work. No commits, deployments, migration execution, emails, live writes, MFA/login changes or Dart/Flutter commands.
- Keep the existing feature checkouts and their dependency caches. No branch/worktree mutation, reset, clean or automatic installs. No parallel Cargo runs.
- Store new schema only in hrms-database. Existing attendance rows are never bulk rewritten.
- Keep evidence in documentation: no test/compile result implies applied schema or runtime proof.

## Task 1: Policy, window mathematics and persistence

**Files:** Create services/attendance_day/{mod.rs,calendar.rs,repository.rs,tests.rs} in kabipay-attendance; register from services/mod.rs. Create hrms-database/changelog/migrations/0087_attendance_day_boundary/attendance_day_boundary.xml after checking that 0087 remains free; update tenant master and generate corresponding d0087 entities. Add offline persistence tests under kabipay-attendance/tests/attendance_day_policy.rs and a database structural contract script.

**Produces:** `AttendanceDayWindow { work_date: NaiveDate, starts_at: DateTime<Utc>, ends_at: DateTime<Utc>, timezone: String, boundary_minutes: i32 }`; tenant-scoped policy versions with optimistic revision, future effective work date and one pending replacement. Expose read-only `window_for_date(db, tenant_id, clock, work_date, now)` and `current_window(db, tenant_id, clock, now)`, transaction-owned `ensure_window(db, tenant_id, clock, work_date, now)`, plus policy query/schedule repository methods. Publish exact Rust signatures in the task report before dependent work.

- [x] Write failing pure tests before implementation. Literal fixtures: Kolkata 2026-09-11T23:29:59Z belongs to work date Sep11; at 23:30Z belongs to Sep12. A normal Sep11 window is Sep10T23:30Z..Sep11T23:30Z. For 05:00->06:00 effective Sep12, Sep12 starts Sep11T23:30Z and ends Sep13T00:30Z (25h); 05:00->04:00 ends Sep12T22:30Z (23h). Active Sep11 never changes.
- [x] Run `cargo test --offline -p kabipay-attendance attendance_day` and record the expected missing-behavior failure. Use injectable clocks in pure/test boundaries, never global test clocks in production.
- [x] Implement validated minute-of-day parsing, effective-date version selection, explicit transition windows and deterministic DST resolution (earlier repeated instant, first valid skipped instant). Reject nonincreasing windows and overflow. Preserve historical timezone/version in frozen windows.

```rust
// Consumer-visible invariant; expected instants in tests are literal, not calculated by this helper.
assert!(window.starts_at <= instant && instant < window.ends_at);
assert_eq!(previous.ends_at, next.starts_at);
```

- [x] Implement tenant-qualified policy/window persistence, uniqueness/check constraints and consistent tenant-policy lock. Initialize durable activation once in a write transaction: existing historical data keeps legacy midnight semantics through its active day; a future transition adopts 05:00. Fresh tenants start at 05:00. Reads never seed or persist rows. Before initialization, read fallback must agree with the eventual write initialization and explicitly expose legacy/pending activation, not silently apply 05:00 to history.
- [x] New attendance days freeze their UTC bounds/version when mutated. Scheduling rejects changes to past, active or already-frozen affected windows, compares expected revision, and audits policy edits using existing audit infrastructure. Preserve historic versions when replacing one still-future pending setting.
- [x] Generate entities only from the new database migration. Run focused pure/persistence tests and XML/generator checks; do not apply migrations. Write report with RED/GREEN evidence and exact public interfaces for Task2.

## Task 2: Backend consumers, expiry, adjustments and API

**Files:** attendance_service.rs, attendance_summary_service.rs, attendance_duration.rs, attendance_regularization_service.rs, attendance_management_service.rs, resolvers/{query,mutation,types}.rs; focused new attendance_day expiry/adjustment modules; kabipay-outbox-worker/{Cargo.toml,src/main.rs}; existing offline attendance tests. Inspect analytics/payroll attendance consumers and change only actual calendar-date reinterpretation defects.

**Consumes:** Task1 immutable window and policy repository interfaces. **Produces GraphQL:** `attendanceDayPolicy`, `scheduleAttendanceDayPolicy(input)` (time HH:mm, future effectiveWorkDate, expectedRevision); summary window metadata (startsAt, endsAt, timezone, boundaryMinutes). Existing summary/segment signatures remain compatible via additive metadata. Publish final DTO/operation shapes for Task3.

- [x] Add failing boundary-punch and expiry tests: at exactly end, prior OPEN becomes INCOMPLETE with null checkout and no worked-minute credit; the same request creates a new day's OPEN segment. Assert post-lock clock use, one open row, preserved completed records and correction-vs-expiry atomicity.
- [x] Integrate policy-first then employee/date locks in all writers. Re-read clock and locked rows before decisions. Expiry changes status/reason/audit only. Current and historical reads derive effective INCOMPLETE without writes; old OPEN must never remain actionable when worker is unavailable.
- [x] Add an idempotent bounded worker sweep under attendance entitlement; skip completed/corrected rows, retry failures without logging GPS or attendance personal detail. Mutations retain enforcement when worker is delayed.
- [x] Add failing adjustment tests with actual calendar-date inputs: Sep11 work date allows Sep12 02:00->04:00; rejects checkout after window end, overlapping intervals, excess worked hours, unauthorized employee edits and stale approval. Correct original incomplete segment without duplicate time. Retain original legacy interpretation when no new window applies.
- [x] Wire settings query and mutation using exact existing admin ALL authority; respondent summary may read boundary metadata but cannot schedule. Validate HH:mm/revision/date before persistence; use policy repository transaction for concurrent edits and metadata audit.
- [x] Review attendance lists, summary/report grouping and payroll inputs. Keep grouping by stored work_date; use canonical instants for durations. Do not globally change TenantBusinessClock or leave/timesheet periods.
- [x] Run focused Cargo regressions, then attendance library/integration suites once and worker production compile. Export local schema using existing attendance example. Report exact contracts and acceptance limits.

## Task 3: Settings, dashboard, adjustment UI and contracts

**Files:** existing admin/attendance-policy page (resolve current route import), dashboard/components/PunchInOut.tsx and attendance summary types/query; attendance editor/hooks/components and generated attendance client; focused policy/day-boundary helpers/components/tests. Do not restructure unrelated pages.

**Consumes:** Task2 final GraphQL shapes and server-authoritative window endpoints. **Produces:** configurable policy UI, safe rollover and actual-date correction payloads through existing screens.

- [x] Write failing UI tests for admin policy load/schedule confirmation/revision conflict and permission denial; current vs scheduled policy and exact transition interval shown in tenant timezone.
- [x] Implement settings form with time, future effective date, expected revision, preview and confirmation. Preserve pending input on failure; reload conflict rather than overwriting; do not issue unauthorized operations.
- [x] Write failing dashboard tests for a pre-05:00 instant belonging to yesterday, exact-end invalidation, replacement summary loading, worker-late INCOMPLETE and StrictMode. Replace browser calendar-date ownership with server work date/window; block stale punch actions and invalidate identity-owned state on tenant/user/scope changes.
- [x] Implement rollover timer against endsAt; revalidate on focus/visibility resume. A stale summary response must not enable an expired day. Display attendance work date and local window while retaining actual clock/calendar date clarity.
- [x] Write failing adjustment tests for overnight actual dates, correcting original INCOMPLETE ID, validation messages, and retained approval restrictions. Implement actual date/time selectors and canonical payload conversion using tenant timezone/history metadata, not browser timezone or midnight guesses.
- [x] Regenerate/validate attendance operations against the local exported schema. Run focused tests, scoped lint and UI typecheck. No signed-in mutation or live tenant validation.

## Task 4: Independent integration review and handoff

- [x] Review spec compliance and quality after each task using its report and exact scoped diff, without repeated builds on unchanged code. Fix concrete findings with covering regression tests.
- [x] Final review checks multi-tenant locks, historical activation semantics, no credit on expiry, adjustment authority, API compatibility, UI stale-state ownership, payroll/report grouping and migration ownership.
- [x] Record final commands/results and unresolved runtime acceptance in a final verification record; update the remaining-work handoff. Leave existing dirty files and all changes available for manual review; no commits or cleanup that removes evidence.
