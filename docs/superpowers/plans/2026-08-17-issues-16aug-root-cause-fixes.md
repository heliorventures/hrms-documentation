# Issues 16-Aug Root-Cause Fixes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Correct the four recurring 10-Aug defects and twelve Issues_16Aug findings across authentication, employee identity, leave, workflows, expenses, attendance, notifications, reports, and profile settings.

**Architecture:** Authoritative authorization and business validation remain in Rust and tenant persistence; React consumes stable GraphQL/REST results and never infers security from presentation state. Tenant migrations update existing standard roles/workflows while seed scripts establish the same behavior for new tenants.

**Tech Stack:** React 18, TypeScript, graphql-request, async-graphql, Axum, Rust, SeaORM, PostgreSQL, Liquibase XML, PowerShell seed scripts.

## Global Constraints

- Do not run unit tests; the user will run them and share output.
- Do not run Dart or Flutter commands.
- Do not commit, push, or create a pull request.
- Preserve unrelated dirty files in `hrms-ui` and `hrms-documentation`.
- Test commands below are handoff commands for the user, not commands for the agent.
- Use static inspection and `git diff --check` for agent-side verification.

---

### Task 1: Stable domain errors and active-user request validation

**Files:**
- Modify: `hrms-svc/crates/kabipay-common/src/error.rs`
- Modify: `hrms-svc/crates/kabipay-common/src/subgraph.rs`
- Test: `hrms-svc/crates/kabipay-common/src/error.rs`

**Interfaces:**
- Produces: `KabiPayError::BusinessRule { code: &'static str, message: String }`.
- Produces: `ensure_active_client_user(db, tenant_id, user_id) -> KabiPayResult<()>`.
- Consumes: decoded `ClientClaims` before they enter the GraphQL request context.

- [x] Add tests demonstrating that a business-rule error preserves its stable GraphQL/HTTP code and that inactive/deleted/missing users are rejected.
- [ ] User-run red command: `cargo test -p kabipay-common business_rule -- --nocapture`.
- [x] Add the `BusinessRule` variant, map it to HTTP 400, and expose its code through GraphQL extensions.
- [x] Resolve the tenant connection once at the shared GraphQL request boundary and query the linked user by tenant/user ID.
- [x] Reject missing, inactive, or deleted client users before executing the GraphQL operation; leave operator JWT and explicit unauthenticated development paths unchanged.
- [ ] User-run green command: `cargo test -p kabipay-common -- --nocapture`.

Core behavior:

```rust
if row.tenant_id != tenant_id || !row.is_active || row.is_deleted {
    return Err(KabiPayError::Unauthorised);
}
```

### Task 2: Password-change errors and durable success feedback

**Files:**
- Modify: `hrms-svc/crates/kabipay-auth/src/handlers.rs`
- Modify: `hrms-ui/src/modules/profile/components/SecurityTab.tsx`
- Modify: `hrms-ui/src/modules/profile/ProfileSettingsPage.tsx`
- Modify: `hrms-ui/src/modules/auth/LoginPage.tsx`
- Modify: `hrms-ui/src/utils/graphqlUserMessage.ts`
- Test: `hrms-ui/src/utils/graphqlUserMessage.test.ts`

**Interfaces:**
- Produces REST codes `CURRENT_PASSWORD_INCORRECT` and `PASSWORD_REUSE_NOT_ALLOWED`.
- Produces navigation state `{ passwordChanged: true }` consumed by `LoginPage`.

- [x] Add message-mapping cases for the two password codes.
- [ ] User-run red command: `npm test -- src/utils/graphqlUserMessage.test.ts`.
- [x] Return `BusinessRule` for an incorrect authenticated current password and for reuse of the current password.
- [x] Validate current/new equality in `SecurityTab` before the request while keeping the server authoritative.
- [x] After successful session revocation, navigate immediately to `/login` with `passwordChanged: true`.
- [x] Render an accessible success banner on Login and clear the navigation state with `replaceState` semantics so refresh does not repeat it.
- [ ] User-run green command: `npm test -- src/utils/graphqlUserMessage.test.ts` and `cargo test -p kabipay-auth -- --nocapture`.

### Task 3: Employee login email and authoritative self-profile resolution

