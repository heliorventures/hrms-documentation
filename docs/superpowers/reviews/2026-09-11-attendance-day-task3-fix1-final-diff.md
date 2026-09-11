# Task 3 fix round 1 final scoped diff

Exact pre-review-fix snapshot to current source. Read with task3 review and report. No backend changes.

## hrms-ui/src/modules/admin/AdminAttendancePolicyPage.tsx

```diff
warning: in the working copy of 'D:/work/heliorventures/hrms-documentation/.superpowers/sdd/2026-09-11-configurable-attendance-day/task3-fix1-base/src__modules__admin__AdminAttendancePolicyPage.tsx', LF will be replaced by CRLF the next time Git touches it
diff --git a/D:/work/heliorventures/hrms-documentation/.superpowers/sdd/2026-09-11-configurable-attendance-day/task3-fix1-base/src__modules__admin__AdminAttendancePolicyPage.tsx b/src/modules/admin/AdminAttendancePolicyPage.tsx
index dfe4340..9f9bf72 100644
--- a/D:/work/heliorventures/hrms-documentation/.superpowers/sdd/2026-09-11-configurable-attendance-day/task3-fix1-base/src__modules__admin__AdminAttendancePolicyPage.tsx
+++ b/src/modules/admin/AdminAttendancePolicyPage.tsx
@@ -1,11 +1,19 @@
-import { useCallback, useEffect, useState, type FormEvent } from 'react';
+import {
+  useCallback,
+  useEffect,
+  useLayoutEffect,
+  useMemo,
+  useRef,
+  useState,
+  type FormEvent,
+} from 'react';
 
 import {
   AttendancePolicySettingsDocument,
   type AttendancePolicySettingsQuery,
 } from '../../api/attendance/graphql';
 import { ClientOpsUpsertAttendancePunchPolicyDocument } from '../../api/graphql/graphql';
-import { createPermissionService } from '../../auth/permissionService';
+import { authorizationStateKey, createPermissionService } from '../../auth/permissionService';
 import Button from '../../components/common/Button';
 import Card from '../../components/common/Card';
 import Input from '../../components/common/Input';
@@ -42,8 +50,12 @@ const isValidIpv4CidrToken = (token: string) => {
   return mask >= 0 && mask <= 32;
 };
 
-const AuthorizedAttendancePolicyPage = () => {
+const AuthorizedAttendancePolicyPage = ({ identity }: { identity: string }) => {
   const client = useGraphClient('client');
+  const owner = useMemo(() => ({ client, identity }), [client, identity]);
+  const mounted = useRef(false);
+  const generation = useRef(0);
+  const [loadedOwner, setLoadedOwner] = useState<typeof owner | null>(null);
   const [policy, setPolicy] = useState<{
     id?: string | null;
     isEnforced: boolean;
@@ -78,43 +90,67 @@ const AuthorizedAttendancePolicyPage = () => {
   const [ipAllowlist, setIpAllowlist] = useState('');
 
   const load = useCallback(async () => {
+    void identity;
     return client.request<AttendancePolicySettingsQuery>(AttendancePolicySettingsDocument);
-  }, [client]);
+  }, [client, identity]);
+
+  const ownsRequest = useCallback(
+    (request: number) => mounted.current && generation.current === request,
+    []
+  );
+
+  const applySettings = useCallback(
+    (result: AttendancePolicySettingsQuery) => {
+      setPolicy(result.attendancePunchPolicy);
+      setDayPolicy(result.attendanceDayPolicy);
+      setShifts(result.shifts);
+      const punchPolicy = result.attendancePunchPolicy;
+      setIsEnforced(punchPolicy.isEnforced);
+      setSiteLatitude(punchPolicy.siteLatitude != null ? String(punchPolicy.siteLatitude) : '');
+      setSiteLongitude(punchPolicy.siteLongitude != null ? String(punchPolicy.siteLongitude) : '');
+      setMaxDistanceMeters(
+        punchPolicy.maxDistanceMeters != null ? String(punchPolicy.maxDistanceMeters) : ''
+      );
+      setIpAllowlist(punchPolicy.ipAllowlist ?? '');
+      setLoadedOwner(owner);
+    },
+    [owner]
+  );
+
+  useLayoutEffect(() => {
+    mounted.current = true;
+    generation.current += 1;
+    setLoadedOwner(null);
+    setLoading(true);
+    setError(null);
+    setSaving(false);
+    setFormError(null);
+    return () => {
+      mounted.current = false;
+      generation.current += 1;
+    };
+  }, [owner]);
 
   useEffect(() => {
-    let c = false;
+    const request = generation.current;
     void (async () => {
       try {
-        setLoading(true);
-        setError(null);
-        const r = await load();
-        if (c) return;
-        setPolicy(r.attendancePunchPolicy);
-        setDayPolicy(r.attendanceDayPolicy);
-        setShifts(r.shifts);
-        const p = r.attendancePunchPolicy;
-        setIsEnforced(p.isEnforced);
-        setSiteLatitude(p.siteLatitude != null ? String(p.siteLatitude) : '');
-        setSiteLongitude(p.siteLongitude != null ? String(p.siteLongitude) : '');
-        setMaxDistanceMeters(p.maxDistanceMeters != null ? String(p.maxDistanceMeters) : '');
-        setIpAllowlist(p.ipAllowlist ?? '');
+        const result = await load();
+        if (!ownsRequest(request)) return;
+        applySettings(result);
       } catch (e) {
-        if (!c) setError(graphQlUserMessage(e));
+        if (ownsRequest(request)) setError(graphQlUserMessage(e));
       } finally {
-        if (!c) setLoading(false);
+        if (ownsRequest(request)) setLoading(false);
       }
     })();
-    return () => {
-      c = true;
-    };
-  }, [load]);
+  }, [applySettings, load, ownsRequest]);
 
   const reloadPolicy = useCallback(async () => {
+    const request = generation.current;
     const result = await load();
-    setPolicy(result.attendancePunchPolicy);
-    setDayPolicy(result.attendanceDayPolicy);
-    setShifts(result.shifts);
-  }, [load]);
+    if (ownsRequest(request)) applySettings(result);
+  }, [applySettings, load, ownsRequest]);
 
   const onSave = async (e: FormEvent) => {
     e.preventDefault();
@@ -156,6 +192,7 @@ const AuthorizedAttendancePolicyPage = () => {
       );
       return;
     }
+    const request = generation.current;
     setSaving(true);
     try {
       await client.request(ClientOpsUpsertAttendancePunchPolicyDocument, {
@@ -167,15 +204,18 @@ const AuthorizedAttendancePolicyPage = () => {
           ipAllowlist: ipAllowlist.trim() || null,
         },
       });
+      if (!ownsRequest(request)) return;
       const r = await load();
-      if (r.attendancePunchPolicy) setPolicy(r.attendancePunchPolicy);
+      if (ownsRequest(request)) applySettings(r);
     } catch (err) {
-      setFormError(graphQlUserMessage(err));
+      if (ownsRequest(request)) setFormError(graphQlUserMessage(err));
     } finally {
-      setSaving(false);
+      if (ownsRequest(request)) setSaving(false);
     }
   };
 
+  const ownerIsCurrent = loadedOwner === owner;
+
   return (
     <div className="space-y-4">
       <h1 className="sr-only">Attendance punch policy</h1>
@@ -184,15 +224,18 @@ const AuthorizedAttendancePolicyPage = () => {
           <p className="text-sm text-red-600 dark:text-red-400">{error}</p>
         </Card>
       )}
-      {dayPolicy ? (
+      {ownerIsCurrent && dayPolicy ? (
         <AttendanceDayPolicySettings
+          ownerKey={identity}
           policy={dayPolicy}
-          onPolicyChanged={setDayPolicy}
+          onPolicyChanged={(nextPolicy) => {
+            if (loadedOwner === owner) setDayPolicy(nextPolicy);
+          }}
           reloadPolicy={reloadPolicy}
         />
       ) : null}
       <Card title="Live Punch Policy">
-        {loading ? (
+        {loading || !ownerIsCurrent ? (
           <p className="text-sm text-gray-500">Loading...</p>
         ) : (
           <form onSubmit={(e) => void onSave(e)} className="space-y-4">
@@ -252,14 +295,14 @@ const AuthorizedAttendancePolicyPage = () => {
         <Card title="Shifts">
           {loading ? (
             <p className="text-sm text-gray-500">Loading...</p>
-          ) : shifts.length ? (
+          ) : ownerIsCurrent && shifts.length ? (
             <ul className="divide-y divide-gray-200 dark:divide-gray-700">
               {shifts.map((s) => (
                 <li key={s.id} className="py-3">
                   <p className="font-medium text-gray-900 dark:text-white">{s.name}</p>
                   <p className="text-xs text-gray-500">
-                    {s.startTime ?? 'â€”'} â€“ {s.endTime ?? 'â€”'}
-                    {s.workHours != null ? ` Â· ${s.workHours}h` : ''}
+                    {s.startTime ?? '—'} – {s.endTime ?? '—'}
+                    {s.workHours != null ? ` · ${s.workHours}h` : ''}
                   </p>
                 </li>
               ))}
@@ -274,7 +317,7 @@ const AuthorizedAttendancePolicyPage = () => {
 };
 
 const AdminAttendancePolicyPage = () => {
-  const { clientSession } = useAuth();
+  const { clientSession, tenantId, user } = useAuth();
   const permissions = createPermissionService(clientSession);
   if (!permissions.canRoute('/admin/attendance-policy')) {
     return (
@@ -283,7 +326,8 @@ const AdminAttendancePolicyPage = () => {
       </p>
     );
   }
-  return <AuthorizedAttendancePolicyPage />;
+  const identity = `${tenantId ?? ''}:${user?.id ?? ''}:${authorizationStateKey(clientSession)}`;
+  return <AuthorizedAttendancePolicyPage key={identity} identity={identity} />;
 };
 
 export default AdminAttendancePolicyPage;

```

