# Attendance Punch Authorization Implementation Plan

> **For agentic workers:** Execute inline and review each task before continuing. Do not dispatch subagents unless the user explicitly requests delegation.

**Goal:** Make `attendance:punch_self` the single UI/backend authorization contract while preserving existing effective access and restoring the demo user's Web Punch In/Out card.

**Architecture:** The UI already uses the desired explicit permission and needs no production change. Tighten the shared Rust claims helper, grant the permission in deterministic demo seeds, and add an idempotent tenant Liquibase migration that converts legacy role/directory fallbacks into explicit role-permission assignments before the backend fallback disappears.

**Tech Stack:** Rust, React/TypeScript authorization contracts, PostgreSQL, Liquibase XML, PowerShell seed data.

## Global Constraints

- Do not run unit tests; the user will run them and share the output.
- Do not run Dart or Flutter commands.
- Do not create commits.
- Preserve unrelated staged and untracked work, especially `0047_user_username_login.xml`.
- Do not change punch business logic, policies, history, or dashboard layout.

---

### Task 1: Lock the Backend Permission Contract

**Files:**
- Modify: `hrms-svc/crates/kabipay-common/src/context.rs`

**Interfaces:**
- Consumes: JWT `permissions: Vec<String>` and `PERM_ATTENDANCE_PUNCH_SELF`.
- Produces: `ClientClaims::can_record_own_attendance_punches() -> bool` governed only by `attendance:punch_self`.

- [ ] Add focused `#[cfg(test)]` cases constructing `ClientClaims` and asserting that `attendance:punch_self` returns `true`, while `HR_ADMIN` alone and `employee:write` alone return `false`.
- [ ] Do not execute those tests, per repository instructions; provide the exact Cargo test command for the user.
- [ ] Replace the legacy role/directory fallback with `self.has_any_permission(&[PERM_ATTENDANCE_PUNCH_SELF])` and update the method comment.
- [ ] Inspect every caller to confirm the helper remains limited to own punch-day operations and self-service manual segments.

### Task 2: Correct New and Reseeded Demo Tenants

**Files:**
- Modify: `hrms-database/scripts/seed-demo-data.ps1`

**Interfaces:**
- Consumes: `$RoleHrAdminId` and `$PermAttendancePunchSelfId`.
- Produces: an idempotent `role_permission` row for `HR_ADMIN`; the existing `TENANT_ADMIN` copy step inherits it.

- [ ] Add an `INSERT ... ON CONFLICT DO NOTHING` assignment from `HR_ADMIN` to `attendance:punch_self` beside the other HR administrator attendance permissions.
- [ ] Update the demo-login summary so `demo@kabipay.local` accurately states that self-service punch access is included.
- [ ] Statically confirm line manager and demo staff assignments remain unchanged.

### Task 3: Preserve Existing Tenant Access Explicitly

**Files:**
- Create: `hrms-database/changelog/migrations/0048_attendance_punch_authorization/attendance_punch_authorization.xml`
- Modify: `hrms-database/changelog/tenant.changelog-master.xml`

**Interfaces:**
- Consumes: tenant `role`, `permission`, and `role_permission` tables plus `kabipay_ops.module` code `ATTENDANCE`.
- Produces: the `attendance:punch_self` permission, when the tenant has the Attendance module, and explicit mappings for roles previously accepted by backend fallback logic.

- [ ] Add a Liquibase changeSet that inserts the missing permission using the active `ATTENDANCE` module ID and `gen_random_uuid()`, guarded by `NOT EXISTS`.
- [ ] Add a second data changeSet that assigns the canonical permission to non-deleted roles named `HR_ADMIN`, `TENANT_ADMIN`, or `ORG_ADMIN`, or roles already holding `employee:write` or `employee:manage`; use `ON CONFLICT DO NOTHING`.
- [ ] Document the role-assignment data change as intentionally non-revoking on rollback: automatically deleting permission mappings could remove pre-existing or subsequently approved access. A rollback must not delete the permission catalog entry or any role assignment.
- [ ] Include migration `0048` after `0047` in the tenant master changelog without editing the user's staged `0047` file.

### Task 4: Static Verification and Handoff

**Files:**
- Review all files changed by Tasks 1-3.

**Interfaces:**
- Consumes: completed diffs.
- Produces: evidence-backed handoff and user-run commands.

- [ ] Parse the new XML with PowerShell's XML parser and verify the tenant master include resolves to an existing file.
- [ ] Search frontend, backend, seed, and migration sources to confirm `attendance:punch_self` is the shared contract.
- [ ] Run `git diff --check` separately in `hrms-svc` and `hrms-database`.
- [ ] Review `git status --short` and diffs to ensure the pre-existing `0047` staged change and UI generated/config changes are untouched.
- [ ] Report that unit tests were not run and ask the user to run the targeted Cargo test plus their normal database migration validation.
