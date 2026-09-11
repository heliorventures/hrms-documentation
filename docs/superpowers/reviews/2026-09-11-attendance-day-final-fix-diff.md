# Final integrated fix wave: scoped diff

Pre-wave source captured before fixes for both final-review findings. UI only; backend/schema/auth unchanged. Existing files compared to exact snapshot, new files to NUL. All source frozen after covering21 tests/18 affected-page tests and typecheck;3 inherited duration eqeqeq lint findings match baseline.

## hrms-ui/src/modules/hr/attendance/ManagedAttendanceTable.test.tsx

```diff
diff --git a/D:/work/heliorventures/hrms-documentation/.superpowers/sdd/2026-09-11-configurable-attendance-day/final-fix-base/src__modules__hr__attendance__ManagedAttendanceTable.test.tsx b/src/modules/hr/attendance/ManagedAttendanceTable.test.tsx
index 55ddcef..10e903e 100644
--- a/D:/work/heliorventures/hrms-documentation/.superpowers/sdd/2026-09-11-configurable-attendance-day/final-fix-base/src__modules__hr__attendance__ManagedAttendanceTable.test.tsx
+++ b/src/modules/hr/attendance/ManagedAttendanceTable.test.tsx
@@ -108,3 +108,54 @@ describe('ManagedAttendanceTable', () => {
   });
 });
 
+describe('ManagedAttendanceTable canonical durations', () => {
+  it('uses canonical instants for an overnight Kolkata segment', () => {
+    render(
+      <ManagedAttendanceTable
+        rows={[
+          {
+            ...row,
+            checkInAt: '2026-09-11T17:30:00Z',
+            checkOutAt: '2026-09-11T22:30:00Z',
+            checkInTime: '23:00:00',
+            checkOutTime: '04:00:00',
+          },
+        ]}
+        loading={false}
+        errorMessage={null}
+      />
+    );
+
+    expect(screen.getAllByText('5h 00m')[0]).toBeTruthy();
+  });
+
+  it('uses canonical instants across DST and keeps partial canonical rows unavailable', () => {
+    render(
+      <ManagedAttendanceTable
+        rows={[
+          {
+            ...row,
+            id: 'dst-complete',
+            checkInAt: '2026-11-01T03:00:00Z',
+            checkOutAt: '2026-11-01T09:00:00Z',
+            checkInTime: '23:00:00',
+            checkOutTime: '04:00:00',
+          },
+          {
+            ...row,
+            id: 'canonical-incomplete',
+            checkInAt: '2026-11-01T03:00:00Z',
+            checkOutAt: null,
+            checkInTime: '23:00:00',
+            checkOutTime: '04:00:00',
+          },
+        ]}
+        loading={false}
+        errorMessage={null}
+      />
+    );
+
+    expect(screen.getAllByText('6h 00m')[0]).toBeTruthy();
+    expect(screen.getAllByText('Unavailable')[0]).toBeTruthy();
+  });
+});

```

## hrms-ui/src/modules/hr/attendance/ManagedAttendanceTable.tsx