## hrms-ui/src/modules/admin/AdminAttendancePolicyPage.test.tsx

```diff
warning: in the working copy of 'D:/work/heliorventures/hrms-documentation/.superpowers/sdd/2026-09-11-configurable-attendance-day/task3-fix1-base/src__modules__admin__AdminAttendancePolicyPage.test.tsx', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of 'src/modules/admin/AdminAttendancePolicyPage.test.tsx', LF will be replaced by CRLF the next time Git touches it
diff --git a/D:/work/heliorventures/hrms-documentation/.superpowers/sdd/2026-09-11-configurable-attendance-day/task3-fix1-base/src__modules__admin__AdminAttendancePolicyPage.test.tsx b/src/modules/admin/AdminAttendancePolicyPage.test.tsx
index aa47d90..0eff242 100644
--- a/D:/work/heliorventures/hrms-documentation/.superpowers/sdd/2026-09-11-configurable-attendance-day/task3-fix1-base/src__modules__admin__AdminAttendancePolicyPage.test.tsx
+++ b/src/modules/admin/AdminAttendancePolicyPage.test.tsx
@@ -1,6 +1,6 @@
 // @vitest-environment jsdom
 
-import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
+import { act, cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
 import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
 
 import {
@@ -14,6 +14,8 @@ import AdminAttendancePolicyPage from './AdminAttendancePolicyPage';
 
 const state = vi.hoisted(() => ({
   client: { request: vi.fn() },
+  tenantId: 'tenant-1',
+  userId: 'admin-user-1',
   session: {
     employeeId: 'admin-1',
     jwtRoles: [],
@@ -27,10 +29,24 @@ const state = vi.hoisted(() => ({
 
 vi.mock('../../hooks/useGraphClient', () => ({ useGraphClient: () => state.client }));
 vi.mock('../../contexts/AuthContext', () => ({
-  useAuth: () => ({ clientSession: state.session }),
+  useAuth: () => ({
+    clientSession: state.session,
+    tenantId: state.tenantId,
+    user: { id: state.userId },
+  }),
 }));
 
-const policy = (revision = 7) => ({
+const deferred = <T,>() => {
+  let resolve!: (value: T | PromiseLike<T>) => void;
+  let reject!: (reason?: unknown) => void;
+  const promise = new Promise<T>((res, rej) => {
+    resolve = res;
+    reject = rej;
+  });
+  return { promise, reject, resolve };
+};
+
+const policy = (revision = 7, ipAllowlist: string | null = null) => ({
   attendanceDayPolicy: {
     revision,
     initialized: true,
@@ -60,7 +76,7 @@ const policy = (revision = 7) => ({
     siteLatitude: null,
     siteLongitude: null,
     maxDistanceMeters: null,
-    ipAllowlist: null,
+    ipAllowlist,
     updatedAt: null,
   },
   shifts: [],
@@ -87,6 +103,8 @@ const preview = {
 };
 
 beforeEach(() => {
+  state.tenantId = 'tenant-1';
+  state.userId = 'admin-user-1';
   state.session.permissions = new Set(['attendance:punch_policy']);
   state.session.permissionScopes = { 'attendance:punch_policy': 'ALL' };
   state.client = { request: vi.fn() };
@@ -174,3 +192,172 @@ describe('attendance day policy settings', () => {
     expect(state.client.request).toHaveBeenCalledWith(AttendancePolicySettingsDocument);
   });
 });
+
+describe('attendance day proposal ownership', () => {
+  it('discards a delayed preview when the administrator edits the proposal', async () => {
+    const firstPreview = deferred<typeof preview>();
+    let previewCount = 0;
+    state.client.request.mockImplementation((document: unknown) => {
+      if (document === AttendancePolicySettingsDocument) return Promise.resolve(policy());
+      if (document === PreviewAttendanceDayPolicyDocument) {
+        previewCount += 1;
+        return previewCount === 1 ? firstPreview.promise : Promise.resolve(preview);
+      }
+      if (document === ScheduleAttendanceDayPolicyDocument) {
+        return Promise.resolve({ scheduleAttendanceDayPolicy: policy(8).attendanceDayPolicy });
+      }
+      throw new Error('Unexpected operation');
+    });
+    render(<AdminAttendancePolicyPage />);
+    await screen.findByText('Current start: 05:00');
+
+    fireEvent.change(screen.getByLabelText('Attendance day starts at'), {
+      target: { value: '06:00' },
+    });
+    fireEvent.change(screen.getByLabelText('Effective work date'), {
+      target: { value: '2026-09-20' },
+    });
+    fireEvent.click(screen.getByRole('button', { name: 'Preview change' }));
+    fireEvent.change(screen.getByLabelText('Attendance day starts at'), {
+      target: { value: '07:00' },
+    });
+
+    await act(async () => {
+      firstPreview.resolve(preview);
+      await firstPreview.promise;
+    });
+
+    expect(screen.queryByRole('button', { name: 'Schedule change' })).toBeNull();
+    fireEvent.click(screen.getByRole('button', { name: 'Preview change' }));
+    await screen.findByRole('button', { name: 'Schedule change' });
+    fireEvent.click(screen.getByRole('checkbox', { name: /confirm this exact transition/i }));
+    fireEvent.click(screen.getByRole('button', { name: 'Schedule change' }));
+    await waitFor(() =>
+      expect(state.client.request).toHaveBeenCalledWith(ScheduleAttendanceDayPolicyDocument, {
+        input: {
+          boundaryTime: '07:00',
+          effectiveWorkDate: '2026-09-20',
+          expectedRevision: 7,
+        },
+      })
+    );
+  });
+
+  it('discards policy and preview responses owned by a replaced tenant, user, and client', async () => {
+    const stalePreview = deferred<typeof preview>();
+    const oldClient = state.client;
+    oldClient.request.mockImplementation((document: unknown) => {
+      if (document === AttendancePolicySettingsDocument) return Promise.resolve(policy(7));
+      if (document === PreviewAttendanceDayPolicyDocument) return stalePreview.promise;
+      throw new Error('Unexpected operation');
+    });
+    const view = render(<AdminAttendancePolicyPage />);
+    await screen.findByText('Current start: 05:00');
+    fireEvent.change(screen.getByLabelText('Attendance day starts at'), {
+      target: { value: '06:00' },
+    });
+    fireEvent.change(screen.getByLabelText('Effective work date'), {
+      target: { value: '2026-09-20' },
+    });
+    fireEvent.click(screen.getByRole('button', { name: 'Preview change' }));
+
+    const replacementPolicy = policy(7, '10.0.0.1');
+    replacementPolicy.attendanceDayPolicy.currentPolicy.boundaryMinutes = 420;
+    replacementPolicy.attendancePunchPolicy.id = 'policy-tenant-2';
+    state.tenantId = 'tenant-2';
+    state.userId = 'admin-user-2';
+    state.client = { request: vi.fn().mockResolvedValue(replacementPolicy) };
+    view.rerender(<AdminAttendancePolicyPage />);
+
+    expect(await screen.findByText('Current start: 07:00')).toBeTruthy();
+    expect(document.querySelector<HTMLTextAreaElement>('textarea')?.value).toBe('10.0.0.1');
+    await act(async () => {
+      stalePreview.resolve(preview);
+      await stalePreview.promise;
+    });
+
+    expect(screen.queryByRole('button', { name: 'Schedule change' })).toBeNull();
+    expect(screen.getByText('Current start: 07:00')).toBeTruthy();
+    expect(state.client.request).not.toHaveBeenCalledWith(
+      ScheduleAttendanceDayPolicyDocument,
+      expect.anything()
+    );
+  });
+});
+
+describe('attendance policy context ownership', () => {
+  it('does not publish a delayed live-punch policy load after context replacement', async () => {
+    const staleLoad = deferred<ReturnType<typeof policy>>();
+    const oldClient = state.client;
+    oldClient.request.mockReturnValue(staleLoad.promise);
+    const view = render(<AdminAttendancePolicyPage />);
+    await waitFor(() =>
+      expect(oldClient.request).toHaveBeenCalledWith(AttendancePolicySettingsDocument)
+    );
+
+    const replacementPolicy = policy(7, '10.0.0.2');
+    replacementPolicy.attendanceDayPolicy.currentPolicy.boundaryMinutes = 420;
+    state.tenantId = 'tenant-2';
+    state.userId = 'admin-user-2';
+    state.client = { request: vi.fn().mockResolvedValue(replacementPolicy) };
+    view.rerender(<AdminAttendancePolicyPage />);
+    expect(await screen.findByText('Current start: 07:00')).toBeTruthy();
+
+    const stalePolicy = policy(7, '192.0.2.1');
+    await act(async () => {
+      staleLoad.resolve(stalePolicy);
+      await staleLoad.promise;
+    });
+
+    expect(screen.getByText('Current start: 07:00')).toBeTruthy();
+    expect(document.querySelector<HTMLTextAreaElement>('textarea')?.value).toBe('10.0.0.2');
+  });
+
+  it('does not reload or publish a delayed schedule conflict after context replacement', async () => {
+    const staleSchedule = deferred<never>();
+    const oldClient = state.client;
+    oldClient.request.mockImplementation((document: unknown) => {
+      if (document === AttendancePolicySettingsDocument) return Promise.resolve(policy(7));
+      if (document === PreviewAttendanceDayPolicyDocument) return Promise.resolve(preview);
+      if (document === ScheduleAttendanceDayPolicyDocument) return staleSchedule.promise;
+      throw new Error('Unexpected operation');
+    });
+    const view = render(<AdminAttendancePolicyPage />);
+    await screen.findByText('Current start: 05:00');
+    fireEvent.change(screen.getByLabelText('Attendance day starts at'), {
+      target: { value: '06:00' },
+    });
+    fireEvent.change(screen.getByLabelText('Effective work date'), {
+      target: { value: '2026-09-20' },
+    });
+    fireEvent.click(screen.getByRole('button', { name: 'Preview change' }));
+    await screen.findByRole('button', { name: 'Schedule change' });
+    fireEvent.click(screen.getByRole('checkbox', { name: /confirm this exact transition/i }));
+    fireEvent.click(screen.getByRole('button', { name: 'Schedule change' }));
+
+    const replacementPolicy = policy(7);
+    replacementPolicy.attendanceDayPolicy.currentPolicy.boundaryMinutes = 420;
+    state.tenantId = 'tenant-2';
+    state.userId = 'admin-user-2';
+    state.client = { request: vi.fn().mockResolvedValue(replacementPolicy) };
+    view.rerender(<AdminAttendancePolicyPage />);
+    await screen.findByText('Current start: 07:00');
+
+    await act(async () => {
+      staleSchedule.reject({ code: 'CONFLICT' });
+      try {
+        await staleSchedule.promise;
+      } catch {
+        // The rejected request is intentionally stale.
+      }
+    });
+
+    expect(screen.queryByText(/changed while you were reviewing/i)).toBeNull();
+    expect(screen.getByText('Current start: 07:00')).toBeTruthy();
+    expect(
+      oldClient.request.mock.calls.filter(
+        ([document]) => document === AttendancePolicySettingsDocument
+      )
+    ).toHaveLength(1);
+  });
+});

```

