# Attendance boundary integration map

Read-only source mapping for Tasks 2 and 3; not implementation or runtime evidence.

## Backend

- `attendance_service.rs`: `attendance_business_date_time` uses calendar date; `punch_today` samples time before transaction/locks. Replace attendance-only day resolution and sample again after policy then employee/date locks. Keep timesheet functions in the same file on calendar dates.
- `attendance_regularization_service.rs`: `SegmentTimes::to_instants` converts both times on work_date, while overlap validation compares NaiveTime. Overnight correction needs actual dates and canonical intervals, not simply allowing out < in.
- Existing cap rejects total >= 24 hours; preserve it even for a 25-hour transition window.
- `lock_employee_dates` sorts and deduplicates dates, then advisory-locks `attendance:{tenant}:{employee}:{date}`. Every attendance writer and expiry must take the distinct tenant policy lock first.
- Task1 exposes explicit timestamps, not a system-clock callback. Caller must select candidate date locks, sample time after locks and re-resolve the active window; if the date changed while waiting, acquire the newly required date safely (or retry the transaction) before mutation. A pre-lock date must never determine the final punch target.
- Self-service update rereads the original ID and employee under locks and excludes that ID from overlap checks. Preserve this path for INCOMPLETE corrections, rather than insert a second segment.
- Managed mutations currently compute instants and `clock.now_date()` before calling transaction-owned orchestration. Move window-based validation inside the common locking boundary while preserving scope checks, reason/audit and expectedUpdatedAt.
- Existing adjustment flow is direct self-service / managed regularization; do not invent a new approval workflow. Preserve any existing restrictions actually present.
- `upsert_attendance_adjustment_policy` uses `require_all_authority(ctx, PERM_ATTENDANCE_PUNCH_POLICY)`. New scheduling must retain exact ALL authority, not a role-name check.
- Queries default work_date using `clock.now_date()` today. Change attendance-only defaults; do not shift leave/timesheet periods or generic TenantBusinessClock.

## Worker and reporting

- Existing outbox worker loads TenantBusinessClock and then EMPLOYEE entitlement for survey/celebration/performance sweeps. Attendance expiry requires ATTENDANCE entitlement, independently of EMPLOYEE. Reuse one entitlement load if practical without modifying unrelated sweep semantics.
- `attendance_summary_service.rs` queries and groups stored work_date and canonical instants.
- Analytics `hr_report_attendance.rs` likewise groups stored work_date; missing checkout marks incomplete and adds no duration. Preserve legacy fallback for rows without canonical timestamps.
- Targeted search of 14 files under `kabipay-payroll/src` found no direct attendance/check_in/worked_minutes consumer. Do not modify payroll speculatively.

## UI

- Settings route `admin/attendance-policy` imports `src/modules/admin/AdminAttendancePolicyPage.tsx`; reuse page and authority rather than new navigation.
- Dashboard `PunchInOut.tsx` computes browser-visible tenant calendar `today` and rejects summaries with another workDate. Replace ownership with server interval metadata; a pre-05:00 summary legitimately belongs to yesterday.
- Existing `useAttendanceEditor` and `useAttendancePageModel` own correction state; preserve tenant/user/scope and original segment identity while adding actual calendar-date inputs.
- Existing ownership/paging/refresh tests and StrictMode safeguards remain relevant regressions.
- `useAttendanceEditor.ts` computes self-adjust age with browser-local midnight and defaults to browser today; its caller `useAttendancePageModel` also creates browser `new Date()` for the attendance period. Use server attendance work date for attendance defaults/edit eligibility, while keeping intentionally selected historical month navigation stable.
- `ManualAttendanceModal.tsx` currently receives time-only defaults, validates through `utils/attendanceValidation`, and sends workDate/checkInTime/checkOutTime. Carry canonical original timestamps/window metadata and actual calendar dates into this existing form; do not let old time-only validation reject valid overnight corrections before the API call.
- Preserve editor identity ownership in `useAttendanceEditor` and parent keyed modal behavior. Server authorization remains authoritative even when the UI hides invalid actions.
- Dedicated client generator `scripts/generate-attendance-client.mjs --schema-path <exported SDL>` validates `src/api/documents/attendance.graphql` against the real attendance schema without another Cargo invocation. Add relevant operations there and reuse the Task2 exported SDL; existing dashboard/manual imports currently use broad `api/graphql`, which need not force a full gateway schema regeneration.
- Managed correction is separately rendered by `src/modules/hr/attendance/AttendanceRegularizationModal.tsx` and `useAttendanceRegularization.ts`; include this existing form in actual-date integration, retaining reason validation, original ID, expectedUpdatedAt and mutation-generation ownership. It shares the old time-only `utils/attendanceValidation` and browser-local today default. Its regression files are `AttendanceRegularizationModal.test.tsx`, `HrAttendanceManagementPage.test.tsx` and `.context.test.tsx`.

No production inspection, schema application, live data adjustment or deployment performed for this mapping.
