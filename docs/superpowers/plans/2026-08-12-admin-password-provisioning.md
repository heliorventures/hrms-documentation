# Admin Password Provisioning Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add admin initial-password provisioning, admin password reset, and forced next-login user password change.

**Architecture:** Tenant user account writes live in `kabipay-employee` because they are tied to employee records and RBAC admin screens. Client login/change-password remains in `kabipay-auth`, with a `must_change_password` flag carried through JWT/session state so the UI can force the user to the existing Security tab.

**Tech Stack:** Rust async-graphql, SeaORM, Argon2 helper, Liquibase XML migrations, React/TypeScript, graphql-request, GraphQL codegen.

## Global Constraints

- Do not run unit tests.
- Do not auto-commit.
- Do not run Dart or Flutter commands.
- Email is optional.
- Username is tenant-scoped and required for login accounts.
- Admin-set and admin-reset passwords are temporary.
- Password hashes use Argon2 and session revocation happens on password reset/change.

---

### Task 1: Tenant Password State

**Files:**
- Create: `hrms-database/changelog/migrations/0049_user_must_change_password/user_must_change_password.xml`
- Modify: `hrms-database/changelog/tenant.changelog-master.xml`
- Modify: `hrms-svc/crates/kabipay-db-entities/src/tenant/d0005_auth_rbac.rs`

**Interfaces:**
- Produces: `user.must_change_password: bool`

- [ ] Add Liquibase column `must_change_password BOOLEAN DEFAULT false NOT NULL` with precondition.
- [ ] Include migration after 0048 in tenant master changelog.
- [ ] Add `must_change_password: bool` to the SeaORM `user::Model`.

### Task 2: Auth Forced-Change Contract

**Files:**
- Modify: `hrms-svc/crates/kabipay-common/src/context.rs`
- Modify: `hrms-svc/crates/kabipay-auth/src/jwt.rs`
- Modify: `hrms-svc/crates/kabipay-auth/src/handlers.rs`
- Modify: `hrms-ui/src/auth/authClient.ts`
- Modify: `hrms-ui/src/auth/clientSession.ts`
- Modify: `hrms-ui/src/contexts/AuthContext.tsx`
- Modify: `hrms-ui/src/routes/RouteGuards.tsx`
- Modify: `hrms-ui/src/modules/profile/ProfileSettingsPage.tsx`
- Modify: `hrms-ui/src/modules/profile/components/SecurityTab.tsx`

**Interfaces:**
- Produces: `TokenPair.mustChangePassword: boolean`
- Produces: `ParsedClientSession.mustChangePassword: boolean`

- [ ] Add `must_change_password` to `ClientClaims` with serde default.
- [ ] Add `mustChangePassword` to auth `TokenPair`.
- [ ] Pass `user.must_change_password` into login and refresh token issuing.
- [ ] Set `must_change_password = false` in `client_change_password`.
- [ ] Parse `must_change_password` from JWT in UI session parsing.
- [ ] Force authenticated users with `mustChangePassword` to `/profile/settings?tab=security`.
- [ ] Make Profile Settings open the Security tab from `?tab=security`.
- [ ] Show forced-change copy in Security tab.

### Task 3: Employee Account Mutations

**Files:**
- Modify: `hrms-svc/crates/kabipay-employee/src/resolvers/types.rs`
- Modify: `hrms-svc/crates/kabipay-employee/src/resolvers/mutation.rs`
- Modify: `hrms-svc/crates/kabipay-employee/src/services/employee_service.rs`
- Modify: `hrms-svc/crates/kabipay-employee/src/services/rbac_admin_service.rs`

**Interfaces:**
- Produces: `CreateEmployeeInput.loginAccount`
- Produces: `provisionEmployeeLogin(input): Employee`
- Produces: `resetEmployeePassword(input): Boolean`

- [ ] Add GraphQL input objects for login creation, provisioning, and reset.
- [ ] Hash admin-provided passwords with `tokio::task::spawn_blocking`.
- [ ] Create employee plus user plus user roles in one transaction.
- [ ] Add provision-login for existing employee without linked user.
- [ ] Add reset-password for linked employee user, set `must_change_password = true`, and delete sessions.
- [ ] Enforce tenant RBAC admin permission for all credential mutations.

### Task 4: GraphQL Documents And Admin UI

**Files:**
- Modify: `hrms-ui/src/api/documents/clientOperations.graphql`
- Modify: `hrms-ui/src/api/schema-extensions/hrms-rbac.graphql`
- Modify: `hrms-ui/src/modules/admin/components/CreateEmployeeModal.tsx`
- Modify: `hrms-ui/src/modules/admin/components/EditEmployeeModal.tsx`
- Modify: `hrms-ui/src/modules/admin/AdminEmployeesPage.tsx`
- Modify: generated files under `hrms-ui/src/api/graphql/`

**Interfaces:**
- Consumes: Task 3 GraphQL mutations.

- [ ] Extend create employee operation with account fields.
- [ ] Add provision and reset mutations to documents.
- [ ] Load tenant roles for role selection in employee modal.
- [ ] Replace warning text with account creation fields.
- [ ] Add edit-modal provision/reset controls.
- [ ] Refresh employee list after successful account provisioning or reset.
- [ ] Update generated GraphQL documents and types.

### Task 5: Static Verification

**Files:**
- Inspect changed files only.

**Interfaces:**
- Consumes: all prior tasks.

- [ ] Run non-test static checks that are available and reasonable.
- [ ] Run `git diff --check` in each touched repo.
- [ ] Report unit tests were not run and list exact commands for the user to run.
