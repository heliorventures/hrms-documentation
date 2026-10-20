# Source membership lifecycle implementation

## Owned implementation

- `hrms-svc/crates/kabipay-organization-tenant/src/membership_lifecycle.rs`: transaction-owned `require_active` SHARE fence and verified `install` exclusive drain. Lifecycle transport calls `lock_installation` immediately after BEGIN, before actor/command receipt locks, preventing actor/fence lock inversion. Caller must verify tenant-bound policy, roll back errors and ACK only after confirmed commit.
- `hrms-database/changelog/migrations/0117_organization_membership_lifecycle/organization_membership_lifecycle.xml`: tenant-local installed membership and permanent minimal lifecycle receipt tables; grant installation status; bootstrap PAUSED/STOPPED; actual membership/fanout/ownership helpers. Parent owns master inclusion; tenant implementer owns transport wiring and0115 baseline helpers.

## Behavior and persistence

- Exact canonical DTO hash and positive revisions required. Tenant-wide command advisory lock prevents conflicting concurrent command reuse; company-wide installation advisory lock serializes first installations. Existing fence UPDATE lock drains commands holding the exact ACTIVE membership/version SHARE lock until commit.
- ACTIVE starts bounded bootstrap and suspends grants from older membership revisions. SUSPENDED stops fanout and pauses bootstrap while preserving assignments and ownership freeze. Resume never silently reactivates old grant ACKs.
- Desired DETACHING atomically installs operational DETACHED at the same desired revision/hash, copies only current effective same-company primary manager IDs into legacy employee routing, clears current foreign manager routing, ends all old organization assignments including future periods, revokes installed grants and stops bootstrap. No business receipts, facts, outbox records or historical references are deleted.
- Retirement uses wall-clock time after lock drain. Missing/deleted/self local manager references fail reconciliation rather than fabricating a manager. Other active/suspended organization ownership prevents retirement bypass.
- Private retirement guard requires exact tenant/org/membership tuple plus the current transaction ID and matching terminal desired fence, and is restored before return. Reusing a tuple in another transaction cannot bypass ownership. Database owner authority remains the existing trust boundary.
- Rollback refuses when lifecycle ownership, retained receipts or paused/stopped jobs exist; no destructive downgrade is automatic.

## Verification

`cargo test -p kabipay-organization-tenant --lib membership_lifecycle --offline`: PASS, one canonical configuration test; the explicit PostgreSQL fixture remained ignored in the ordinary run. The freshly built test executable then ran `postgres_lifecycle_drains_preserves_and_retires --ignored --exact` against the approved localhost synthetic acceptance PostgreSQL: PASS, one test in2.65s. It applied the actual0117 SQL in a new random schema and removed only that schema afterward. Assertions cover shared-lock drain, suspension preserving all assignments and ownership while pausing bootstrap/grants, own/foreign/current/future manager routing, all-assignment retirement, retained minimal receipts, exact terminal replay, conflicting command/stale revision rejection and stale retirement context rejection.

Tenant implementer separately reported actual0112/0115/0117 application and nine canonical source fact assertions passing with an explicitly installed ACTIVE fence. Their extended bootstrap test also passed with the actual0117 fence, stable same-version event hash and legacy guard assertions. This is source migration evidence, not central lifecycle or deployed acceptance.

Additional `cargo clippy -p kabipay-organization-tenant --all-targets --offline --no-deps -- -D warnings` was queued behind the shared Cargo lock (session7283). On later resume the tool reported Unknown process id; final output is unavailable, so no pass claim is made. Lifecycle code compiled and both focused tests above passed. No production membership installation, central detach coordinator E2E or live data operation was executed.

## Executed review correction

The source review identified legacy employee→assignment lock order and local review cycle→participant→employee FK order outside organization command fences. Retirement now drains sorted affected cycles, sorted affected employees, sorted pending participants, then sorted assignments, and samples its effective clock only after these locks. It rebinds only unsubmitted current manager-review snapshots to the actual restored local manager (foreign current manager becomes NULL); submitted and future manager snapshots are retained. The extended real-PG regression holds both a local cycle/participant workflow and a separate legacy Leave employee lock while actual retirement waits, then verifies both can finish assignment/FK reads without deadlock.

Focused lifecycle compile/unit: PASS (one passed, explicit fixture ignored in ordinary run). Fresh compiled real-PG extended fixture: PASS1 in1.25s, actual0117 plus representative source FK tables in a new random isolated schema, cleaned afterward. It verified both legacy lock paths, pending current own/foreign review manager rebinding and preserved submitted/future snapshots. Strict tenant `--lib` Clippy completed and found one unrelated new transport.rs671 needless borrow (`serde_json::to_value(&outcome)`); reported to its owner. No lifecycle warning was emitted, but no whole-crate strict Clippy pass is claimed until the owner reruns. Tenant owner separately aligned relationship installer cycle-first and creation guard employee-KEY-SHARE-before-assignment-SHARE order; their compilation/fixtures remain separate evidence.
