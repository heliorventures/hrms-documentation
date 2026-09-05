# Permission Contract Convergence Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make permission plus exact permission scope the only runtime authorization contract, provide a safe all-employee directory, prevent manager salary access, and align every affected React route and request with Rust enforcement.

**Architecture:** A new post-`0068` tenant migration converges the permission catalogue and default role bundles without editing applied changesets. Rust separates directory, profile, and payroll-sensitive authorization; React consumes one declarative capability contract and issues only operations authorized for the current permission owner.

**Tech Stack:** PostgreSQL 16, Liquibase XML, PowerShell contract tests, Rust 2024, async-graphql, SeaORM, React 19, TypeScript, graphql-request, Vitest, Testing Library, GraphQL Code Generator.

**Spec:** `docs/superpowers/specs/2026-08-30-permission-contract-convergence-design.md`

## Global Constraints

- Runtime authorization must never compare role names.
- Permissions are feature actions; `SELF`, `TEAM`, `DEPARTMENT`, and `ALL` are scopes on the exact permission.
- Every active employee can read only the whitelisted company-directory projection for colleagues.
- Managers can read only their own payroll-sensitive data; team hierarchy never broadens payroll or tax access.
- Company payroll processing requires `payroll:manage=ALL`.
- Already-applied migrations `0067` and `0068` are immutable; add a new migration.
- Generated GraphQL files are changed only by codegen against the updated running gateway.
- Preserve unrelated dirty files, especially `hrms-svc/data/`.
- Do not run Dart or Flutter commands.
- Do not apply migrations, restart services, run codegen, stage files, commit, push, or perform remote operations automatically.
- Ask for approval before token- or time-expensive test suites.

## File Map

### Database

- Create `hrms-database/changelog/migrations/0069_permission_contract_convergence/permission_contract_convergence.xml`: transactional catalogue, grant, role-remap, invariant, and session-revocation migration.
- Modify `hrms-database/changelog/tenant.changelog-master.xml`: include `0069` immediately after `0068`.
- Create `hrms-database/scripts/test-permission-contract-convergence-migration.ps1`: static migration and writer-parity contract.
- Modify `hrms-database/scripts/test-canonical-rbac-migration.ps1`: keep `0067` historical checks while moving current writer parity to the `0069` contract.
- Modify `hrms-database/scripts/bootstrap-tenant-admins.ps1`: emit the four current default bundles and converged permissions.
- Modify `hrms-database/scripts/seed-demo-data.ps1`: use the same current default bundles and grants.

### Rust

- Modify `hrms-svc/crates/kabipay-common/src/context.rs`: add directory permission constant and retire employee-self permission handling.
- Modify `hrms-svc/crates/kabipay-common/src/lib.rs`: export the converged constants.
- Modify `hrms-svc/crates/kabipay-employee/src/resolvers/scope.rs`: define exact directory, profile, and payroll-sensitive scope helpers.
- Modify `hrms-svc/crates/kabipay-employee/src/resolvers/query.rs`: enforce safe directory projection, profile scope, and salary isolation.
- Modify `hrms-svc/crates/kabipay-employee/src/resolvers/types.rs`: expose server-derived payroll-sensitive capability on profile access.
- Modify relevant tests inside the files above; keep tests close to existing resolver authorization inventories.
- Review `hrms-svc/crates/kabipay-payroll/src/resolvers/query.rs` and `mutation.rs`: strengthen tests proving `SELF` reads and `ALL` management without role fallbacks.
- Review `hrms-svc/crates/kabipay-tax/src/resolvers/query.rs` and `mutation.rs`: preserve the same self/all boundary.

### React and GraphQL documents

