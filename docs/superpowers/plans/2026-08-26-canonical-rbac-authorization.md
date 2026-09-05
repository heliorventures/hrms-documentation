# Canonical RBAC Authorization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make canonical roles, granular permissions, and permission scopes the single authorization model across tenant data, Rust services, JWT claims, and React feature visibility.

**Architecture:** Liquibase owns the permission catalogue, five canonical system roles, their permission assignments, and their scopes. Authentication derives exact permission and scope claims from the user's assigned roles. Rust resolvers remain the enforcement authority; React consumes the same exact permission codes to hide inaccessible routes, actions, and data requests. No runtime authorization decision may depend on role names.

**Tech Stack:** PostgreSQL, Liquibase XML, PowerShell migration checks, Rust, SeaORM, async-graphql, React, TypeScript, graphql-request, Vitest, Testing Library.

**Spec:** `docs/superpowers/specs/2026-08-26-canonical-rbac-authorization-design.md`

## Global Constraints

- Do not commit, push, fetch, or rewrite unrelated work.
- Preserve custom tenant roles. Only migrate and remove `DEMO_STAFF`, `LINE_MANAGER`, `HR_ADMIN`, `ACCOUNTING_APPROVER`, and `TENANT_ADMIN`.
- Role names are setup data only. Runtime authorization must use exact permission codes and the scope attached to that exact permission.
- Rust is the security boundary. React visibility is defense in depth and must match the backend contract.
- Never broaden a missing scope. A granted permission without an explicit scope must fail closed for scoped data access.
- Define `TEAM` consistently: read permissions cover the manager plus the reporting subtree; approval permissions cover the reporting subtree but always exclude the acting manager's own request.
- Do not edit generated GraphQL output directly. This plan does not require a schema change; if execution reveals one, edit source GraphQL/schema first and run codegen.
- Do not include JWTs, email addresses, employee names, coordinates, passwords, or database URLs in logs.
- Stop and reconcile if any planned file changes while it is being edited by another worker.

---

## Task 1: Lock the database RBAC contract with a failing migration test

**Files:**

- Create: `hrms-database/scripts/test-canonical-rbac-migration.ps1`
- Reference: `hrms-database/changelog/tenant.changelog-master.xml`
- Reference: `hrms-database/scripts/test-attendance-management-migration.ps1`

- [ ] Add a PowerShell static contract test that requires migration `0067_canonical_rbac_authorization/canonical_rbac_authorization.xml` to be included by the tenant master changelog.
- [ ] Require the migration to contain exactly the five canonical system-role names: `EMPLOYEE`, `MANAGER`, `HR`, `PAYROLL`, and `ADMIN`.
- [ ] Require explicit legacy mappings: `DEMO_STAFF -> EMPLOYEE`, `LINE_MANAGER -> MANAGER`, `HR_ADMIN -> HR`, `ACCOUNTING_APPROVER -> PAYROLL`, and `TENANT_ADMIN -> ADMIN`.
- [ ] Require all approved permission pairs from the design spec, including the missing read/write/submit permissions for attendance, timesheet, leave, expense, travel, payroll, tax, notifications, and employees.
- [ ] Require migration statements for all role foreign-key consumers: `user_role`, `workflow_step.approver_role_id`, `approval_rule.approver_role_id`, and `expense_policy.role_id`.
- [ ] Require transfer/removal order: create canonical rows, remap dependent rows, populate the canonical matrix/scopes, then delete only mapped legacy role rows.
- [ ] Add a negative assertion that the delete predicate cannot delete roles outside the five-name legacy allowlist.
- [ ] Run the test and confirm it fails because migration 0067 does not exist yet:

```powershell
pwsh -NoProfile -File .\scripts\test-canonical-rbac-migration.ps1
```

Run from: `hrms-database`

## Task 2: Add the idempotent canonical RBAC tenant migration

**Files:**

- Create: `hrms-database/changelog/migrations/0067_canonical_rbac_authorization/canonical_rbac_authorization.xml`
- Modify: `hrms-database/changelog/tenant.changelog-master.xml`
- Test: `hrms-database/scripts/test-canonical-rbac-migration.ps1`

