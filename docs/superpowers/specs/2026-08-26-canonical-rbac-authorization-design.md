# Canonical Tenant RBAC Authorization Design

## Problem

Runtime authorization was changed from broad resource scopes and role-name fallbacks to exact
permissions, but the matching read permissions, role assignments, scopes, and React capability
gates were not migrated together. As a result, authenticated employees can navigate to Attendance,
Timesheet, Leave, Expenses, and Payroll while the Rust services reject the data queries.

The live `Helior Prd` tenant confirms the drift:

- `aniket.dhobada` has the legacy `DEMO_STAFF` role;
- that role grants only `assets:self`, `attendance:punch_self`, `benefits:self`,
  `grievance:self`, and `onboarding:self`;
- the tenant permission catalog does not contain the read permissions now required by the Rust
  resolvers; and
- React currently treats several employee routes as available to every authenticated user.

Attendance punch-in is a separate failure. The user already has `attendance:punch_self`, is linked
to an active employee, and has no attendance row for the current business date. It must therefore
be diagnosed as a punch execution failure, not repaired by broadening authorization.

## Selected Model

Authorization has five layers with one direction of authority:

1. A permission identifies one feature action, such as `leave:read` or `timesheet:approve`.
2. A permission scope limits the records available through that exact permission: `SELF`, `TEAM`,
   `DEPARTMENT`, or `ALL`.
3. A role is only a reusable collection of permissions and scopes.
4. A user receives one or more roles. Login resolves their effective permissions and widest scope
   for each exact permission into the JWT.
5. React uses JWT permissions for visibility, while Rust independently enforces the same permission
   and scope. Runtime code never grants access because of a role name.

Roles do not appear in runtime authorization branches. Role names are assignment templates only.

## Canonical Roles

The tenant will use exactly these standard system roles:

| Role | Purpose |
| --- | --- |
| `EMPLOYEE` | Personal HRMS self-service only |
| `MANAGER` | Employee self-service plus team visibility and team approvals |
| `HR` | Tenant-wide people, attendance, leave, workflow, and HR administration |
| `PAYROLL` | Tenant-wide payroll, tax, reimbursement, and accounting operations |
| `ADMIN` | Full tenant administration |

The five current legacy roles map as follows:

| Legacy role | Canonical role |
| --- | --- |
| `DEMO_STAFF` | `EMPLOYEE` |
| `LINE_MANAGER` | `MANAGER` |
| `HR_ADMIN` | `HR` |
| `ACCOUNTING_APPROVER` | `PAYROLL` |
| `TENANT_ADMIN` | `ADMIN` |

Users, approval rules, workflow steps, and expense policies must be remapped before a legacy role is
deleted. The migration must abort rather than delete a referenced role when a safe mapping cannot be
proved. Unknown tenant-created custom roles are preserved; only the five named legacy roles are
replaced automatically.

## Permission Catalogue

The current granular management permissions remain. The missing employee-facing permissions are
added so every visible feature has an explicit runtime authority.

| Feature | Permissions |
| --- | --- |
| Employee profile/directory | `employee:self`, `employee:read`, `employee:write`, `employee:manage` |
| Attendance | `attendance:read`, `attendance:punch_self`, `attendance:regularize`, `attendance:punch_policy` |
| Timesheet | `timesheet:read`, `timesheet:write`, `timesheet:approve`, `timesheet:manage` |
| Leave | `leave:read`, `leave:submit`, `leave:approve`, `leave:manage` |
| Expenses | `expense:read`, `expense:submit`, `expense:approve`, `expense:manage`, `expense:pay` |
| Travel | `travel:read`, `travel:submit`, `travel:approve`, `travel:manage` |
| Payroll | `payroll:read`, `payroll:manage`, `payroll:statutory_export` |
| Tax | `tax:read`, `tax:submit`, `tax:approve`, `tax:manage` |
| Notifications | `notification:read`, `notification:manage` |
| RBAC/workflows | `role:manage`, `workflow:manage` |

Existing workplace permissions such as `benefits:self`, `benefits:manage`, `assets:self`,
`assets:read`, `assets:manage`, `onboarding:self`, and `onboarding:manage` remain feature-specific
permissions and follow the same role/JWT/UI/backend contract.

`payroll:read` becomes the authority for personal and tenant-wide payslip access. Payroll must not
reuse `employee:read`, because permission to read a payslip is not permission to browse the employee
directory.

## Role Permission and Scope Matrix

`EMPLOYEE` receives personal self-service permissions:

- `employee:self`;
- `attendance:read` with `SELF` and `attendance:punch_self`;
- `timesheet:read` with `SELF` and `timesheet:write` for the JWT-linked employee;
- `leave:read` with `SELF` and `leave:submit` for the JWT-linked employee;
- `expense:read` with `SELF` and `expense:submit` for the JWT-linked employee;
- `travel:read` with `SELF` and `travel:submit` for the JWT-linked employee;
- `payroll:read` with `SELF`;
- `tax:read` with `SELF` and `tax:submit` for the JWT-linked employee;
- `notification:read`; and
- the existing workplace `*:self` permissions.

`MANAGER` includes the employee permissions and changes read/approval visibility to `TEAM` where a
manager acts on direct reports:

- `employee:read`, `attendance:read`, `timesheet:read`, `leave:read`, `expense:read`, and
  `travel:read` with `TEAM`;
- `timesheet:approve`, `leave:approve`, `expense:approve`, and `travel:approve` with `TEAM`; and
- `attendance:regularize` with `TEAM`.