```diff
diff --git a/D:/work/heliorventures/hrms-documentation/.superpowers/sdd/2026-09-11-configurable-attendance-day/final-fix-base/src__modules__hr__attendance__ManagedAttendanceTable.tsx b/src/modules/hr/attendance/ManagedAttendanceTable.tsx
index 05f8125..5e5899e 100644
--- a/D:/work/heliorventures/hrms-documentation/.superpowers/sdd/2026-09-11-configurable-attendance-day/final-fix-base/src__modules__hr__attendance__ManagedAttendanceTable.tsx
+++ b/src/modules/hr/attendance/ManagedAttendanceTable.tsx
@@ -2,7 +2,11 @@ import Badge from '../../../components/common/Badge';
 import Button from '../../../components/common/Button';
 import Card from '../../../components/common/Card';
 import DataTable, { type DataTableColumn } from '../../../components/common/DataTable';
-import { formatMinutesAsHhMm, naiveTimeToMinutes } from '../../../utils/attendanceDuration';
+import {
+  canonicalSegmentMinutes,
+  formatMinutesAsHhMm,
+  naiveTimeToMinutes,
+} from '../../../utils/attendanceDuration';
 import { formatBackendTime } from '../../../utils/timeFormat';
 
 import {
@@ -36,6 +40,11 @@ function statusVariant(status: string | null | undefined) {
 }
 
 function completedSameDayDuration(row: ManagedAttendanceRow): string {
+  const canonicalMinutes = canonicalSegmentMinutes(row);
+  if (canonicalMinutes !== undefined) {
+    return canonicalMinutes === null ? 'Unavailable' : formatMinutesAsHhMm(canonicalMinutes);
+  }
+
   const checkIn = naiveTimeToMinutes(String(row.checkInTime ?? ''));
   const checkOut = naiveTimeToMinutes(String(row.checkOutTime ?? ''));
   if (!Number.isFinite(checkIn) || !Number.isFinite(checkOut) || checkOut <= checkIn)
@@ -68,12 +77,12 @@ function attendanceColumns(
       cell: (row) => formatBackendTime(String(row.checkOutTime ?? '')),
     },
     { id: 'duration', header: 'Duration', cell: completedSameDayDuration, numeric: true },
-    { id: 'source', header: 'Source', cell: (row) => String(row.source ?? 'â€”') },
+    { id: 'source', header: 'Source', cell: (row) => String(row.source ?? '—') },
     { id: 'attendance-status', header: 'Attendance Status', cell: StatusCell },
     {
       id: 'regularization-status',
       header: 'Regularization Status',
-      cell: (row) => String(row.regularizationStatus ?? 'â€”'),
+      cell: (row) => String(row.regularizationStatus ?? '—'),
     },
   ];
   if (onAdd || onAdjust)
@@ -97,7 +106,7 @@ const DateCell = (row: ManagedAttendanceRow) => (
   <span className="whitespace-nowrap tabular-nums">{row.workDate}</span>
 );
 const StatusCell = (row: ManagedAttendanceRow) => (
-  <Badge variant={statusVariant(String(row.status ?? ''))}>{String(row.status ?? 'â€”')}</Badge>
+  <Badge variant={statusVariant(String(row.status ?? ''))}>{String(row.status ?? '—')}</Badge>
 );
 const ActionsCell = ({
   row,
@@ -145,7 +154,7 @@ const ManagedAttendanceTable = ({
 
   const state = tableState(loading, errorMessage, rows.length);
   const stateMessage = loading
-    ? 'Loading attendance recordsâ€¦'
+    ? 'Loading attendance records…'
     : (errorMessage ?? 'No attendance records match these filters.');
 
   return (
@@ -183,4 +192,3 @@ const ManagedAttendanceTable = ({
 };
 
 export default ManagedAttendanceTable;
-

```

## hrms-ui/src/modules/attendance/hooks/attendanceSegmentRows.ts

```diff
diff --git a/D:/work/heliorventures/hrms-documentation/.superpowers/sdd/2026-09-11-configurable-attendance-day/final-fix-base/src__modules__attendance__hooks__attendanceSegmentRows.ts b/src/modules/attendance/hooks/attendanceSegmentRows.ts
index 68a89d7..c4620f8 100644
--- a/D:/work/heliorventures/hrms-documentation/.superpowers/sdd/2026-09-11-configurable-attendance-day/final-fix-base/src__modules__attendance__hooks__attendanceSegmentRows.ts
+++ b/src/modules/attendance/hooks/attendanceSegmentRows.ts
@@ -1,4 +1,4 @@
-import { segmentWorkedMinutes } from '../../../utils/attendanceDuration';
+import { attendanceSegmentMinutes } from '../../../utils/attendanceDuration';
 import { isoDateRangeContains } from '../../../utils/calendarRange';
 import { formatBackendTime } from '../../../utils/timeFormat';
 import type { AttendanceRow, FlatSegmentRow } from '../types';
@@ -13,7 +13,7 @@ export function attendanceSegmentRows(
     if (!isoDateRangeContains(r.workDate, monthBounds.start, monthBounds.end)) continue;
     out.push({
       ...r,
-      segmentMinutes: segmentWorkedMinutes(r.checkInTime, r.checkOutTime),
+      segmentMinutes: attendanceSegmentMinutes(r),
     });
   }
   out.sort((a, b) => {
@@ -25,4 +25,3 @@ export function attendanceSegmentRows(
   });
   return out;
 }
-

```

