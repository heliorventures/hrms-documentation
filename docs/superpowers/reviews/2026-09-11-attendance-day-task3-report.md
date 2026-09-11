# Configurable attendance day — Task 3 UI implementation report

Date: 2026-09-11  
Status: complete with documented pre-existing lint debt; ready for independent review  
UI checkout: `D:/work/heliorventures/hrms-ui`  
Branch/base: `codex/ui-ux-modernization` at `402309e81cc5405e01ed1912677d2c026860c31d`  
Commits/deployments/live actions: none

## Delivered behavior

- The existing Admin Attendance Policy page now loads the dedicated typed attendance settings query, retains the live-punch policy UI, and adds current/pending attendance-day policy, active canonical window, future effective date/boundary inputs, exact transition/following preview, explicit confirmation, optimistic revision scheduling, and conflict reload while retaining the draft. The component issues no policy operation unless `attendance:punch_policy` has exact `ALL` scope through the existing permission service.
- Dashboard punch state uses server-owned `workDate`, `startsAt`, `endsAt`, `timezone`, and `boundaryMinutes`. It refreshes at the exact exclusive end and on focus/visible resume, coalesces resume refreshes, rejects out-of-window responses, disables stale actions, rechecks after geolocation, and prevents old tenant/user/client or StrictMode work from publishing. `INCOMPLETE` is shown as missed-punch correction with no fabricated checkout.
- Self and managed correction flows now render/send paired actual check-in/check-out dates. Defaults derive from canonical timestamps in the retained historical window timezone. Validation converts tenant-local values without the browser timezone, enforces canonical window containment/order/less-than-24-hours, excludes the original ID, preserves incomplete/overlap safeguards, and defers cross-row checks when paging coverage is incomplete.
- Personal attendance loads the server current attendance-day window for initial month/default work date and self-service age eligibility, while preserving an explicitly selected historical month. Managed corrections fail closed without a frozen table-context work date instead of using browser midnight.
- New logic was split into policy-draft, attendance-window, dashboard-summary lifecycle, canonical date/time, and validation helpers. No SWR or package addition was introduced.

## Typed API integration

The dedicated attendance client is generated only from the reviewed Task 2 SDL:

`D:/work/heliorventures/hrms-documentation/docs/superpowers/reviews/2026-09-11-attendance-day-task2-schema.graphql`

The generator now maps `DateTime`, `NaiveDate`, and `NaiveTime` to `string`, matching the SDL wire contract rather than leaking `any` into UI state. Dedicated operations use unique names so future broad codegen does not collide with existing federated documents:

- `AttendanceCurrentDayWindow`
- `AttendanceCorrectionWindows`
- `AttendancePolicySettings`
- `PreviewAttendanceDayPolicy`
- `ScheduleAttendanceDayPolicy`
- `AttendancePunchDaySummary`
- `AttendancePunchToday`
- `AttendanceAddManualSegment` / `AttendanceUpdateManualSegment`
- `AttendanceAddManagedSegment` / `AttendanceUpdateManagedSegment`

Generation/SDL validation:

```text
node scripts/generate-attendance-client.mjs --schema-path D:\work\heliorventures\hrms-documentation\docs\superpowers\reviews\2026-09-11-attendance-day-task2-schema.graphql
[SUCCESS] Load GraphQL schemas
[SUCCESS] Load GraphQL documents
[SUCCESS] Generate
[SUCCESS] Generate outputs
exit 0
```

Generator syntax and cross-source duplicate-name validation:

```text
node --check scripts/generate-attendance-client.mjs
exit 0

node --input-type=module -e "import fs from 'node:fs'; import path from 'node:path'; import { parse } from 'graphql'; const walk=(dir)=>fs.readdirSync(dir,{withFileTypes:true}).flatMap((entry)=>entry.isDirectory()?walk(path.join(dir,entry.name)):[path.join(dir,entry.name)]); const files=walk('src').filter((file)=>file.endsWith('.graphql')); const seen=new Map(); const duplicates=[]; for(const file of files){for(const definition of parse(fs.readFileSync(file,'utf8')).definitions){if(definition.kind!=='OperationDefinition'||!definition.name)continue; const name=definition.name.value; if(seen.has(name))duplicates.push(name+' :: '+seen.get(name)+' :: '+file); else seen.set(name,file);}} if(duplicates.length){console.error(duplicates.join('\\n'));process.exit(1);} console.log('Unique GraphQL operation names: '+seen.size+' across '+files.length+' source document files.');"
Unique GraphQL operation names: 258 across 23 source document files.
exit 0
```

