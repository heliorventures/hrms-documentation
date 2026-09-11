# Configurable attendance day final UI fix report

Date: 2026-09-12  
Scope: the two Important findings in `2026-09-11-attendance-day-final-review.md`  
Status: source frozen for scoped re-review; no commit created

## Outcome

Both findings are fixed without a backend or GraphQL contract change.

- Personal and managed attendance tables now prefer elapsed duration from the canonical `checkInAt`/`checkOutAt` instant pair. The shared canonical parser has three deliberate outcomes: a duration for a valid complete pair, `null` for a partial/malformed/non-positive canonical pair, and `undefined` only when both canonical fields are absent. This prevents incomplete canonical rows from acquiring a fabricated wall-time duration.
- Legacy fallbacks are retained only when both canonical timestamps are absent: personal rows keep their existing 24-hour-wrap fallback, while managed rows keep their existing same-day-only fallback.
- Employee self-adjust eligibility now ages against the trusted tenant-calendar date derived from normalized `currentTenant.timezone`, matching the retained backend tenant-calendar-day deadline. Attendance `currentWorkDate` remains the grouping, initial-month, and missed-punch default.
- Tenant-calendar eligibility has its own exact midnight timer and focus/visibility refresh. Timer state is owned by tenant/user authorization identity plus timezone, so a stale owner cannot publish into a replacement context.

## TDD evidence

RED command (before production changes):

```powershell
node node_modules/vitest/vitest.mjs run src/modules/attendance/hooks/attendanceSegmentRows.test.ts src/modules/hr/attendance/ManagedAttendanceTable.test.tsx src/modules/attendance/AttendancePage.editorOwnership.test.tsx
```

Result: 3 files failed; 5 tests failed and 7 passed. The failures demonstrated personal DST fallback displaying 300 rather than 360 minutes, partial canonical data falling back to wall time, managed overnight/DST canonical durations displaying `Unavailable`, and the tenant-midnight self-adjust deadline remaining open.

Final focused covering command:

```powershell
node node_modules/vitest/vitest.mjs run src/utils/attendanceDuration.test.ts src/modules/attendance/hooks/attendanceSegmentRows.test.ts src/modules/hr/attendance/ManagedAttendanceTable.test.tsx src/utils/tenantCalendar.test.ts src/modules/attendance/hooks/useTenantCalendarDate.test.tsx src/modules/attendance/AttendancePage.editorOwnership.test.tsx
```

Result: 6 files passed; 21 tests passed; exit 0. Coverage includes personal and managed New York DST fallback durations, managed Kolkata overnight duration, partial-canonical fail-closed behavior, legacy-only fallback, exact Kolkata midnight, focus refresh, identity replacement, self-adjust expiry, and unchanged attendance-work-date default.

Affected personal-page regression command:

```powershell
node node_modules/vitest/vitest.mjs run src/modules/attendance/AttendancePage.test.tsx src/modules/attendance/AttendancePage.refresh.test.tsx src/modules/attendance/AttendancePage.paging.test.tsx src/modules/attendance/AttendancePage.ownership.test.tsx src/modules/attendance/AttendancePage.editorOwnership.test.tsx
```

Result: 5 files passed; 18 tests passed; exit 0. Output contained only the inherited React Router v7 future-flag warnings recorded by the final review.

The first sandboxed Vitest attempt could not start esbuild (`spawn EPERM`). The same direct-node command was rerun with the approved scoped subprocess permission; this is an environment restriction, not a test failure.

## Static checks

Type check:

```powershell
node node_modules/typescript/bin/tsc --noEmit
```

Result: exit 0, no output.

Scoped lint:

```powershell
node node_modules/eslint/bin/eslint.js src/utils/attendanceDuration.ts src/utils/attendanceDuration.test.ts src/modules/attendance/hooks/attendanceSegmentRows.ts src/modules/attendance/hooks/attendanceSegmentRows.test.ts src/modules/hr/attendance/ManagedAttendanceTable.tsx src/modules/hr/attendance/ManagedAttendanceTable.test.tsx src/utils/tenantCalendar.ts src/utils/tenantCalendar.test.ts src/modules/attendance/hooks/useTenantCalendarDate.ts src/modules/attendance/hooks/useTenantCalendarDate.test.tsx src/modules/attendance/hooks/useAttendancePageModel.ts src/modules/attendance/hooks/useAttendanceEditor.ts src/modules/attendance/attendancePageTestSupport.tsx src/modules/attendance/AttendancePage.editorOwnership.test.tsx --report-unused-disable-directives
```

Result: 3 findings, all inherited `eqeqeq` findings in `src/utils/attendanceDuration.ts` (current lines 5 and 68 twice); no introduced lint findings.

Exact pre-wave baseline comparison:

```powershell
Get-Content -Raw D:\work\heliorventures\hrms-documentation\.superpowers\sdd\2026-09-11-configurable-attendance-day\final-fix-base\src__utils__attendanceDuration.ts | node node_modules/eslint/bin/eslint.js --stdin --stdin-filename src/utils/attendanceDuration.ts --rule "prettier/prettier: off"
```

Result: the same 3 `eqeqeq` findings (baseline lines 5 and 32 twice). `prettier/prettier` is disabled only for this stdin baseline comparison because the PowerShell pipeline normalizes the snapshot's line endings. All final-wave formatting findings, test metrics, promise handling, and production statement-count findings introduced during implementation were resolved.

## Changed files

Production:

- `hrms-ui/src/utils/attendanceDuration.ts`
- `hrms-ui/src/modules/attendance/hooks/attendanceSegmentRows.ts`
- `hrms-ui/src/modules/hr/attendance/ManagedAttendanceTable.tsx`
- `hrms-ui/src/utils/tenantCalendar.ts`
- `hrms-ui/src/modules/attendance/hooks/useTenantCalendarDate.ts` (new)
- `hrms-ui/src/modules/attendance/hooks/useAttendancePageModel.ts`
- `hrms-ui/src/modules/attendance/hooks/useAttendanceEditor.ts`

Tests/support:

- `hrms-ui/src/utils/attendanceDuration.test.ts`
- `hrms-ui/src/modules/attendance/hooks/attendanceSegmentRows.test.ts` (new)
- `hrms-ui/src/modules/hr/attendance/ManagedAttendanceTable.test.tsx`
- `hrms-ui/src/utils/tenantCalendar.test.ts`
- `hrms-ui/src/modules/attendance/hooks/useTenantCalendarDate.test.tsx` (new)
- `hrms-ui/src/modules/attendance/AttendancePage.editorOwnership.test.tsx`
- `hrms-ui/src/modules/attendance/attendancePageTestSupport.tsx`

## Boundaries and remaining release evidence

- No Rust, backend, schema, generated client, dependency, migration, deployment, live-data, login, MFA, or commit operation was performed.
- No signed-in browser acceptance was performed. The automated jsdom coverage proves state and deadline behavior, not production deployment or real-browser visual behavior.
- The three inherited duration-helper lint findings and the final review's separately recorded broader lint metrics remain baseline debt; this wave did not broaden into unrelated cleanup.

