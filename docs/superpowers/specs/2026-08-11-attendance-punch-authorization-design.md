# Attendance Punch Authorization Design

## Problem

The dashboard renders the Web Punch In/Out card only when the client JWT contains
`attendance:punch_self`. The attendance backend currently also accepts
`employee:write`, `employee:manage`, `HR_ADMIN`, `TENANT_ADMIN`, and `ORG_ADMIN`.
The demo user receives `HR_ADMIN` and `employee:write`, but the demo seed does not
grant `attendance:punch_self`, so the backend would accept the request while the UI
hides the card.

## Considered Approaches

1. **Use `attendance:punch_self` as the canonical permission (selected).**
   Keep the UI's explicit gate, make the backend require the same permission, grant
   it to intended demo roles, and migrate existing roles that previously depended on
   backend fallbacks. This provides one auditable least-privilege contract without
   unexpectedly removing existing punch access.
2. **Copy the backend fallbacks into the UI.**
   This would make the card appear immediately for administrators, but it would keep
   self-service attendance coupled to unrelated directory permissions and role names.
3. **Change only the demo seed.**
   This would fix the reported account, but the UI/backend authorization drift would
   remain and could recur for other tenants or roles.

## Authorization Contract

`attendance:punch_self` is the only authority for recording and reading the current
user's punch-day activity. Administrative attendance correction remains separately
controlled by `attendance:regularize`; configuring punch rules remains controlled by
`attendance:punch_policy`.

The frontend continues mapping `action.attendance.punch` directly to
`attendance:punch_self`. The backend helper
`ClientClaims::can_record_own_attendance_punches` will check only that permission and
will no longer infer self-service access from employee-directory permissions or role
names.

## Data Compatibility

The demo seed will grant `attendance:punch_self` to `HR_ADMIN`. `TENANT_ADMIN`
inherits the HR administrator permission set in the existing seed flow, so both demo
administrator accounts retain punch access after reseeding.

A new tenant Liquibase data migration will preserve existing effective access before
the backend fallback is removed. It will ensure the attendance self-punch permission
catalog entry exists for subscribed attendance tenants and grant it to roles that
previously qualified through:

- role name `HR_ADMIN`, `TENANT_ADMIN`, or `ORG_ADMIN`; or
- `employee:write` or `employee:manage` permission assignment.

The migration will be idempotent through existence checks and the existing
`role_permission` primary key. It will not modify users, punch history, attendance
policies, or unrelated permissions.

## Session Behaviour

Permissions are embedded in the client access token. After migration or reseeding,
an existing user must receive a refreshed token or sign in again before the dashboard
can render the card.

## Verification

Add focused backend authorization tests proving that:

- `attendance:punch_self` grants self-punch access;
- an administrator role without the explicit permission does not grant access; and
- `employee:write` alone does not grant access.

Per repository instructions, Codex will not run unit tests. Static verification will
include targeted source inspection, XML parsing, repository diff review, and
`git diff --check`. The user will run the relevant test commands and share the output.

## Scope

No dashboard layout, punch business logic, attendance policy enforcement, or existing
attendance data will change. No automatic commit will be created.