## hrms-ui/src/modules/attendance/hooks/useAttendancePageModel.ts

```diff
diff --git a/D:/work/heliorventures/hrms-documentation/.superpowers/sdd/2026-09-11-configurable-attendance-day/final-fix-base/src__modules__attendance__hooks__useAttendancePageModel.ts b/src/modules/attendance/hooks/useAttendancePageModel.ts
index 6d2c9ae..9c3f8e5 100644
--- a/D:/work/heliorventures/hrms-documentation/.superpowers/sdd/2026-09-11-configurable-attendance-day/final-fix-base/src__modules__attendance__hooks__useAttendancePageModel.ts
+++ b/src/modules/attendance/hooks/useAttendancePageModel.ts
@@ -2,6 +2,7 @@ import { useEffect, useMemo, useRef } from 'react';
 
 import { authorizationStateKey, createPermissionService } from '../../../auth/permissionService';
 import { useAuth } from '../../../contexts/AuthContext';
+import { useTenant } from '../../../contexts/TenantContext';
 import { useGraphClient } from '../../../hooks/useGraphClient';
 import { attendancePolicyMessage } from '../../../utils/attendancePolicyMessage';
 import { monthBoundsIso } from '../../../utils/calendarRange';
@@ -13,6 +14,7 @@ import { useCurrentAttendanceDayWindow } from './useAttendanceDayWindows';
 import { useAttendanceEditor } from './useAttendanceEditor';
 import { useAttendancePeriod } from './useAttendancePeriod';
 import { usePersonalAttendanceBoard } from './usePersonalAttendanceBoard';
+import { useTenantCalendarDate } from './useTenantCalendarDate';
 
 export function useAttendancePageModel() {
   const client = useGraphClient('client');
@@ -80,7 +82,7 @@ export function useAttendancePageModel() {
     useAttendanceAdjustmentPolicy(client);
   const policyReady = adjustmentPolicyReady && currentWindow.phase === 'ready';
   const policyMessage = attendancePolicyMessage(adjustPolicyDays, canRegularize);
-  const editor = useAttendanceEditor(adjustPolicyDays, client, identity, currentWorkDate);
+  const editor = useTenantCalendarEditor(adjustPolicyDays, client, identity, currentWorkDate);
   const filteredSegments = useMemo(
     () => attendanceSegmentRows(currentBoard?.attendance ?? [], monthBounds),
     [currentBoard?.attendance, monthBounds]
@@ -123,3 +125,19 @@ export function useAttendancePageModel() {
 }
 export type AttendancePageModel = ReturnType<typeof useAttendancePageModel>;
 
+function useTenantCalendarEditor(
+  adjustPolicyDays: number,
+  client: object,
+  identity: string,
+  currentWorkDate: string | null
+) {
+  const { currentTenant } = useTenant();
+  const currentCalendarDate = useTenantCalendarDate(currentTenant.timezone, identity);
+  return useAttendanceEditor(
+    adjustPolicyDays,
+    client,
+    identity,
+    currentWorkDate,
+    currentCalendarDate
+  );
+}

```

## hrms-ui/src/modules/attendance/AttendancePage.editorOwnership.test.tsx