- Modify `hrms-ui/src/auth/permissions.ts`: add `employeeDirectoryRead`; remove `employeeSelf` after source migration.
- Modify `hrms-ui/src/auth/permissionService.ts`: replace partial direct maps with declarative exact-scope requirements and `anyOf` report authority.
- Modify `hrms-ui/src/auth/permissionService.test.ts`: add role-independent, scope-exact route regression tests.
- Modify `hrms-ui/src/routes/RouteGuards.test.tsx`: prove denied lazy modules do not load.
- Modify `hrms-ui/src/api/documents/clientOperations.graphql`: request the server-derived payroll-sensitive capability and separate salary-bearing profile data.
- Modify `hrms-ui/src/modules/organization/OrganizationEmployeesPage.tsx`: use directory authority and clear stale rows when authorization changes.
- Modify `hrms-ui/src/modules/organization/employee-profile/hooks/useEmployeeProfileData.ts`: sequence basic, private, and payroll-sensitive requests by server capability.
- Modify `hrms-ui/src/modules/organization/employee-profile/EmployeeProfileShell.tsx`: show salary from payroll capability, never HR/manager labels.
- Create `hrms-ui/src/modules/organization/employee-profile/employeeProfileDocuments.test.ts`: source-document sensitivity contract that does not depend on stale generated output.
- Create `hrms-ui/src/modules/organization/employee-profile/hooks/useEmployeeProfileData.authorization.test.tsx`: request-suppression and stale-owner tests after codegen.
- Create `hrms-ui/src/modules/organization/employee-profile/EmployeeProfileShell.authorization.test.tsx`: salary-rendering capability tests after codegen.
- Modify `hrms-ui/src/modules/admin/AdminReportsPage.tsx`: permission-filter report types and remove the omnibus metadata request.
- Modify `hrms-ui/src/modules/admin/AdminReportsPage.test.tsx`: prove unauthorized report operations are never sent.
- Regenerate `hrms-ui/src/api/graphql/gql.ts` and `graphql.ts` only after the updated employee subgraph and gateway are running.

---

### Task 1: Add the Post-0068 Permission Convergence Migration

**Files:**
- Create: `hrms-database/scripts/test-permission-contract-convergence-migration.ps1`
- Create: `hrms-database/changelog/migrations/0069_permission_contract_convergence/permission_contract_convergence.xml`
- Modify: `hrms-database/changelog/tenant.changelog-master.xml`

**Interfaces:**
- Consumes: existing `${schema}` parameter, `role`, `permission`, `role_permission`, `permission_scope`, `user_role`, workflow/expense role foreign keys, and `user_session` tables.
- Produces: `employee_directory:read`, four canonical role bundles, no `employee:self` permission, no canonical `PAYROLL` role, and revoked affected sessions.

- [ ] **Step 1: Write the failing static contract**

Create assertions that normalize the `0069` SQL and require these exact outcomes:

```powershell
Assert-True ($includes[-1] -eq 'migrations/0069_permission_contract_convergence/permission_contract_convergence.xml') '0069 must be the final tenant migration'
Assert-True ($sql -match "'employee_directory'\s*,\s*'read'") 'directory permission is missing'
Assert-True ($sql -match "'employee'\s*,\s*'read'\s*,\s*'SELF'") 'employee self profile grant must use employee:read=SELF'
Assert-True ($sql -match "'MANAGER'\s*,\s*'payroll'\s*,\s*'read'\s*,\s*'SELF'") 'manager payroll access must remain SELF'
Assert-True ($sql -match "'HR'\s*,\s*'payroll'\s*,\s*'manage'\s*,\s*'ALL'") 'HR company payroll authority is missing'
Assert-True ($sql -match "'ADMIN'\s*,\s*'payroll'\s*,\s*'manage'\s*,\s*'ALL'") 'Admin company payroll authority is missing'
Assert-True ($sql -match 'DELETE FROM .*user_session') 'permission rewrite must revoke sessions'
Assert-True ($sql -match 'RAISE EXCEPTION') 'migration must fail closed on invariant violations'
```

The contract must also reject any final canonical `PAYROLL` role and any final `employee:self` grant.

- [ ] **Step 2: Run the focused contract and verify RED**

Run only after approval:

```powershell
cd D:\work\heliorventures\hrms-database
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\test-permission-contract-convergence-migration.ps1
```

Expected: FAIL because the `0069` migration and master include do not exist.

- [ ] **Step 3: Implement the transactional migration**

Use one Liquibase changeset with an explicit `LOCK TABLE ... NOWAIT` boundary. Build temporary normalized tables for:

```text
canonical_roles: EMPLOYEE, MANAGER, HR, ADMIN
legacy role remap: PAYROLL -> HR
permission rename: employee:self -> employee:read with scope precedence SELF < TEAM < DEPARTMENT < ALL
```