## hrms-ui/src/modules/admin/AttendanceDayPolicySettings.tsx

```diff
warning: in the working copy of 'D:/work/heliorventures/hrms-documentation/.superpowers/sdd/2026-09-11-configurable-attendance-day/task3-fix1-base/src__modules__admin__AttendanceDayPolicySettings.tsx', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of 'src/modules/admin/AttendanceDayPolicySettings.tsx', LF will be replaced by CRLF the next time Git touches it
diff --git a/D:/work/heliorventures/hrms-documentation/.superpowers/sdd/2026-09-11-configurable-attendance-day/task3-fix1-base/src__modules__admin__AttendanceDayPolicySettings.tsx b/src/modules/admin/AttendanceDayPolicySettings.tsx
index 3a19077..5c999fd 100644
--- a/D:/work/heliorventures/hrms-documentation/.superpowers/sdd/2026-09-11-configurable-attendance-day/task3-fix1-base/src__modules__admin__AttendanceDayPolicySettings.tsx
+++ b/src/modules/admin/AttendanceDayPolicySettings.tsx
@@ -63,7 +63,7 @@ const AttendanceDayPolicySettings = (props: Props) => {
               Current start: {boundaryTime(policy.currentPolicy.boundaryMinutes)}
             </p>
             <p className="mt-1 text-content-secondary">
-              Effective {policy.currentPolicy.effectiveWorkDate} Â· {policy.currentPolicy.timezone}
+              Effective {policy.currentPolicy.effectiveWorkDate} · {policy.currentPolicy.timezone}
             </p>
           </div>
           <div className="rounded-lg bg-canvas p-3">
@@ -98,6 +98,7 @@ const AttendanceDayPolicySettings = (props: Props) => {
               label="Attendance day starts at"
               value={boundary}
               onChange={(event) => changeDraft(() => setBoundary(event.target.value))}
+              disabled={busy === 'schedule'}
               fullWidth
               required
             />
@@ -106,6 +107,7 @@ const AttendanceDayPolicySettings = (props: Props) => {
               label="Effective work date"
               value={effectiveDate}
               onChange={(event) => changeDraft(() => setEffectiveDate(event.target.value))}
+              disabled={busy === 'schedule'}
               fullWidth
               required
             />
@@ -115,7 +117,7 @@ const AttendanceDayPolicySettings = (props: Props) => {
             variant="outline"
             disabled={busy !== null || !boundary || !effectiveDate}
           >
-            {busy === 'preview' ? 'Loading previewâ€¦' : 'Preview change'}
+            {busy === 'preview' ? 'Loading preview…' : 'Preview change'}
           </Button>
         </form>
 
@@ -138,6 +140,7 @@ const AttendanceDayPolicySettings = (props: Props) => {
                 type="checkbox"
                 className="mt-0.5"
                 checked={confirmed}
+                disabled={busy !== null}
                 onChange={(event) => setConfirmed(event.target.checked)}
               />
               I confirm this exact transition interval and timezone.
@@ -147,7 +150,7 @@ const AttendanceDayPolicySettings = (props: Props) => {
               disabled={!confirmed || busy !== null}
               onClick={() => void schedule()}
             >
-              {busy === 'schedule' ? 'Schedulingâ€¦' : 'Schedule change'}
+              {busy === 'schedule' ? 'Scheduling…' : 'Schedule change'}
             </Button>
           </div>
         ) : null}

```

