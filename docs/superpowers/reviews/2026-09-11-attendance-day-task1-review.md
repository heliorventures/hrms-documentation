# Task 1 independent review

Reviewer: attendance_foundation_review. Spec compliance: issues found. Quality: needs fixes.

## Important finding

Make missing-profile fallback use one database snapshot. `hrms-svc/crates/kabipay-attendance/src/services/attendance_day/repository.rs:52` reads profile/version state, then `:74` separately checks attendance existence. Under READ COMMITTED, a fresh tenant's first mutation can initialize its 05:00 policy and insert attendance between these statements. The reader combines no profile from the earlier snapshot with attendance exists from the later snapshot and returns the legacy midnight fallback at `:86`.

At 03:00 local on September 12, this can incorrectly identify September 12 as current when both the pre-initialization fresh fallback and committed 05:00 policy identify September 11. Fetch profile, versions and attendance existence together in one statement/snapshot, preserving write-free reads. Add a focused regression covering this bootstrap interleaving; existing sequential proxy fixtures do not cover it.

## Other review results

- Literal calendar fixtures, transition continuity, tenant-qualified constraints and immutable-history triggers reviewed positively.
- Existing audit schema cross-contract check found no mismatch.
- No Critical or Minor findings. No tests rerun; final implementer evidence records 20 passing tests.
- PostgreSQL execution/concurrency remains unverified; post-lock timestamp handling and punch/UI integration are downstream Tasks2/3 responsibilities.

Fix round 1 approved by independent scoped reviewer attendance_foundation_rereview: unified snapshot addresses the finding; nullable revision distinguishes missing profile while corrupt existing versions still fail closed. Regression covers both snapshots, literal date/UTC bounds, one statement, tenant qualification and SELECT-only access. Exact RED and14/14 GREEN recorded in implementer report. No new breakage or out-of-scope observations. Task1 review gate is now approved.
