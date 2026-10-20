# Tenant execution progress

Owned work: source tenant runtime, Employee/Leave/Attendance/Performance/Payroll adapters and source migration 0115. No commits, deployment, live company database reads, Dart, Flutter or RTK commands.

## Implemented

- Fixed-company command boundary with 64 KiB raw-body limit, exact RS256 delegation intent checks, independent company credential to live organization policy and source local installation fences.
- Source transactional receipts bind principal, source account, organization, membership, immutable request hash and command. Status reads require original command, operation and hash plus current authority. Read responses are not persisted as receipts.
- Authoritative grant/relationship installation, local actor references, monotonic versions/hashes and post-commit company-authenticated acknowledgements. Relationship installation explicitly binds unsubmitted performance review snapshots.
- Employee directory pages expose purpose-limited identity/employment fields; disabled/deleted source accounts retain stable identity links, and duplicate/missing account links fail explicitly.
- Leave and timesheet source decisions retain existing workflow locks, step checks, balance/comp-off helpers and finalization. Foreign workflow actors use actor references; pure reporting-manager steps still require an active PRIMARY assignment.
- Performance protected detail, employee-visible feedback and manager appraisal use existing template/question/rating/revision validation and source snapshots.
- Payroll reviewed calculation/finalization share transaction-aware business cores with existing local callers. Foreign actor proof cannot be built from a wire DTO. Loan recovery retains its module, eligibility, quote/fingerprint and posting rules with nullable legacy user attribution plus principal references.
- 0115 source tables/triggers provide resource counters, minimal receipts, logical business attribution and atomic whitelisted company events. Existing webhook/Finance endpoints remain mounted.
- Durable bounded bootstrap snapshots use a source cursor/phase job and Employee worker (100 rows per two-second tick). Directory/install outcomes expose source bootstrap progress. Feedback uses employee resources and advances their source version without placing feedback bodies in events.
- Effective canonical PRIMARY assignments override legacy local TEAM/workflow/queue authority. Foreign managers never fall back to a previous local manager. Future participant manager snapshots are installed explicitly and selected by effective intervals; new participants bind already installed source assignments.
- Directory preserves verified source account identity when accounts/employees become inactive or deleted, and emits deleted rows as tombstones. Account ambiguity is a conflict; eligibility remains separately verified.
- Internal business commands retain current module subscription checks in addition to live organization authority. Source metadata installation/sync remains a separate permission boundary.

## Executed evidence

- TDD red: `cargo test -p kabipay-organization-tenant --lib --offline` failed with three E0425 errors for intentionally missing `parse_command` before implementation.
- First focused `cargo check` compiled tenant runtime, Leave and Attendance; Performance stopped on a private proof type introduced during the build. This was a source-edit timing issue; final focused check is pending.
- Follow-up focused `cargo check -p kabipay-organization-tenant -p kabipay-employee -p kabipay-leave -p kabipay-attendance -p kabipay-performance -p kabipay-payroll --all-targets --offline` passed before the later canonical-manager/directory hardening. Current full source check will be repeated after those changes.
- `cargo test -p kabipay-organization-tenant --lib --offline`: five tests passed (intent validation, current identity epochs, company/actor/employee binding, restricted private payroll proof). A sixth credential-before-source-query regression was added afterward.
- Real isolated PostgreSQL 16: actual 0112 and 0115 SQL executed against synthetic prerequisite tables; nine canonical facts passed corrections, date moves, deletion, private body exclusion, workflow/feedback version propagation, envelope consistency and transactional rollback assertions. This is SQL/trigger proof, not a complete Liquibase tenant upgrade.
- Real Rust bootstrap integration test passed with limit-one batches, persisted cursors, COMPLETE phase and no private body leakage. Canonical future/foreign-manager coverage was added afterward and awaits rerun.
- Source migration rollback refused a populated synthetic runtime as intended, preserving evidence; a separate empty synthetic schema rolled back successfully.
- TDD canonical-manager regression: existing TEAM SQL test failed on the new canonical-manager join assertion before implementation; the recursive query has since been fixed and awaits green rerun.

## Remaining validation

- Complete focused compilation and tests, then fix any failures.
- Verify migration SQL with isolated PostgreSQL and real source/organization HTTP chain if infrastructure is available. No deployment, live data, migration execution, broker capture or browser evidence is claimed here.
- Final independent reviews are coordinated by the root agent.

## Follow-up hardening (source work in progress)

