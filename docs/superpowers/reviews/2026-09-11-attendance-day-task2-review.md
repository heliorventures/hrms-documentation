# Task2 independent backend review

Reviewer: attendance_backend_review. Behavioral spec compliance: approved. Quality: needs fixes.

## Important

`attendance_day/preview.rs:25-52` duplicates scheduling validation/proposal logic in `attendance_day/repository.rs:223-254`: revision, active-date restriction, affected frozen-window range, proposed versions and transition continuity. Preview separately reconstructs legacy activation at lines34-37. Current ordinary behavior agrees, but there are two implementations of the preview/save contract. Extract shared read-only proposal validation, retaining scheduling's locked revalidation and persistence ownership.

## Minor

`attendance_service.rs:333-335` still documents same-calendar-day-only manual entry despite actual-date/window support. Correct the documentation.

## Positive checks and limits

- Policy-first locking/post-lock clocks, exact-end expiry without fabricated checkout, write-free projections, canonical interval correction, original-ID/revision/scope safeguards and independently entitled worker integration checked positively.
- No additional production correctness defect established. Final runtime test fixture models a legal correction interleaving before worker policy-lock ownership.
- Named unchanged dependencies checked: preview/scheduling, punch-close hunk, canonical duration, attendance summaries/reports and writer lock call sites.
- Real PostgreSQL execution, migration, gateway and signed-in acceptance remain unauthorized/unverified. Root previously inspected analytics stored-workdate grouping and found no direct payroll attendance consumer; no speculative payroll edits needed.
- Review's pending-SDL warning is resolved: implementer subsequently completed real local schema export and recorded it in Task2 report.

Fix round1 dispatched to original implementer. No tests rerun by reviewer.
Fix round1 approved by attendance_backend_rereview: shared read-only proposal/bootstrap logic removes duplication; scheduling retains locked reload/revalidation and write ownership; preview remains write-free with transient IDs cleared. Stale documentation corrected.18/18 covering tests passed after exact exhausted-revision RED. No new breakage or out-of-scope observations. Task2 gate approved.