Team scope includes the manager's own employee record. Self-write permissions never allow a manager
to edit a report's personal submission directly.

`HR` includes employee self-service plus tenant-wide HR permissions:

- `employee:read`, `employee:write`, and `employee:manage` with `ALL`;
- Attendance, Timesheet, Leave, Expense, and Travel read/approval or regularization permissions with
  `ALL` where HR is an approved fallback;
- the corresponding HR configuration permissions;
- `workflow:manage` and `notification:manage`; and
- existing workplace `*:manage` permissions.

HR retains only `SELF` access to personal payroll and tax data unless a Payroll or Admin role is also
assigned.

`PAYROLL` includes employee self-service plus:

- `payroll:read`, `payroll:manage`, and `payroll:statutory_export` with `ALL`;
- `tax:read`, `tax:manage`, and `tax:approve` with `ALL`; and
- `expense:read`, `expense:approve`, and `expense:pay` with `ALL` for the accounting reimbursement
  stage.

`ADMIN` receives every tenant permission. Read, management, approval, payment, and export permissions
use `ALL`; self-submission permissions remain constrained to the JWT-linked employee unless the admin
uses a dedicated management operation.

## Database Migration

A new forward-only tenant Liquibase migration will:

1. Create every missing permission catalog row with its correct module.
2. Create the five canonical system roles.
3. Insert the canonical `role_permission` and `permission_scope` rows from the matrix above.
4. Copy each legacy role's user assignments to its canonical replacement.
5. Remap `workflow_step.approver_role_id`, `approval_rule.approver_role_id`, and
   `expense_policy.role_id` before removing legacy references.
6. Verify that every active user linked to an active employee has at least one canonical role.
7. Delete mappings and rows for the five legacy roles only after all references are migrated.
8. Fail the changeset if any legacy role remains referenced.

The migration is idempotent through stable lookup keys and conflict handling. It does not silently
grant permissions to unknown custom roles.

Seed and tenant-bootstrap scripts will create the same catalog and canonical roles for new tenants.
The employee-login UI must require at least one role assignment; it must not create a login with an
empty role list.

## Backend Enforcement

Each protected resolver will require the permission for its exact action. Read/list/detail operations
will resolve scope from that same permission. Self-submission operations will resolve the employee
from the JWT and will not accept an arbitrary employee ID.

The backend audit includes:

- adding missing permission constants and replacing payroll's `employee:read` check with
  `payroll:read`;
- requiring `attendance:read` for personal attendance history;
- requiring write/submit permissions for Timesheet, Leave, Expense, Travel, and Tax self-service
  mutations;
- removing remaining role-name and unrelated-permission authorization fallbacks; and
- returning structured `FORBIDDEN` errors naming the missing permission.

Permission scope remains exact to the action. For example, `leave:approve=TEAM` must not broaden
`leave:read=SELF` unless the role explicitly receives `leave:read=TEAM`.

## React Enforcement

React will use the JWT permission set as its only authorization input:

- sidebar destinations and route guards require the matching read permission;
- dashboard cards load only when their read permission is present;
- action buttons require the matching submit, approve, manage, pay, export, punch, or regularize
  permission;
- direct navigation to a forbidden route renders the access-denied page without issuing protected
  GraphQL queries; and
- roles are never inspected by React authorization code.

Subscriptions still decide whether a module is available to the tenant. Permissions decide what the
signed-in user may do inside an available module. Both conditions must pass.

## Attendance Punch Failure

The fresh punch failure for `aniket.dhobada` is not an RBAC failure. Implementation will first add a
rollback-isolated PostgreSQL regression that executes the same Rust punch service path for an active
employee with no attendance row on the current tenant business date.

Separately, the migration will quarantine legacy `OPEN` rows that have no canonical `check_in_at` by
marking them `INCOMPLETE`, and the database constraint will prevent future `OPEN` rows without a
canonical check-in instant. Rust will only close an `OPEN` row when its canonical check-in instant is
present. This protects old tenants but will not be presented as the explanation for Aniket's fresh
punch until the reproducing test identifies the exact failing operation.

Backend errors will be logged with request ID, tenant ID, operation name, and safe error code while
excluding JWTs, passwords, and sensitive employee data. React will show actionable GPS, policy,
validation, and permission messages instead of mapping every punch failure to a database-style
generic message.

## Session and Deployment Behaviour

Role permissions and scopes are resolved at login and embedded in the access token. After migration
or role changes, affected users must sign out and sign in again. The UI already warns administrators
about this requirement and will continue to do so.

Deployment order is:

1. apply the tenant migration;
2. deploy/restart Auth and affected Rust services;
3. deploy the gateway schema and React UI; and
4. sign out and sign in to obtain the new claims.

## Verification

Regression coverage will include:

- migration tests for catalog creation, role mappings, scopes, user remapping, reference remapping,
  deletion safety, and idempotency;
- Rust tests proving exact permission and exact-scope behavior for all five roles;
- Rust tests proving role names and unrelated permissions grant no authority;
- Rust tests for self-submission employee binding and manager team boundaries;
- PostgreSQL attendance tests for fresh punch, legacy open-row quarantine, and concurrent punch
  serialization; and
- React tests for sidebar visibility, route guards, dashboard query suppression, and action-button
  permissions.

No production data change, commit, or push will be performed automatically. Test suites will not be
run without explicit approval when they are token- or time-expensive.

## Out of Scope

- Operator-plane roles and permissions.
- Automatic deletion of unknown tenant-created custom roles.
- Permission inference from job titles, email addresses, or role names.
- Changing module subscriptions as part of RBAC migration.
