# Permission Contract Convergence Design

## Purpose

The canonical RBAC rollout established permission-based authorization, but some permissions still
combine an operation with a scope (for example, `employee:self`), and several React routes check
only permission presence while their GraphQL operations require a stronger scope. This allows a
route to appear even though its data requests are correctly rejected by Rust.

This design makes permission plus permission scope the only runtime authorization authority across
the database, JWT, Rust services, and React UI. Role names remain configuration labels used to
assemble default permission bundles. Runtime code must not authorize by role name.

## Security Boundaries

Employee information is divided into three independent data classes:

1. **Company directory data**: employee name, employee code, department, designation, and work
   contact information. Every active employee may view this data for active colleagues.
2. **Employee profile data**: personal and employment information that is not part of the company
   directory. An employee may view their own profile, a manager may view profiles in their team,
   and authorized tenant-wide people administrators may view all profiles.
3. **Payroll-sensitive data**: salary, compensation amounts, payslips, payroll results, tax data,
   bank details used for payroll, and statutory documents. Employee-profile permissions never grant
   access to this data.

A manager may view only their own payroll-sensitive data. Team scope must never broaden salary,
payslip, tax, or bank-detail access.

## Permission Model

The canonical permissions and scopes are:

| Permission | Scope | Authority |
| --- | --- | --- |
| `employee_directory:read` | `ALL` | Read the whitelisted basic company directory projection |
| `employee:read` | `SELF` | Read the signed-in employee's profile |
| `employee:read` | `TEAM` | Read the signed-in employee and authorized team profiles |
| `employee:read` | `ALL` | Read all tenant employee profiles |
| `employee:write` | `ALL` | Update employee records through approved HR operations |
| `employee:manage` | `ALL` | Perform employee lifecycle and login-management operations |
| `payroll:read` | `SELF` | Read the signed-in employee's salary and payslips |
| `payroll:read` | `ALL` | Read company payroll data and employee payroll results |
| `payroll:manage` | `ALL` | Process company payroll |
| `payroll:statutory_export` | `ALL` | Export company statutory payroll data |
| `tax:read` | `SELF` | Read the signed-in employee's tax data |
| `tax:read` | `ALL` | Read company employee tax data |
| `tax:manage` | `ALL` | Manage company tax processing |

`employee:self` is retired. Its intended authority becomes `employee:read=SELF`; scope is no
longer encoded in the permission action.

The company directory resolver returns a fixed safe projection. Possessing
`employee_directory:read=ALL` must not authorize employee profile resolvers or any payroll-sensitive
field.

## Default Role Bundles

Default roles are permission bundles only. These names must not appear in runtime authorization
branches.

| Default role | Employee directory | Employee profile | Payroll and tax | Company payroll processing |
| --- | --- | --- | --- | --- |
| `EMPLOYEE` | `employee_directory:read=ALL` | `employee:read=SELF` | `payroll:read=SELF`, `tax:read=SELF` | None |
| `MANAGER` | `employee_directory:read=ALL` | `employee:read=TEAM` | `payroll:read=SELF`, `tax:read=SELF` | None |
| `HR` | `employee_directory:read=ALL` | `employee:read=ALL`, write/manage as assigned | Payroll/tax read `ALL` | Payroll/tax manage and statutory export `ALL` |
| `ADMIN` | `employee_directory:read=ALL` | Tenant-wide employee permissions | Payroll/tax read `ALL` | Payroll/tax manage and statutory export `ALL` |

Other feature permissions remain independently assignable. Removing a permission from a role must
remove the corresponding access after the user's authorization session is refreshed.

The separate default `PAYROLL` role is retired because company payroll processing is assigned to
the default HR and Admin bundles. Existing `PAYROLL` role assignments are remapped to `HR` during
the migration. Unknown tenant-created custom roles are preserved and are never authorized by name.

## Database Migration

A new tenant migration is added after `0068`; already-applied migrations are not edited. It will:

1. Add `employee_directory:read` to the permission catalogue.
2. Convert every existing `employee:self` role grant and scope to `employee:read` with at least
   `SELF`, preserving any existing wider `employee:read` scope.
3. Remove `employee:self` role grants, scopes, and the retired permission after verifying that no
   references remain.
4. Assign `employee_directory:read=ALL` to the canonical Employee, Manager, HR, and Admin bundles.
5. Assign payroll and tax `SELF` access to Employee and Manager and `ALL` read/manage authority to
   HR and Admin as defined above.
6. Remap users and foreign-key consumers of the canonical `PAYROLL` role to `HR`, then remove the
   `PAYROLL` role only after referential-integrity checks succeed.