Before deleting `PAYROLL`, remap `user_role`, `workflow_step.approver_role_id`, `approval_rule.approver_role_id`, `expense_policy.role_id`, and normalized `ROLE:PAYROLL` announcement audiences. Populate the exact matrix, verify missing and extra grants/scopes, remove retired rows, then revoke tenant sessions.

- [ ] **Step 4: Run the focused contract and verify GREEN**

Run the command from Step 2. Expected: `Permission contract convergence migration passed.`

- [ ] **Step 5: Run migration format checks**

```powershell
git -C D:\work\heliorventures\hrms-database diff --check
```

Expected: exit code `0`; line-ending notices are informational.

- [ ] **Step 6: Review checkpoint**

Inspect only Task 1 changes. Do not stage or commit them.

### Task 2: Converge Tenant Bootstrap and Demo Seed Writers

**Files:**
- Modify: `hrms-database/scripts/bootstrap-tenant-admins.ps1`
- Modify: `hrms-database/scripts/seed-demo-data.ps1`
- Modify: `hrms-database/scripts/test-canonical-rbac-migration.ps1`
- Modify: `hrms-database/scripts/test-permission-contract-convergence-migration.ps1`

**Interfaces:**
- Consumes: the exact current matrix declared by Task 1.
- Produces: new tenants and demo tenants with the same four bundles and permission scopes as migrated tenants.

- [ ] **Step 1: Extend the failing contract for writer parity**

Parse the tuple sources in both writers and compare normalized sets to the `0069` expected matrix:

```powershell
$expectedRoles = @('ADMIN', 'EMPLOYEE', 'HR', 'MANAGER')
Assert-SetEqual $bootstrapRoles $expectedRoles 'bootstrap roles must match the current canonical role set'
Assert-SetEqual $seedRoles $expectedRoles 'seed roles must match the current canonical role set'
Assert-True (-not ($bootstrapText -match "'employee'\s*,\s*'self'")) 'bootstrap must not recreate employee:self'
Assert-True (-not ($seedText -match "'PAYROLL'")) 'seed must not recreate the retired PAYROLL role'
```

- [ ] **Step 2: Run the contract and verify RED**

Use Task 1's PowerShell command. Expected: FAIL because both writers still match `0067`.

- [ ] **Step 3: Update both writers from one explicit matrix shape**

Keep each script self-contained, but use identical permission tuples. HR and Admin receive company payroll/tax authority; Employee and Manager retain payroll/tax `SELF`; every bundle receives `employee_directory:read=ALL`.

- [ ] **Step 4: Remove obsolete current-writer assertions from the historical 0067 test**

Keep `0067` migration assertions intact. Move only bootstrap/seed parity assertions to the new `0069` contract so historical migration content remains immutable.

- [ ] **Step 5: Verify both migration contracts**

