# Attendance-day acceptance checklist

Status: planned checks, not runtime results. Execution against a tenant or real database requires separate authorization. Do not use these examples to alter existing employee records.

## Default cutoff, tenant timezone Asia/Kolkata

- A work date of 11 September spans 11 September 05:00 through, but not including, 12 September 05:00.
- A punch at 12 September 04:59:59 belongs to 11 September; a punch at exactly 05:00 belongs to 12 September.
- If the 11 September segment has no checkout at the boundary, it becomes effectively INCOMPLETE with checkout still empty, even if the worker is unavailable.
- The next punch opens a new 12 September segment; it must not complete the previous segment.
- Completed totals do not include the unfinished interval. Existing completed intervals remain unchanged.

## Correction of original segment

- Open the original INCOMPLETE segment in the existing adjustment screen.
- Show attendance work date separately from actual check-in/check-out calendar dates and times.
- A segment belonging to 11 September may be corrected to 12 September 02:00 through 04:00.
- A checkout exactly at its 05:00 end is allowed; checkout after that end is rejected.
- Persist correction against the original ID, without duplicate minutes or a second segment.
- Retain employee ownership, management scope, edit-window, reason/audit, stale-update and duration-cap restrictions as applicable to the existing flow.
- Before 05:00, default/group by the prior attendance work date but evaluate self-adjustment age against the current tenant calendar date, matching the existing backend limit. With a 14-day limit at September 12 03:00 Kolkata, August 28 is expired (15 calendar days), not available as 14 attendance-label days. Recheck at tenant midnight and on resume.

## Future policy change

- Show current policy, pending policy, timezone, effective work date and exact transition start/end before confirmation.
- Changing 05:00 to 06:00 creates one 25-hour transition window, then ordinary 06:00 windows.
- Changing 05:00 to 04:00 creates one 23-hour transition window, then ordinary 04:00 windows.
- Neither change alters the active day's end or historical stored work dates/windows.
- Reject stale revision, unauthorized setting changes, past/active dates and changes affecting frozen windows.
- Replacing a still-future setting preserves its superseded audit record and shows the actual replacement date.
- Change a draft while its preview request is pending; the old response must not restore confirmation. Scheduling must use exactly the displayed, confirmed proposal.
- Replace tenant/user/client or remove authority during a policy request. Old previews, saves and conflict reloads must not appear in the replacement context.
- Existing legacy tenants remain on midnight interpretation until their durable future activation; fresh tenants default to 05:00.

## Consistency and concurrency

- Dashboard refreshes at the server window end and after focus/visibility resume. Expired or identity-stale summaries cannot enable a punch.
- Personal Attendance also refreshes its current work date at cutoff/resume without changing an explicitly selected historical month. Expired responses must not enable adjustment eligibility.
- Replace the API client during a pending punch. The new context must load its own summary and must not remain stuck busy or display the old response.
- On a25-hour transition, reject a requested interval of24 hours or more even when the displayed segment list is incompletely loaded; a shorter valid interval may end exactly at the window endpoint.
- Two concurrent punch requests do not create duplicate OPEN segments; expiry cannot overwrite a concurrent completed correction.
- Attendance list, monthly summary and exports group canonical durations by stored work date. Leave and timesheet calendar dates remain unchanged.
- HR and personal rows must agree with canonical durations: Kolkata September 11 23:00 to September 12 04:00 is 5 hours; New York October 31 23:00 to November 1 04:00 across the 2026 autumn DST transition is 6 hours. Partial/invalid canonical timestamps must not silently fall back to wall-time arithmetic; only genuinely legacy records may use the documented fallback.
- Worker reruns are idempotent; attendance entitlement is checked independently of employee-module entitlement.
- Repeat representative cases in a DST timezone and after a tenant timezone change; frozen historical windows retain their original timezone/UTC bounds.

## Release gates

- Local Rust/UI/schema tests and independent code review must be reported separately from this checklist.
- Real PostgreSQL locking/constraint tests, migration application, matched service/UI/worker deployment and signed-in browser acceptance remain pending until explicitly performed and evidenced.
- No live tenant correction, migration or deployment is authorized by this checklist.