- Source scope fences check current locked actor/subject employee rows for SELF/DEPARTMENT grants, including active status and nonnull current department equality.
- Organization commands retain an actual local user FK only for a verified own-company account; foreign principals remain logical actor references. Existing legacy local entry points retain their original attribution.
- Current ops entitlement snapshots travel only inside private verified payroll proofs, including LOANS and tenant currency, so physically separate source databases do not query ops tables through business transactions.
- Canonical event envelopes retain typed verified organization actors, actual known local users or explicit system attribution. Resource-version rows retain immutable actor and occurred-at evidence so bounded snapshots match same-version event hashes.
- Directory exposes legacy reporting-manager IDs. Source bootstrap registration transfers graph ownership: nontrivial legacy reporting-manager changes are rejected by a database trigger and employee service error; same-value writes remain valid. Lifecycle STOPPED markers return local ownership and stop event fanout (0117 lifecycle implementation belongs to integration agent).
- Updated actual0112/0115 SQL plus actor rollback assertions passed again against isolated PostgreSQL (nine canonical events). The latest Rust bootstrap test adds immutable snapshot equality and effective-manager/legacy-edit denial coverage; execution is queued.
- Actual Auth/Employee/Leave fixture child process is authored and compiling. Central full-chain orchestration belongs to root; no full-chain result is claimed yet.

### Refreshed evidence and lifecycle wiring

- Full generated synthetic source schema (237 entity tables plus the real raw-only payroll input audit table and composite tenant keys) accepted actual0112/0115/0117 SQL in PostgreSQL16. Checked-in fixture DDL contains no account data or secrets.
- Source canonical fact assertions passed with actual0117 membership fences, including nine events and transaction-local actor rollback.
- Refreshed Rust bootstrap integration passed with actual installed ACTIVE membership fence, bounded job cursor, same-version envelope equality (excluding event ID), foreign/future manager resolution and legacy reporting edit rejection.
- Refreshed multi-package lib run compiled all requested packages. Performance SQL-boundary fixtures then failed14 tests because they had no canonical-assignment query response; fixtures now explicitly model no installed relationship and add an installed-foreign-manager denial regression. Fresh focused rerun remains queued. This is not recorded as a passing full suite.
- InstallMembership now uses the private lifecycle module, exclusive fence before actor/receipt locks and source-authenticated postcommit ACK. All other source commands/status reads hold an exact ACTIVE shared membership fence through commit. Bootstrap takes that fence before locking its job.
- Domain-row/version-row order now matches existing local AFTER-trigger writes. Payroll prepares its existing coordination/input locks before cycle/version locks.
- The integration agent independently executed the source lifecycle PostgreSQL test (actual0117, shared fence drain, suspend preservation, terminal retirement and idempotency); that agent owns the definitive lifecycle evidence.


### Recovery and lock-order hardening (2026-10-18 22:00 UTC)

- Added source-confirmed cancellation receipts for never-committed commands. Both receipt wrappers serialize on the original command ID; the compact original receipt binds actor, hash, operation, resource and expected version. Late original delivery observes `CANCELLED_NOT_EXECUTED` and cannot execute. Metadata cancellation registers only the verified logical actor needed by the receipt FK. This is implemented; fresh HTTP race execution is pending.
- Receipt recovery re-ACKs the original source-confirmed installation only when its immutable configuration hash matches fresh policy. Cancelled receipts never ACK an installation. Strict wrappers reject nested recovery, missing cancellation resource and extra resource data on status reads.
- Source Performance now prepares cycle and participant locks before generic participant/version locking and assignment authorization. Relationship installation takes review cycles, sorted employee rows, participants, then assignments. Local manager snapshot reads avoid an inverse assignment lock under participant locks; new participant creation locks actual employee FK targets before assignment snapshots.
- Metadata actor installation sorts all verified actor UUIDs and rejects conflicting duplicate snapshots before grant/assignment writes. Business commands require preinstalled actor refs and refresh without waiting on unrelated actor locks.
- Payroll existing-draft reads and final readiness retain the private current company date from live ops entitlement proof, including the prior-review read during recalculation. Added a strict source-only repeated-read regression; fresh execution pending.
- Refreshed tenant library check passed. Actual0112/0115/0117 SQL plus canonical-fact/actor rollback assertions passed again in the isolated synthetic PostgreSQL database (nine events). Latest multi-package tests and refreshed HTTP fixture build remain in progress; no passing full-chain claim is made.

- Four-package source library tests completed successfully (session71192,9m48s): Employee88passed/2ignored; Payroll74passed; Performance46passed/1ignored; tenant library also passed. This closes the previously recorded Employee FNF merged-root fixture and Performance stage/proxy failures. The latest recovery-wrapper helper edit and the ignored PostgreSQL Performance order test still require their fresh targeted runs.