Run only after approval:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\test-canonical-rbac-migration.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\test-permission-contract-convergence-migration.ps1
```

Expected: both PASS.

- [ ] **Step 6: Review checkpoint**

Compare migrated and newly provisioned matrices. Do not run a live migration or provisioning command.

### Task 3: Converge Shared Rust Permission Constants

**Files:**
- Modify: `hrms-svc/crates/kabipay-common/src/context.rs`
- Modify: `hrms-svc/crates/kabipay-common/src/lib.rs`

**Interfaces:**
- Produces: `PERM_EMPLOYEE_DIRECTORY_READ = "employee_directory:read"` and retained `PERM_EMPLOYEE_READ = "employee:read"`.
- Removes: production use/export of `PERM_EMPLOYEE_SELF`.

- [ ] **Step 1: Write failing common authorization tests**

Add assertions to the existing permission inventory:

```rust
assert_eq!(PERM_EMPLOYEE_DIRECTORY_READ, "employee_directory:read");
assert!(claims("employee:read", "SELF").has_any_permission(&[PERM_EMPLOYEE_READ]));
assert_eq!(claims("employee:read", "SELF").scope_for_permission(PERM_EMPLOYEE_READ), Some(ScopeType::Self_));
assert!(!claims("employee:self", "SELF").has_any_permission(&[PERM_EMPLOYEE_READ]));
```

- [ ] **Step 2: Run focused tests and verify RED**

Run only after approval:

```powershell
cd D:\work\heliorventures\hrms-svc
cargo test -p kabipay-common --quiet
```

Expected: compile failure because `PERM_EMPLOYEE_DIRECTORY_READ` is absent.

- [ ] **Step 3: Add/export the new constant and remove retired production references**

Do not add aliases from `employee:self` to `employee:read`; exact permissions must stay exact.

- [ ] **Step 4: Run focused tests and verify GREEN**

Run Task 3 Step 2. Expected: all `kabipay-common` tests pass.

- [ ] **Step 5: Review checkpoint**

Search for runtime role checks and retired permission usage:

```powershell
rg -n --glob '!target/**' 'PERM_EMPLOYEE_SELF|employee:self|roles.*contains|role.*==' crates
```

Any remaining `employee:self` occurrence must be historical migration text or an explicit negative regression test.

### Task 4: Separate Directory, Profile, and Payroll-Sensitive Rust Access

**Files:**
- Modify: `hrms-svc/crates/kabipay-employee/src/resolvers/scope.rs`
- Modify: `hrms-svc/crates/kabipay-employee/src/resolvers/query.rs`
- Modify: `hrms-svc/crates/kabipay-employee/src/resolvers/types.rs`

**Interfaces:**
- Produces: `data_scope_employee_directory(ctx) -> Result<ScopeType>` requiring `ALL`.
- Produces: `employee_profile_access` with `can_view_payroll_sensitive: bool` derived from `payroll:read` and target employee.
- Preserves: safe `EmployeeDirectoryEntryDto` as the only all-employee directory projection.

- [ ] **Step 1: Write failing resolver authorization tests**

Name the tests `directory_and_profile_permissions_do_not_substitute_for_each_other` and
`payroll_sensitive_profile_access_ignores_team_scope_and_role_labels`.

Add focused tests using the existing schema execution helpers:

```rust
// Directory permission reaches DB; employee:read and role labels do not substitute.
assert_authorization_reached_db(
    execute_query(claims(PERM_EMPLOYEE_DIRECTORY_READ, Some("ALL"), own_id),
                  "{ employeeDirectoryPage { hasMore } }").await,
    PERM_EMPLOYEE_DIRECTORY_READ,
);
assert_forbidden_before_db(
    execute_query(claims(PERM_EMPLOYEE_READ, Some("ALL"), own_id),
                  "{ employeeDirectoryPage { hasMore } }").await,
    PERM_EMPLOYEE_DIRECTORY_READ,
);

