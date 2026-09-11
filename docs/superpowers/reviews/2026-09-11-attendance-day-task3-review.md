# Task3 independent UI review

Reviewer: attendance_ui_review. Spec compliance: issues found. Quality: needs fixes.

## Important findings

1. `useAttendanceDayPolicyDraft.ts:60/83/91`: a delayed preview publishes after draft edits invalidate it. Preview06:00, change07:00 while loading, confirm returned06 interval, then save sends current07 input. Bind response/confirmation/save to exact input, revision and request generation.
2. `AdminAttendancePolicyPage.tsx:112/186/286` and draft hook`:52/101`: tenant/user/client/authorization replacement retains old policy/draft/confirmation; old preview/save/conflict-load completions can publish into replacement context. Matching revision does not protect ownership. Reset and gate all state and completion paths.
3. `useAttendanceDayWindows.ts:15/26`, page model`:81/83`: current-window query never expires or refreshes on resume, and accepts expired responses. Personal attendance retains yesterday's defaults/age eligibility indefinitely after cutoff. Add current-window lifecycle/fail-closed refresh while preserving selected months and historical corrections.
4. `PunchInOut.tsx:121/139/161`: client-only replacement invalidates mutation generation without clearing submittingRef/submitting. Old finally skips cleanup, leaving new context permanently busy. Reset all mutation-owned state on owner replacement and suppress old completions.
5. `attendanceValidation.ts:240/257`: incomplete/outside paging coverage returns before own-interval duration cap. Validate intrinsic actual duration below24h before deferring cross-row checks; backend cap already remains enforced.

## Minor / positive checks / limits

- Inherited React Router future-flag warnings remain; no unrelated router change requested.
- Exact ALL permission, typed real-SDL operations, paired dates, original IDs, managed reason/revision, canonical overlap and exclusive window endpoint behavior checked positively.
- Named dependencies checked: retained queries, graph client identity, permission service, selected-period retention and segment correction defaults.
- Final supplied test evidence78/78, typecheck and scoped new-production lint passed, but did not cover the five findings. Reviewer reran no tests and performed no writes.
- Signed-in visuals, gateway, tenant data, PostgreSQL/migration and deployed worker acceptance remain unverified/outside execution authority.

Fix round1 dispatched to original UI implementer with targeted regressions. Review not yet approved.
