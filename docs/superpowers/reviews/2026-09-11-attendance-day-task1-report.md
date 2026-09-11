# Attendance-day foundation: Task 1

Status: Task 1 foundation complete and ready for independent review. Final combined verification passed: 7 calendar + 13 persistence tests (20 total). No commit, database migration application, deployment or live data operation.

Checkouts retained: service `codex/hrms-attendance-monthly-summary` at `62092ac5b72f34e26844e2a392d7feb391936ee0`; database `codex/leave-queue-index` at `e4f6d4d4c1a8c7857a1e65c93eff1439ff070c51`. Existing database README, migration README and Solvian seed files remain untouched.

## Consumer contract

Public facade: `kabipay_attendance::attendance_day` (within attendance crate: `crate::services::attendance_day`).

```rust
pub struct AttendanceDayWindow {
    pub work_date: chrono::NaiveDate,
    pub starts_at: chrono::DateTime<chrono::Utc>,
    pub ends_at: chrono::DateTime<chrono::Utc>,
    pub timezone: String,
    pub boundary_minutes: i32,
    pub policy_version_id: uuid::Uuid,
}
pub struct PolicyVersion {
    pub id: uuid::Uuid,
    pub effective_work_date: chrono::NaiveDate,
    pub boundary_minutes: i32,
    pub timezone: String,
}
pub struct AttendanceDayPolicy {
    pub revision: i64,
    pub initialized: bool,
    pub legacy_activation_pending: bool,
    pub legacy_activation_date: Option<chrono::NaiveDate>,
    pub versions: Vec<PolicyVersion>,
}
pub struct SchedulePolicyCommand {
    pub expected_revision: i64,
    pub effective_work_date: chrono::NaiveDate,
    pub boundary_minutes: i32,
}

pub fn parse_boundary_minutes(value: &str) -> KabiPayResult<i32>;
pub fn resolve_window(versions: &[PolicyVersion], work_date: NaiveDate) -> KabiPayResult<AttendanceDayWindow>;
pub fn resolve_current_window(versions: &[PolicyVersion], now: DateTime<Utc>) -> KabiPayResult<AttendanceDayWindow>;
pub async fn policy<C: ConnectionTrait>(db: &C, tenant_id: Uuid, clock: TenantBusinessClock, now: DateTime<Utc>) -> KabiPayResult<AttendanceDayPolicy>;
pub async fn window_for_date<C: ConnectionTrait>(db: &C, tenant_id: Uuid, clock: TenantBusinessClock, work_date: NaiveDate, now: DateTime<Utc>) -> KabiPayResult<AttendanceDayWindow>;
pub async fn current_window<C: ConnectionTrait>(db: &C, tenant_id: Uuid, clock: TenantBusinessClock, now: DateTime<Utc>) -> KabiPayResult<AttendanceDayWindow>;
pub async fn lock_policy(db: &DatabaseTransaction, tenant_id: Uuid) -> KabiPayResult<()>;
pub async fn ensure_window(db: &DatabaseTransaction, tenant_id: Uuid, clock: TenantBusinessClock, work_date: NaiveDate, now: DateTime<Utc>) -> KabiPayResult<AttendanceDayWindow>;
pub async fn schedule_policy(db: &DatabaseTransaction, tenant_id: Uuid, clock: TenantBusinessClock, claims: &ClientClaims, command: SchedulePolicyCommand, now: DateTime<Utc>) -> KabiPayResult<AttendanceDayPolicy>;
```

All errors use existing `kabipay_common::KabiPayResult`/`KabiPayError`. Clock is passed by value (Copy); timestamps are explicit. Reads do not initialize or freeze rows. Consumers should begin a transaction, acquire `lock_policy`, acquire employee/day locks in the established deterministic order, then sample their injected/system clock. Pass that post-lock instant to current-window selection, ensure/freeze and punch/expiry mutations. `ensure_window` and scheduling also acquire the same transaction advisory lock defensively; no function commits its caller's transaction. Roll back the transaction on any error.

Settings writes enforce the claim tenant, exact `attendance:punch_policy` permission and explicit `ALL` scope. Actor is `claims.sub`; upstream token verification, current authority and tenant database resolution remain existing resolver responsibilities.

Policy versions retain timezone snapshots. Changing the general tenant timezone alone does not reinterpret an existing attendance policy; scheduling a new attendance policy captures the supplied tenant clock timezone. Frozen windows always win over policy resolution.

