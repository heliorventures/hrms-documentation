# Task 2: Attendance-day backend integration

Status: Task2 local implementation and verification complete, ready for independent review. No commits, migration execution, deployment, emails, live tenant writes, editor/process changes, package installation or Dart/Flutter commands. No owned Cargo process remains active.

Service checkout remains `D:/work/heliorventures/hrms-svc`, branch `codex/hrms-attendance-monthly-summary`. Task1's reviewed uncommitted foundation and unrelated work are preserved. This report distinguishes Task2 edits from the already-dirty foundation.

## Implementation and decisions

- Live punch acquires the tenant policy lock before sorted employee/day locks, then samples its clock. If the active date changes while waiting, it locks the extended date set and samples again, with a bounded conflict retry. Only the resulting immutable current window determines the target work date and timezone. At the exact exclusive end, the old row becomes INCOMPLETE and the same request inserts the new day's OPEN row.
- Expiry updates only status, the `MISSED_PUNCH_OUT` regularization reason and updated-at, plus an audit record. It never sets either checkout field, GPS or worked time. Its guarded SQL checks tenant, employee, original ID, OPEN and both null checkout fields; locked rows are re-read before deciding. The generic `audit_log` receives EXPIRE with before/after metadata and no user actor for this system transition.
- The existing worker calls the bounded sweep with 50 candidates (service clamps 1..100). ATTENDANCE is checked independently of EMPLOYEE using the same entitlement snapshot. Each candidate employee is processed in its own transaction. Failed expiry/audit rolls back and is reported for retry; logs contain only tenant/count/error code, no GPS or employee attendance detail. Existing employee sweep behavior is retained.
- Punch summaries and attendance/list queries derive effective INCOMPLETE without writes, retaining the persisted updated-at revision. Expired rows cannot remain the summary's actionable open segment when the worker is unavailable. Current date defaults are attendance-specific; holidays and timesheet defaults are unchanged.
- Self/managed correction inputs accept a paired actual check-in/out date. Conversion uses the retained window timezone, UTC containment and actual duration. Check-in must be inside the half-open window; checkout can equal its end. Missing actual dates are accepted only when exactly one valid interval exists. Legacy midnight windows retain same-day behavior; long transition ambiguity is rejected with a request for actual dates. Ambiguous/nonexistent local manual timestamps are rejected rather than using the boundary-specific DST rule.
- Canonical overlap checks exclude the original corrected ID, sum actual seconds and preserve the less-than-24-hour cap even in a 25-hour window. Another unfinished row still blocks adding duplicate attendance. Existing SELF authority, employee ownership, calendar-day age limit, managed TEAM/ALL scope, reason length, original ID and expectedUpdatedAt restrictions remain. No new approval process was added. Managed snapshots now represent null checkout and canonical instants, so incomplete originals can use the existing audited update path. Managed updates additionally assert that the employee/source date still match the locked identity.
- All attendance day-lock callers defensively acquire the policy lock first. Managed orchestration wrappers lock before sampling the clock; self writes likewise resolve/validate after locks. Transaction ownership remains with callers; SeaORM rollback-on-drop protects error exits, and worker error paths explicitly roll back.
- Policy/preview/scheduling reuse exact ALL `attendance:punch_policy` authority. Scheduling parses strict HH:mm before persistence, locks before sampling time and invokes Task1's optimistic revision/future/frozen-window/audit transaction. Preview is read-only and uses the same core calendar resolver and authority/revision/future/frozen/continuity checks; scheduling revalidates it when saving.

## Task1 interface use

The initial Task2 integration left the reviewed `calendar.rs` and `repository.rs` unchanged. Review fix round 1 below subsequently consolidates shared proposal/initialization logic inside `repository.rs`; `calendar.rs` remains unchanged. The new `attendance_day/preview.rs`, re-exported from its module, supplies the concrete additional UI requirement:

```rust
pub struct AttendanceDayPolicyPreview {
    pub revision: i64,
    pub transition: AttendanceDayWindow,
    pub following: AttendanceDayWindow,
}
pub async fn preview_policy<C: ConnectionTrait>(
    db: &C, tenant_id: Uuid, clock: TenantBusinessClock,
    claims: &ClientClaims, command: SchedulePolicyCommand, now: DateTime<Utc>,
) -> KabiPayResult<AttendanceDayPolicyPreview>;
```

The public managed-create Rust command now carries `clock: TenantBusinessClock` and `actual_dates: Option<(NaiveDate, NaiveDate)>` in place of precomputed `instants` and `today`, so transaction-owned code performs those decisions after locks. The existing ignored PostgreSQL consumer fixture was adapted and remains unexecuted. The worker facade exports `sweep_expired_attendance(db, tenant_id, clock, limit)` and `ExpirySweepResult { expired, failed }`.

