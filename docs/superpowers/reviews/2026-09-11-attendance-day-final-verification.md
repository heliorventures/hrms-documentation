# Configurable attendance day: verification record

Status: source implementation, local checks and independent review complete (12 September). No open Critical/Important source-review findings. Runtime QA/release gates remain pending; this is not a production-readiness or deployment acceptance claim.

## Approved behavior

Tenant-local default 05:00, configurable by an authorized administrator for a future attendance day. Active and historical windows stay fixed. At the exclusive end, an unfinished segment becomes INCOMPLETE with null checkout and no invented worked time. Employees/HR correct the original segment through existing authority and audit paths, using actual calendar dates inside its retained window. Generic leave/timesheet calendar dates are unchanged.

## Evidence by source boundary

| Scope | Recorded result | Source boundary |
| --- | --- | --- |
| Foundation calendar | 7 real-crate tests passed | Calendar unchanged afterward |
| Foundation persistence | 14 tests passed after bootstrap snapshot race fix | Later shared proposal refactor covered below |
| Database structural contract | Passed | Migration0087 XML, tenant keys/references/master only; no application |
| Scoped entity generator tests | 2 passed | Only0087 generated; no unrelated regeneration |
| Backend attendance suite | 106 passed,2 PostgreSQL tests ignored | Before final shared proposal refactor |
| Final current-backend attendance suite | 109 passed,2 PostgreSQL tests ignored; exit0 | Root `cargo test --offline -p kabipay-attendance --lib --tests`, after all backend fixes,1m40s build; no warnings |
| Backend runtime regressions | 7 passed | After final test fixture assertions; runtime source unchanged afterward |
| Worker production check | Passed without warnings | Before shared proposal refactor; worker interfaces unchanged |
| Shared preview/save proposal | 18 policy tests passed without warnings | Latest backend review fix, includes bootstrap/revision/frozen/preview agreement |
| Real local SDL export | Passed | Public contracts unchanged by subsequent policy-only refactor |
| UI affected regression suite | 90 passed across12 files | After all behavioral fixes, before final hook-only complexity extraction/test grouping |
| UI final covering regression suite | 45 passed across5 files,exit0 | After final extraction/test grouping; no later source edits |
| UI TypeScript | Passed,exit0 | Final Task3 source |
| UI scoped lint | New/non-baseline set passed;26 residual metrics versus29 pre-fix and34 HEAD | Existing Admin/Manual/test debt remains; one new Admin component complexity metric disclosed |
| UI GraphQL contracts | Exact local SDL generation passed;258 unique named operations across23 documents | Final Task3 source; no live gateway request |
| Final integration-fix tests | 21 passed across6 files;18 passed across5 affected page files | Frozen final UI-only wave; overlaps between suites are not added as unique test counts |
| Final integration-fix typecheck/lint | TypeScript passed;0 introduced lint findings | 3 duration-helper eqeqeq findings exactly match pre-wave baseline; earlier disclosed lint debt remains |
| Final integrated review | Both Important findings closed; no Critical/Important findings remain | Final scoped reviewer confirmed canonical row durations and calendar-day deadlines, with no new breakage |

Exact commands, RED/GREEN output and local build/environment caveats are in the [foundation report](2026-09-11-attendance-day-task1-report.md) and [backend report](2026-09-11-attendance-day-task2-report.md). Independent reviews and scoped re-reviews resolved all Task1/2 findings; there are no parked findings from those tasks.

UI commands, baseline comparisons and regression output are in the [UI report](2026-09-11-attendance-day-task3-report.md). The five initial Important UI findings have implementation fixes and covering test evidence; [scoped re-review](2026-09-11-attendance-day-task3-rereview.md) confirmed all addressed with no new breakage. Inherited React Router future-flag warnings remain in tests. Root `git diff --check` passed in all four repositories; Git emitted line-ending notices, not whitespace errors.

The [whole-feature review](2026-09-11-attendance-day-final-review.md) found two additional integration omissions in previously unchanged dependencies. The [final UI-only fix report](2026-09-11-attendance-day-final-fix-report.md) records their RED/GREEN evidence and exact commands. It uses existing trusted tenant timezone metadata and canonical segment timestamps; it does not change backend adjustment deadlines or require another schema change. Earlier suites are scoped to their recorded source boundary; the final21/18 runs cover the amended code. The reviewed source consists of the original whole-feature package plus the final scoped fix diff.

The [final scoped re-review](2026-09-11-attendance-day-final-rereview.md) closed both findings with no new breakage. Final tracked `git diff --check` passed in all four repositories, and service/UI/database HEADs still match the recorded starting commits. All source remains available for manual review; no commit or cleanup was performed.

## Release and runtime gates still required

- Apply database-owned migration0087 only with authorization and the normal reviewed tenant migration workflow. Existing attendance rows are not rewritten by this migration.
- Release matching attendance service, worker, gateway composition and UI versions. Old services cannot satisfy the new UI operations. Do not roll out UI alone.
- Verify real PostgreSQL locking, rollback, constraints and immutable-history triggers. SQL proxy tests do not prove these database behaviors.
- Validate signed-in admin, employee and HR flows, actual cutoff rollover, delayed worker, concurrent correction/expiry, historical grouping and visual/accessibility behavior against an authorized test tenant.
- Use the [acceptance checklist](2026-09-11-attendance-day-acceptance.md) for concrete cases. No live tenant mutation is authorized by this document.

## Preservation and exclusions

All work remains uncommitted for manual review. Existing unrelated database README/seed work and documentation deployment settings are preserved. No migrations, deployments, emails, live tenant data changes, MFA/login edits or Dart/Flutter commands were performed. Rustfmt is unavailable in the installed toolchain; no installation was attempted. Rust Analyzer background builds caused delays; the user reported stopping it, and the agents did not change editor settings or terminate its processes.
