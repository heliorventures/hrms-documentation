# Notification Defect Root-Cause Repair Design

Date: 2026-08-12
Status: Approved design recorded, pending implementation plan

## Scope

This design covers the notification defects documented in `hrms-documentation/test/Issues_Notifications_11-Aug.docx`.

The affected areas are:

- Staff announcement creation permissions and form behavior
- Announcement attachment download URL generation and production routing
- Direct notification success feedback in the admin page
- Notification bell click navigation behavior

No auto-commit will be performed. Unit tests and Dart/Flutter commands will not be run by Codex.

## Root Causes

1. Staff users can open the announcement composer and submit a company-wide/HR-only announcement shape. The backend correctly rejects that request as `FORBIDDEN`, but the UI exposes controls that let a non-admin create that invalid payload.

2. Attachment URLs are generated with `KABIPAY_EMPLOYEE_PUBLIC_BASE`, which falls back to `http://127.0.0.1:4013`. Production deployment examples do not publish the employee document download route through Caddy or require a public base URL, so browsers receive a loopback URL that only works on the server.

3. The direct notification mutation returns a created count, clears the form, and refreshes data, but the admin page has no success state or status message.

4. The notification dropdown opens absolute action URLs in a new tab. Other notification UI already normalizes internal action URLs, but the bell dropdown bypasses that helper and allows blank/external/absolute paths to behave inconsistently.

## Approved Decisions

- Staff users keep access to employee-style announcement posts, but the UI will only send staff-created announcements as `employeePost: true`.
- Staff users will not see or control admin-only company-wide targeting options.
- Signed attachment URLs stay token-based. The production fix is to expose the employee document download endpoint through the public API host and configure the service with that public base.
- Direct notification sends will show an accessible success message with the number of notifications created.
- Bell notification clicks will navigate in the same tab to a safe internal route. If there is no valid internal action URL, they will fall back to `/notifications`.

## Components

### Staff Announcement Form

Modify `hrms-ui/src/modules/notifications/components/CreateAnnouncementModal.tsx`.

For users without notification management capability:

- Force `employeePost` to `true` in the submitted mutation input.
- Hide the admin-only employee/company-wide checkbox.
- Avoid sending misleading free-form targeting fields that do not enforce audience visibility.
- Keep the staff user flow focused on title, body, priority, optional image, and optional document attachment.

For HR/admin users:

- Keep existing management options available.
- Preserve the backend permission model that rejects HR-only targeting unless the user has notification management capability.

### Attachment Download Routing

Modify deployment documentation/configuration under `hrms-documentation/deploy`.

Production should set:

```env
KABIPAY_EMPLOYEE_PUBLIC_BASE=https://api.heliorsoft.com
```

Caddy should route:

```text
/files/employee-document*
```

to the employee/subgraphs service on port `4013`.

The signed token remains the authorization boundary for file download. The route only makes the existing token-protected endpoint reachable from a browser.

### Admin Direct Notification Feedback

Modify `hrms-ui/src/modules/admin/AdminNotificationsPage.tsx`.

After a successful `CreateDirectNotifications` mutation:

- Read the returned count.
- Clear previous errors.
- Show a success message such as `Created 3 direct notification(s).`.
- Use `role="status"` or `aria-live="polite"` so the feedback is accessible.
- Clear stale success feedback when a new send starts or an error occurs.

### Bell Notification Navigation

Modify `hrms-ui/src/components/layout/NotificationDropdown.tsx`.

Use the existing `normalizeInternalActionUrl` helper from `hrms-ui/src/utils/actionUrl.ts`.

Navigation behavior:

- Same-origin absolute URLs become same-tab internal navigation.
- Relative internal URLs navigate in the same tab.
- Blank, invalid, or external URLs fall back to `/notifications`.
- The dropdown should not call `window.open` for notification actions.

## Verification Plan

Codex will not run unit tests because AGENTS.md forbids it. Codex may perform static inspection and non-test checks only.

The user should run the relevant UI test/typecheck commands after implementation and share output. Recommended manual verification:

- Staff user can submit an announcement without `FORBIDDEN`.
- Staff user cannot submit company-wide/HR-only announcement options.
- Announcement attachment opens a public `https://api.heliorsoft.com/files/employee-document?...` URL in production after deployment config is applied.
- Admin direct notification send shows a success message.
- Bell notification item opens the notification target in the same tab, falling back to `/notifications` when no safe target is available.
