# Notification Defect Root-Cause Fixes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. Do not use subagents unless the user explicitly asks for delegation.

**Goal:** Fix the four notification defects documented in `Issues_Notifications_11-Aug.docx`.

**Architecture:** Keep backend permission enforcement intact. Fix invalid UI payload creation at the source, normalize notification action navigation through existing URL safety helpers, add admin success feedback from the mutation result, and expose the existing signed document endpoint through production routing config.

**Tech Stack:** React 18, TypeScript, GraphQL generated types, Vitest, Docker Compose, Caddy.

## Global Constraints

- Do not run unit tests; ask the user to run the listed commands and share output.
- Do not run Dart or Flutter commands.
- Do not auto-commit changes.
- Preserve unrelated dirty work in all repos.
- Fix root causes, not symptoms.

---

### Task 1: Announcement Input Contract

**Files:**
- Create: `hrms-ui/src/modules/notifications/createAnnouncementInput.ts`
- Create: `hrms-ui/src/modules/notifications/createAnnouncementInput.test.ts`
- Modify: `hrms-ui/src/modules/notifications/CreateAnnouncementModal.tsx`

**Interfaces:**
- Produces: `buildCreateAnnouncementInput(values, files): CreateAnnouncementInput`
- Consumes: generated `CreateAnnouncementInput` from `src/api/graphql/graphql.ts`

- [ ] **Step 1: Write the failing test**

```ts
import { describe, expect, it } from 'vitest';
import { buildCreateAnnouncementInput } from './createAnnouncementInput';

const emptyFiles = {
  imageFileName: null,
  imageMimeType: null,
  imageContentBase64: null,
  documentFileName: null,
  documentMimeType: null,
  documentContentBase64: null,
};

describe('buildCreateAnnouncementInput', () => {
  it('forces staff announcements to employee posts without admin targeting', () => {
    const input = buildCreateAnnouncementInput(
      {
        hrCompose: false,
        title: '  System update  ',
        body: '  Read this  ',
        targetAudience: 'Engineering',
        targetDepartmentId: 'dept-1',
        targetLocationId: 'loc-1',
        targetRoleCode: 'HR_ADMIN',
        publishAt: '2026-08-12T08:00:00.000Z',
        expiresAt: '2026-08-13T08:00:00.000Z',
        employeePost: false,
      },
      emptyFiles
    );

    expect(input).toMatchObject({
      title: 'System update',
      body: 'Read this',
      targetAudience: null,
      targetDepartmentId: null,
      targetLocationId: null,
      targetRoleCode: null,
      publishAt: null,
      expiresAt: null,
      employeePost: true,
    });
  });
});
```

- [ ] **Step 2: User-run red verification**

Run: `npm test -- src/modules/notifications/createAnnouncementInput.test.ts`

Expected before implementation: FAIL because `createAnnouncementInput.ts` does not exist.

- [ ] **Step 3: Implement the helper and wire the modal**

Create the helper exactly where the test imports it. In the modal, replace inline mutation input assembly with `buildCreateAnnouncementInput(...)`. Hide non-HR target audience and employee/company checkbox controls so staff cannot submit HR-only payloads.

- [ ] **Step 4: User-run green verification**

Run: `npm test -- src/modules/notifications/createAnnouncementInput.test.ts`

Expected after implementation: PASS.

### Task 2: Notification Action Destination

**Files:**
- Modify: `hrms-ui/src/utils/actionUrl.ts`
- Create: `hrms-ui/src/utils/actionUrl.test.ts`
- Modify: `hrms-ui/src/components/layout/NotificationDropdown.tsx`

**Interfaces:**
- Produces: `notificationActionDestination(url): string`
- Consumes: existing `normalizeInternalActionUrl(url): string | null`

- [ ] **Step 1: Write the failing test**

