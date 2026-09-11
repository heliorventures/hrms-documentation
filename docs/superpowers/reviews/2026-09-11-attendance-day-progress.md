# SDD ledger — plan: docs/superpowers/plans/2026-09-11-configurable-attendance-day.md

Approved spec: ../specs/2026-09-11-configurable-attendance-day-design.md.

## Execution rulings

- Ruling: retain the current feature checkouts and caches; no new worktrees/branches or automatic commits. User approved work in this workspace and explicitly requires preserving it. Cost: no additional checkout isolation; use scoped ownership and diffs.
- Ruling: keep task briefs/reports here under documentation instead of commit-range-only scratch cleanup. User forbids commits; review uncommitted changes against captured bases and preserve evidence. Cost: documentation artifacts remain for manual review.
- Ruling: legacy activation metadata is initialized transactionally by normal write/worker paths, never read queries. No migration rewrites existing punches. Cost: default activation is pending until the first normal initializer runs; expose that state to admins.
- Ruling: the automatic pending legacy-to-05:00 activation is replaceable using the same future-date, revision and frozen-window guards as an admin pending setting. Preserve its original version as superseded history and show the replacement interval explicitly. This avoids temporarily blocking admin configuration. Cost: an admin can intentionally delay default activation; legacy midnight remains until the selected transition.
- Ruling: allow an isolated rustc harness against the actual pure calendar source and existing dependency artifacts while the single Cargo run compiles cold dependencies. Use separate temporary output and a test-only common error alias; full crate tests remain required. Cost: harness success alone does not verify crate linkage or production error integration.

## Baseline

Service branch codex/hrms-attendance-monthly-summary and UI branch codex/ui-ux-modernization clean at start.
Database branch codex/leave-queue-index: preserve README.md, three migration README additions (0083/0085/0086), and two Solvian seed scripts.
Documentation: preserve deploy/.env.example and approved design.

## Preflight dependency review

| Tasks | Shared surface | Review |
| --- | --- | --- |
| 1 / 2 | AttendanceDayWindow and transaction repository | Task1 must publish signatures before Task2; writes lock policy before employee/day. |
| 2 / 3 | GraphQL summary/settings/adjustment metadata | Task2 publishes additive contract before UI; no browser-side independent work-date rule. |
| 1 / 3 | Transition and legacy activation display | UI displays server interval; no re-derived 24-hour assumptions. |
| 1 | Persistence and calendar tests | Literal UTC fixtures align with Kolkata; 23/25-hour transition preserves prior active day. |
| 2 | Expiry versus adjustment | Both require the original window and common locking; no fabricated checkout. |
| 3 | Effects and query ownership | Timer/visibility/StrictMode tests required; settings authority unchanged. |
| 4 | Completion versus release | Local checks never imply real migration/runtime proof. |

Service base: 62092ac5b72f34e26844e2a392d7feb391936ee0. Database base: e4f6d4d4c1a8c7857a1e65c93eff1439ff070c51. UI base: 402309e81cc5405e01ed1912677d2c026860c31d.