## hrms-ui/src/modules/admin/useAttendanceDayPolicyDraft.ts

```diff
warning: in the working copy of 'D:/work/heliorventures/hrms-documentation/.superpowers/sdd/2026-09-11-configurable-attendance-day/task3-fix1-base/src__modules__admin__useAttendanceDayPolicyDraft.ts', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of 'src/modules/admin/useAttendanceDayPolicyDraft.ts', LF will be replaced by CRLF the next time Git touches it
diff --git a/D:/work/heliorventures/hrms-documentation/.superpowers/sdd/2026-09-11-configurable-attendance-day/task3-fix1-base/src__modules__admin__useAttendanceDayPolicyDraft.ts b/src/modules/admin/useAttendanceDayPolicyDraft.ts
index 235c183..d341d4b 100644
--- a/D:/work/heliorventures/hrms-documentation/.superpowers/sdd/2026-09-11-configurable-attendance-day/task3-fix1-base/src__modules__admin__useAttendanceDayPolicyDraft.ts
+++ b/src/modules/admin/useAttendanceDayPolicyDraft.ts
@@ -1,5 +1,5 @@
 import { ClientError } from 'graphql-request';
-import { useEffect, useRef, useState, type FormEvent } from 'react';
+import { useLayoutEffect, useRef, useState, type FormEvent } from 'react';
 
 import {
   PreviewAttendanceDayPolicyDocument,
@@ -15,11 +15,65 @@ export type AttendanceDayPolicy = AttendancePolicySettingsQuery['attendanceDayPo
 type Preview = PreviewAttendanceDayPolicyQuery['previewAttendanceDayPolicy'];
 
 export interface AttendanceDayPolicyDraftOptions {
+  ownerKey: string;
   policy: AttendanceDayPolicy;
   onPolicyChanged: (policy: AttendanceDayPolicy) => void;
   reloadPolicy: () => Promise<void>;
 }
 
+interface PolicyProposalInput {
+  boundaryTime: string;
+  effectiveWorkDate: string;
+  expectedRevision: number;
+}
+
+interface PolicyProposal {
+  input: PolicyProposalInput;
+  preview: Preview;
+}
+
+function useRequestOwnership(client: object, ownerKey: string) {
+  const mounted = useRef(false);
+  const ownerGeneration = useRef(0);
+  const previewGeneration = useRef(0);
+  const scheduleGeneration = useRef(0);
+  useLayoutEffect(() => {
+    mounted.current = true;
+    ownerGeneration.current += 1;
+    previewGeneration.current += 1;
+    scheduleGeneration.current += 1;
+    return () => {
+      mounted.current = false;
+      ownerGeneration.current += 1;
+      previewGeneration.current += 1;
+      scheduleGeneration.current += 1;
+    };
+  }, [client, ownerKey]);
+  return {
+    ownerGeneration,
+    ownsRequest: (generation: number) => mounted.current && ownerGeneration.current === generation,
+    previewGeneration,
+    scheduleGeneration,
+  };
+}
+
+const conflictMessage = async (reloadPolicy: () => Promise<void>) => {
+  try {
+    await reloadPolicy();
+    return 'The attendance day policy changed while you were reviewing it. The latest policy was reloaded; preview your retained draft again.';
+  } catch {
+    return 'The attendance day policy changed while you were reviewing it. Your draft was retained, but the latest policy could not be reloaded. Reload the page before previewing again.';
+  }
+};
+
+function proposalIsConfirmed(
+  proposal: PolicyProposal | null,
+  confirmed: boolean,
+  busy: 'preview' | 'schedule' | null
+): proposal is PolicyProposal {
+  return proposal !== null && confirmed && busy === null;
+}
+
 function isConflict(error: unknown) {
   if (error instanceof ClientError) {
     return error.response.errors?.some(
@@ -35,42 +89,54 @@ function isConflict(error: unknown) {
 }
 
 export function useAttendanceDayPolicyDraft({
+  ownerKey,
   policy,
   onPolicyChanged,
   reloadPolicy,
 }: AttendanceDayPolicyDraftOptions) {
   const client = useGraphClient('client');
-  const initialized = useRef(false);
   const [boundary, setBoundary] = useState('');
   const [effectiveDate, setEffectiveDate] = useState('');
-  const [preview, setPreview] = useState<Preview | null>(null);
+  const [proposal, setProposal] = useState<PolicyProposal | null>(null);
   const [confirmed, setConfirmed] = useState(false);
   const [busy, setBusy] = useState<'preview' | 'schedule' | null>(null);
   const [error, setError] = useState<string | null>(null);
   const [success, setSuccess] = useState<string | null>(null);
+  const policyRef = useRef(policy);
+  policyRef.current = policy;
+  const { ownerGeneration, ownsRequest, previewGeneration, scheduleGeneration } =
+    useRequestOwnership(client, ownerKey);
 
-  useEffect(() => {
-    if (initialized.current) return;
-    initialized.current = true;
-    const draft = policy.pendingPolicy ?? policy.currentPolicy;
+  useLayoutEffect(() => {
+    const currentPolicy = policyRef.current;
+    const draft = currentPolicy.pendingPolicy ?? currentPolicy.currentPolicy;
     setBoundary(boundaryTime(draft.boundaryMinutes));
-    setEffectiveDate(policy.pendingPolicy?.effectiveWorkDate ?? '');
-  }, [policy]);
+    setEffectiveDate(currentPolicy.pendingPolicy?.effectiveWorkDate ?? '');
+    setProposal(null);
+    setConfirmed(false);
+    setBusy(null);
+    setError(null);
+    setSuccess(null);
+  }, [client, ownerKey]);
 
   const changeDraft = (change: () => void) => {
+    previewGeneration.current += 1;
     change();
-    setPreview(null);
+    setProposal(null);
     setConfirmed(false);
     setError(null);
     setSuccess(null);
-  };
-  const input = {
-    boundaryTime: boundary,
-    effectiveWorkDate: effectiveDate,
-    expectedRevision: policy.revision,
+    setBusy((current) => (current === 'preview' ? null : current));
   };
   const requestPreview = async (event: FormEvent) => {
     event.preventDefault();
+    const input: PolicyProposalInput = {
+      boundaryTime: boundary,
+      effectiveWorkDate: effectiveDate,
+      expectedRevision: policy.revision,
+    };
+    const request = ++previewGeneration.current;
+    const owner = ownerGeneration.current;
     setBusy('preview');
     setError(null);
     setSuccess(null);
@@ -80,47 +146,48 @@ export function useAttendanceDayPolicyDraft({
         PreviewAttendanceDayPolicyDocument,
         { input }
       );
-      setPreview(result.previewAttendanceDayPolicy);
+      if (!ownsRequest(owner) || previewGeneration.current !== request) return;
+      setProposal({ input, preview: result.previewAttendanceDayPolicy });
     } catch (reason) {
-      setPreview(null);
+      if (!ownsRequest(owner) || previewGeneration.current !== request) return;
+      setProposal(null);
       setError(graphQlUserMessage(reason));
     } finally {
-      setBusy(null);
+      if (ownsRequest(owner) && previewGeneration.current === request) setBusy(null);
     }
   };
   const schedule = async () => {
-    if (!preview || !confirmed || busy) return;
+    if (!proposalIsConfirmed(proposal, confirmed, busy)) return;
+    const confirmedProposal = proposal;
+    const request = ++scheduleGeneration.current;
+    const owner = ownerGeneration.current;
+    const ownsSchedule = () => ownsRequest(owner) && scheduleGeneration.current === request;
     setBusy('schedule');
     setError(null);
     setSuccess(null);
     try {
       const result = await client.request<{ scheduleAttendanceDayPolicy: AttendanceDayPolicy }>(
         ScheduleAttendanceDayPolicyDocument,
-        { input }
+        { input: confirmedProposal.input }
       );
+      if (!ownsSchedule()) return;
       onPolicyChanged(result.scheduleAttendanceDayPolicy);
-      setPreview(null);
+      setProposal(null);
       setConfirmed(false);
       setSuccess('Attendance day change scheduled.');
     } catch (reason) {
-      setPreview(null);
+      if (!ownsSchedule()) return;
+      setProposal(null);
       setConfirmed(false);
       if (!isConflict(reason)) {
         setError(graphQlUserMessage(reason));
       } else {
-        setError(
-          'The attendance day policy changed while you were reviewing it. The latest policy was reloaded; preview your retained draft again.'
-        );
-        try {
-          await reloadPolicy();
-        } catch {
-          setError(
-            'The attendance day policy changed while you were reviewing it. Your draft was retained, but the latest policy could not be reloaded. Reload the page before previewing again.'
-          );
-        }
+        const message = await conflictMessage(reloadPolicy);
+        if (!ownsSchedule()) return;
+        setError(message);
       }
     } finally {
-      setBusy(null);
+      if (ownsSchedule()) setBusy(null);
     }
   };
   return {
@@ -130,7 +197,7 @@ export function useAttendanceDayPolicyDraft({
     confirmed,
     effectiveDate,
     error,
-    preview,
+    preview: proposal?.preview ?? null,
     requestPreview,
     schedule,
     setBoundary,

```