## Exact GraphQL contracts for Task3

New operations (camelCase is the exported schema spelling):

```graphql
attendanceDayPolicy: AttendanceDayPolicy!
attendanceDayWindow(workDate: NaiveDate): AttendanceDayWindow!
previewAttendanceDayPolicy(input: ScheduleAttendanceDayPolicyInput!): AttendanceDayPolicyPreview!
scheduleAttendanceDayPolicy(input: ScheduleAttendanceDayPolicyInput!): AttendanceDayPolicy!

input ScheduleAttendanceDayPolicyInput {
  boundaryTime: String!
  effectiveWorkDate: NaiveDate!
  expectedRevision: Int!
}
type AttendanceDayWindow {
  workDate: NaiveDate!
  startsAt: DateTime!
  endsAt: DateTime!
  timezone: String!
  boundaryMinutes: Int!
}
type AttendanceDayPolicyVersion {
  effectiveWorkDate: NaiveDate!
  boundaryMinutes: Int!
  timezone: String!
}
type AttendanceDayPolicy {
  revision: Int!
  initialized: Boolean!
  legacyActivationPending: Boolean!
  legacyActivationDate: NaiveDate
  currentPolicy: AttendanceDayPolicyVersion!
  pendingPolicy: AttendanceDayPolicyVersion
  currentWindow: AttendanceDayWindow!
}
type AttendanceDayPolicyPreview {
  revision: Int!
  transition: AttendanceDayWindow!
  following: AttendanceDayWindow!
}
```

`attendanceDayWindow` requires scoped attendance:read and exposes no employee data; omit workDate for the active window or provide a historical label for corrections. Settings query and preview require the same ALL authority as scheduling. A normal employee can read window metadata but cannot read/administer policy configuration. Use the exact pendingPolicy.effectiveWorkDate; legacyActivationDate is the original rollout anchor and may differ after an administrator delays a pending activation. Missing legacy profiles are read-only with initialized=false, revision=0, legacyActivationPending=true and no invented activation date.

Existing `punchDaySummary(workDate: NaiveDate)` keeps its operation signature and original fields. It adds non-null `startsAt: DateTime!`, `endsAt: DateTime!`, `timezone: String!`, `boundaryMinutes: Int!` directly on `PunchDaySummary`. Its `workDate` is server-authoritative and can legitimately be the prior calendar date before the boundary. `openSegment` is null after expiry, while its original segment remains present with status INCOMPLETE and null checkout. Keep stale-response ownership protections and refresh at endsAt; do not apply a browser-side 05:00 offset.

All four existing input objects add optional `checkInDate: NaiveDate` and `checkOutDate: NaiveDate`:

- AddManualAttendanceSegmentInput
- UpdateManualAttendanceSegmentInput
- AddManagedAttendanceSegmentInput
- UpdateManagedAttendanceSegmentInput

Both must be supplied together or both omitted. All existing fields, operation names and return types remain. UpdateManagedAttendanceSegmentInput still requires reason and expectedUpdatedAt; self updates still use the original ID and existing SELF authority. Keep `workDate` as the attendance label and display actual date/time inputs independently. Use existing canonical checkInAt/checkOutAt to display completed actual dates and use attendanceDayWindow for allowed historical bounds.

Example correction of the original Sep11 incomplete row:

```graphql
mutation Correct($input: UpdateManualAttendanceSegmentInput!) {
  updateManualAttendanceSegment(input: $input) {
    id workDate checkInAt checkOutAt status updatedAt
  }
}
# input = {
#   id: ORIGINAL_ID, workDate: "2026-09-11",
#   checkInDate: "2026-09-12", checkInTime: "02:00:00",
#   checkOutDate: "2026-09-12", checkOutTime: "04:00:00"
# }
```

Preview and schedule take the same input. Display preview.transition exact startsAt/endsAt/timezone and then schedule with the same expectedRevision. A Conflict requires refreshing policy/preview before resubmission. Preview creates no profile, policy version, frozen window or audit row. No preview result is a persistence reservation.

## TDD and verification evidence

Commands run from `D:/work/heliorventures/hrms-svc`; only one owned Cargo was active at a time.