**Files:**
- Modify: `hrms-ui/src/modules/admin/components/EditEmployeeModal.tsx`
- Modify: `hrms-svc/crates/kabipay-employee/src/resolvers/query.rs`
- Modify: `hrms-ui/src/modules/profile/ProfileSettingsPage.tsx`
- Create: `hrms-ui/src/modules/profile/myEmployeeQuery.ts`

**Interfaces:**
- Produces GraphQL field `myEmployee: Employee` resolved from the authenticated user-to-employee link.
- Produces a narrow `MyEmployeeQuery` containing the authoritative employee `id` needed by the profile shell.

- [x] Change the Login Email UI gate to the same `employee:write` capability used by the update resolver, retaining elevated HR/tenant-admin compatibility.
- [x] Keep role-directory loading behind its separate `role:manage` capability so employee administrators can edit login details without failing the modal query.
- [x] Add `my_employee` to the employee subgraph and resolve the current employee through `employee.user_id` rather than an optional token claim.
- [x] Load `myEmployee` when the profile page mounts instead of branching solely on the optional JWT `employee_id` claim.
- [x] Render `EmployeeProfileShell` with the authoritative ID, show a clear unlinked-profile state when none exists, and remove fabricated organization placeholders from this path.
- [ ] User-run command: `npm test -- src/modules/profile` and `cargo test -p kabipay-employee -- --nocapture`.

### Task 4: Leave overlap integrity and same-scope employee labels

**Files:**
- Modify: `hrms-svc/crates/kabipay-leave/src/services/leave_service.rs`
- Modify: `hrms-svc/crates/kabipay-leave/src/resolvers/types.rs`
- Modify: `hrms-svc/crates/kabipay-leave/src/resolvers/query.rs`
- Modify: `hrms-ui/src/modules/leave/leaveBoardQuery.ts`
- Modify: `hrms-ui/src/modules/leave/LeavePage.tsx`
- Modify: `hrms-ui/src/utils/graphqlUserMessage.ts`

**Interfaces:**
- Produces business code `LEAVE_DATE_OVERLAP`.
- Adds `employeeName` and `employeeCode` to `LeaveRequest`.

- [ ] Add service tests for full-day overlap, pending/approved conflicts, rejected/cancelled non-conflicts, distinct AM/PM half days, and concurrent submissions.
- [ ] User-run red command: `cargo test -p kabipay-leave overlap -- --nocapture`.
- [x] Acquire a transaction-scoped advisory lock keyed by tenant and employee before checking active leave rows.
- [x] Reject intersecting `PENDING` or `APPROVED` ranges; permit only complementary half-day sessions on the same single date.
- [x] Batch-load employee rows for the already-authorized leave result set and attach name/code to each DTO.
- [x] Request and render the DTO labels in `LeavePage`; remove the differently scoped Org Chart name join while retaining Org Chart only for manager action context.
- [x] Map `LEAVE_DATE_OVERLAP` to a clear apply-leave message.
- [ ] User-run green command: `cargo test -p kabipay-leave -- --nocapture` and `npm test -- src/modules/leave`.

### Task 5: Expense/travel workflow fallback and accounting attendance permissions

**Files:**
- Create: `hrms-database/changelog/migrations/0054_qa_authorization_workflow_integrity/qa_authorization_workflow_integrity.xml`
- Modify: `hrms-database/changelog/tenant.changelog-master.xml`
- Modify: `hrms-database/scripts/seed-demo-data.ps1`
- Modify: `hrms-ui/src/modules/attendance/AttendancePage.tsx`

**Interfaces:**
- Existing standard first steps become `REPORTING_MANAGER_OR_ROLE` with the tenant's `HR_ADMIN` role.
- `ACCOUNTING_APPROVER` receives `attendance:punch_self`.

- [x] Add an idempotent tenant migration that updates only standard `EXPENSE` and `TRAVEL_REQUEST` first steps currently configured as reporting-manager-only.
- [x] Grant `attendance:punch_self` to existing `ACCOUNTING_APPROVER` roles by Attendance module plus resource/action lookup.
- [x] Update seed workflow steps and accounting role permissions to match migrated tenants.
- [x] Gate Add Missed Punches with `action.attendance.punch`, matching the backend mutation gate.
- [x] Keep regularization-window privilege separate from ordinary self-punch permission.
- [ ] User-run command: `liquibase validate` for the tenant changelog followed by the tenant migration in the intended environment.

### Task 6: Expense currency safety and stable limit errors