```diff
diff --git a/D:/work/heliorventures/hrms-documentation/.superpowers/sdd/2026-09-11-configurable-attendance-day/final-fix-base/src__modules__attendance__AttendancePage.editorOwnership.test.tsx b/src/modules/attendance/AttendancePage.editorOwnership.test.tsx
index 22e49eb..faaa870 100644
--- a/D:/work/heliorventures/hrms-documentation/.superpowers/sdd/2026-09-11-configurable-attendance-day/final-fix-base/src__modules__attendance__AttendancePage.editorOwnership.test.tsx
+++ b/src/modules/attendance/AttendancePage.editorOwnership.test.tsx
@@ -14,6 +14,7 @@ import {
   policyResponse,
   renderPage,
   rerenderPage,
+  tenantState,
 } from './attendancePageTestSupport';
 
 it('discards an open attendance edit when the client or employee changes, including returning to the previous identity', async () => {
@@ -108,3 +109,42 @@ it('preserves a selected historical month while the current attendance window re
   expect(month.value).toBe('6');
 });
 
+it('expires self-adjustment at tenant midnight while retaining the attendance work-date default', async () => {
+  vi.setSystemTime(new Date('2026-09-11T18:29:59.900Z'));
+  tenantState.timezone = 'Asia/Kolkata';
+  authState.clientSession.permissions = new Set(['attendance:punch_self']);
+  const historicalRow = {
+    ...boardResponse().myAttendance.edges[0].node,
+    id: 'deadline-row',
+    workDate: '2026-08-28',
+  };
+  graphClient.request.mockImplementation((document: unknown) => {
+    if (document === AttendanceAdjustmentPolicyDocument) return Promise.resolve(policyResponse);
+    if (document === AttendanceCurrentDayWindowDocument) {
+      return Promise.resolve({
+        attendanceDayWindow: {
+          ...currentWindowResponse.attendanceDayWindow,
+          workDate: '2026-09-11',
+          startsAt: '2026-09-10T23:30:00Z',
+          endsAt: '2026-09-11T23:30:00Z',
+        },
+      });
+    }
+    return Promise.resolve(boardResponse({ rows: [historicalRow] }));
+  });
+  renderPage();
+
+  fireEvent.change(await screen.findByLabelText<HTMLSelectElement>('Month'), {
+    target: { value: '7' },
+  });
+  const adjust = await screen.findByRole<HTMLButtonElement>('button', { name: 'Adjust day' });
+  expect(adjust.disabled).toBe(false);
+  await act(async () => {
+    vi.advanceTimersByTime(100);
+    await Promise.resolve();
+  });
+  expect(adjust.disabled).toBe(true);
+
+  fireEvent.click(screen.getByRole('button', { name: 'Add Missed Punches' }));
+  expect(screen.getByLabelText<HTMLInputElement>('Work Date').value).toBe('2026-09-11');
+});

```

## hrms-ui/src/utils/attendanceDuration.ts

```diff
diff --git a/D:/work/heliorventures/hrms-documentation/.superpowers/sdd/2026-09-11-configurable-attendance-day/final-fix-base/src__utils__attendanceDuration.ts b/src/utils/attendanceDuration.ts
index 4bc8aa9..b59fdfc 100644
--- a/D:/work/heliorventures/hrms-documentation/.superpowers/sdd/2026-09-11-configurable-attendance-day/final-fix-base/src__utils__attendanceDuration.ts
+++ b/src/utils/attendanceDuration.ts
@@ -21,6 +21,42 @@ export function segmentWorkedMinutes(
   return diff > 0 ? diff : null;
 }
 
+export interface AttendanceSegmentDurationInput {
+  checkInAt?: unknown;
+  checkOutAt?: unknown;
+  checkInTime?: string | null;
+  checkOutTime?: string | null;
+}
+
+/**
+ * Returns undefined only for legacy rows where both canonical timestamps are absent.
+ * A partial or malformed canonical pair is intentionally incomplete and must not fall
+ * back to wall-clock values, which can be ambiguous around overnight and DST boundaries.
+ */
+export function canonicalSegmentMinutes({
+  checkInAt,
+  checkOutAt,
+}: Pick<AttendanceSegmentDurationInput, 'checkInAt' | 'checkOutAt'>): number | null | undefined {
+  const checkInAbsent = checkInAt === null || checkInAt === undefined;
+  const checkOutAbsent = checkOutAt === null || checkOutAt === undefined;
+  if (checkInAbsent && checkOutAbsent) return undefined;
+  if (typeof checkInAt !== 'string' || typeof checkOutAt !== 'string') return null;
+
+  const checkInMillis = Date.parse(checkInAt);
+  const checkOutMillis = Date.parse(checkOutAt);
+  if (!Number.isFinite(checkInMillis) || !Number.isFinite(checkOutMillis)) return null;
+
+  const durationMinutes = (checkOutMillis - checkInMillis) / 60_000;
+  return durationMinutes > 0 ? durationMinutes : null;
+}
+
+export function attendanceSegmentMinutes(input: AttendanceSegmentDurationInput): number | null {
+  const canonicalMinutes = canonicalSegmentMinutes(input);
+  return canonicalMinutes === undefined
+    ? segmentWorkedMinutes(input.checkInTime, input.checkOutTime)
+    : canonicalMinutes;
+}
+
 export function formatMinutesAsHhMm(totalMinutes: number): string {
   const roundedMinutes = Math.round(totalMinutes);
   const h = Math.floor(roundedMinutes / 60);
@@ -34,4 +70,3 @@ export function formatLatLng(lat?: string | null, lng?: string | null): string {
   const ln = lng?.trim() || '-';
   return `${la}, ${ln}`;
 }
-

```