- [ ] Add idempotent permission catalogue inserts keyed by `(resource, action)` using `gen_random_uuid()` only for missing rows.
- [ ] Add or reactivate the five canonical system roles for the current tenant, keyed case-insensitively by canonical name.
- [ ] Build an in-migration legacy-to-canonical role map and insert missing `user_role` assignments for each legacy assignment.
- [ ] Remap `workflow_step.approver_role_id`, `approval_rule.approver_role_id`, and `expense_policy.role_id` through the same map before deleting any legacy row.
- [ ] Replace canonical system-role `role_permission` rows with the exact approved matrix. Do not touch permission rows for custom roles.
- [ ] Replace canonical `permission_scope` rows with exact per-permission scopes: self-service permissions use `SELF`, manager read/approval permissions use `TEAM`, HR operational permissions use `ALL` while payroll/tax self-service remains `SELF`, PAYROLL accounting permissions use `ALL`, and ADMIN uses `ALL`.
- [ ] Preserve `permission_scope` uniqueness by deleting/reinserting scopes only for the five canonical role IDs inside the change set transaction.
- [ ] Delete only the five mapped legacy role rows after all foreign-key consumers are remapped. Rely on explicit predicates, not `is_system_role` alone.
- [ ] Treat the destructive role consolidation as forward-only because deleted pre-migration customizations cannot be reconstructed safely. Document tenant-schema backup/restore as the rollback strategy and do not provide a misleading partial rollback.
- [ ] Include migration 0067 after 0066 in `tenant.changelog-master.xml`.
- [ ] Run the static migration contract test and confirm it passes:

```powershell
pwsh -NoProfile -File .\scripts\test-canonical-rbac-migration.ps1
```

Run from: `hrms-database`

## Task 3: Make seed and admin bootstrap produce the same canonical model

**Files:**

- Modify: `hrms-database/scripts/seed-demo-data.ps1`
- Modify: `hrms-database/scripts/bootstrap-tenant-admins.ps1`
- Modify: `hrms-database/scripts/test-attendance-management-migration.ps1`
- Test: `hrms-database/scripts/test-canonical-rbac-migration.ps1`

- [ ] Replace deterministic legacy role IDs and displayed legacy role names in the demo seed with canonical role IDs/names.
- [ ] Assign demo users to canonical roles only. Keep the intended persona mapping: staff `EMPLOYEE`, line manager `MANAGER`, HR demo user `HR`, accounting user `PAYROLL`, tenant administrator `ADMIN`.
- [ ] Generate the complete permission catalogue and role matrix from one PowerShell data structure so role grants and scope inserts cannot drift within the seed script.
- [ ] Update workflow fallback role references to canonical roles. Manager workflow stages continue to use reporting-manager semantics; role fallbacks use `MANAGER`, `HR`, `PAYROLL`, or `ADMIN` as specified by the workflow.
- [ ] Change `bootstrap-tenant-admins.ps1` to ensure `HR` and `ADMIN`, grant the canonical matrix, assign `ADMIN` to tenant admins, and stop creating `HR_ADMIN`/`TENANT_ADMIN`.
- [ ] Update attendance migration static assertions that currently expect `HR_ADMIN`, `TENANT_ADMIN`, or `ORG_ADMIN` so they assert canonical permission grants instead of role-name authorization.
- [ ] Extend `test-canonical-rbac-migration.ps1` to assert neither seed nor bootstrap creates any of the five retired names.
- [ ] Run all RBAC-related database static checks:

```powershell
pwsh -NoProfile -File .\scripts\test-canonical-rbac-migration.ps1
pwsh -NoProfile -File .\scripts\test-attendance-management-migration.ps1
pwsh -NoProfile -File .\scripts\test-approval-integrity-migration.ps1
```

Run from: `hrms-database`

## Task 4: Define the exact Rust permission vocabulary and fail-closed scope behavior

**Files:**

- Modify: `hrms-svc/crates/kabipay-common/src/context.rs`
- Modify: `hrms-svc/crates/kabipay-common/src/lib.rs`
- Modify: `hrms-svc/crates/kabipay-auth/src/rbac.rs`
- Test: inline unit tests in the same Rust modules