// Manager-like TEAM employee scope does not grant another employee's salary history.
assert_forbidden_before_db(
    execute_query(claims(PERM_EMPLOYEE_READ, Some("TEAM"), manager_id), salary_query).await,
    PERM_PAYROLL_READ,
);
```

Add capability tests proving `payroll:read=SELF` is true only for the JWT-linked employee and `payroll:read=ALL` is true for any in-tenant target.

- [ ] **Step 2: Run focused employee tests and verify RED**

Run only after approval:

```powershell
cargo test -p kabipay-employee directory_and_profile_permissions_do_not_substitute_for_each_other -- --nocapture
cargo test -p kabipay-employee payroll_sensitive_profile_access_ignores_team_scope_and_role_labels -- --nocapture
```

Expected: FAIL because directory still uses `employee:read` and profile access lacks payroll capability.

- [ ] **Step 3: Implement exact scope helpers**

Use `data_scope_from_context` for exact permission lookup. Require `ALL` for directory reads. Replace self-profile authorization with `employee:read` and constrain the target using the resolved viewer and `resolve_employee_scope_filter`.

- [ ] **Step 4: Make basic profile access directory-safe**

Authorize `employee_profile_access` with `employee_directory:read=ALL` for the basic projection. Derive private profile and payroll-sensitive booleans separately; do not fetch salary while calculating access.

- [ ] **Step 5: Remove salary authority alternatives**

Change `employment_history_read_access` so salary-bearing records accept only:

```text
payroll:read=SELF with target == JWT employee
payroll:read=ALL for any in-tenant target
```

`employee:read`, `employee:manage`, manager hierarchy, and role labels must not substitute.

- [ ] **Step 6: Run focused tests and verify GREEN**

Run Task 4 Step 2. Expected: focused employee authorization tests pass.

- [ ] **Step 7: Run the employee crate suite**

Run only after approval:

```powershell
cargo test -p kabipay-employee --quiet
```

Expected: permission tests pass; separately report the known unrelated masked-summary baseline failure if it remains.

- [ ] **Step 8: Review checkpoint**

Confirm directory DTOs contain no salary, tax, bank-account number, government identity value, private phone/address, or document payload.

### Task 5: Prove Payroll and Tax Boundaries Independently of Roles

**Files:**
- Modify tests in `hrms-svc/crates/kabipay-payroll/src/resolvers/query.rs`
- Modify tests in `hrms-svc/crates/kabipay-payroll/src/resolvers/mutation.rs`
- Modify tests in `hrms-svc/crates/kabipay-tax/src/resolvers/query.rs`
- Modify tests in `hrms-svc/crates/kabipay-tax/src/resolvers/mutation.rs`

**Interfaces:**
- Consumes: exact permission/scope claims from `kabipay-common`.
- Produces: regression proof that own payroll remains available while company payroll requires `ALL`.

- [ ] **Step 1: Add failing security cases**

Extend authorization tables with these cases:

```rust
// Allowed to reach scoped read path.
(PERM_PAYROLL_READ, Some("SELF"), own_employee_id, true),
// Denied before DB or target service.
(PERM_PAYROLL_READ, Some("SELF"), report_employee_id, false),
(PERM_PAYROLL_READ, Some("TEAM"), report_employee_id, false),
(PERM_EMPLOYEE_READ, Some("ALL"), report_employee_id, false),
// Company processing.
(PERM_PAYROLL_MANAGE, Some("ALL"), true),
(PERM_PAYROLL_MANAGE, Some("SELF"), false),
```

Do not put `HR`, `ADMIN`, `MANAGER`, or `PAYROLL` into claims as authorization inputs.

- [ ] **Step 2: Run focused tests and verify their behavior**

Run only after approval:

```powershell
cargo test -p kabipay-payroll --quiet
cargo test -p kabipay-tax --quiet
```

If new cases already pass, document that the backend boundary was already correct; do not change production code merely to force a RED state. If a case fails, make the exact resolver helper change needed and rerun.

- [ ] **Step 3: Review checkpoint**

Search payroll/tax production code for employee or role fallbacks. Any match must be removed or proven to be non-authorization display logic.

### Task 6: Replace React's Partial Route Map with Exact Capability Requirements

**Files:**
- Modify: `hrms-ui/src/auth/permissions.ts`
- Modify: `hrms-ui/src/auth/permissionService.ts`
- Modify: `hrms-ui/src/auth/permissionService.test.ts`
- Modify: `hrms-ui/src/routes/RouteGuards.test.tsx`

**Interfaces:**
- Produces: `PermissionRequirement` and declarative capability rules consumed by sidebar, command palette, routes, pages, and actions.
- Produces: `employeeDirectoryRead` permission code.

- [ ] **Step 1: Write failing permission-service tests**

Add these exact regressions:

```ts
expect(serviceWith(['attendance:read'], [], { 'attendance:read': 'SELF' })
  .canRoute('/admin/reports')).toBe(false);
expect(serviceWith(['attendance:read'], [], { 'attendance:read': 'ALL' })
  .canRoute('/admin/reports')).toBe(true);
expect(serviceWith(['leave:read'], [], { 'leave:read': 'ALL' })
  .canRoute('/admin/reports')).toBe(true);
expect(serviceWith(['payroll:read'], [], { 'payroll:read': 'ALL' })
  .canRoute('/admin/reports')).toBe(true);
expect(serviceWith(['employee_directory:read'], [], { 'employee_directory:read': 'ALL' })
  .canRoute('/organization/employees')).toBe(true);
