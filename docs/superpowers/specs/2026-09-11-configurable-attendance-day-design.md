# Configurable attendance day

Status: approved by user on 11 September 2026; local implementation and independent review complete on 12 September. Runtime QA/release remains pending; see the final verification record.

## Confirmed requirements

- Tenant-specific, admin-configurable attendance start time; default 05:00 in the tenant timezone.
- A normal day labelled D spans [D at the configured time, D+1 at that time).
- A punch still open at its day end is INCOMPLETE, not automatically punched out.
- Employees repair missed punches through the existing adjustment workflow and its authority,
  approval, audit and edit-window restrictions. Do not create a second correction workflow.
- Configuration changes apply only to future attendance days. Historical records and the active
  day's boundaries cannot be reinterpreted by a later setting change.
- Preserve unrelated work. No commits, deployments, migration execution, emails, live writes,
  MFA/login changes or Dart/Flutter commands.

## Approach and alternatives

Use an attendance-specific, effective-dated policy and immutable attendance-day windows. Keep
TenantBusinessClock's general calendar-date behavior unchanged. Replacing that global clock would
also shift unrelated leave/payroll/calendar behavior. A mutable setting plus frontend date offset
would be smaller but would reinterpret history and disagree with backend adjustments and reports.

Store policy versions and resolved day windows in hrms-database-owned forward schema changes;
generate service entities through the existing generator. Allocate a migration number only after
checking the current master. Existing settings screens and authorization patterns are reused.

## Future changes and activation

Admin selects a local start time and future effective work date. Show current and scheduled policy,
timezone, activation date and exact transition interval before confirmation. Reject past/active-day
changes and stale concurrent updates. Keep one pending change; replacement is permitted only while
it remains future and does not alter a frozen window. Audit old/new configuration and actor.

Every next day starts exactly when its predecessor ends. The first future transition day retains
that inherited start and ends on the following calendar date at the new boundary. Subsequent days
use the new boundary normally. Thus 05:00 to 06:00 produces one 25-hour window; 05:00 to 04:00
produces one 23-hour window. Neither leaves a gap nor changes the already-active day. Window length
does not relax existing worked-hours limits or manufacture paid time.

Initial rollout also needs an explicit activation anchor: preserve existing calendar-day records
and the active legacy day, then introduce the 05:00 default through a future transition window.
No historical work_date rewrite or automatic data backfill is included. Record the anchor durably,
not from each request's current date. Fresh tenants default to 05:00 without legacy conversion.

Resolve and retain the policy version, timezone, start/end UTC instants and work-date label for each
day. Later timezone changes cannot alter a frozen window. For DST, choose the earlier occurrence
of a repeated boundary and the first valid instant after a skipped boundary; verify continuity and
strictly increasing endpoints. Display the actual interval rather than assuming every day is 24h.

## Punch and expiry semantics

The backend is authoritative for the active attendance day. Under consistent tenant-policy and
employee/day locks, sample the clock after acquiring locks, retire expired OPEN segments, then
apply the punch to the current window. A punch at the end boundary belongs to the next day and
cannot check out yesterday's segment. Prevent concurrent punch, expiry and adjustment operations
from producing duplicate OPEN segments or overwriting a completed/corrected record.

Use the existing tenant worker for bounded, idempotent expiry sweeps. A delayed/stopped worker must
not keep an expired punch actionable: reads expose its effective INCOMPLETE state without writing,
and live mutations enforce expiry transactionally. Persist status/reason/audit only on actual
transitions. Leave checkout timestamps empty and exclude incomplete intervals from completed totals.

## UI, adjustments and reporting

Return current work date, UTC window endpoints and boundary metadata with the attendance summary.
Dashboard/punch UI uses that result, refreshes at the boundary, and blocks stale-day actions until
the replacement summary is ready. Preserve tenant/user/permission ownership and StrictMode safety.

Adjustment inputs show the attendance work date plus actual calendar dates/times for check-in/out,
so after-midnight times are unambiguous. Correct the original incomplete segment through the
existing permitted path rather than adding a duplicate segment. Validate interval containment,
overlap, actual duration, existing caps, authorization and adjustment deadlines using its historical
window. Checkout may equal the window end; a new check-in must be before the end.

Review live/manual/admin attendance entry, regularization approvals, dashboards, attendance lists,
monthly summaries, exports and attendance-derived payroll/report consumers for consistent stored
work-date grouping. Preserve canonical UTC instants and existing legacy interpretation where no
new window exists. Do not shift leave dates, timesheet calendar periods or unrelated survey logic.

## Verification and release boundaries

Before implementation, write focused failing tests for 04:59:59/05:00, custom boundaries,
midnight/year/month transitions, 23/25-hour policy transitions, historical/active-day preservation,
initial activation, DST, tenant isolation, unauthorized/stale settings writes, worker downtime,
post-lock clock races, duplicate punches and correction-vs-expiry. Cover actual-date adjustment
inputs, dashboard rollover, stale responses, StrictMode and report work-date grouping.

Then run focused Rust/UI tests, scoped lint/typechecks, worker compile, schema/operation validation
and migration structural checks. Real PostgreSQL concurrency, migration application and signed-in
tenant acceptance remain separately authorized execution gates, not claims established by mocks.

Self-review: requirements, transition semantics, activation compatibility, ownership and release
limits are explicit. User approved this design before implementation planning/build work.