Uninitialized reads expose `revision=0`, `initialized=false`, nil transient version IDs, and legacy midnight for tenants with attendance (including deleted historical attendance). Fresh tenants read 05:00. A missing legacy profile is explicitly `legacy_activation_pending=true`; no future activation date is invented on reads. Initialization durably records the original next-local-calendar-date anchor. Initial legacy transition starts at that date's midnight and ends on the following date at 05:00. Existing historical work dates are untouched.

Root ruling: the initial automatic pending activation is replaceable under the same optimistic revision, future-day and frozen-window rules as any later pending version, at the same or a later future effective date. Its original version remains as superseded history; the original profile anchor is retained. The UI must display the actual pending version's effective date, not assume the original anchor is still its effective date. An administrator may intentionally delay activation. There is only one live future version after a scheduling write.

## Evidence so far

- Checked 0087 was free before allocation.
- Structural contract RED: missing migration XML failed the script as expected.
- Structural contract GREEN: migration XML table/tenant-key/composite-reference/master checks passed.
- Scoped generator ran with `--only 0087_attendance_day_boundary`; no unrelated entity regeneration.
- Calendar RED used an isolated harness compiling the exact production `calendar.rs` and `tests.rs`: six positive scenarios failed with explicit missing-behavior errors; the rejection scenario passed because the initial stub rejected everything. The harness substitutes only the common error enum/result alias, not calendar behavior. Adjacent valid-case tests prevent blanket rejection from passing GREEN.
- Calendar GREEN: isolated harness 7/7, then full real-crate `cargo test --offline -p kabipay-attendance attendance_day` 7/7 (70 existing library tests filtered), exit 0. Initial cold compile took 30m58s with project `build.jobs=1`.
- The initial Cargo metadata snapshot preceded addition of the new integration target/dev proxy feature, so it did not discover persistence tests. Targeted `cargo test --offline -p kabipay-attendance --test attendance_day_policy` then compiled successfully with finalized metadata and established repository RED: 0 passed, 13 failed for explicit missing-behavior stubs or absent expected Forbidden/Conflict/Database errors. Cargo reported 281m19s elapsed including external lock delay and a tool wall-time anomaly; this is reported build output, not a clean compile-duration benchmark.
- The repository implementation followed observed RED. Targeted GREEN passed 13/13, exit 0, in reported 6m32s including initial lock wait. Earlier competing checks were identified read-only as Rust Analyzer children and released naturally; a later check held the build lock until the user stopped Rust Analyzer. The agent did not stop processes or change editor settings.
- Final combined `cargo test --offline -p kabipay-attendance attendance_day` passed with exit 0: 7 calendar tests + 13 persistence tests, 0 failures, reported build time 3m10s. Existing unrelated library tests (70) and PostgreSQL tests were filtered. No Cargo run remains owned by this task.
- Service and database `git diff --check` both exited 0; only normal CRLF conversion warnings were emitted.
- Entity generator unit suite: 2/2 passed. Initial sandbox execution failed writing temporary fixture directories; the same focused command passed with approved escalation. Scoped generator and XML checks passed without escalation. Generated Python bytecode files were removed.
- `rustfmt` is unavailable in the installed stable Windows toolchain; no alternate installed formatter was found and no installation was attempted.

Isolated harness commands (from `D:/work/heliorventures`, artifact hashes are local to this run):

```powershell
rustc --test --edition=2021 .codex-tmp/attendance-day-calendar-harness.rs --extern chrono=hrms-svc/target/debug/deps/libchrono-39c63af6d17852e6.rlib --extern uuid=hrms-svc/target/debug/deps/libuuid-43dd899b31a8a34d.rlib -L dependency=hrms-svc/target/debug/deps -o .codex-tmp/attendance-day-calendar-tests.exe
& ./.codex-tmp/attendance-day-calendar-tests.exe attendance_day
# GREEN adds chrono-tz for the implemented calendar algorithm:
rustc --test --edition=2021 .codex-tmp/attendance-day-calendar-harness.rs --extern chrono=hrms-svc/target/debug/deps/libchrono-39c63af6d17852e6.rlib --extern uuid=hrms-svc/target/debug/deps/libuuid-43dd899b31a8a34d.rlib --extern chrono_tz=hrms-svc/target/debug/deps/libchrono_tz-b81ea4225996ceda.rlib -L dependency=hrms-svc/target/debug/deps -o .codex-tmp/attendance-day-calendar-tests.exe
& ./.codex-tmp/attendance-day-calendar-tests.exe attendance_day
```

Real PostgreSQL constraint execution, concurrency, migration application and signed-in acceptance remain unverified and outside this task's execution authority.

## Implementation self-review