- [ ] Add unit tests in `context.rs` for every new exact permission constant used by resolvers and for `scope_for_permission` returning only that permission's explicit scope.
- [ ] Add a regression test proving `leave:approve:TEAM` does not grant `leave:read`, `expense:read`, or any broader resource scope.
- [ ] Add a regression test proving multiple assigned roles merge the same permission to the widest valid explicit scope without broadening unrelated actions.
- [ ] Add tests proving read-scope `TEAM` includes the manager's own employee row plus the configured reporting subtree, while approval-scope `TEAM` excludes the actor's own request.
- [ ] Add constants and exports for `employee:self`, `employee:read`, `employee:manage`, `timesheet:read`, `timesheet:write`, `leave:read`, `leave:submit`, `expense:read`, `expense:submit`, `travel:read`, `travel:submit`, `payroll:read`, `payroll:manage`, `tax:read`, `tax:submit`, `tax:manage`, and `notification:read`.
- [ ] Keep JWT authorization derivation based only on `user_role -> role_permission -> permission` and the exact `permission_scope` row. Remove or stop consuming broad resource fallbacks for authorization decisions.
- [ ] Ensure a permission with no explicit scope cannot inherit scope from another action on the same resource.
- [ ] Run focused unit tests:

```powershell
cargo test -p kabipay-common context::tests
cargo test -p kabipay-auth rbac::tests
```

Run from: `hrms-svc`

## Task 5: Enforce exact read permissions and scopes in Rust queries

**Files:**

- Modify: `hrms-svc/crates/kabipay-attendance/src/resolvers/query.rs`
- Modify: `hrms-svc/crates/kabipay-leave/src/resolvers/query.rs`
- Modify: `hrms-svc/crates/kabipay-expense/src/resolvers/query.rs`
- Modify: `hrms-svc/crates/kabipay-payroll/src/resolvers/query.rs`
- Modify: relevant inline/test modules for these resolvers

- [ ] Add failing authorization tests for a self-scoped employee, a team-scoped manager, an all-scoped administrator, and a user missing the exact read permission.
- [ ] Require `attendance:read` for `myAttendance`, day-summary reads, attendance reports, and managed attendance lists; apply its exact `SELF`, `TEAM`, or `ALL` scope.
- [ ] Require `timesheet:read` for timesheet entry/list queries and apply exact scope when an employee target is accepted.
- [ ] Keep leave list/balance queries on `leave:read`, and verify `SELF`, `TEAM`, and `ALL` return only authorized employees.
- [ ] Keep expense claims on `expense:read`; split travel request queries to `travel:read` instead of reusing the expense permission.
- [ ] Replace `employee:read` on payslip queries with `payroll:read`, using `SELF` for an employee and `ALL` for PAYROLL/ADMIN.
- [ ] Require `tax:read` for employee tax/proof queries and exact scope for any target employee.
- [ ] Require `notification:read` on notification list/detail queries while preserving tenant/user filtering.
- [ ] Confirm every resolver calls `data_scope_from_context` with the exact permission it checked; do not call ordinary service `.get()` methods inside transaction callbacks.
- [ ] Run focused service tests:

```powershell
cargo test -p kabipay-attendance
cargo test -p kabipay-leave
cargo test -p kabipay-expense
cargo test -p kabipay-payroll
```

Run from: `hrms-svc`

## Task 6: Enforce exact self-service and management permissions in Rust mutations

**Files:**

- Modify: `hrms-svc/crates/kabipay-attendance/src/resolvers/mutation.rs`
- Modify: `hrms-svc/crates/kabipay-leave/src/resolvers/mutation.rs`
- Modify: `hrms-svc/crates/kabipay-expense/src/resolvers/mutation.rs`
- Modify: `hrms-svc/crates/kabipay-payroll/src/resolvers/mutation.rs`
- Modify: corresponding resolver/service tests