## hrms-ui/src/modules/attendance/hooks/useAttendanceDayWindows.ts

```diff
warning: in the working copy of 'D:/work/heliorventures/hrms-documentation/.superpowers/sdd/2026-09-11-configurable-attendance-day/task3-fix1-base/src__modules__attendance__hooks__useAttendanceDayWindows.ts', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of 'src/modules/attendance/hooks/useAttendanceDayWindows.ts', LF will be replaced by CRLF the next time Git touches it
diff --git a/D:/work/heliorventures/hrms-documentation/.superpowers/sdd/2026-09-11-configurable-attendance-day/task3-fix1-base/src__modules__attendance__hooks__useAttendanceDayWindows.ts b/src/modules/attendance/hooks/useAttendanceDayWindows.ts
index 7db6756..e27ed92 100644
--- a/D:/work/heliorventures/hrms-documentation/.superpowers/sdd/2026-09-11-configurable-attendance-day/task3-fix1-base/src__modules__attendance__hooks__useAttendanceDayWindows.ts
+++ b/src/modules/attendance/hooks/useAttendanceDayWindows.ts
@@ -12,6 +12,19 @@ import { graphQlUserMessage } from '../../../utils/graphqlUserMessage';
 
 type GraphClient = ReturnType<typeof useGraphClient>;
 
+type CurrentWindow = AttendanceCurrentDayWindowQuery['attendanceDayWindow'];
+
+function validateCurrentWindow(window: CurrentWindow): void {
+  const startsAt = Date.parse(window.startsAt);
+  const endsAt = Date.parse(window.endsAt);
+  if (!Number.isFinite(startsAt) || !Number.isFinite(endsAt) || startsAt >= endsAt) {
+    throw new Error('Attendance day window response was invalid.');
+  }
+  if (Date.now() < startsAt || Date.now() >= endsAt) {
+    throw new Error('Attendance day window response was outside the current attendance day.');
+  }
+}
+
 export function useCurrentAttendanceDayWindow(client: GraphClient, identity: string) {
   const load = useCallback(async () => {
     void identity;
@@ -21,9 +34,62 @@ export function useCurrentAttendanceDayWindow(client: GraphClient, identity: str
     if (!result.attendanceDayWindow) {
       throw new Error('Attendance day window response was incomplete.');
     }
+    validateCurrentWindow(result.attendanceDayWindow);
     return result.attendanceDayWindow;
   }, [client, identity]);
-  return useRetainedQuery(load);
+  const { data, error, phase, refresh } = useRetainedQuery(load);
+  const refreshedBoundary = useRef<string | null>(null);
+  const resumeInFlight = useRef<Promise<void> | null>(null);
+
+  useEffect(() => {
+    refreshedBoundary.current = null;
+    resumeInFlight.current = null;
+  }, [client, identity]);
+
+  useEffect(() => {
+    const endsAt = data?.endsAt;
+    if (!endsAt) return;
+    const refreshBoundary = () => {
+      if (refreshedBoundary.current === endsAt) return;
+      refreshedBoundary.current = endsAt;
+      void refresh();
+    };
+    const delay = Date.parse(endsAt) - Date.now();
+    if (delay <= 0) {
+      refreshBoundary();
+      return;
+    }
+    const timer = window.setTimeout(refreshBoundary, Math.min(delay, 2_147_483_647));
+    return () => window.clearTimeout(timer);
+  }, [data?.endsAt, refresh]);
+
+  useEffect(() => {
+    const resume = () => {
+      if (resumeInFlight.current) return;
+      const request = refresh();
+      resumeInFlight.current = request;
+      void request.finally(() => {
+        if (resumeInFlight.current === request) resumeInFlight.current = null;
+      });
+    };
+    const visible = () => {
+      if (document.visibilityState === 'visible') resume();
+    };
+    window.addEventListener('focus', resume);
+    document.addEventListener('visibilitychange', visible);
+    return () => {
+      window.removeEventListener('focus', resume);
+      document.removeEventListener('visibilitychange', visible);
+    };
+  }, [refresh]);
+
+  const dataIsCurrent = Boolean(
+    phase === 'ready' &&
+    data &&
+    Date.now() >= Date.parse(data.startsAt) &&
+    Date.now() < Date.parse(data.endsAt)
+  );
+  return { data: dataIsCurrent ? data : null, error, phase, refresh };
 }
 
 interface CorrectionWindowsState {

```

## hrms-ui/src/modules/attendance/hooks/useAttendanceDayWindows.test.tsx