Task 1: running, agent attendance_day_foundation; core calendar/persistence/schema only. Root mapping downstream consumers read-only; no parallel implementation or Cargo.
Task 1 checkpoint: seven calendar tests passed in isolated harness and real attendance crate. Initial cold Cargo took 30m58s. Targeted persistence RED run (session 95037) refreshes dev-proxy metadata omitted by the initial invocation, and is waiting for an externally held build-directory lock. No external processes stopped. Schema structural/generator checks passed; migration remains unapplied.
Task 1 checkpoint: user confirmed no manual build. Read-only process inspection identified two automatic VS Code Rust Analyzer workspace checks. They finished naturally; session 95037 acquired the lock and began compiling proxy-enabled dependencies. No termination or editor-setting change was needed.
Task 1 checkpoint: user stopped Rust Analyzer after recurring contention. Persistence GREEN 13/13; calendar GREEN 7/7. Combined verification session 82917 pending. Source snapshot packaged in task1-diff.md including untracked new files, excluding unrelated dirty files. Independent read-only review agent attendance_foundation_review started; no duplicate Cargo run.
Task 2: pending.
Task 2: running, fresh agent attendance_backend_integration; backend writers/readers/expiry/worker/GraphQL only. UI remains Task3. No concurrent Cargo; user stopped Rust Analyzer. Task1 source baseline captured before shared-file edits for scoped uncommitted review.
Task 1: review found one Important bootstrap snapshot race (separate missing-profile and attendance-existence reads). Fix round 1/5 dispatched to original implementer with one-snapshot read and interleaving regression requirement. No other findings; real PostgreSQL execution deferred by authorization, downstream integration remains Tasks2/3.
Task 1: fix round 1/5 (1 addressed, 0 open). Exact bootstrap RED reproduced; covering persistence GREEN14/14. Scoped reviewer attendance_foundation_rereview approved unified snapshot and fail-closed corruption handling, with no new breakage.
Task 1: complete (uncommitted changes against captured bases, review clean). No parked findings. Latest evidence is14 persistence tests after fix; prior7 calendar tests unchanged. Task2 may consume published APIs.
Task 3: pending.
Task 3: running, fresh agent attendance_ui_integration. UI confirmed clean at base402309e81cc5405e01ed1912677d2c026860c31d before dispatch. Owns existing admin/day dashboard/employee and HR correction forms, typed operations/tests; backend source remains reviewed and unchanged. No Cargo required for schema-based client generation.
Task3 checkpoints: focused47 tests and later personal/dashboard29 + HR17 regressions passed before lint refactor; TypeScript passed. Root found duplicate operation names against broad clientOperations; dedicated operations renamed Attendance*, real SDL generator scalars typed as strings. New production lint now0; broader changed-file lint still has legacy/test metrics under baseline comparison. Final affected tests must be rerun after hook extraction; no complete/UI-clean claim yet.
Task3 source stable and packaged in task3-diff.md. Independent reviewer attendance_ui_review started. Report baseline: Admin29->26,Manual4->2,validationtest1->1,HRmodal0->0; new production lint/typecheck pass, combined final tests pending. Root final offline backend suite session74701 now recompiles current source after shared-policy refactor; no other Cargo authorized concurrently.
Task2 review: behavior spec compliant; Important duplicated preview/scheduling proposal validation requires shared read-only validation, retaining locked save revalidation. Fix round1/5 dispatched to original implementer. Minor stale manual-entry documentation recorded and assigned alongside existing fix. SDL warning resolved by completed export; realPG/release acceptance remains out of scope.
Task 2: fix round1/5 (Important shared validation and minor stale comment addressed,0open). Reviewer attendance_backend_rereview approved locked scheduling, read-only preview and shared initialization, no new breakage. Covering18/18 policy tests after fix; prior106 service tests,7 runtime tests,worker production check and SDL export evidence retained with exact source boundaries.
Task 2: complete (uncommitted source, review clean). No parked/deferred findings. Final API/SDL unchanged by review fix; Task3 may consume task2-schema.graphql.
Task 4: pending.
Task3 review: five Important findings in delayed preview binding, policy context ownership, current-window expiry, client-only punch busy reset and intrinsic duration cap with incomplete coverage. Fix round1/5 dispatched to original UI agent; exact details in task3-review.md. Minor inherited router warnings deferred for final review; legacy lint29 vs HEAD34 remains disclosed.
Final backend check: root session74701 completed109 tests passed,2 explicitly ignored PostgreSQL tests,exit0,no warnings,1m40s build after shared-policy fix. No active root Cargo.
Task3 fix round1 source frozen: final covering45/45 tests after extraction, affected90/90 before final hook-only extraction; tsc, scoped lint, exact SDL generation and258 unique operations passed. Reviewer attendance_ui_rereview checking five findings against task3-fix1-final-diff.md. Current legacy lint26 versus29 pre-fix versus34 HEAD; one new Admin complexity metric disclosed, no introduced unsafe/type/hook/format findings. Router warnings and lint metrics carried to final review.
Root preservation check: git diff --check exited0 in service, UI, database and documentation (Git CRLF notices only); pre-existing database README/seed artifacts and deploy/.env.example remain present. No source changes by root.
Task 3: fix round1/5 (5 addressed,0 open). Reviewer attendance_ui_rereview confirmed exact proposal binding, ownership, current-window lifecycle, punch reset and intrinsic duration cap; no new breakage/out-of-scope observations.
Task 3: complete (uncommitted source against captured base, review clean). No parked Critical/Important findings. Minor inherited router warnings and disclosed lint metrics carried to final integration review. Signed-in/gateway/PG acceptance remains release scope, not local proof.
Task 4: running, final whole-feature independent review against final-review-diff.md; no further implementation or duplicate test runs unless concrete findings require them.
Task4 final review: two Important integration findings, no Critical: canonical overnight/DST table durations and UI/backend calendar-day self-adjust deadline agreement. One consolidated final fix wave assigned, followed by one scoped re-review. Full details in final-review.md. Existing lint/router observations do not establish additional functional/security defects and remain disclosed.
Task4 final fix checkpoint: trusted currentTenant.timezone reused; no backend/schema change. Pre-wave targetedRED5failed/7passed reproduced canonical DST, partial-canonical fail-closed, HRovernight/DST and calendar-midnight deadline cases. CoveringGREEN21/21 across6 files after fixes; affected page regressions/typecheck/scopedlint still pending. Known esbuild spawn EPERM resolved with approved direct-node fallback; no new blocker. Exact pre-wave14-path snapshot preserved under final-fix-base.
Task4 final fix source frozen: final21/21 covering and18/18 affected tests passed;tsc0;3 duration eqeqeq findings identical to exactpre-wave3, no introduced lint. All14 UI files captured in final-fix-diff.md; report final-fix-report.md. One scoped re-review assigned to attendance_final_review; no backend/schema/generated changes and no duplicate backend tests.
Task4 final scoped re-review:2 addressed,0 open; attendance_final_review confirmed canonical duration and calendar-day deadline fixes, no new breakage/out-of-scope findings. Existing lint/Router observations are non-blocking and disclosed. No second fix wave needed.
Task 4: complete (12 September2026, uncommitted source, final review clean). Final verification record and remaining-work handoff updated; source implemented/local checks complete, runtime QA/release pending. Preserve all evidence and existing dirty files. HEADs unchanged; final tracked diff checks passed. No commit/deploy/migration/email/live-data/MFA/login/Dart/Flutter action.