expect(serviceWith([], ['ADMIN']).canRoute('/admin/reports')).toBe(false);
```

Add table tests requiring `ALL` for each `/admin/*` configuration route and proving the same permission with `SELF` is denied.

- [ ] **Step 2: Run the focused test and verify RED**

Run only after approval:

```powershell
cd D:\work\heliorventures\hrms-ui
npm test -- --run src/auth/permissionService.test.ts src/routes/RouteGuards.test.tsx
```

Expected: current `attendance:read=SELF` report test fails the new assertion.

- [ ] **Step 3: Implement declarative capability rules**

Introduce these types:

```ts
type PermissionRequirement = {
  permission: PermissionCode;
  scopes: readonly ExplicitPermissionScope[];
};

type CapabilityRequirement =
  | PermissionRequirement
  | { anyOf: readonly PermissionRequirement[] };
```

Implement one evaluator that fails closed for absent/invalid scope. Define `/admin/reports` as `anyOf` attendance, leave, or payroll read with `ALL`. Define directory routes with `employeeDirectoryRead=ALL`. Keep role labels out of capability evaluation.

- [ ] **Step 4: Verify route and lazy-loader behavior GREEN**

Run Task 6 Step 2. Expected: both test files pass and denied route loaders remain uncalled.

- [ ] **Step 5: Review checkpoint**

Confirm Sidebar, CommandPalette, notification action URLs, and RouteGuards still delegate to `canAccessTenantPath`, which now consumes the single exact capability contract.

### Task 7: Align Employee Directory and Profile UI Data Requests

**Files:**
- Modify: `hrms-ui/src/api/documents/clientOperations.graphql`
- Modify: `hrms-ui/src/modules/organization/OrganizationEmployeesPage.tsx`
- Modify: `hrms-ui/src/modules/organization/employee-profile/hooks/useEmployeeProfileData.ts`
- Modify: `hrms-ui/src/modules/organization/employee-profile/EmployeeProfileShell.tsx`
- Create: `hrms-ui/src/modules/organization/employee-profile/employeeProfileDocuments.test.ts`
- Create: `hrms-ui/src/modules/organization/employee-profile/hooks/useEmployeeProfileData.authorization.test.tsx`
- Create: `hrms-ui/src/modules/organization/employee-profile/EmployeeProfileShell.authorization.test.tsx`

**Interfaces:**
- Consumes: `employeeProfileAccess.canViewPrivateProfile` and new `canViewPayrollSensitive`.
- Produces: separate `EmployeePrivateProfile` and `EmployeePayrollSensitiveProfile` operations.

- [ ] **Step 1: Write the failing source-document sensitivity test**

Read `src/api/documents/clientOperations.graphql` and assert that `EmployeePrivateProfile` no
longer selects `employmentHistoryRecords`, `EmployeePayrollSensitiveProfile` does select it, and
`EmployeeProfileAccess` selects `canViewPayrollSensitive`.

```ts
expect(operationBody(source, 'EmployeePrivateProfile')).not.toContain('employmentHistoryRecords');
expect(operationBody(source, 'EmployeePayrollSensitiveProfile')).toContain('monthlySalary');
expect(operationBody(source, 'EmployeeProfileAccess')).toContain('canViewPayrollSensitive');
```

- [ ] **Step 2: Run the document contract and verify RED**

Run only after approval:

```powershell
cd D:\work\heliorventures\hrms-ui
npm test -- --run src/modules/organization/employee-profile/employeeProfileDocuments.test.ts
```

Expected: FAIL because salary is still selected by `EmployeePrivateProfile` and the new access
field/operation are absent.

- [ ] **Step 3: Split GraphQL documents by sensitivity**

Keep `EmployeePrivateProfile` free of `employmentHistoryRecords.monthlySalary`. Add:

```graphql
query EmployeePayrollSensitiveProfile($employeeId: ID!) {
  employmentHistoryRecords(employeeId: $employeeId, limit: 48) {
    id
    monthlySalary
    effectiveFrom
    effectiveTo
    changeReason
    updatedAt
  }
}
```

Request `canViewPayrollSensitive` from `EmployeeProfileAccess`, then rerun Step 2 and expect PASS.

- [ ] **Step 4: Regenerate GraphQL output before importing the new operation**

After Task 4's updated employee service and the gateway are running, obtain approval and run:

```powershell
npm run codegen
```

Expected: generated types expose `canViewPayrollSensitive` and
`EmployeePayrollSensitiveProfileDocument`. Do not hand-edit generated files.

- [ ] **Step 5: Write failing request-suppression tests**

Test these request sequences:

```ts
// Basic colleague directory access: access query only, no private or payroll query.
expect(request).toHaveBeenCalledWith(EmployeeProfileAccessDocument, { employeeId: 'colleague' });
expect(request).not.toHaveBeenCalledWith(EmployeePrivateProfileDocument, expect.anything());
expect(request).not.toHaveBeenCalledWith(EmployeePayrollSensitiveProfileDocument, expect.anything());

// Own profile: private and payroll-sensitive requests are both allowed.
// Manager/team profile: private request follows server capability, payroll-sensitive request never runs.
```

Add a rerender test changing the authorization owner key and assert old employee rows, private model, salary, and errors are cleared before the new request settles.

- [ ] **Step 6: Run focused tests and verify RED**

Run only after approval:

```powershell
npm test -- --run src/modules/organization/employee-profile/hooks/useEmployeeProfileData.authorization.test.tsx src/modules/organization/employee-profile/EmployeeProfileShell.authorization.test.tsx
```

Expected: FAIL because the hook does not request salary separately and salary rendering still uses
employee-management capability.

- [ ] **Step 7: Sequence requests from server capabilities**

Fetch access first. Fetch private profile only when `canViewPrivateProfile`; fetch salary data only when `canViewPayrollSensitive`. Start independent allowed requests together with `Promise.all`. Clear data when the target employee or authorization owner changes.

- [ ] **Step 8: Remove persona-derived salary rendering**

Replace:

```ts
const showSalary = canManageOrganizationFields;
```

with the server-derived payroll-sensitive capability. Manager labels and HR/Admin persona labels must not control salary rendering.

- [ ] **Step 9: Verify focused tests GREEN**

Run Task 7 Step 6. Expected: all request-suppression and stale-data tests pass.

- [ ] **Step 10: Review checkpoint**

Confirm no salary value is present in the manager/team GraphQL response, React state, rendered DOM, or error logging.

### Task 8: Make Admin Reports Permission-Selective

**Files:**
- Modify: `hrms-ui/src/modules/admin/AdminReportsPage.tsx`
- Modify: `hrms-ui/src/modules/admin/AdminReportsPage.test.tsx`

**Interfaces:**
- Consumes: exact capability service and current authorization owner key.
- Produces: authorized report type list and one domain request path per selected report.

- [ ] **Step 1: Write failing report isolation tests**

Render with explicit sessions and assert:

```ts
// attendance:read=ALL
expect(screen.getByRole('option', { name: 'Attendance Report' })).toBeTruthy();
expect(screen.queryByRole('option', { name: 'Payroll Report' })).toBeNull();
expect(request).not.toHaveBeenCalledWith(expect.stringContaining('leaveRequests'), expect.anything());
expect(request).not.toHaveBeenCalledWith(expect.stringContaining('payrollCycles'), expect.anything());

// payroll:read=ALL
expect(screen.getByRole('option', { name: 'Payroll Report' })).toBeTruthy();
expect(request).not.toHaveBeenCalledWith(AdminAttendanceDailyReportDocument, expect.anything());
```

Add a permission-change rerender asserting report rows and summaries are cleared and the selected report falls back to the first newly authorized type.

- [ ] **Step 2: Run the report test and verify RED**

Run only after approval:

```powershell
npm test -- --run src/modules/admin/AdminReportsPage.test.tsx
```

Expected: FAIL because the page currently displays all report types and executes one omnibus reference query.

- [ ] **Step 3: Remove the omnibus reference-data operation**

Replace `ClientOpsAdminReportsReferenceDataDocument` with separate leave and payroll documents. Attendance uses only generated attendance report operations. Leave employee labels come from the safe directory operation and only when leave report authority is present.

- [ ] **Step 4: Implement authorized report descriptors**

Use a descriptor array with `id`, `label`, permission/scope requirement, and loader. Filter descriptors through the permission service. Do not infer report availability from role or persona.

- [ ] **Step 5: Verify report tests GREEN**

Run Task 8 Step 2. Expected: all report isolation tests pass.

- [ ] **Step 6: Review checkpoint**

Confirm `attendance:read=SELF` hides the sidebar destination and direct route, while `attendance:read=ALL` exposes only attendance reporting unless other report permissions are present.

### Task 9: Regenerate GraphQL Types and Run Focused Cross-Layer Verification

**Files:**
- Generated: `hrms-ui/src/api/graphql/gql.ts`
- Generated: `hrms-ui/src/api/graphql/graphql.ts`
- No hand edits to generated files.

**Interfaces:**
- Consumes: running updated employee subgraph and stitching gateway.
- Produces: generated TypeScript types for the new profile capability and split operations.

- [ ] **Step 1: Verify service prerequisites**

Check that the employee subgraph and gateway are listening and that gateway startup reports a nonzero stitched subgraph count. Do not run codegen against an empty gateway.

- [ ] **Step 2: Run codegen with approval**

```powershell
cd D:\work\heliorventures\hrms-ui
npm run codegen
```

Expected: only generated GraphQL files change for schema/document updates.

- [ ] **Step 3: Run TypeScript verification with approval**

```powershell
npx tsc --noEmit
```

Expected: exit code `0`.

- [ ] **Step 4: Run the focused React authorization suite with approval**

```powershell
npm test -- --run src/auth/permissionService.test.ts src/routes/RouteGuards.test.tsx src/modules/admin/AdminReportsPage.test.tsx
```

Also include the exact employee-profile test paths added in Task 7. Expected: all pass.

- [ ] **Step 5: Run focused Rust suites with approval**

```powershell
cd D:\work\heliorventures\hrms-svc
cargo test -p kabipay-common -p kabipay-auth --quiet
cargo test -p kabipay-employee --quiet
cargo test -p kabipay-payroll -p kabipay-tax --quiet
```

Expected: authorization tests pass; report any unrelated baseline failure separately and do not hide it.

- [ ] **Step 6: Run repository hygiene checks**

```powershell
git -C D:\work\heliorventures\hrms-database diff --check
git -C D:\work\heliorventures\hrms-svc diff --check
git -C D:\work\heliorventures\hrms-ui diff --check
git -C D:\work\heliorventures\hrms-database status --short
git -C D:\work\heliorventures\hrms-svc status --short
git -C D:\work\heliorventures\hrms-ui status --short
```

Expected: no diff errors. Report staged, unstaged, untracked, and unrelated `hrms-svc/data/` artifacts separately.

### Task 10: Final Authorization Audit and Runtime QA Handoff

**Files:**
- Review all changed files; no automatic production changes.

**Interfaces:**
- Produces: evidence-backed readiness report and exact migration/runtime QA commands.

- [ ] **Step 1: Search for forbidden runtime patterns**

```powershell
rg -n --glob '!target/**' --glob '!node_modules/**' --glob '!changelog/migrations/0067*/**' 'employee:self|PERM_EMPLOYEE_SELF|HR_ADMIN|TENANT_ADMIN|roles.*contains|role.*==' hrms-svc hrms-ui
```

Classify every result. Tests may assert denial for role-only claims; production authorization must have no role-name grant branch.

- [ ] **Step 2: Review every new utility/service method**

For each method, record runtime support, error behavior, concurrency behavior, and testability. Confirm no static initializer performs IO, randomness, environment access, Firebase/platform access, or other fallible work.

- [ ] **Step 3: Review transaction boundaries**

Inside every modified `runTransaction` or database transaction callback, confirm helpers use the passed transaction/connection or pure computation only. Ensure migration locks, role remaps, invariant checks, and session revocation are one atomic changeset.

- [ ] **Step 4: Prepare live migration command without executing it**

```powershell
cd D:\work\heliorventures\hrms-database
.\scripts\update-tenant-liquibase.ps1 -Schema tenant_e6d4fc13
```

State that applying it requires explicit approval and causes affected sessions to be revoked.

- [ ] **Step 5: Prepare runtime QA matrix**

After migration, service restart, gateway restart, and fresh login, verify:

```text
Employee: directory all; own profile/salary/payslip/tax; no admin reports or payroll processing.
Manager: directory all; team operational data; own salary/payslip/tax; no report salary or team salary.
HR permission bundle: directory/profile all; authorized tenant reports; company payroll processing.
Admin permission bundle: same company-wide authorities according to assigned permissions.
Custom role: behavior follows only assigned exact permissions and scopes, never its name.
```

- [ ] **Step 6: Final review checkpoint**

Do not stage, commit, push, apply migrations, or restart services. Present changed files, verification evidence, residual risks, and the user's next commands.