```ts
import { describe, expect, it } from 'vitest';
import { notificationActionDestination } from './actionUrl';

describe('notificationActionDestination', () => {
  it('uses a safe same-tab fallback when the action URL is absent or external', () => {
    expect(notificationActionDestination(null)).toBe('/notifications');
    expect(notificationActionDestination('https://evil.example/path')).toBe('/notifications');
  });

  it('normalizes same-origin absolute URLs to internal routes', () => {
    expect(notificationActionDestination(`${window.location.origin}/admin/notifications`)).toBe(
      '/admin/notifications'
    );
  });
});
```

- [ ] **Step 2: User-run red verification**

Run: `npm test -- src/utils/actionUrl.test.ts`

Expected before implementation: FAIL because `notificationActionDestination` is not exported.

- [ ] **Step 3: Implement same-tab navigation**

Add `notificationActionDestination` to `actionUrl.ts`. Import it in `NotificationDropdown.tsx`, replace `window.open(...)` and manual path handling with `navigate(notificationActionDestination(n.actionUrl))`, and keep mark-as-read behavior unchanged.

- [ ] **Step 4: User-run green verification**

Run: `npm test -- src/utils/actionUrl.test.ts`

Expected after implementation: PASS.

### Task 3: Direct Notification Success Feedback

**Files:**
- Modify: `hrms-ui/src/modules/admin/AdminNotificationsPage.tsx`

**Interfaces:**
- Consumes: `CreateDirectNotificationsMutation` generated type whose `createDirectNotifications` field is a number.

- [ ] **Step 1: Implement feedback state**

Add a success state that is cleared when a send starts or when an error is set. Capture the mutation response:

```ts
const response = await client.request<CreateDirectNotificationsMutation>(
  CreateDirectNotificationsDocument,
  { input: ... }
);
setSuccess(`Created ${response.createDirectNotifications} direct notification(s).`);
```

Render it with `role="status"` and `aria-live="polite"` near the existing error card.

- [ ] **Step 2: User-run verification**

Manual check: Send direct notifications to selected users. The form should clear, bell count should update after reload, and a success message should be visible.

### Task 4: Production Attachment Download Routing

**Files:**
- Modify: `hrms-documentation/deploy/Caddyfile.example`
- Modify: `hrms-documentation/deploy/docker-compose.prod.yml`
- Modify: `hrms-documentation/deploy/.env.example`

**Interfaces:**
- Consumes: `KABIPAY_EMPLOYEE_PUBLIC_BASE`
- Produces: browser-reachable signed URL base `https://api.heliorsoft.com/files/employee-document?token=...`

- [ ] **Step 1: Add public base env**

Set this in `.env.example`:

```env
KABIPAY_EMPLOYEE_PUBLIC_BASE=https://api.heliorsoft.com
```

Pass it explicitly to `kabipay-subgraphs` in `docker-compose.prod.yml`.

- [ ] **Step 2: Add Caddy route**

Add `handle /files/employee-document* { reverse_proxy kabipay-subgraphs:4013 }` to the API host and fallback UI hosts before the generic UI/API handlers.

- [ ] **Step 3: User-run deployment verification**

After applying production config, open an announcement document link. It should use the public API host and should not point to `127.0.0.1`.

### Task 5: Static Verification

**Files:**
- Review changed files only.

- [ ] **Step 1: Run allowed static checks**

Codex may run:

```powershell
git diff --check
git diff -- hrms-ui/src/modules/notifications/createAnnouncementInput.ts hrms-ui/src/modules/notifications/CreateAnnouncementModal.tsx hrms-ui/src/utils/actionUrl.ts hrms-ui/src/components/layout/NotificationDropdown.tsx hrms-ui/src/modules/admin/AdminNotificationsPage.tsx hrms-documentation/deploy/Caddyfile.example hrms-documentation/deploy/docker-compose.prod.yml hrms-documentation/deploy/.env.example
```

- [ ] **Step 2: Report unrun tests**

Ask the user to run:

```powershell
cd D:\work\heliorventures\hrms-ui
npm test -- src/modules/notifications/createAnnouncementInput.test.ts src/utils/actionUrl.test.ts
npm run build
```
