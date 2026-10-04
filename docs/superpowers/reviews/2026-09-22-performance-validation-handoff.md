# Performance completion: user-run validation

Source implementation and targeted review are complete. This document is a command and acceptance checklist, not evidence of passing checks. Source has not been compiled; import/type integration and runtime behavior remain unverified. No migration execution or release approval is implied. Earlier accepted features retain their historical acceptance; these checks cover the new performance changes.

## Local checks

Run from PowerShell with existing project dependencies installed. These commands validate local source, may produce local build artifacts, and do not commit, deploy, or apply migrations. Share failures with the relevant command and concise output.

```powershell
Set-Location D:\work\heliorventures\hrms-ui
rtk npm run lint
rtk npm run test -- src/modules/workplace
rtk npm run build

Set-Location D:\work\heliorventures\hrms-svc
rtk cargo test -p kabipay-performance
rtk cargo check -p kabipay-outbox-worker

Set-Location D:\work\heliorventures\hrms-gateway
rtk npm test
rtk npm run build

Set-Location D:\work\heliorventures\hrms-database
rtk npm test
```

Database-backed Rust checks may require the project's existing test database configuration. Do not point tests at production. Applying migration 0088 is a separate environment-specific operation using the established migration procedure.

## New-flow acceptance after migration in the test environment

- Calibration: manager submission preserves manager assessment and leaves final rating unset when calibration is enabled. Only HR can decide, with a required reason and rating bounds. Repeated decisions retain their history. Advancement waits for every included current revision.
- Corrections: HR can reopen an eligible submitted self or manager review with a reason. Old answers, calibration, KPI evidence and acknowledgement remain available to HR. Stale clients cannot submit into the new revision. Other participants retain their submissions.
- Participants: exclusions and reinclusions require a reason and stop at the first review stage. Cross-tenant and unassigned-manager requests fail. Excluded participants cannot contribute new review or KPI writes.
- Private feedback: only HR can create/read it, including history queries. Optional goal associations must belong to the same employee and cycle. Employee and team views reveal neither text nor counts.
- Archive: archival blocks manual and scheduled creation while existing cycles continue. Concurrent archive/creation obeys the same program lock.
- Population and KPI: each population mode snapshots the intended tenant employees. Lists paginate without dropping selections. KPI identifiers cannot be used to read, move, update or delete another participant's data. Target edits reset approval; actuals require the proper open stage, role and revision.
- Automatic transitions: tenant-local deadlines, missing-deadline manual behavior, at most one advancement per cycle per poll, shared manual/retry prerequisites, persisted deduplicated exceptions, and truthful retry resolution. Check optional-weight programs and legacy cycles.
- Empty population: manual launch rolls back with a validation error. Scheduled launch retains an unresolved `NO_ELIGIBLE_PARTICIPANTS` exception and a blocked cycle. Retry must neither duplicate that exception nor advance the empty cycle. Existing population snapshots are immutable; this change does not add a participant backfill/relaunch workflow for already-created empty cycles.
- UI: switch participants, stages and revisions during in-flight requests. Old responses and drafts must not overwrite the newly selected review. Unlinked managers and unauthorized users must not issue administration queries.

Production statutory payroll is not covered. Its country/state, effective period, calculation/filing scope and approved reference cases remain to be established.