- [ ] Add denied/allowed tests before changing each mutation gate.
- [ ] Require `timesheet:write` for creating, updating, deleting, and submitting the caller's own timesheet; retain ownership and locked-status validation.
- [ ] Require `leave:submit` for submit/cancel actions on the caller's own leave requests; retain ownership and workflow state checks.
- [ ] Require `expense:submit` for expense submission and caller-owned edits/cancellations; require `travel:submit` for travel submission and caller-owned edits/cancellations.
- [ ] Keep approvals on exact `*:approve` permissions and use their explicit scope plus workflow-current-step authority. A manager sees/acts only on requests for employees in the manager's team and only when the workflow step permits it.
- [ ] Require `payroll:manage` for cycle/run/configuration mutations and keep `expense:pay` for payment status actions.
- [ ] Require `tax:submit` for employee proof submission, `tax:approve` for review, and `tax:manage` for tax configuration.
- [ ] Verify rare branches: self-approval, stale workflow step, inactive employee, missing reporting manager, and concurrent approval remain fail closed with stable error codes.
- [ ] Run the same focused service tests from Task 5.

## Task 7: Prevent login accounts and access-management updates without roles

**Files:**

- Modify: `hrms-svc/crates/kabipay-employee/src/services/employee_service.rs`
- Modify: `hrms-svc/crates/kabipay-employee/src/services/rbac_admin_service.rs`
- Modify: `hrms-svc/crates/kabipay-employee/src/resolvers/mutation.rs`
- Modify: `hrms-ui/src/modules/admin/components/CreateEmployeeModal.tsx`
- Modify: `hrms-ui/src/modules/admin/components/EditEmployeeModal.tsx`
- Modify: `hrms-ui/src/modules/hr/HrAccessManagementPage.tsx`
- Test: `hrms-ui/src/modules/admin/components/CreateEmployeeModal.test.tsx`
- Test: add or extend Rust inline tests for role validation

- [ ] Add Rust tests proving employee login creation/provisioning rejects an empty role list and rejects deleted/cross-tenant role IDs.
- [ ] Add a service-level invariant that any active tenant login user managed through employee provisioning must retain at least one active tenant role.
- [ ] Make `set_user_roles` reject an empty final assignment for active employee-linked users. Allow clearing roles only as part of the existing deactivate/offboard transaction that also disables sessions.
- [ ] Keep role updates transactional: validate all role IDs first, replace assignments, revoke active sessions/refresh tokens, then commit.
- [ ] Add React validation tests requiring a role whenever login-account creation/provisioning is enabled.
- [ ] Default the employee create/provision UI to the canonical `EMPLOYEE` role when that role is present, while still requiring explicit user confirmation in the form.
- [ ] Ensure role-management UI displays only active roles and labels the five canonical system roles consistently.
- [ ] Run focused tests:

```powershell
cargo test -p kabipay-employee
npm test -- src/modules/admin/components/CreateEmployeeModal.test.tsx
```

Run the Rust command from `hrms-svc` and the npm command from `hrms-ui`.

## Task 8: Make React routes and actions use exact permissions

**Files:**

- Modify: `hrms-ui/src/auth/permissions.ts`
- Modify: `hrms-ui/src/auth/permissionService.ts`
- Modify: `hrms-ui/src/auth/permissionService.test.ts`
- Modify: `hrms-ui/src/routes/RouteGuards.test.tsx`
- Modify: `hrms-ui/src/components/layout/Sidebar.test.tsx`

- [ ] Add failing permission-service tests for each affected route using a logged-in session with no domain permission; attendance, timesheet, leave, expenses/travel, payroll, and tax must be denied.
- [ ] Add all Rust-backed permission codes to `PERMISSIONS` using identical strings.
- [ ] Map self-service routes to exact read permissions: attendance to `attendance:read`, timesheet to `timesheet:read`, leave to `leave:read`, expenses to `expense:read` or `travel:read`, payslips to `payroll:read`, and employee tax pages to `tax:read`.
- [ ] Correct the reversed payroll route contract: `/payroll/pay` requires `payroll:manage`, while `/payroll/payslips` requires `payroll:read`; `/payroll/tax` allows employee self-service with `tax:read` and separately gates review/configuration controls with `tax:approve`/`tax:manage`.
- [ ] Keep actions separately gated: punch, write, submit, approve, manage, and pay buttons must not inherit route-read access.
- [ ] Define dashboard card capabilities separately so a user may open the dashboard while unauthorized cards are omitted and their GraphQL requests are never sent.
- [ ] Update route-guard tests to prove denied lazy routes are not loaded and authorized routes render with the exact permission.
- [ ] Update sidebar tests to prove navigation reflects permission changes rather than role names.
- [ ] Run focused tests:

```powershell
npm test -- src/auth/permissionService.test.ts src/routes/RouteGuards.test.tsx src/components/layout/Sidebar.test.tsx
```

Run from: `hrms-ui`

## Task 9: Suppress unauthorized React data requests and controls

**Files:**

- Modify: `hrms-ui/src/modules/dashboard/components/PunchInOut.tsx`
- Modify: `hrms-ui/src/modules/dashboard/components/LeaveBalanceCard.tsx`
- Modify: `hrms-ui/src/modules/timesheet/TimesheetPage.tsx`
- Modify: `hrms-ui/src/modules/leave/LeavePage.tsx`
- Modify: expense/travel page and hook files that issue list/submission operations
- Modify: payroll page/hook files that issue payslip/tax operations
- Test: existing colocated component/page tests, including `PunchInOut.test.tsx` and `LeaveBalanceCard.test.tsx`

- [ ] Add tests proving a missing read permission renders no card/page data section and sends no GraphQL request.
- [ ] Add tests proving read-only permission loads data but does not render punch/write/submit/approve/manage controls.
- [ ] Pass permission-derived `enabled` conditions into each data hook or guard effects before calling `client.request`; do not fetch and then hide the response.
- [ ] Keep independent dashboard requests parallel for authorized cards and avoid serial request waterfalls.
- [ ] Clear stale page/card data when the session or permission set changes, so data from a previous user cannot flash for the next user.
- [ ] Preserve user-visible forbidden feedback for direct deep links while preventing forbidden requests during ordinary navigation.
- [ ] Run affected component tests, then the complete UI test suite:

```powershell
npm test -- src/modules/dashboard/components/PunchInOut.test.tsx src/modules/dashboard/components/LeaveBalanceCard.test.tsx
npm test
npm run lint
npm run build
```

Run from: `hrms-ui`

## Task 10: Verify migration, JWT refresh, and the five persona journeys

**Files:**

- Modify only if needed: `hrms-documentation` deployment/runbook documentation for tenant migration and forced re-login
- Do not modify production data until the user explicitly approves the migration command and target tenant.

- [ ] Capture pre-migration counts for roles, user-role assignments, role permissions, permission scopes, and all role foreign-key consumers.
- [ ] Back up the target tenant schema before applying migration 0067.
- [ ] Apply the tenant Liquibase migration using the repository's existing tenant update procedure.
- [ ] Run post-migration SQL assertions: all five canonical roles exist once, the five legacy names are absent, no user lost their mapped role, no role foreign key is orphaned, and custom roles remain unchanged.
- [ ] Restart affected Rust services, then force users to sign out/in so access JWTs contain the new exact permissions and scopes.
- [ ] Verify these journeys through GraphQL and UI:
  - `EMPLOYEE`: own attendance/timesheet/leave/expense/travel/payroll/tax only; no approval or administration.
  - `MANAGER`: own self-service plus direct/recursive team reads and approvals according to the implemented team definition; no all-tenant access.
  - `HR`: all employee/attendance/timesheet/leave/expense/travel HR operations; own payroll/tax only.
  - `PAYROLL`: accounting, payroll, tax, and expense-payment work; no HR directory management unless separately granted.
  - `ADMIN`: all tenant features and all scopes.
- [ ] Verify an inactive employee's login and sessions remain disabled.
- [ ] Verify a user assigned multiple roles receives the union of exact permissions and the widest scope only for duplicate permissions.
- [ ] Run final static checks without committing:

```powershell
git diff --check
git status --short
```

Run separately in `hrms-database`, `hrms-svc`, and `hrms-ui`.