## hrms-ui/src/modules/attendance/hooks/useAttendanceEditor.ts

```diff
diff --git a/D:/work/heliorventures/hrms-documentation/.superpowers/sdd/2026-09-11-configurable-attendance-day/final-fix-base/src__modules__attendance__hooks__useAttendanceEditor.ts b/src/modules/attendance/hooks/useAttendanceEditor.ts
index a93d454..fe6822d 100644
--- a/D:/work/heliorventures/hrms-documentation/.superpowers/sdd/2026-09-11-configurable-attendance-day/final-fix-base/src__modules__attendance__hooks__useAttendanceEditor.ts
+++ b/src/modules/attendance/hooks/useAttendanceEditor.ts
@@ -13,7 +13,8 @@ export function useAttendanceEditor(
   adjustPolicyDays: number,
   client: object,
   identity: string,
-  currentWorkDate: string | null
+  currentWorkDate: string | null,
+  currentCalendarDate: string
 ) {
   const owner = useMemo(() => ({ client, identity }), [client, identity]);
   const currentOwner = useRef<typeof owner | null>(owner);
@@ -39,7 +40,7 @@ export function useAttendanceEditor(
 
   const selfAdjustAllowedForDate = (workIso: string) => {
     const work = dateOrdinal(workIso);
-    const current = currentWorkDate ? dateOrdinal(currentWorkDate) : null;
+    const current = dateOrdinal(currentCalendarDate);
     if (work === null || current === null) return false;
     const delta = current - work;
     if (delta < 0) return false;
@@ -55,4 +56,3 @@ export function useAttendanceEditor(
     selfAdjustAllowedForDate,
   };
 }
-

```

## hrms-ui/src/modules/attendance/attendancePageTestSupport.tsx

```diff
diff --git a/D:/work/heliorventures/hrms-documentation/.superpowers/sdd/2026-09-11-configurable-attendance-day/final-fix-base/src__modules__attendance__attendancePageTestSupport.tsx b/src/modules/attendance/attendancePageTestSupport.tsx
index d45b13c..4a8e7d9 100644
--- a/D:/work/heliorventures/hrms-documentation/.superpowers/sdd/2026-09-11-configurable-attendance-day/final-fix-base/src__modules__attendance__attendancePageTestSupport.tsx
+++ b/src/modules/attendance/attendancePageTestSupport.tsx
@@ -26,6 +26,7 @@ const authState = vi.hoisted(() => ({
     mustChangePassword: false,
   } as ParsedClientSession,
 }));
+const tenantState = vi.hoisted(() => ({ timezone: 'Asia/Kolkata' }));
 
 vi.mock('../../hooks/useGraphClient', () => ({
   useGraphClient: () => graphClientState.current,
@@ -34,6 +35,9 @@ vi.mock('../../hooks/useGraphClient', () => ({
 vi.mock('../../contexts/AuthContext', () => ({
   useAuth: () => authState,
 }));
+vi.mock('../../contexts/TenantContext', () => ({
+  useTenant: () => ({ currentTenant: { timezone: tenantState.timezone } }),
+}));
 
 export const policyResponse = { attendanceAdjustmentPolicy: { maxSelfAdjustDays: 14 } };
 export const currentWindowResponse = {
@@ -134,6 +138,7 @@ beforeEach(() => {
   graphClientState.current = graphClient;
   authState.clientSession.employeeId = 'employee-self';
   authState.clientSession.permissions = new Set();
+  tenantState.timezone = 'Asia/Kolkata';
   graphClient.request.mockReset();
   graphClient.request.mockImplementation((document: unknown) => {
     if (document === AttendanceAdjustmentPolicyDocument) return Promise.resolve(policyResponse);
@@ -152,5 +157,4 @@ afterEach(() => {
 export const requestCalls = () =>
   graphClient.request.mock.calls as Array<[unknown, Record<string, unknown>?]>;
 
-export { graphClientState, authState };
-
+export { graphClientState, authState, tenantState };

```