**Files:**
- Modify: `hrms-svc/crates/kabipay-expense/src/services/expense_service.rs`
- Modify: `hrms-ui/src/modules/expenses/utils/formatters.ts`
- Modify: `hrms-ui/src/modules/expenses/components/SubmitExpenseModal.tsx`
- Modify: `hrms-ui/src/utils/graphqlUserMessage.ts`
- Test: `hrms-ui/src/utils/graphqlUserMessage.test.ts`

**Interfaces:**
- Produces `normalize_currency_code(raw: &str) -> KabiPayResult<String>`.
- Produces business codes `EXPENSE_CLAIM_LIMIT_EXCEEDED` and `EXPENSE_MONTHLY_LIMIT_EXCEEDED`.

- [ ] Add Rust cases for blank, malformed, lowercase, and valid currency codes plus stable expense-limit errors.
- [x] Add TypeScript cases proving formatting never throws for partial user input and mappings show category/monthly limit messages.
- [ ] User-run red commands: `cargo test -p kabipay-expense currency -- --nocapture` and `npm test -- src/utils/graphqlUserMessage.test.ts`.
- [x] Normalize currency once at the Rust service boundary to exactly three uppercase ASCII letters and store the normalized value.
- [x] Make `formatCurrency` catch invalid/partial codes and return a plain amount fallback during editing.
- [x] Pass only a normalized currency to submission-hint rendering.
- [x] Replace generic validation errors for category/monthly caps with stable business-rule codes.
- [ ] User-run green commands: `cargo test -p kabipay-expense -- --nocapture` and `npm test -- src/utils/graphqlUserMessage.test.ts`.

### Task 7: Attendance and leave report export correctness

**Files:**
- Modify: `hrms-ui/src/modules/admin/AdminReportsPage.tsx`

**Interfaces:**
- Produces employee maps containing both label and `employeeCode`.
- Reuses `formatBackendTime` for CSV projection.

- [x] Build memoized employee metadata keyed by UUID once per data load.
- [x] Export Employee Code instead of the internal employee UUID in attendance and leave reports.
- [x] Reuse the canonical time formatter so CSV values do not contain fractional seconds.
- [x] Preserve CSV formula-injection protection in `escapeCsv`.
- [ ] User-run command: generate an attendance CSV in Excel/LibreOffice and confirm employee codes and `HH:mm:ss` values.

### Task 8: Notification filter scope and safe action destination display

**Files:**
- Modify: `hrms-ui/src/modules/notifications/NotificationsPage.tsx`
- Modify: `hrms-ui/src/modules/notifications/components/PrivateNotificationList.tsx`
- Modify: `hrms-ui/src/modules/admin/components/DirectNotificationComposer.tsx`
- Modify: `hrms-ui/src/utils/actionUrl.ts`
- Test: `hrms-ui/src/utils/actionUrl.test.ts`

**Interfaces:**
- `directNotificationActionUrl` accepts only normalized same-origin internal paths and falls back to `/notifications`.
- Private notification rows display the sanitized internal destination.

- [x] Add action URL cases for internal routes, same-origin absolute URLs, external origins, protocol-relative URLs, and malformed inputs.
- [ ] User-run red command: `npm test -- src/utils/actionUrl.test.ts`.
- [x] Move Show Unread/Show All and Mark all read controls into the Private Notifications section and label their scope explicitly.
- [x] Display the sanitized destination near the View action without rendering arbitrary HTML or external links.
- [x] Clarify composer helper text that only internal application paths are accepted.
- [ ] User-run green command: `npm test -- src/utils/actionUrl.test.ts`.

### Task 9: Static review, deployment order, and QA handoff

**Files:**
- Review all modified files.
- Update this plan's checkboxes as implementation evidence.

**Interfaces:**
- Produces a deployment order and issue-by-issue retest matrix.

- [x] Run `git diff --check` independently in `hrms-ui`, `hrms-svc`, `hrms-database`, and `hrms-documentation`.
- [x] Inspect `git status --short` and separate pre-existing changes from task changes.
- [x] Review Rust changes for cross-tenant filters, PII-safe errors/logging, transaction boundaries, and panic-free paths.
- [x] Review React effects for cancellation, stable dependencies, render safety, and permission parity.
- [ ] Hand off, without executing, exact unit-test commands from Tasks 1-8.
- [ ] State explicitly that runtime tests, build, migrations, and deployment were not run.
- [ ] Deployment order: tenant migration, Rust services/common/auth, React UI; then force a new login before retest.