## TDD evidence

Initial RED, run from `D:/work/heliorventures/hrms-ui`:

```text
node node_modules/vitest/vitest.mjs run src/modules/admin/AdminAttendancePolicyPage.test.tsx src/modules/dashboard/components/PunchInOut.test.tsx src/utils/attendanceValidation.test.ts src/modules/attendance/components/ManualAttendanceModal.test.tsx src/modules/hr/attendance/AttendanceRegularizationModal.test.tsx
Test Files 5 failed (5)
Tests 17 failed | 30 passed (47)
```

The sandbox attempt first failed because esbuild could not spawn (`Error: spawn EPERM`); the same approved direct Vitest command was rerun with scoped elevation. Failures were behavior-specific: missing attendance-day policy UI, browser-day dashboard assumptions, missing actual-date fields, and old time-only/out-of-window validation.

Incremental GREEN evidence:

```text
admin + dashboard + validation: 3 files passed, 29/29 tests
managed correction modal: 1 file passed, 11/11 tests
self-service correction modal: 1 file passed, 7/7 tests
personal attendance ownership/paging/refresh + dashboard: 5 files passed, 29/29 tests
HR attendance page/context regressions: 2 files passed, 17/17 tests
```

Final combined GREEN, after all source and operation renaming:

```text
node node_modules/vitest/vitest.mjs run src/modules/admin/AdminAttendancePolicyPage.test.tsx src/modules/dashboard/components/PunchInOut.test.tsx src/utils/attendanceValidation.test.ts src/modules/attendance/components/ManualAttendanceModal.test.tsx src/modules/hr/attendance/AttendanceRegularizationModal.test.tsx src/modules/attendance/AttendancePage.editorOwnership.test.tsx src/modules/attendance/AttendancePage.ownership.test.tsx src/modules/attendance/AttendancePage.paging.test.tsx src/modules/attendance/AttendancePage.refresh.test.tsx src/modules/hr/HrAttendanceManagementPage.test.tsx src/modules/hr/HrAttendanceManagementPage.context.test.tsx
Test Files 11 passed (11)
Tests 78 passed (78)
Duration 39.67s
exit 0
```

## Static validation and lint evidence

```text
node node_modules/typescript/bin/tsc --noEmit
exit 0
```

The focused Task 3 production-source lint is clean after extracting the new policy, dashboard lifecycle, HR field/status, and canonical validation helpers:

```text
node node_modules/eslint/bin/eslint.js src/modules/admin/AdminAttendancePolicyPage.test.tsx src/modules/admin/AttendanceDayPolicySettings.tsx src/modules/admin/useAttendanceDayPolicyDraft.ts src/modules/attendance/AttendancePage.editorOwnership.test.tsx src/modules/attendance/AttendancePage.ownership.test.tsx src/modules/attendance/AttendancePage.paging.test.tsx src/modules/attendance/AttendancePage.refresh.test.tsx src/modules/attendance/attendancePageTestSupport.tsx src/modules/attendance/components/AttendancePageFeedback.tsx src/modules/attendance/components/ManualAttendanceModal.test.tsx src/modules/attendance/hooks/useAttendanceDayWindows.ts src/modules/attendance/hooks/useAttendanceEditor.ts src/modules/attendance/hooks/useAttendancePageModel.ts src/modules/dashboard/components/AttendanceSummaryDetails.tsx src/modules/dashboard/components/PunchInOut.tsx src/modules/dashboard/components/PunchInOut.test.tsx src/modules/dashboard/components/attendanceSummaryTypes.ts src/modules/dashboard/components/usePunchDaySummary.ts src/modules/hr/HrAttendanceManagementPage.context.test.tsx src/modules/hr/HrAttendanceManagementPage.test.tsx src/modules/hr/attendance/AttendanceRegularizationModal.tsx src/modules/hr/attendance/AttendanceRegularizationModal.test.tsx src/modules/hr/attendance/useAttendanceRegularization.ts src/utils/attendanceDay.ts src/utils/attendanceValidation.ts --report-unused-disable-directives --max-warnings 0 --format compact
exit 0
```