## hrms-ui/src/modules/attendance/hooks/useTenantCalendarDate.test.tsx

```diff
diff --git a/src/modules/attendance/hooks/useTenantCalendarDate.test.tsx b/src/modules/attendance/hooks/useTenantCalendarDate.test.tsx
new file mode 100644
index 0000000..7196032
--- /dev/null
+++ b/src/modules/attendance/hooks/useTenantCalendarDate.test.tsx
@@ -0,0 +1,44 @@
+// @vitest-environment jsdom
+
+import { act, cleanup, renderHook } from '@testing-library/react';
+import { afterEach, beforeEach, expect, it, vi } from 'vitest';
+
+import { useTenantCalendarDate } from './useTenantCalendarDate';
+
+beforeEach(() => {
+  vi.useFakeTimers({ shouldAdvanceTime: true });
+  vi.setSystemTime(new Date('2026-09-11T18:29:59.999Z'));
+});
+
+afterEach(() => {
+  cleanup();
+  vi.useRealTimers();
+});
+
+it('expires eligibility at the exact tenant-calendar midnight', async () => {
+  const { result } = renderHook(() => useTenantCalendarDate('Asia/Kolkata', 'tenant-1:user-1'));
+  expect(result.current).toBe('2026-09-11');
+
+  await act(async () => {
+    vi.advanceTimersByTime(1);
+    await Promise.resolve();
+  });
+
+  expect(result.current).toBe('2026-09-12');
+});
+
+it('refreshes a suspended owner on focus and resets for a replacement identity', async () => {
+  let identity = 'tenant-1:user-1';
+  const { result, rerender } = renderHook(() => useTenantCalendarDate('Asia/Kolkata', identity));
+  vi.setSystemTime(new Date('2026-09-12T18:30:00Z'));
+  await act(async () => {
+    window.dispatchEvent(new Event('focus'));
+    await Promise.resolve();
+  });
+  expect(result.current).toBe('2026-09-13');
+
+  identity = 'tenant-2:user-2';
+  vi.setSystemTime(new Date('2026-09-13T18:30:00Z'));
+  rerender();
+  expect(result.current).toBe('2026-09-14');
+});

```

## hrms-ui/src/modules/attendance/hooks/attendanceSegmentRows.test.ts

```diff
diff --git a/src/modules/attendance/hooks/attendanceSegmentRows.test.ts b/src/modules/attendance/hooks/attendanceSegmentRows.test.ts
new file mode 100644
index 0000000..dd37b65
--- /dev/null
+++ b/src/modules/attendance/hooks/attendanceSegmentRows.test.ts
@@ -0,0 +1,38 @@
+import { describe, expect, it } from 'vitest';
+
+import type { AttendanceRow } from '../types';
+
+import { attendanceSegmentRows } from './attendanceSegmentRows';
+
+const row = (overrides: Partial<AttendanceRow> = {}): AttendanceRow => ({
+  id: 'segment-1',
+  employeeId: 'employee-1',
+  workDate: '2026-10-31',
+  checkInAt: '2026-11-01T03:00:00Z',
+  checkOutAt: '2026-11-01T09:00:00Z',
+  checkInTime: '23:00:00',
+  checkOutTime: '04:00:00',
+  status: 'PRESENT',
+  source: 'WEB',
+  ...overrides,
+});
+
+describe('attendanceSegmentRows canonical duration', () => {
+  it('shows six actual hours across the New York DST fallback', () => {
+    const [segment] = attendanceSegmentRows([row()], {
+      start: '2026-10-01',
+      end: '2026-10-31',
+    });
+
+    expect(segment.segmentMinutes).toBe(360);
+  });
+
+  it('keeps an incomplete canonical row incomplete despite a legacy checkout time', () => {
+    const [segment] = attendanceSegmentRows([row({ checkOutAt: null })], {
+      start: '2026-10-01',
+      end: '2026-10-31',
+    });
+
+    expect(segment.segmentMinutes).toBeNull();
+  });
+});

```

## hrms-ui/src/modules/attendance/hooks/useTenantCalendarDate.ts