7. Verify the exact resulting default-role matrix and reject extra or missing grants.
8. Revoke affected tenant sessions after all grants and scopes are rewritten.

The migration runs under an explicit lock boundary and fails on ambiguous normalized role or
permission rows. It does not infer permissions from job titles, email addresses, or runtime roles.

Tenant bootstrap and seed writers must produce the same catalogue and four default role bundles for
new tenants.

## Rust Enforcement

Rust remains the security authority:

- Company-directory queries require exactly `employee_directory:read=ALL` and return only the safe
  directory DTO.
- Employee-profile resolvers require exactly `employee:read` and constrain records using that
  permission's `SELF`, `TEAM`, `DEPARTMENT`, or `ALL` scope.
- Salary, payslip, payroll-result, bank-for-payroll, and tax resolvers require their payroll or tax
  permission. They never accept `employee:read` as an alternative.
- Company payroll mutations require `payroll:manage=ALL`; company tax mutations require their exact
  tax-management permission and scope.
- Manager relationship checks can narrow `employee:read=TEAM`, attendance, leave, expense, travel,
  and timesheet data, but cannot be reused for payroll-sensitive records.
- Role names and sibling permissions grant no authority.

Authorization tests must assert denial before database access for missing permissions, invalid
scopes, sibling permissions, and role-name-only claims.

## React Enforcement

React uses the JWT permission and exact permission scope to control visibility and request
execution. It is not a substitute for backend checks.

The current partial direct-permission map is replaced by an explicit capability contract that can
express one required permission/scope or an `anyOf` set. Sidebar destinations, command-palette
destinations, route guards, page sections, actions, and GraphQL hooks consume this same contract.

All administrator routes require the exact `ALL`-scoped authority expected by the page's backend
operations. A route denied by the contract must not load its lazy page module or issue protected
GraphQL operations.

The employee directory route requires `employee_directory:read=ALL`. Employee-profile controls and
sensitive sections are rendered independently from the directory permission. Salary, payslip, and
tax UI elements use only payroll/tax permissions and scopes.

Permission changes clear protected cached state and suppress stale UI from the previous
authorization owner.

## Reports and Analytics

`/admin/reports` must not be exposed by `attendance:read=SELF`. The route is available only when the
user has at least one supported tenant-wide report authority:

- attendance report: `attendance:read=ALL`;
- leave report: `leave:read=ALL` plus the safe directory permission for employee labels; or
- payroll report: `payroll:read=ALL`.

The page displays only report types authorized by the current session. It loads only the currently
selected report's data. The existing omnibus reference-data request is removed because it combines
employee, leave, and payroll operations even when the user selected only attendance.

`analytics:read` continues to authorize the separate Insights feature. It does not bypass the
domain permission protecting attendance, leave, or payroll records.

## Error and Session Behaviour

Expected permission denial is handled before request execution in React. Backend denial remains a
structured `FORBIDDEN` response and is not converted into a generic server failure.

The migration revokes affected sessions. Users must sign in again so the JWT contains the new
permissions and scopes. No role or permission change is considered active in an existing JWT.

## Test-First Verification

Implementation follows red-green-refactor. Regression coverage includes:

- migration contract tests for permission conversion, scope preservation, exact default bundles,
  Payroll-to-HR remapping, deletion safety, bootstrap parity, and session revocation;
- Rust tests for directory projection boundaries, employee profile scopes, manager salary denial,
  employee self-payroll access, and HR/Admin company payroll authority expressed only through
  permissions;
- React tests proving unauthorized admin navigation is absent, denied lazy modules do not load,
  report types are permission-filtered, unauthorized report queries do not execute, and stale data
  is cleared on authorization change; and
- source-level checks proving runtime authorization does not compare role names.

Expensive test suites are run only after explicit approval. No migration is applied, service is
restarted, generated file is overwritten, commit is created, or remote operation is performed
automatically.

## Deployment Order

This is a coordinated authorization contract change:

1. stop affected tenant traffic or services;
2. deploy the updated Auth and Rust services and React assets together with the migration;
3. apply the new tenant migration;
4. restart services and the gateway;
5. regenerate GraphQL client output only if the exposed schema changed;
6. sign in again to obtain refreshed permission claims; and
7. execute role-by-role runtime QA.

## Out of Scope

- Operator-plane authorization.
- Granting salary visibility through manager hierarchy.
- Inferring authorization from default role names.
- Deleting unknown custom roles.
- Applying the migration or changing live tenant data without explicit approval.