The all-changed-file lint remains non-zero only in files that already failed the same rules at `HEAD`. Read-only baseline comparison used these exact commands (one command per file):

```text
git show HEAD:src/modules/admin/AdminAttendancePolicyPage.tsx | node node_modules/eslint/bin/eslint.js --stdin --stdin-filename src/modules/admin/AdminAttendancePolicyPage.tsx --format compact
git show HEAD:src/modules/attendance/components/ManualAttendanceModal.tsx | node node_modules/eslint/bin/eslint.js --stdin --stdin-filename src/modules/attendance/components/ManualAttendanceModal.tsx --format compact
git show HEAD:src/modules/hr/attendance/AttendanceRegularizationModal.tsx | node node_modules/eslint/bin/eslint.js --stdin --stdin-filename src/modules/hr/attendance/AttendanceRegularizationModal.tsx --format compact
git show HEAD:src/utils/attendanceValidation.test.ts | node node_modules/eslint/bin/eslint.js --stdin --stdin-filename src/utils/attendanceValidation.test.ts --format compact
```

| File | HEAD findings | Current findings | Classification |
| --- | ---: | ---: | --- |
| `AdminAttendancePolicyPage.tsx` | 29 | 26 | legacy equality/complexity/a11y/size debt; three existing style findings removed |
| `ManualAttendanceModal.tsx` | 4 | 2 | legacy component-size and nested-ternary findings; unsafe-any findings removed by typed client |
| `AttendanceRegularizationModal.tsx` | 0 | 0 | introduced size finding removed through component extraction |
| `attendanceValidation.test.ts` | 1 | 1 | pre-existing describe callback size rule |

No lint rule was disabled and no unrelated Admin/live-punch refactor was undertaken.

The final non-passing subset was reproduced with:

```text
node node_modules/eslint/bin/eslint.js src/modules/admin/AdminAttendancePolicyPage.tsx src/modules/attendance/components/ManualAttendanceModal.tsx src/modules/hr/attendance/AttendanceRegularizationModal.tsx src/utils/attendanceValidation.test.ts --report-unused-disable-directives --max-warnings 0 --format compact
29 problems
exit 1
```

The final split changed-file result is therefore 29 findings total, all accounted for by the four baseline-compared files above; the same four files had 34 findings at `HEAD`. The complementary Task 3 set in the exact passing command has zero findings.

## Self-review and limitations

- Permission decisions use exact scoped permissions, not role names. Query/mutation state is owned by client plus tenant/user/session/work-date context, and late responses fail closed.
- Preview and schedule send the same `boundaryTime`, `effectiveWorkDate`, and `expectedRevision`; any draft change invalidates preview/confirmation. Conflict handling recognizes both GraphQL `ClientError` extension codes and plain test errors.
- Checkout may equal the canonical window end, matching the backend contract; check-in remains inside the half-open window. Valid after-midnight corrections such as `02:00` on the next calendar date are not rejected by the old same-date ordering rule.
- No browser signed-in acceptance, real gateway call, live data write, deployment, migration, or production validation was performed. Existing React Router future-flag warnings remain in page tests. Visual behavior therefore still needs signed-in browser acceptance after matching UI/service/gateway release.
- No commit was created.

## Independent review fix round 1 (2026-09-11)

The five Important review findings were reproduced and fixed at their ownership and validation boundaries:

- Attendance-day proposals now retain the exact immutable `boundaryTime`, `effectiveWorkDate`, and `expectedRevision` that produced the displayed preview. Draft edits invalidate the request generation, preview, and confirmation; scheduling can only submit that confirmed proposal.
- Admin policy loads, previews, schedules, conflict reloads, and live-punch policy state are owned by the exact client plus tenant/user/authorization identity. Replacing any owner fails closed and discards late completions even when permissions and revision numbers match.
- The personal attendance current-window query validates that each response contains the current instant, refreshes at the exact exclusive `endsAt`, and refreshes on focus/visible resume. Retained historical month selection and historical correction-window requests remain independent.
- Dashboard client replacement resets mutation busy/error/last-punch state while generation checks discard the prior client's completion.
- The intrinsic requested interval is checked against the strict `< 24 hours` cap before incomplete/out-of-range coverage can defer only cross-row overlap and aggregate checks.

Fix-round source/test files:

- `src/modules/admin/AdminAttendancePolicyPage.tsx`
- `src/modules/admin/AdminAttendancePolicyPage.test.tsx`
- `src/modules/admin/AttendanceDayPolicySettings.tsx`
- `src/modules/admin/useAttendanceDayPolicyDraft.ts`
- `src/modules/attendance/AttendancePage.editorOwnership.test.tsx`
- `src/modules/attendance/hooks/useAttendanceDayWindows.ts`
- `src/modules/attendance/hooks/useAttendanceDayWindows.test.tsx` (new)
- `src/modules/dashboard/components/PunchInOut.tsx`
- `src/modules/dashboard/components/PunchInOut.test.tsx`
- `src/utils/attendanceValidation.ts`
- `src/utils/attendanceValidation.test.ts`

Focused RED after adding the review regressions:

```text
node node_modules/vitest/vitest.mjs run src/modules/admin/AdminAttendancePolicyPage.test.tsx src/modules/attendance/hooks/useAttendanceDayWindows.test.tsx src/modules/dashboard/components/PunchInOut.test.tsx src/utils/attendanceValidation.test.ts
Test Files 4 failed (4)
Tests 8 failed | 32 passed (40)
exit 1
```

The failures covered obsolete delayed preview publication, stale same-revision context publication, missing exact-end/resume/expired-response current-window lifecycle, stuck dashboard mutation state after client-only replacement, and intrinsic 24-hour cap bypass with incomplete/out-of-range coverage. A corrected admin-only RED rerun after removing an unrelated textarea-label query issue remained behavior-specific: 2 ownership failures and 3 passes.

Initial focused GREEN:

```text
node node_modules/vitest/vitest.mjs run src/modules/admin/AdminAttendancePolicyPage.test.tsx src/modules/attendance/hooks/useAttendanceDayWindows.test.tsx src/modules/dashboard/components/PunchInOut.test.tsx src/utils/attendanceValidation.test.ts
Test Files 4 passed (4)
Tests 40 passed (40)
exit 0
```

Expanded affected regression suite before the final hook-only complexity extraction:

```text
node node_modules/vitest/vitest.mjs run src/modules/admin/AdminAttendancePolicyPage.test.tsx src/modules/attendance/hooks/useAttendanceDayWindows.test.tsx src/modules/dashboard/components/PunchInOut.test.tsx src/utils/attendanceValidation.test.ts src/modules/attendance/components/ManualAttendanceModal.test.tsx src/modules/hr/attendance/AttendanceRegularizationModal.test.tsx src/modules/attendance/AttendancePage.editorOwnership.test.tsx src/modules/attendance/AttendancePage.ownership.test.tsx src/modules/attendance/AttendancePage.paging.test.tsx src/modules/attendance/AttendancePage.refresh.test.tsx src/modules/hr/HrAttendanceManagementPage.test.tsx src/modules/hr/HrAttendanceManagementPage.context.test.tsx
Test Files 12 passed (12)
Tests 90 passed (90)
Duration 39.33s
exit 0
```

Final focused GREEN after the hook-only ownership/complexity extraction and test grouping:

```text
node node_modules/vitest/vitest.mjs run src/modules/admin/AdminAttendancePolicyPage.test.tsx src/modules/attendance/hooks/useAttendanceDayWindows.test.tsx src/modules/attendance/AttendancePage.editorOwnership.test.tsx src/modules/dashboard/components/PunchInOut.test.tsx src/utils/attendanceValidation.test.ts
Test Files 5 passed (5)
Tests 45 passed (45)
Duration 64.85s
exit 0
```

Final fix-round gates:

```text
node node_modules/typescript/bin/tsc --noEmit
exit 0

node node_modules/eslint/bin/eslint.js src/modules/admin/AdminAttendancePolicyPage.test.tsx src/modules/admin/AttendanceDayPolicySettings.tsx src/modules/admin/useAttendanceDayPolicyDraft.ts src/modules/attendance/AttendancePage.editorOwnership.test.tsx src/modules/attendance/hooks/useAttendanceDayWindows.ts src/modules/attendance/hooks/useAttendanceDayWindows.test.tsx src/modules/dashboard/components/PunchInOut.tsx src/modules/dashboard/components/PunchInOut.test.tsx src/utils/attendanceValidation.ts --report-unused-disable-directives --max-warnings 0 --format compact
exit 0

node scripts/generate-attendance-client.mjs --schema-path D:\work\heliorventures\hrms-documentation\docs\superpowers\reviews\2026-09-11-attendance-day-task2-schema.graphql
[SUCCESS] Generate outputs
exit 0

node --input-type=module -e "import fs from 'node:fs'; import path from 'node:path'; import { parse } from 'graphql'; const walk=(dir)=>fs.readdirSync(dir,{withFileTypes:true}).flatMap((entry)=>entry.isDirectory()?walk(path.join(dir,entry.name)):[path.join(dir,entry.name)]); const files=walk('src').filter((file)=>file.endsWith('.graphql')); const seen=new Map(); const duplicates=[]; for(const file of files){for(const definition of parse(fs.readFileSync(file,'utf8')).definitions){if(definition.kind!=='OperationDefinition'||!definition.name)continue; const name=definition.name.value; if(seen.has(name))duplicates.push(name+' :: '+seen.get(name)+' :: '+file); else seen.set(name,file);}} if(duplicates.length){console.error(duplicates.join('\\n'));process.exit(1);} console.log('Unique GraphQL operation names: '+seen.size+' across '+files.length+' source document files.');"
Unique GraphQL operation names: 258 across 23 source document files.
exit 0
```

The Admin page was compared to the exact pre-fix review snapshot with formatting disabled equally for both stdin/current runs because the preserved snapshot uses LF while this checkout's Prettier rule requires CRLF:

```text
Get-Content -Raw D:\work\heliorventures\hrms-documentation\.superpowers\sdd\2026-09-11-configurable-attendance-day\task3-fix1-base\src__modules__admin__AdminAttendancePolicyPage.tsx | node node_modules/eslint/bin/eslint.js --stdin --stdin-filename src/modules/admin/AdminAttendancePolicyPage.tsx --rule "prettier/prettier: off" --format compact
26 problems

node node_modules/eslint/bin/eslint.js src/modules/admin/AdminAttendancePolicyPage.tsx --rule "prettier/prettier: off" --format compact
23 problems
```

The current Admin page has one new function-complexity metric for the owner-gated component, while four pre-fix `no-unnecessary-condition` findings were removed; all substantive unsafe, hook-dependency, typing, and formatting findings introduced in this round are zero. Per the approved legacy-baseline limit, the component was not restructured further solely to chase an existing-file metric. Combining the current Admin 23 with the unchanged baseline-only `ManualAttendanceModal.tsx` 2, `AttendanceRegularizationModal.tsx` 0, and `attendanceValidation.test.ts` 1 leaves 26 changed-file findings total, versus 29 immediately before review fix round 1 and 34 at `HEAD`.

No source edits remain after these final gates. The only console noise was the already-recorded React Router v7 future-flag warnings. No browser, live API, backend, Cargo, migration, deployment, or commit action was performed.