1. RED `cargo test --offline -p kabipay-attendance --lib attendance_day_expiry`: 1 passed, 1 failed, exit 1, build 43.51s. Exact-end test failed because the initial expiry implementation left the original row OPEN. The preserved-completed-row case passed.
2. RED `cargo test --offline -p kabipay-attendance --lib attendance_day_`: 9 passed, 3 failed, exit 1, build 1m53s. Actual-date correction returned 2026-09-10T20:30:00Z instead of 2026-09-11T20:30:00Z; managed snapshot rejected null checkout; punch used pre-lock 23:29:59Z instead of post-lock 23:30:00Z.
3. RED `cargo test --offline -p kabipay-attendance --test attendance_day_policy attendance_day_preview`: 0 passed, 1 failed, exit 1, build 2m09s. Preview did not enforce the required Forbidden authority boundary before SQL.
4. GREEN `cargo test --offline -p kabipay-attendance attendance_day_`: 12 library + 15 policy/preview proxy tests passed, exit 0, build 3m32s. This preceded the final added worker/read/authority coverage and generated dead-code warnings for not-yet-wired surfaces.
5. Latest focused GREEN `cargo test --offline -p kabipay-attendance --lib attendance_day_`: 19 passed, 0 failed, exit 0, build 52.87s. Covers before/at cutoff, post-lock clock movement, worker idempotency and correction-after-lock, audit-failure retry, write-free effective reads, actual-date overlap/cap/original-ID/age/legacy/ambiguity cases and settings read/preview authority.

The first attempt at expanded proxy fixtures caught two compile mistakes (foreign Arc trait implementation and an omitted type annotation), both corrected before the behavioral RED run. Some earlier Cargo calls queued behind Rust Analyzer's externally owned workspace check. No process was stopped or editor configuration changed by this task. Reported build durations include any such delay and are not benchmarks.

6. Final `cargo test --offline -p kabipay-attendance --lib --tests`: exit 0, build 4m10s, 88 library + 2 backfill-helper unit + 15 policy/preview integration + 1 library-boundary test passed (106 total); 2 explicitly ignored PostgreSQL tests stayed ignored. No compiler warnings in this final run.

7. Production `cargo check --offline -p kabipay-outbox-worker --bin kabipay-outbox-worker`: exit 0, 2m04s, no warnings. This checks the production dependency path without relying on the attendance dev proxy feature.

Two test-fixture assertions/interleavings were tightened during self-review after the full run: the SQL proxy now checks the checkout TIME value is truly null, and the correction commits while the expiry worker acquires its policy lock (after the initial candidate snapshot), rather than simulating a writer inside a held policy lock.

8. Covering `cargo test --offline -p kabipay-attendance --lib attendance_day_runtime`: 7 passed, 0 failed, exit 0, 37.90s, no warnings. This is the latest test evidence for those test-only amendments; production code is unchanged from the full passing suite.
9. Service `git diff --check`: exit 0; only Git's normal LF/CRLF working-copy notices. Cargo.lock diff contains only the new local attendance dependency of the outbox worker.

10. `cargo build --offline -p kabipay-attendance --example export_schema`: exit 0, 21.40s, no warnings. Executing `./target/debug/examples/export_schema.exe` returned exit 0 without database access. Its 14,584-character real SDL output was saved to `D:/work/heliorventures/hrms-documentation/docs/superpowers/reviews/2026-09-11-attendance-day-task2-schema.graphql`. Exported scalar names, settings/window/preview/schedule signatures, paired date inputs and summary metadata match the contracts above. Task3 can use its existing `scripts/generate-attendance-client.mjs --schema-path` support against this file without another Cargo run.

Final result: 106 full-suite tests passed with 2 deliberately ignored PostgreSQL tests, followed by 7/7 covering runtime tests after test-fixture self-review amendments; production worker check and local schema export passed. No final compiler warnings. All local verification requested for this task is complete within the documented execution limits.

## Files changed by Task2

- `hrms-svc/Cargo.lock`: local worker dependency edge only.
- `crates/kabipay-attendance/src/lib.rs`, `src/services/mod.rs`: runtime module/facade registration (preserving Task1 registrations).
- `src/services/attendance_day_runtime.rs` and `attendance_day_runtime_tests.rs`: locking, expiry, bounded sweep, read projection and SQL-boundary regressions.
- `src/services/attendance_day/mod.rs`, new `preview.rs`: read-only settings preview facade.
- `src/services/attendance_service.rs`: current-window punch/summary and locked self corrections.
- `src/services/attendance_regularization_service.rs`: window/actual-date/canonical validation, post-lock managed preparation and nullable canonical audit snapshots.
- `src/resolvers/query.rs`, `mutation.rs`, `types.rs`: additive operations/metadata/date inputs and existing authority regression inventory.
- `tests/attendance_day_policy.rs`: preview regression added to reviewed foundation tests.
- `tests/attendance_management_postgres.rs`: command shape and isolated policy/window fixture tables adapted; ignored tests not run.
- `crates/kabipay-outbox-worker/Cargo.toml`, `src/main.rs`: attendance dependency and independently entitled expiry sweep.
- This report and the exported local SDL artifact.