- Read-only policy revision and live versions are fetched in one SQL statement/MVCC snapshot. LEFT JOIN makes a profile missing its versions fail closed instead of falling back to a fresh tenant. Every statement is tenant-qualified, including joins, updates, frozen-window lookup and audit.
- The advisory lock namespace is `attendance-day-policy:{tenant_id}`, hashed with PostgreSQL `hashtextextended(..., 0)`. It is distinct from existing employee/day attendance locks. Mutation callers must acquire it before employee/day locks and sample `now` afterward; repeated acquisition in the same transaction is defensive and does not release ownership.
- Initialization is private and reachable only through transaction-owned ensure/schedule paths. Existing attendance, including deleted historical rows, selects a midnight baseline. The next local date anchor and automatic 05:00 version are written once. Fresh tenants have one 05:00 baseline version. Existing frozen windows return immediately without reinitialization or rewriting.
- Window freezing uses the real policy algorithm and verifies any frozen previous/next window endpoints before insertion. SQL uniqueness and a composite `(tenant_id, policy_version_id)` reference protect ownership; database triggers prevent window mutation and preserve activation/version history.
- Scheduling checks exact claims permission plus explicit ALL scope and claim tenant before any SQL, validates minute bounds, takes the same lock, compares expected revision and rejects active/past work dates. It rejects any frozen date at or after the earliest changed pending date (conservative when replacement dates differ), validates the transition and following window, compares-and-swaps revision, supersedes old pending rows without deletion, inserts the new version and writes before/after state and actor into existing `audit_log` in the same transaction.
- On any repository error, including audit failure, the caller must roll back its transaction. These functions deliberately do not commit or roll back an externally owned transaction. Proxy tests verify SQL boundaries and error propagation, not PostgreSQL locking or trigger execution.
- General `TenantBusinessClock`, punch/adjustment/report resolvers, workers and UI are untouched. Foundation integration and release coordination remain dependent work; these changes alone do not change live punch behavior.

## Handoff

Task 2 can consume the public API above after independent review. Preserve lock order and post-lock sampling, roll back on every repository error, and use immutable windows for historical adjustment validation. Queries must keep the read-only functions; only mutation/worker transactions may call `ensure_window` or scheduling.

Local verification is complete for this foundation. Remaining execution limits are real PostgreSQL migration/constraint/concurrency tests, formatter availability, and the deliberately separate resolver/worker/UI integration and signed-in acceptance. Do not infer deployment readiness from the proxy tests.

## Review fix round 1: consistent bootstrap read snapshot

Independent review identified a READ COMMITTED race in the original missing-profile fallback. The profile/version SELECT could observe an uninitialized fresh tenant, then a bootstrap transaction could commit a 05:00 profile and first attendance row before the separate attendance-existence SELECT. Combining those snapshots incorrectly selected legacy midnight. At `2026-09-11T21:30:00Z` (03:00 local September 12 in Kolkata), the old code returned work date September 12; both consistent before/after bootstrap states require September 11.

The repository now retrieves attendance existence, nullable profile state and live versions in one SELECT. A scalar existence row survives a missing profile; nullable revision distinguishes that state. An existing profile without valid live versions still fails closed. Reads remain write-free, all tenant predicates remain parameterized, and public interfaces are unchanged. Existing proxy fixtures now mirror the unified row shape.

The new regression executes the real repository through a SQL-boundary proxy. Its first statement observes a snapshot, then the fixture commits the bootstrap state before any second statement. It verifies both pre-bootstrap and already-committed snapshots, literal work date and UTC bounds, and one read-only SQL statement. This verifies the repository boundary; it does not claim a real PostgreSQL concurrency test.

RED command, run from `D:/work/heliorventures/hrms-svc` before the repository change:

```powershell
cargo test --offline -p kabipay-attendance --test attendance_day_policy attendance_day_bootstrap_interleaving_keeps_one_consistent_read_snapshot
```

Observed output (exit 1; build 22.39s):

```text
running 1 test
attendance_day_bootstrap_interleaving_keeps_one_consistent_read_snapshot ... FAILED
assertion `left == right` failed
  left: 2026-09-12
 right: 2026-09-11
test result: FAILED. 0 passed; 1 failed; 13 filtered out
```

Covering GREEN command after the change:

```powershell
cargo test --offline -p kabipay-attendance --test attendance_day_policy
```

Observed output (exit 0; build 58.43s):

```text
running 14 tests
attendance_day_bootstrap_interleaving_keeps_one_consistent_read_snapshot ... ok
test result: ok. 14 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out
```

Round 1 is complete. Only the repository read, its targeted persistence fixtures/regression and this report changed. No additional Cargo run remains active, and no commit, deployment, migration execution or live write occurred. The original combined 20-test verification above predates this review fix; the latest verification is the covering 14-test persistence suite, as requested.