```diff
diff --git a/src/modules/attendance/hooks/useTenantCalendarDate.ts b/src/modules/attendance/hooks/useTenantCalendarDate.ts
new file mode 100644
index 0000000..804b6e6
--- /dev/null
+++ b/src/modules/attendance/hooks/useTenantCalendarDate.ts
@@ -0,0 +1,67 @@
+import { useEffect, useState } from 'react';
+
+import { millisecondsUntilTenantDateChange } from '../../../utils/tenantCalendar';
+import { tenantDateKey } from '../../../utils/tenantTime';
+
+interface TenantCalendarDateState {
+  ownerKey: string;
+  date: string;
+}
+
+function currentTenantDate(timezone: string): string {
+  return tenantDateKey(new Date(), timezone);
+}
+
+/**
+ * Maintains the tenant calendar date independently of the configured attendance-day cutoff.
+ * The owner key prevents a prior tenant/user timer from publishing into a replacement context.
+ */
+export function useTenantCalendarDate(timezone: string, identity: string): string {
+  const ownerKey = `${identity}:${timezone}`;
+  const [state, setState] = useState<TenantCalendarDateState>(() => ({
+    ownerKey,
+    date: currentTenantDate(timezone),
+  }));
+  const visibleDate = state.ownerKey === ownerKey ? state.date : currentTenantDate(timezone);
+
+  useEffect(() => {
+    let timerId: number | null = null;
+    let active = true;
+
+    const refresh = () => {
+      if (!active) return;
+      setState({ ownerKey, date: currentTenantDate(timezone) });
+    };
+    const schedule = () => {
+      if (timerId !== null) window.clearTimeout(timerId);
+      const now = new Date();
+      timerId = window.setTimeout(
+        () => {
+          refresh();
+          schedule();
+        },
+        millisecondsUntilTenantDateChange(now, timezone)
+      );
+    };
+    const resume = () => {
+      refresh();
+      schedule();
+    };
+    const handleVisibility = () => {
+      if (document.visibilityState === 'visible') resume();
+    };
+
+    refresh();
+    schedule();
+    window.addEventListener('focus', resume);
+    document.addEventListener('visibilitychange', handleVisibility);
+    return () => {
+      active = false;
+      if (timerId !== null) window.clearTimeout(timerId);
+      window.removeEventListener('focus', resume);
+      document.removeEventListener('visibilitychange', handleVisibility);
+    };
+  }, [ownerKey, timezone]);
+
+  return visibleDate;
+}

```

## hrms-ui/src/utils/tenantCalendar.test.ts

```diff
diff --git a/D:/work/heliorventures/hrms-documentation/.superpowers/sdd/2026-09-11-configurable-attendance-day/final-fix-base/src__utils__tenantCalendar.test.ts b/src/utils/tenantCalendar.test.ts
index 9a4dc2d..68a6001 100644
--- a/D:/work/heliorventures/hrms-documentation/.superpowers/sdd/2026-09-11-configurable-attendance-day/final-fix-base/src__utils__tenantCalendar.test.ts
+++ b/src/utils/tenantCalendar.test.ts
@@ -1,6 +1,6 @@
 import { describe, expect, it } from 'vitest';
 
-import { tenantCalendarPeriod } from './tenantCalendar';
+import { millisecondsUntilTenantDateChange, tenantCalendarPeriod } from './tenantCalendar';
 
 describe('tenantCalendarPeriod', () => {
   it('uses the tenant timezone when browser-local and tenant calendar dates differ', () => {
@@ -15,5 +15,10 @@ describe('tenantCalendarPeriod', () => {
   it('rejects invalid tenant timezone configuration', () => {
     expect(() => tenantCalendarPeriod(new Date(), 'Not/A-Timezone')).toThrow(RangeError);
   });
-});
 
+  it('finds the exact next tenant midnight independently of the browser timezone', () => {
+    expect(
+      millisecondsUntilTenantDateChange(new Date('2026-09-11T18:29:59.900Z'), 'Asia/Kolkata')
+    ).toBe(100);
+  });
+});

```

## hrms-ui/src/utils/attendanceDuration.test.ts