Attendance summary/report services, canonical duration helper, analytics and payroll were reviewed but did not need speculative changes. Existing reports group by stored work_date and use canonical instants; the analytics attendance report groups its map by row.work_date. The targeted payroll source search found no direct attendance/check-in/worked-minutes consumer. General TenantBusinessClock, leave dates and timesheet periods are unchanged.

## Self-review and limits

- Locks are policy-first across all normal attendance writers found in the service checkout, with re-read and post-lock clock sampling. Duplicate OPEN protection still relies on both this serialized path and the existing database unique OPEN constraint.
- SQL proxy tests exercise real service/calendar code and emitted SQL at the external boundary. They are not PostgreSQL lock/trigger/isolation acceptance. Their in-memory SQL fixture does not claim real rollback semantics; actual transaction rollback/concurrency and migration constraints remain separately authorized tests.
- The two existing PostgreSQL tests remain ignored. Their disposable schema fixture now contains the policy/window tables needed by the real resolver, but does not stand in for migration 0087's trigger/constraint execution.
- No production migration, deployment, gateway composition, browser session or signed-in tenant acceptance was performed. UI integration remains Task3. Release needs matching migration/service/worker/gateway/UI and signed-in acceptance.
- rustfmt is unavailable in this installed Windows toolchain, as established by Task1; no installation or editor/process mutation was attempted. The large existing regularization file was changed within its established orchestration abstraction, without unrelated restructuring.

## Review fix round 1: shared proposal validation

Status: complete. The review's important maintainability finding and minor stale comment are addressed. No commit or live operation; no owned Cargo remains active.

`repository.rs` now owns a shared read-only `propose_policy_change` used by both preview and scheduling. It checks expected revision, active/future date, the earliest affected pending/frozen date, proposed versions, transition continuity and revision increment availability. Common authority/minute validation also has one implementation. `prepare_initialization` computes the legacy activation anchor/default versions once and is reused by proposal validation and ordinary window initialization; `persist_initialization` alone writes that prepared state. Preview no longer reconstructs bootstrap rules independently.

Scheduling still acquires the policy lock, obtains its own current snapshot and rebuilds the proposal under that lock. It does not accept or trust a prior preview. Only after proposal validation does it persist any bootstrap state, compare-and-swap revision, preserve/supersede pending history and audit the actor in the caller's transaction. Preview remains write-free and retains its transient nil policy IDs. Public Rust APIs and GraphQL signatures are unchanged, so the existing SDL artifact remains valid without another export.

The agreement matrix verifies literal transition endpoints and initial revision/anchor behavior for fresh tenants, uninitialized legacy tenants, delayed legacy activation and custom pending replacement. It checks stale revision, active-date and frozen-window rejection in both entry points, including the exact affected-date SQL parameter when replacing a pending version. Existing initialization, snapshot, authority, audit and freezing tests remain in the covering suite.

The new exhausted-revision case exposed a real asymmetry: preview previously accepted `i64::MAX`, while scheduling rejected the increment. The shared proposal now rejects that input consistently. This behavior correction followed observed RED; the already-correct agreement cases were refactored while green rather than introducing artificial failing stubs.

Commands from `D:/work/heliorventures/hrms-svc`:

```text
cargo test --offline -p kabipay-attendance --test attendance_day_policy attendance_day_preview_schedule_agreement
Finished test profile in 58.40s
running 3 tests
attendance_day_preview_schedule_agreement_preserves_bootstrap_and_replacement_intervals ... ok
attendance_day_preview_schedule_agreement_rejects_stale_active_and_affected_frozen_dates ... ok
attendance_day_preview_schedule_agreement_rejects_exhausted_revision ... FAILED
preview and save must reject an exhausted revision; schedule=false
test result: FAILED. 2 passed; 1 failed; 15 filtered out
exit 1

cargo test --offline -p kabipay-attendance --test attendance_day_policy
Finished test profile in 1m 31s
running 18 tests
test result: ok. 18 passed; 0 failed; 0 ignored; 0 filtered out
exit 0
```

The covering run compiled the actual attendance library/consumer and emitted no warnings. Service `git diff --check` also exited 0, with only the normal CRLF conversion notices. The full 106-test suite and worker compile were not repeated because this round changes only shared policy proposal/initialization logic, its tests and one comment; their earlier evidence and PostgreSQL/browser execution limits remain as stated above.

Files amended this round: `src/services/attendance_day/repository.rs`, `src/services/attendance_day/preview.rs`, `tests/attendance_day_policy.rs`, the inaccurate same-calendar-day comment above `add_manual_attendance_segment` in `src/services/attendance_service.rs`, and this report. No module registration, calendar algorithm, schema, migration or UI changes.
