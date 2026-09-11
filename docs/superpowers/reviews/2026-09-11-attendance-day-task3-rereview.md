# Task 3 fix round 1 scoped re-review

Reviewer: attendance_ui_rereview (read-only); exact source snapshot task3-fix1-final-diff.md.

1. Obsolete delayed preview confirmation: ADDRESSED. useAttendanceDayPolicyDraft.ts:122 invalidates generation/confirmation;133 captures input/revision;149 rejects stale response;171 schedules captured confirmed input.
2. Tenant/user/client/authorization ownership: ADDRESSED. AdminAttendancePolicyPage.tsx:328 keys identity;54 changes client owner;121 invalidates lifecycle;98 guards requests;217 gates rendering. Draft hook:35 guards ownership;110 resets;179/186 suppress stale conflict/completion.
3. Current-window expiry/resume: ADDRESSED. useAttendanceDayWindows.ts:17 rejects expired responses;49 schedules exclusive-end refresh;66 refreshes focus/visibility;86 exposes only ready/current data. Historical selection regression retained.
4. Client-only punch busy reset: ADDRESSED. PunchInOut.tsx:121 resets mutation state/ref/error/last punch on ownership change; generation suppresses old completion. Test:240 covers new punch before old response.
5. Intrinsic duration cap with incomplete paging: ADDRESSED. attendanceValidation.ts:258 enforces<24h before coverage-dependent checks; regressions cover incomplete/outside coverage and exact endpoint.

New breakage: none. Out-of-scope observations: none. Verdict: all five addressed; no new Critical/Important breakage.

Checks: reviewer read brief, findings, fix report, scoped diff and necessary dependencies. Covering45/45, broader90/90, typecheck/lint/SDL/258operations evidence matched tests; no reruns or mutations. Inherited lint debt remains disclosed for final review.