```diff
diff --git a/D:/work/heliorventures/hrms-documentation/.superpowers/sdd/2026-09-11-configurable-attendance-day/final-fix-base/src__utils__attendanceDuration.test.ts b/src/utils/attendanceDuration.test.ts
index 0463f3a..1b4216c 100644
--- a/D:/work/heliorventures/hrms-documentation/.superpowers/sdd/2026-09-11-configurable-attendance-day/final-fix-base/src__utils__attendanceDuration.test.ts
+++ b/src/utils/attendanceDuration.test.ts
@@ -1,6 +1,6 @@
 import { describe, expect, it } from 'vitest';
 
-import { formatMinutesAsHhMm } from './attendanceDuration';
+import { attendanceSegmentMinutes, formatMinutesAsHhMm } from './attendanceDuration';
 
 describe('formatMinutesAsHhMm', () => {
   it('rounds the total before splitting hours and minutes', () => {
@@ -10,3 +10,35 @@ describe('formatMinutesAsHhMm', () => {
   });
 });
 
+describe('attendanceSegmentMinutes', () => {
+  it('uses canonical instants across the New York DST fallback', () => {
+    expect(
+      attendanceSegmentMinutes({
+        checkInAt: '2026-11-01T03:00:00Z',
+        checkOutAt: '2026-11-01T09:00:00Z',
+        checkInTime: '23:00:00',
+        checkOutTime: '04:00:00',
+      })
+    ).toBe(360);
+  });
+
+  it('does not fall back to wall times for an incomplete canonical segment', () => {
+    expect(
+      attendanceSegmentMinutes({
+        checkInAt: '2026-09-11T17:30:00Z',
+        checkOutAt: null,
+        checkInTime: '23:00:00',
+        checkOutTime: '04:00:00',
+      })
+    ).toBeNull();
+  });
+
+  it('retains the legacy overnight fallback only when canonical timestamps are absent', () => {
+    expect(
+      attendanceSegmentMinutes({
+        checkInTime: '23:00:00',
+        checkOutTime: '04:00:00',
+      })
+    ).toBe(300);
+  });
+});

```

## hrms-ui/src/utils/tenantCalendar.ts

```diff
diff --git a/D:/work/heliorventures/hrms-documentation/.superpowers/sdd/2026-09-11-configurable-attendance-day/final-fix-base/src__utils__tenantCalendar.ts b/src/utils/tenantCalendar.ts
index 14c64b3..5de4bf8 100644
--- a/D:/work/heliorventures/hrms-documentation/.superpowers/sdd/2026-09-11-configurable-attendance-day/final-fix-base/src__utils__tenantCalendar.ts
+++ b/src/utils/tenantCalendar.ts
@@ -1,3 +1,5 @@
+import { tenantDateKey } from './tenantTime';
+
 export interface TenantCalendarPeriod {
   month: number;
   year: number;
@@ -28,10 +30,7 @@ export function normalizeTenantTimezone(value: unknown): string {
   return normalized;
 }
 
-export function tenantCalendarPeriod(
-  instant: Date,
-  timezone: string
-): TenantCalendarPeriod {
+export function tenantCalendarPeriod(instant: Date, timezone: string): TenantCalendarPeriod {
   const parts = calendarFormatter(timezone).formatToParts(instant);
   const month = Number(parts.find((part) => part.type === 'month')?.value);
   const year = Number(parts.find((part) => part.type === 'year')?.value);
@@ -47,3 +46,25 @@ export function millisecondsUntilNextMinute(instant: Date): number {
   return 60_000 - elapsed + 100;
 }
 
+/** Finds the first instant belonging to the tenant's next calendar date. */
+export function millisecondsUntilTenantDateChange(instant: Date, timezone: string): number {
+  const start = instant.getTime();
+  if (!Number.isFinite(start)) throw new RangeError('A valid instant is required.');
+
+  const currentDate = tenantDateKey(instant, timezone);
+  let lowerBound = start;
+  let upperBound = start + 48 * 60 * 60 * 1_000;
+  if (tenantDateKey(new Date(upperBound), timezone) === currentDate) {
+    throw new RangeError('The next tenant calendar date could not be determined.');
+  }
+
+  while (lowerBound + 1 < upperBound) {
+    const midpoint = lowerBound + Math.floor((upperBound - lowerBound) / 2);
+    if (tenantDateKey(new Date(midpoint), timezone) === currentDate) {
+      lowerBound = midpoint;
+    } else {
+      upperBound = midpoint;
+    }
+  }
+  return upperBound - start;
+}

```