```diff
warning: in the working copy of 'src/modules/attendance/hooks/useAttendanceDayWindows.test.tsx', LF will be replaced by CRLF the next time Git touches it
diff --git a/src/modules/attendance/hooks/useAttendanceDayWindows.test.tsx b/src/modules/attendance/hooks/useAttendanceDayWindows.test.tsx
new file mode 100644
index 0000000..06b8091
--- /dev/null
+++ b/src/modules/attendance/hooks/useAttendanceDayWindows.test.tsx
@@ -0,0 +1,124 @@
+// @vitest-environment jsdom
+
+import { act, cleanup, renderHook, waitFor } from '@testing-library/react';
+import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
+
+import { AttendanceCurrentDayWindowDocument } from '../../../api/attendance/graphql';
+import type { useGraphClient } from '../../../hooks/useGraphClient';
+
+import { useCurrentAttendanceDayWindow } from './useAttendanceDayWindows';
+
+type GraphClient = ReturnType<typeof useGraphClient>;
+
+const deferred = <T,>() => {
+  let resolve!: (value: T | PromiseLike<T>) => void;
+  const promise = new Promise<T>((res) => {
+    resolve = res;
+  });
+  return { promise, resolve };
+};
+
+const windowResponse = (workDate: string, startsAt: string, endsAt: string) => ({
+  attendanceDayWindow: {
+    workDate,
+    startsAt,
+    endsAt,
+    timezone: 'UTC',
+    boundaryMinutes: 0,
+  },
+});
+
+beforeEach(() => {
+  vi.useFakeTimers({ shouldAdvanceTime: true });
+  vi.setSystemTime(new Date('2026-09-11T12:00:00Z'));
+});
+
+afterEach(() => {
+  cleanup();
+  vi.useRealTimers();
+});
+
+describe('useCurrentAttendanceDayWindow lifecycle', () => {
+  it('refreshes at the exact exclusive attendance-day end', async () => {
+    const request = vi
+      .fn()
+      .mockResolvedValueOnce(
+        windowResponse('2026-09-11', '2026-09-10T12:01:00Z', '2026-09-11T12:01:00Z')
+      )
+      .mockResolvedValueOnce(
+        windowResponse('2026-09-12', '2026-09-11T12:01:00Z', '2026-09-12T12:01:00Z')
+      );
+    const client = { request } as unknown as GraphClient;
+    const { result } = renderHook(() => useCurrentAttendanceDayWindow(client, 'tenant-1:user-1'));
+    await waitFor(() => expect(result.current.data?.workDate).toBe('2026-09-11'));
+
+    await act(async () => {
+      vi.advanceTimersByTime(60_000);
+      await Promise.resolve();
+      await Promise.resolve();
+    });
+
+    expect(request).toHaveBeenCalledTimes(2);
+    expect(result.current.data?.workDate).toBe('2026-09-12');
+  });
+
+  it('refreshes when a suspended page regains focus without changing the selected period', async () => {
+    const request = vi
+      .fn()
+      .mockResolvedValueOnce(
+        windowResponse('2026-09-11', '2026-09-10T12:00:00Z', '2026-09-12T12:00:00Z')
+      )
+      .mockResolvedValueOnce(
+        windowResponse('2026-09-12', '2026-09-11T12:00:00Z', '2026-09-13T12:00:00Z')
+      );
+    const client = { request } as unknown as GraphClient;
+    const { result } = renderHook(() => useCurrentAttendanceDayWindow(client, 'tenant-1:user-1'));
+    await waitFor(() => expect(result.current.data?.workDate).toBe('2026-09-11'));
+
+    window.dispatchEvent(new Event('focus'));
+
+    await waitFor(() => expect(result.current.data?.workDate).toBe('2026-09-12'));
+    expect(request).toHaveBeenCalledTimes(2);
+  });
+
+  it('rejects an already-expired current-window response and fails closed', async () => {
+    const request = vi
+      .fn()
+      .mockResolvedValue(
+        windowResponse('2026-09-10', '2026-09-09T12:00:00Z', '2026-09-11T11:59:59Z')
+      );
+    const client = { request } as unknown as GraphClient;
+    const { result } = renderHook(() => useCurrentAttendanceDayWindow(client, 'tenant-1:user-1'));
+
+    await waitFor(() => expect(result.current.phase).toBe('initial-error'));
+    expect(result.current.data).toBeNull();
+  });
+
+  it('does not publish a delayed response after the client and identity change', async () => {
+    const stale = deferred<ReturnType<typeof windowResponse>>();
+    const oldRequest = vi.fn().mockReturnValue(stale.promise);
+    const newRequest = vi
+      .fn()
+      .mockResolvedValue(
+        windowResponse('2026-09-12', '2026-09-11T12:00:00Z', '2026-09-12T12:00:00Z')
+      );
+    let client = { request: oldRequest } as unknown as GraphClient;
+    let identity = 'tenant-1:user-1';
+    const { result, rerender } = renderHook(() => useCurrentAttendanceDayWindow(client, identity));
+    await waitFor(() =>
+      expect(oldRequest).toHaveBeenCalledWith(AttendanceCurrentDayWindowDocument)
+    );
+
+    client = { request: newRequest } as unknown as GraphClient;
+    identity = 'tenant-2:user-2';
+    rerender();
+    await waitFor(() => expect(result.current.data?.workDate).toBe('2026-09-12'));
+
+    await act(async () => {
+      stale.resolve(windowResponse('2026-09-10', '2026-09-09T12:00:00Z', '2026-09-13T12:00:00Z'));
+      await stale.promise;
+    });
+
+    expect(result.current.data?.workDate).toBe('2026-09-12');
+  });
+});

```

## hrms-ui/src/modules/attendance/AttendancePage.editorOwnership.test.tsx

```diff
warning: in the working copy of 'D:/work/heliorventures/hrms-documentation/.superpowers/sdd/2026-09-11-configurable-attendance-day/task3-fix1-base/src__modules__attendance__AttendancePage.editorOwnership.test.tsx', LF will be replaced by CRLF the next time Git touches it
diff --git a/D:/work/heliorventures/hrms-documentation/.superpowers/sdd/2026-09-11-configurable-attendance-day/task3-fix1-base/src__modules__attendance__AttendancePage.editorOwnership.test.tsx b/src/modules/attendance/AttendancePage.editorOwnership.test.tsx
index c1080f2..57899e1 100644
--- a/D:/work/heliorventures/hrms-documentation/.superpowers/sdd/2026-09-11-configurable-attendance-day/task3-fix1-base/src__modules__attendance__AttendancePage.editorOwnership.test.tsx
+++ b/src/modules/attendance/AttendancePage.editorOwnership.test.tsx
@@ -1,5 +1,5 @@
 // @vitest-environment jsdom
-import { fireEvent, screen, waitFor } from '@testing-library/react';
+import { act, fireEvent, screen, waitFor } from '@testing-library/react';
 import { expect, it, vi } from 'vitest';
 
 import { AttendanceCurrentDayWindowDocument } from '../../api/attendance/graphql';
@@ -53,7 +53,7 @@ it('discards an open attendance edit when the client or employee changes, includ
 });
 
 it('uses the server current work date for the initial month and missed-punch default', async () => {
-  vi.setSystemTime(new Date('2026-09-01T00:30:00Z'));
+  vi.setSystemTime(new Date('2026-08-31T20:00:00Z'));
   authState.clientSession.permissions = new Set(['attendance:punch_self']);
   graphClient.request.mockImplementation((document: unknown) => {
     if (document === AttendanceAdjustmentPolicyDocument) return Promise.resolve(policyResponse);
@@ -76,3 +76,34 @@ it('uses the server current work date for the initial month and missed-punch def
   fireEvent.click(screen.getByRole('button', { name: 'Add Missed Punches' }));
   expect(screen.getByLabelText<HTMLInputElement>('Work Date').value).toBe('2026-08-31');
 });
+
+it('preserves a selected historical month while the current attendance window refreshes', async () => {
+  authState.clientSession.permissions = new Set(['attendance:punch_self']);
+  let currentWindowRequests = 0;
+  graphClient.request.mockImplementation((document: unknown) => {
+    if (document === AttendanceAdjustmentPolicyDocument) return Promise.resolve(policyResponse);
+    if (document === AttendanceCurrentDayWindowDocument) {
+      currentWindowRequests += 1;
+      return Promise.resolve({
+        attendanceDayWindow: {
+          ...currentWindowResponse.attendanceDayWindow,
+          workDate: currentWindowRequests === 1 ? '2026-08-25' : '2026-08-26',
+          endsAt: '2026-08-26T23:30:00Z',
+        },
+      });
+    }
+    return Promise.resolve(boardResponse());
+  });
+  renderPage();
+  const month = await screen.findByLabelText<HTMLSelectElement>('Month');
+  fireEvent.change(month, { target: { value: '6' } });
+  await waitFor(() => expect(month.value).toBe('6'));
+
+  await act(async () => {
+    window.dispatchEvent(new Event('focus'));
+    await Promise.resolve();
+  });
+
+  await waitFor(() => expect(currentWindowRequests).toBe(2));
+  expect(month.value).toBe('6');
+});

```