- Actual Performance PostgreSQL cycle-lock regression passed (0.52s) using the newly compiled source test binary: a local cycle holder can acquire the participant and commit while source waits; a participant rebound while waiting is rejected. The test created/dropped only a random schema in the explicit synthetic database.
- Fresh source HTTP fixture build completed successfully (session74795,12m33s) with cancellation/recovery and final source lock/date changes. The HTTP harness owner was notified immediately; its end-to-end result remains pending.


### Actual HTTP recovery/lifecycle evidence

- The harness owner/root reported session42995 EXIT0 using the refreshed source fixture executable and actual Auth, source Employee/Leave and organization HTTP handlers with separate synthetic company databases.
- Covered never-forwarded original command cancellation with no prior receipt, late original delivery remaining fenced, one audit only, cancellation of an already committed command returning its committed outcome, lost postcommit installation ACK recovery through status, atomic reporting replacement/reverse-edge cycle handling, suspended-manager relationship ending and full membership lifecycle.
- This is executed synthetic HTTP evidence for Employee/Leave orchestration and recovery; it is not deployment or live-data acceptance. Payroll/Performance/Attendance business execution retains focused Rust/source/SQL evidence and is not presented as full HTTP coverage.


### Final review correction: ended/expired Performance manager authority

- Reviewer2 confirmed R2-005: a participant created under a canonical local manager retained that FK after ordinary END or natural expiry, allowing stale local fallback authority.
- Relationship installation now recomputes only pending participant FKs after an effective PRIMARY transition, using the current effective PRIMARY (including foreign/null) or the actual employee legacy manager. Future-only installation does not rebind early; submitted participant history remains unchanged.
- Current local authorization resolves actual legacy manager after canonical authority ends/expires, gated by source ownership, retained review installation or retained canonical PRIMARY history. The historical-PRIMARY condition prevents a no-review-capability expired assignment from regaining authority after terminal detach removes ownership.
- Actual PostgreSQL pending-manager helper regression passed (0.63s): regular END restores legacy, submitted history unchanged, future install does not rebind, current foreign manager produces null. Actual GraphQL resolver proxy regression passed (0.02s): old canonical snapshot actor denied and actual legacy manager accepted.
- A real PostgreSQL resolver test for no-review-capability expired PRIMARY with detached ownership/no review marker is queued; it exercises actual SQL resolution, not a mocked successful result. Final tenant default unit rerun passed9, with2 explicitly ignored PostgreSQL tests (both PostgreSQL seams have been run separately).
- Six source packages plus tenant all-target check passed (session75688,8m55s) before this last review correction; fresh affected test/build runs are tracked separately. Fresh source fixture rebuild30361 passed (6m51s), including the installer correction.

- Final actual PostgreSQL Performance run72425 passed2/2 (0.41s): cycle/participant lock ordering and the expired no-review-capability/no-marker PRIMARY fallback with terminal ownership false, for both expired ACTIVE and ENDED retained history. This proves actual resolver SQL against the detached postcondition; actual0117 lifecycle transition/drain proof is maintained separately by the lifecycle owner.
- Refreshed current Performance default suite passed47, with the2 PostgreSQL tests explicitly ignored by default and executed separately as above. Reviewer2 reports no further confirmed defects.
- Strict tenant Clippy without dependency filtering stopped on9 common dependency lints (auto-deref, documentation continuation, redundant Sync bounds, calendar argument count). Those unrelated lint edits were not made; a tenant-only `--no-deps -D warnings` run is queued. The final six-source all-target check is also queued/current.

- Final refreshed current six-source all-target check88892 passed (1m59s), including the final R2-005 resolver/history correction and new tests. Existing Leave dead-code and schema-exporter unused warnings remain. Repository-wide `git diff --check` passed after trimming only trailing blank EOF in explicitly owned files; unrelated loan content was preserved.

- Final tenant-only strict lint `cargo clippy -p kabipay-organization-tenant --lib --offline --no-deps -- -D warnings` passed (session14642,3m25s). The broader dependency-lint limitation remains explicitly recorded above. All source-owned build/test jobs are now finished; no shared build lock is held by this workstream.

## Final source handoff

Implemented all authorized source operations, verified delegation/live-policy/local fences, source receipts/cancellation/ACK recovery, foreign actor attribution, canonical facts/bootstrap, effective manager presentation and review lock/expiry corrections. Employee SDL and checked-in synthetic fixture schema are current. The definitive actual HTTP harness outcome is owned by the root/fixture agent; source business HTTP proof covers Employee/Leave, while Attendance/Performance/Payroll retain focused Rust/SQL proof rather than full business HTTP acceptance. No deployment, live-data execution, commits, Dart/Flutter or RTK commands were performed.