## hrms-ui/src/modules/dashboard/components/PunchInOut.tsx

```diff
warning: in the working copy of 'D:/work/heliorventures/hrms-documentation/.superpowers/sdd/2026-09-11-configurable-attendance-day/task3-fix1-base/src__modules__dashboard__components__PunchInOut.tsx', LF will be replaced by CRLF the next time Git touches it
diff --git a/D:/work/heliorventures/hrms-documentation/.superpowers/sdd/2026-09-11-configurable-attendance-day/task3-fix1-base/src__modules__dashboard__components__PunchInOut.tsx b/src/modules/dashboard/components/PunchInOut.tsx
index 26eeb89..1cb9448 100644
--- a/D:/work/heliorventures/hrms-documentation/.superpowers/sdd/2026-09-11-configurable-attendance-day/task3-fix1-base/src__modules__dashboard__components__PunchInOut.tsx
+++ b/src/modules/dashboard/components/PunchInOut.tsx
@@ -121,9 +121,14 @@ const usePunchMutation = ({
   useLayoutEffect(() => {
     mountedRef.current = true;
     generationRef.current += 1;
+    submittingRef.current = false;
+    setSubmitting(false);
+    setMutationError(null);
+    setLastPunch(null);
     return () => {
       mountedRef.current = false;
       generationRef.current += 1;
+      submittingRef.current = false;
     };
   }, [client, summaryOwner]);
 
@@ -176,7 +181,7 @@ const usePunchMutation = ({
 };
 
 const getButtonLabel = (submitting: boolean, nextIsCheckIn: boolean) => {
-  if (submitting) return 'Recordingâ€¦';
+  if (submitting) return 'Recording…';
   return nextIsCheckIn ? 'Punch In' : 'Punch Out';
 };
 
@@ -200,7 +205,7 @@ const PunchSummaryContent = ({ error, onRefresh, phase, summary }: PunchSummaryC
     return (
       <DashboardCardInitialState
         phase={phase}
-        loadingTitle="Loading Attendance Summaryâ€¦"
+        loadingTitle="Loading Attendance Summary…"
         errorTitle="Attendance Summary Could Not Be Loaded"
         error={error}
         onRetry={onRefresh}
@@ -214,7 +219,7 @@ const PunchSummaryContent = ({ error, onRefresh, phase, summary }: PunchSummaryC
     <>
       <DashboardCardRefreshNotice
         phase={phase}
-        loadingTitle="Refreshing Attendance Summaryâ€¦"
+        loadingTitle="Refreshing Attendance Summary…"
         loadingDescription="Showing the last loaded attendance while this updates."
         staleTitle="Attendance Summary May Be Out of Date"
         staleDescription="Showing the last loaded attendance."
@@ -234,7 +239,7 @@ interface LastPunchDetailsProps {
 const LastPunchDetails = ({ lastEventCoords, lastPunch }: LastPunchDetailsProps) => (
   <div className="rounded-lg border border-gray-200 p-2 text-xs text-gray-600 dark:border-gray-700 dark:text-gray-300">
     <div>
-      In {formatBackendTime(lastPunch.checkInTime)} Â· Out{' '}
+      In {formatBackendTime(lastPunch.checkInTime)} · Out{' '}
       {formatBackendTime(lastPunch.checkOutTime)}
       {lastPunch.status ? (
         <span className="ml-2 inline-block">
@@ -290,7 +295,7 @@ const PunchActionArea = ({
     </label>
     <PageInformation title="Attendance totals">
       <p className="text-center text-xs text-gray-500 dark:text-gray-400">
-        You can punch in and out several times a day. Total time adds up each completed inâ†’out
+        You can punch in and out several times a day. Total time adds up each completed in→out
         block.
       </p>
     </PageInformation>
@@ -298,7 +303,7 @@ const PunchActionArea = ({
       variant="primary"
       fullWidth
       busy={submitting}
-      busyLabel="Recording Attendanceâ€¦"
+      busyLabel="Recording Attendance…"
       disabled={disabled}
       onClick={() => void onPunch()}
     >
@@ -346,7 +351,7 @@ const AuthorizedPunchInOut = ({ canPunch, identity }: AuthorizedPunchInOutProps)
   const lastEventCoords = getLastEventCoords(lastPunch);
 
   return (
-    <Card title="Todayâ€™s attendance">
+    <Card title="Today’s attendance">
       <div className="space-y-4">
         <div className="flex flex-wrap items-baseline justify-between gap-2 border-b border-line pb-3">
           <div className="text-xl font-semibold tabular-nums text-content-primary">
@@ -375,7 +380,7 @@ const AuthorizedPunchInOut = ({ canPunch, identity }: AuthorizedPunchInOutProps)
             variant="quiet"
             size="sm"
             busy={summaryPhase === 'refreshing'}
-            busyLabel="Refreshing Attendance Summaryâ€¦"
+            busyLabel="Refreshing Attendance Summary…"
             onClick={onRefresh}
           >
             Refresh Attendance Summary

```

## hrms-ui/src/modules/dashboard/components/PunchInOut.test.tsx

```diff
warning: in the working copy of 'D:/work/heliorventures/hrms-documentation/.superpowers/sdd/2026-09-11-configurable-attendance-day/task3-fix1-base/src__modules__dashboard__components__PunchInOut.test.tsx', LF will be replaced by CRLF the next time Git touches it
diff --git a/D:/work/heliorventures/hrms-documentation/.superpowers/sdd/2026-09-11-configurable-attendance-day/task3-fix1-base/src__modules__dashboard__components__PunchInOut.test.tsx b/src/modules/dashboard/components/PunchInOut.test.tsx
index 5b6d1f0..6352ee4 100644
--- a/D:/work/heliorventures/hrms-documentation/.superpowers/sdd/2026-09-11-configurable-attendance-day/task3-fix1-base/src__modules__dashboard__components__PunchInOut.test.tsx
+++ b/src/modules/dashboard/components/PunchInOut.test.tsx
@@ -236,6 +236,52 @@ describe('PunchInOut lifecycle ownership', () => {
     expect(screen.queryByText('Attendance work date: 2026-08-20')).toBeNull();
     expect(screen.getByText('Attendance work date: 2026-08-22')).toBeTruthy();
   });
+
+  it('clears an owned busy mutation when only the GraphQL client is replaced', async () => {
+    const staleMutation = deferred<{ punchToday: ReturnType<typeof segment> }>();
+    const oldClient = graphState.client;
+    oldClient.request.mockImplementation((document) => {
+      if (document === AttendancePunchDaySummaryDocument) return Promise.resolve(summary());
+      if (document === AttendancePunchTodayDocument) return staleMutation.promise;
+      throw new Error('Unexpected document');
+    });
+    const user = userEvent.setup();
+    const view = renderCard();
+    await screen.findByText('Session 1');
+    await user.click(screen.getByRole('checkbox', { name: /Record GPS location/i }));
+    await user.click(screen.getByRole('button', { name: 'Punch In' }));
+    expect(screen.getByRole<HTMLButtonElement>('button', { name: /Recording/i }).disabled).toBe(
+      true
+    );
+
+    const replacementPunch = { ...segment(4), source: 'replacement-client' };
+    const replacementClient = {
+      request: vi.fn((document) => {
+        if (document === AttendancePunchDaySummaryDocument) return Promise.resolve(summary(0));
+        if (document === AttendancePunchTodayDocument) {
+          return Promise.resolve({ punchToday: replacementPunch });
+        }
+        throw new Error('Unexpected document');
+      }),
+    };
+    graphState.client = replacementClient;
+    view.rerender(<PunchInOut />);
+
+    const replacementButton = await screen.findByRole<HTMLButtonElement>('button', {
+      name: 'Punch In',
+    });
+    expect(replacementButton.disabled).toBe(false);
+    await user.click(replacementButton);
+    expect(await screen.findByText('Source: replacement-client')).toBeTruthy();
+
+    await act(async () => {
+      staleMutation.resolve({ punchToday: { ...segment(5), source: 'stale-client' } });
+      await staleMutation.promise;
+    });
+
+    expect(screen.queryByText('Source: stale-client')).toBeNull();
+    expect(screen.getByText('Source: replacement-client')).toBeTruthy();
+  });
 });
 
 describe('PunchInOut truthful refresh states', () => {
@@ -261,7 +307,7 @@ describe('PunchInOut truthful refresh states', () => {
     renderCard();
 
     await user.click(await screen.findByRole('button', { name: 'Retry' }));
-    expect(screen.getByText('Loading Attendance Summaryâ€¦')).toBeTruthy();
+    expect(screen.getByText('Loading Attendance Summary…')).toBeTruthy();
 
     act(() => retry.resolve(summary()));
     expect(await screen.findByText('Session 1')).toBeTruthy();
@@ -382,7 +428,7 @@ describe('PunchInOut submission and display safeguards', () => {
     renderCard();
 
     const helper = await screen.findByText(/Open: checked in at/);
-    expect(helper.textContent).toContain('Select â€œPunch Outâ€ to close this block.');
+    expect(helper.textContent).toContain('Select “Punch Out” to close this block.');
     expect(helper.textContent).not.toContain('tap');
     expect(helper.textContent).not.toContain('"Punch Out"');
   });

```

## hrms-ui/src/utils/attendanceValidation.ts

```diff
warning: in the working copy of 'D:/work/heliorventures/hrms-documentation/.superpowers/sdd/2026-09-11-configurable-attendance-day/task3-fix1-base/src__utils__attendanceValidation.ts', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of 'src/utils/attendanceValidation.ts', LF will be replaced by CRLF the next time Git touches it
diff --git a/D:/work/heliorventures/hrms-documentation/.superpowers/sdd/2026-09-11-configurable-attendance-day/task3-fix1-base/src__utils__attendanceValidation.ts b/src/utils/attendanceValidation.ts
index 7e3fdd3..891fc74 100644
--- a/D:/work/heliorventures/hrms-documentation/.superpowers/sdd/2026-09-11-configurable-attendance-day/task3-fix1-base/src__utils__attendanceValidation.ts
+++ b/src/utils/attendanceValidation.ts
@@ -179,6 +179,11 @@ const overlapError = (): ManualAttendanceValidationError => ({
   message: 'This punch range overlaps an existing attendance segment for the day.',
 });
 
+const durationCapError = (): ManualAttendanceValidationError => ({
+  field: 'form',
+  message: 'Total attendance for a day must be less than 24 hours.',
+});
+
 function canonicalExistingSegment(
   segment: AttendanceSegmentInterval,
   requested: ValidatedInterval
@@ -240,7 +245,7 @@ function validateExistingSegments(
   const requestedMinutes = (requested.end - requested.start) / 60_000;
   return existingMinutes + requestedMinutes < MAX_ATTENDANCE_MINUTES_PER_DAY
     ? null
-    : { field: 'form', message: 'Total attendance for a day must be less than 24 hours.' };
+    : durationCapError();
 }
 
 export function validateManualAttendanceSegment(
@@ -250,6 +255,8 @@ export function validateManualAttendanceSegment(
   if (requiredError) return requiredError;
   const { error, interval } = requestedInterval(input);
   if (error || !interval) return error;
+  const requestedMinutes = (interval.end - interval.start) / 60_000;
+  if (requestedMinutes >= MAX_ATTENDANCE_MINUTES_PER_DAY) return durationCapError();
   const isWithinLoadedCoverage =
     input.existingSegmentsCoverage === undefined ||
     (input.workDate >= input.existingSegmentsCoverage.fromDate &&

```

## hrms-ui/src/utils/attendanceValidation.test.ts

```diff
warning: in the working copy of 'D:/work/heliorventures/hrms-documentation/.superpowers/sdd/2026-09-11-configurable-attendance-day/task3-fix1-base/src__utils__attendanceValidation.test.ts', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of 'src/utils/attendanceValidation.test.ts', LF will be replaced by CRLF the next time Git touches it
diff --git a/D:/work/heliorventures/hrms-documentation/.superpowers/sdd/2026-09-11-configurable-attendance-day/task3-fix1-base/src__utils__attendanceValidation.test.ts b/src/utils/attendanceValidation.test.ts
index 511e7ae..9be7323 100644
--- a/D:/work/heliorventures/hrms-documentation/.superpowers/sdd/2026-09-11-configurable-attendance-day/task3-fix1-base/src__utils__attendanceValidation.test.ts
+++ b/src/utils/attendanceValidation.test.ts
@@ -251,4 +251,58 @@ describe('validateManualAttendanceSegment', () => {
       })
     ).toBeNull();
   });
+
+  it('rejects an intrinsically 24-hour interval when segment coverage is incomplete', () => {
+    expect(
+      validateManualAttendanceSegment({
+        ...validInput,
+        checkInDate: '2025-01-15',
+        checkOutDate: '2025-01-16',
+        checkIn: '00:00',
+        checkOut: '00:00',
+        window: {
+          workDate: '2025-01-15',
+          startsAt: '2025-01-14T23:30:00Z',
+          endsAt: '2025-01-16T00:30:00Z',
+          timezone: 'UTC',
+          boundaryMinutes: 0,
+        },
+        existingSegmentsComplete: false,
+      })
+    ).toEqual({
+      field: 'form',
+      message: 'Total attendance for a day must be less than 24 hours.',
+    });
+  });
+
+  it('enforces the intrinsic cap outside loaded coverage while accepting an exact-end interval below it', () => {
+    const transitionInput = {
+      ...validInput,
+      checkInDate: '2025-01-15',
+      checkOutDate: '2025-01-16',
+      checkIn: '00:00',
+      checkOut: '00:00',
+      window: {
+        workDate: '2025-01-15',
+        startsAt: '2025-01-14T23:30:00Z',
+        endsAt: '2025-01-16T00:30:00Z',
+        timezone: 'UTC',
+        boundaryMinutes: 0,
+      },
+      existingSegmentsComplete: true,
+      existingSegmentsCoverage: { fromDate: '2025-02-01', toDate: '2025-02-28' },
+    };
+
+    expect(validateManualAttendanceSegment(transitionInput)).toEqual({
+      field: 'form',
+      message: 'Total attendance for a day must be less than 24 hours.',
+    });
+    expect(
+      validateManualAttendanceSegment({
+        ...transitionInput,
+        checkIn: '00:31',
+        checkOut: '00:30',
+      })
+    ).toBeNull();
+  });
 });

```

