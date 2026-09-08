# Automated Employee Notifications Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Generate private or consented company-wide birthday and work-anniversary in-app notifications automatically, once per tenant-local event date and recipient.

**Architecture:** Add forward-only tenant tables for automation settings, employee consent, and idempotent occurrences. Keep generation in the notification domain, call it from the existing tenant-aware outbox worker, and expose separate Admin/HR settings and employee consent GraphQL/UI flows without changing existing announcement or direct-notification contracts.

**Tech Stack:** PostgreSQL 16, Liquibase XML, PowerShell contract tests, Rust 1.89, SeaORM, async-graphql, Tokio, GraphQL gateway, React 18, TypeScript, graphql-codegen, Vitest, Testing Library.

**Spec:** `hrms-documentation/docs/superpowers/specs/2026-09-08-automated-events-performance-surveys-design.md`

## Global Constraints

- Preserve existing notification, announcement, employee, tenant-clock, outbox, gateway, RBAC, and UI behavior.
- Do not edit already-applied migrations; add `0074_automated_employee_notifications` after the current `0073` include.
- Reuse `notification:manage=ALL` for tenant settings and existing `notification:read` for self-owned consent; do not add, remove, or reassign permissions in Phase 1.
- The consent mutation resolves `employee_id` from authenticated claims and never accepts a target employee ID.
- Company-wide delivery requires tenant company sharing plus the employee's explicit event-specific consent.
- Private delivery targets only the employee and their current reporting manager when each has an active linked user.
- Never include birth year, age, date of birth, or notification message content in logs or audit payloads.
- Use tenant-local business date and time. Observe 29 February birthdays on 28 February in non-leap years.
- Work anniversaries start after one completed year.
- In-app notification delivery is the only delivery channel in this phase.
- Keep authored `.graphql` files authoritative; generated GraphQL files change only through `npm run codegen`.
- Do not run Dart or Flutter commands.
- Do not apply tenant migrations, modify live data, deploy, restart services, create commits, or perform remote operations.
- Broad or expensive test suites require separate user approval; run focused regression tests first.
- Preserve unrelated dirty files, including current changes under attendance, leave tests, database seed work, and `hrms-documentation/deploy/.env.example`.

## File Structure

### Database

- Create `hrms-database/changelog/migrations/0074_automated_employee_notifications/automated_employee_notifications.xml`: Phase 1 tables, indexes, constraints, and forward-only rollback guard.
- Modify `hrms-database/changelog/tenant.changelog-master.xml`: include migration `0074` after `0073`.
- Create `hrms-database/scripts/test-automated-employee-notifications.ps1`: static migration and privacy/RBAC contract.

### Rust services

- Generate `hrms-svc/crates/kabipay-db-entities/src/tenant/d0074_automated_employee_notifications.rs` and update the generated tenant module export.
- Create `hrms-svc/crates/kabipay-notification/src/lib.rs`: library boundary consumed by the binary and worker.
- Modify `hrms-svc/crates/kabipay-notification/src/main.rs`: build the schema from library exports.
- Create `hrms-svc/crates/kabipay-notification/src/services/automation_settings.rs`: settings and employee-consent persistence.
- Create `hrms-svc/crates/kabipay-notification/src/services/automated_events.rs`: event-date rules, recipient resolution, safe templates, transactional generation, and audit writes.
- Modify `hrms-svc/crates/kabipay-notification/src/services/mod.rs`: export Phase 1 services.
- Modify `hrms-svc/crates/kabipay-notification/src/services/notification_preference.rs`: add the `celebration` mute topic and type mapping.
- Modify `hrms-svc/crates/kabipay-notification/src/resolvers/types.rs`: Phase 1 GraphQL types and inputs.
- Modify `hrms-svc/crates/kabipay-notification/src/resolvers/query.rs`: Admin settings and self-consent queries.
- Modify `hrms-svc/crates/kabipay-notification/src/resolvers/mutation.rs`: Admin settings and self-consent mutations.
- Modify `hrms-svc/crates/kabipay-outbox-worker/Cargo.toml`: depend on the notification library.
- Modify `hrms-svc/crates/kabipay-outbox-worker/src/main.rs`: invoke the idempotent celebration sweep with one tenant-local instant.

### Gateway and UI

- Modify `hrms-gateway/src/schemaContract.ts` and `schemaContract.test.ts`: fail closed when Phase 1 GraphQL fields are unavailable.
- Modify `hrms-ui/src/api/schema-extensions/hrms-notification.graphql`: local Phase 1 schema contract.
- Modify `hrms-ui/src/api/documents/clientOperations.graphql`: authored operations.
- Regenerate `hrms-ui/src/api/graphql/`: generated types and documents.
- Create `hrms-ui/src/modules/notifications/celebrationPreferences.ts`: employee query/mutation adapter and state types.
- Create `hrms-ui/src/modules/notifications/CelebrationPreferencesCard.tsx` and test: isolated employee consent UI.
- Modify `hrms-ui/src/modules/profile/components/NotificationsTab.tsx` and add a focused test: add the celebration topic and compose the consent card without coupling failure states.
- Create `hrms-ui/src/modules/admin/notificationAutomation.ts`: Admin settings query/mutation adapter and validation.
- Create `hrms-ui/src/modules/admin/components/NotificationAutomationSettingsCard.tsx` and test: isolated compact settings UI.
- Modify `hrms-ui/src/modules/admin/AdminNotificationsPage.tsx` and its test: compose the settings card while preserving announcement/direct-notification flows.

### Documentation

- Modify `hrms-documentation/docs/module-completion-status.md`: record Phase 1 implementation and verification limits.
- Modify `hrms-documentation/deploy/.env.example` only if implementation introduces an environment variable; the design currently requires none, so the existing dirty change must remain untouched.

---

### Task 1: Lock the database and privacy contract with a failing test

**Files:**
- Create: `hrms-database/scripts/test-automated-employee-notifications.ps1`
- Test: `hrms-database/scripts/test-automated-employee-notifications.ps1`

**Interfaces:**
- Consumes: current `tenant.changelog-master.xml`, employee/user/notification tables, and notification RBAC seeded by existing scripts.
- Produces: an executable contract that requires the exact three Phase 1 tables, uniqueness boundaries, consent defaults, protected foreign keys, master include, forward-only rollback, and zero RBAC reassignment statements.

- [ ] **Step 1: Write the failing PowerShell contract**

Use this structure and exact assertions:

```powershell
[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$DatabaseDir = Split-Path -Parent $PSScriptRoot
$RelativeMigration = 'migrations/0074_automated_employee_notifications/automated_employee_notifications.xml'
$MigrationPath = Join-Path (Join-Path $DatabaseDir 'changelog') $RelativeMigration
$MasterPath = Join-Path $DatabaseDir 'changelog/tenant.changelog-master.xml'

function Assert-True {
    param([bool]$Condition, [string]$Message)
    if (-not $Condition) { throw $Message }
}

Assert-True (Test-Path -LiteralPath $MigrationPath) '0074 automated employee notifications migration is missing'
[xml]$master = Get-Content -Raw -LiteralPath $MasterPath
$includes = @($master.databaseChangeLog.include | ForEach-Object { $_.file })
Assert-True ($includes -contains $RelativeMigration) 'Tenant changelog must include migration 0074'

$migration = Get-Content -Raw -LiteralPath $MigrationPath
foreach ($table in @('notification_automation_setting', 'employee_celebration_preference', 'automated_notification_occurrence')) {
    Assert-True ($migration -match ('createTable tableName="' + [regex]::Escape($table) + '"')) "Migration is missing $table"
}
Assert-True ($migration -match 'share_birthday[\s\S]*?defaultValueBoolean="false"') 'Birthday sharing must default to false'
Assert-True ($migration -match 'share_work_anniversary[\s\S]*?defaultValueBoolean="false"') 'Anniversary sharing must default to false'
Assert-True ($migration -match 'tenant_id,event_type,employee_id,event_date,recipient_user_id') 'Occurrence uniqueness must cover tenant, event, employee, date, and recipient'
Assert-True ($migration -match 'fk_automated_notification_occurrence_notification') 'Occurrence must reference the generated notification'
Assert-True ($migration -match 'requires a forward corrective migration instead of rollback') 'Rollback must be forward-only'
Assert-True ($migration -notmatch '(?i)INSERT\s+INTO[\s\S]*?role_permission') 'Phase 1 must not reassign role permissions'
Assert-True ($migration -notmatch '(?i)DELETE\s+FROM[\s\S]*?permission_scope') 'Phase 1 must not delete permission scopes'

Write-Host 'Automated employee notification migration contract passed.' -ForegroundColor Green
```

- [ ] **Step 2: Run the contract and verify the expected failure**

Run:

```powershell
Set-Location D:\work\heliorventures\hrms-database
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\test-automated-employee-notifications.ps1
```

Expected: FAIL with `0074 automated employee notifications migration is missing`.

- [ ] **Step 3: Confirm only the new test file changed**

Run:

```powershell
git status --short
git diff -- scripts/test-automated-employee-notifications.ps1
```

Expected: the new contract is untracked and existing unrelated changes remain unchanged.

- [ ] **Step 4: Review checkpoint without committing**

Inspect the test for accidental live database commands. It must contain no connection string, Liquibase invocation, `INSERT` execution, or tenant schema mutation.

### Task 2: Add the forward-only migration and generated SeaORM entities

**Files:**
- Create: `hrms-database/changelog/migrations/0074_automated_employee_notifications/automated_employee_notifications.xml`
- Modify: `hrms-database/changelog/tenant.changelog-master.xml`
- Generate: `hrms-svc/crates/kabipay-db-entities/src/tenant/d0074_automated_employee_notifications.rs`
- Modify generated export: `hrms-svc/crates/kabipay-db-entities/src/tenant/mod.rs`
- Test: `hrms-database/scripts/test-automated-employee-notifications.ps1`
- Test: `hrms-svc/scripts/test-generate-db-entities-only.ps1`

**Interfaces:**
- Consumes: `${schema}.employee`, `${schema}.user`, `${schema}.notification`, and `kabipay_ops.set_updated_at()`.
- Produces: SeaORM modules `notification_automation_setting`, `employee_celebration_preference`, and `automated_notification_occurrence`.

- [ ] **Step 1: Create the migration with exact columns and constraints**

Define these tables:

```text
notification_automation_setting
  id UUID primary key
  tenant_id UUID not null unique
  birthday_enabled BOOLEAN not null default true
  work_anniversary_enabled BOOLEAN not null default true
  company_sharing_enabled BOOLEAN not null default true
  delivery_local_time TIME not null default 09:00:00
  birthday_title_template VARCHAR(500) not null default Happy birthday, {employee_name}!
  birthday_message_template TEXT not null default Wishing {employee_name} a wonderful birthday.
  anniversary_title_template VARCHAR(500) not null default Work anniversary: {employee_name}
  anniversary_message_template TEXT not null default Celebrating {employee_name}'s {service_years}-year work anniversary.
  updated_by UUID null references user(id) on delete set null
  created_at TIMESTAMPTZ not null default NOW()
  updated_at TIMESTAMPTZ not null default NOW()

employee_celebration_preference
  id UUID primary key
  tenant_id UUID not null
  employee_id UUID not null references employee(id) on delete cascade
  share_birthday BOOLEAN not null default false
  share_work_anniversary BOOLEAN not null default false
  created_at TIMESTAMPTZ not null default NOW()
  updated_at TIMESTAMPTZ not null default NOW()
  unique (tenant_id, employee_id)

automated_notification_occurrence
  id UUID primary key
  tenant_id UUID not null
  event_type VARCHAR(50) not null with check in EMPLOYEE_BIRTHDAY, EMPLOYEE_WORK_ANNIVERSARY
  employee_id UUID not null references employee(id) on delete cascade
  event_date DATE not null
  recipient_user_id UUID not null references user(id) on delete cascade
  notification_id UUID not null references notification(id) on delete cascade
  created_at TIMESTAMPTZ not null default NOW()
  unique (tenant_id, event_type, employee_id, event_date, recipient_user_id)
```

Add tenant/date and recipient/date indexes. Add updated-at triggers only to the two mutable settings tables. The rollback block must raise the forward-corrective-migration exception and must not drop production data.

- [ ] **Step 2: Include migration `0074` after `0073`**

Add exactly:

```xml
<include file="migrations/0074_automated_employee_notifications/automated_employee_notifications.xml" relativeToChangelogFile="true"/>
```

- [ ] **Step 3: Run the database contract**

Run:

```powershell
Set-Location D:\work\heliorventures\hrms-database
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\test-automated-employee-notifications.ps1
```

Expected: PASS without connecting to PostgreSQL.

- [ ] **Step 4: Generate only the new entity module**

Run:

```powershell
Set-Location D:\work\heliorventures
py -3 .\hrms-svc\scripts\generate_db_entities.py --only 0074_automated_employee_notifications
```

Expected: one new `d0074_automated_employee_notifications.rs` file and one sorted module export; existing generated modules remain byte-for-byte unchanged.

- [ ] **Step 5: Verify generator and diff integrity**

Run:

```powershell
Set-Location D:\work\heliorventures\hrms-svc
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\test-generate-db-entities-only.ps1
git diff --check
```

Expected: generator test PASS and no whitespace errors. Do not commit.

### Task 3: Establish notification-domain library and pure event rules

**Files:**
- Create: `hrms-svc/crates/kabipay-notification/src/lib.rs`
- Modify: `hrms-svc/crates/kabipay-notification/src/main.rs`
- Create: `hrms-svc/crates/kabipay-notification/src/services/automation_settings.rs`
- Create: `hrms-svc/crates/kabipay-notification/src/services/automated_events.rs`
- Modify: `hrms-svc/crates/kabipay-notification/src/services/mod.rs`
- Modify: `hrms-svc/crates/kabipay-notification/src/services/notification_preference.rs`

**Interfaces:**
- Consumes: generated `d0074_automated_employee_notifications` entities and existing notification/employee/user entities.
- Produces: `AutomationSettings`, `CelebrationPreferences`, `CelebrationEventKind`, `CelebrationSweepResult`, `is_event_due`, `render_event_message`, `load_automation_settings`, `load_celebration_preferences`, `save_automation_settings`, `save_celebration_preferences`, and `process_due_celebrations`.

- [ ] **Step 1: Add failing tests for calendar and template rules**

Tests must assert:

```rust
#[test]
fn observes_february_29_birthdays_on_february_28_in_non_leap_years() {
    let birth = chrono::NaiveDate::from_ymd_opt(2000, 2, 29).unwrap();
    let observed = chrono::NaiveDate::from_ymd_opt(2026, 2, 28).unwrap();
    assert!(is_event_due(CelebrationEventKind::Birthday, birth, observed));
}

#[test]
fn anniversary_requires_one_completed_year() {
    let joined = chrono::NaiveDate::from_ymd_opt(2026, 9, 8).unwrap();
    let today = chrono::NaiveDate::from_ymd_opt(2026, 9, 8).unwrap();
    assert!(!is_event_due(CelebrationEventKind::WorkAnniversary, joined, today));
}

#[test]
fn birthday_template_rejects_age_and_birth_year_tokens() {
    assert!(validate_template("Happy {employee_name}", CelebrationEventKind::Birthday).is_ok());
    assert!(validate_template("Age {age}", CelebrationEventKind::Birthday).is_err());
    assert!(validate_template("Born {birth_year}", CelebrationEventKind::Birthday).is_err());
}
```

- [ ] **Step 2: Run the focused tests and verify failure**

Run:

```powershell
Set-Location D:\work\heliorventures\hrms-svc
cargo test -p kabipay-notification automated_events --lib
```

Expected: FAIL because the library and functions do not exist.

- [ ] **Step 3: Add the library boundary without duplicating modules**

`src/lib.rs` exports `resolvers` and `services`. `src/main.rs` removes local `mod` declarations and imports `kabipay_notification::resolvers::{MutationRoot, QueryRoot}`. Existing schema behavior and port `4028` remain unchanged.

- [ ] **Step 4: Implement pure event rules and safe defaults**

Use these public signatures:

```rust
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum CelebrationEventKind { Birthday, WorkAnniversary }

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct CelebrationMessage { pub notification_type: &'static str, pub title: String, pub message: String }

pub fn is_event_due(kind: CelebrationEventKind, source_date: NaiveDate, business_date: NaiveDate) -> bool;
pub fn completed_service_years(joined: NaiveDate, business_date: NaiveDate) -> Option<u32>;
pub fn validate_template(template: &str, kind: CelebrationEventKind) -> KabiPayResult<()>;
pub fn render_event_message(kind: CelebrationEventKind, employee_name: &str, service_years: Option<u32>, title_template: &str, message_template: &str) -> KabiPayResult<CelebrationMessage>;
```

Trim employee display names, enforce title length `1..=500`, enforce message length `1..=4000`, allow only `{employee_name}` and event-appropriate `{service_years}`, and HTML-escape is unnecessary because React renders strings as text.

- [ ] **Step 5: Add the `celebration` preference topic without changing existing mappings**

Append `celebration` to `ALLOWED_MUTED_TOPICS`. Map only `EMPLOYEE_BIRTHDAY` and `EMPLOYEE_WORK_ANNIVERSARY` to it before the existing fallback to `other`. Retain all current leave, expense, travel, tax, HR, broadcast, and other behavior.

- [ ] **Step 6: Run focused library regressions**

Run:

```powershell
cargo test -p kabipay-notification automated_events --lib
cargo test -p kabipay-notification notification_preference --lib
```

Expected: all focused tests PASS. Do not commit.

### Task 4: Implement settings, consent, and idempotent notification generation

**Files:**
- Modify: `hrms-svc/crates/kabipay-notification/src/services/automation_settings.rs`
- Modify: `hrms-svc/crates/kabipay-notification/src/services/automated_events.rs`
- Test in: the same two service modules

**Interfaces:**
- Consumes: `AutomationSettings`, `CelebrationPreferences`, `CelebrationEventKind`, tenant DB, tenant-local date/time.
- Produces:

```rust
pub async fn load_automation_settings(db: &DatabaseConnection, tenant_id: Uuid) -> KabiPayResult<AutomationSettings>;
pub async fn save_automation_settings(db: &DatabaseConnection, tenant_id: Uuid, actor_user_id: Uuid, input: SaveAutomationSettings) -> KabiPayResult<AutomationSettings>;
pub async fn load_celebration_preferences(db: &DatabaseConnection, tenant_id: Uuid, employee_id: Uuid) -> KabiPayResult<CelebrationPreferences>;
pub async fn save_celebration_preferences(db: &DatabaseConnection, tenant_id: Uuid, employee_id: Uuid, input: CelebrationPreferences) -> KabiPayResult<CelebrationPreferences>;
pub async fn process_due_celebrations(db: &DatabaseConnection, tenant_id: Uuid, business_date: NaiveDate, business_time: NaiveTime) -> KabiPayResult<CelebrationSweepResult>;
```

- [ ] **Step 1: Add failing service tests**

Cover defaults when no settings row exists, template validation before write, tenant-scoped updates, self-consent defaults, private recipients, company recipients only with both consent flags, inactive/missing-user exclusion, delivery-time gating, duplicate occurrence conflict, and audit payload exclusion of birth date/message fields.

- [ ] **Step 2: Implement settings and consent persistence**

Use tenant filters on every query. Upsert settings under `(tenant_id)` and consent under `(tenant_id, employee_id)`. Defaults are exactly the migration defaults. Record audit actions `NOTIFICATION_AUTOMATION_UPDATED` and `CELEBRATION_CONSENT_UPDATED` with boolean/configuration metadata only.

- [ ] **Step 3: Implement recipient resolution**

Select only `employee.status = 'ACTIVE'` rows with active linked users. For private delivery, include employee user and active reporting-manager user, de-duplicated. For company delivery, select active users whose current role/permission join grants `notification:read`; never infer from role names.

- [ ] **Step 4: Implement one transaction per event recipient**

Within the transaction, insert each occurrence with:

```sql
INSERT INTO automated_notification_occurrence
    (id, tenant_id, event_type, employee_id, event_date, recipient_user_id, notification_id, created_at)
VALUES
    ($1, $2, $3, $4, $5, $6, $7, NOW())
ON CONFLICT (tenant_id, event_type, employee_id, event_date, recipient_user_id) DO NOTHING
RETURNING id
```

Because `notification_id` is required, allocate both UUIDs before insertion and use a separate
transaction for each recipient. Insert the notification first, then insert the occurrence in that
same transaction. If the occurrence conflicts, roll back that recipient transaction so its newly
inserted notification is also removed, then count `skipped_duplicate`. A duplicate for one recipient
must not roll back notifications created for other recipients. Never delete or rewrite an existing
occurrence.

- [ ] **Step 5: Return and log safe counts**

`CelebrationSweepResult` contains `eligible_events`, `notifications_created`, `duplicates_skipped`, and `before_delivery_time`. It contains no employee names, dates of birth, or message bodies.

- [ ] **Step 6: Run focused service tests**

Run:

```powershell
cargo test -p kabipay-notification automation_settings --lib
cargo test -p kabipay-notification automated_events --lib
```

Expected: all focused tests PASS. Do not commit.

### Task 5: Expose secure GraphQL settings and self-consent operations

**Files:**
- Modify: `hrms-svc/crates/kabipay-notification/src/resolvers/types.rs`
- Modify: `hrms-svc/crates/kabipay-notification/src/resolvers/query.rs`
- Modify: `hrms-svc/crates/kabipay-notification/src/resolvers/mutation.rs`

**Interfaces:**
- Consumes: Phase 1 settings services and existing `require_notification_read`/manage-scope conventions.
- Produces GraphQL fields:

```graphql
type NotificationAutomationSettings {
  birthdayEnabled: Boolean!
  workAnniversaryEnabled: Boolean!
  companySharingEnabled: Boolean!
  deliveryLocalTime: NaiveTime!
  birthdayTitleTemplate: String!
  birthdayMessageTemplate: String!
  anniversaryTitleTemplate: String!
  anniversaryMessageTemplate: String!
}

type CelebrationPreferences {
  shareBirthday: Boolean!
  shareWorkAnniversary: Boolean!
}

extend type Query {
  notificationAutomationSettings: NotificationAutomationSettings!
  myCelebrationPreferences: CelebrationPreferences!
}

extend type Mutation {
  saveNotificationAutomationSettings(input: SaveNotificationAutomationSettingsInput!): NotificationAutomationSettings!
  updateMyCelebrationPreferences(input: UpdateMyCelebrationPreferencesInput!): CelebrationPreferences!
}
```

- [ ] **Step 1: Add authorization-first failing tests**

Assert settings query/mutation deny missing permission and non-`ALL` manage scopes before database access. Assert self query/mutation deny missing `notification:read`, require `claims.employee_id`, and provide no employee ID argument.

- [ ] **Step 2: Add GraphQL DTOs and validated inputs**

Inputs use booleans, `NaiveTime`, and bounded strings. Validation occurs before opening a transaction. Returned types never include `updated_by`, employee ID, or audit state.

- [ ] **Step 3: Add queries and mutations**

Settings operations require `notification:manage=ALL`. Self operations require existing notification read access and pass only `claims.employee_id` to the service. Do not change signatures or authorization behavior of existing notification preference, announcement, direct notification, read-state, or admin-history operations.

- [ ] **Step 4: Run resolver regression tests**

Run:

```powershell
cargo test -p kabipay-notification resolver --lib
cargo test -p kabipay-notification notification --lib
```

Expected: Phase 1 authorization tests and existing notification tests PASS. Do not commit.

### Task 6: Wire the tenant-aware worker without changing current jobs

**Files:**
- Modify: `hrms-svc/crates/kabipay-outbox-worker/Cargo.toml`
- Modify: `hrms-svc/crates/kabipay-outbox-worker/src/main.rs`

**Interfaces:**
- Consumes: `kabipay_notification::services::automated_events::process_due_celebrations` and `TenantBusinessClock::{business_date, local_time}`.
- Produces: one idempotent Phase 1 sweep per active tenant per worker poll.

- [ ] **Step 1: Add the path dependency**

Add:

```toml
kabipay-notification = { path = "../kabipay-notification" }
```

- [ ] **Step 2: Use one UTC instant for all tenant-local calculations in a sweep**

Inside the resolved tenant branch:

```rust
let now = chrono::Utc::now();
let business_date = clock.business_date(now);
let business_time = clock.local_time(now);
match process_due_celebrations(&tdb, tid, business_date, business_time).await {
    Ok(result) if result.notifications_created > 0 => tracing::info!(
        %tid,
        business_date = %business_date,
        created = result.notifications_created,
        duplicates = result.duplicates_skipped,
        "automated employee notifications generated"
    ),
    Ok(_) => {}
    Err(error) => tracing::error!(%tid, code = error.code(), "automated employee notification sweep failed"),
}
```

Call this alongside, not instead of, due offboarding, expired uploads, private-file cleanup, and tenant outbox delivery. Keep the existing sleep interval and retry behavior unchanged.

- [ ] **Step 3: Compile only affected packages**

Run:

```powershell
Set-Location D:\work\heliorventures\hrms-svc
cargo check -p kabipay-notification
cargo check -p kabipay-outbox-worker
```

Expected: both packages compile; existing worker functions remain referenced. Do not commit.

### Task 7: Add gateway and authored GraphQL contracts

**Files:**
- Modify: `hrms-gateway/src/schemaContract.ts`
- Modify: `hrms-gateway/src/schemaContract.test.ts`
- Modify: `hrms-ui/src/api/schema-extensions/hrms-notification.graphql`
- Modify: `hrms-ui/src/api/documents/clientOperations.graphql`
- Generate: `hrms-ui/src/api/graphql/`

**Interfaces:**
- Consumes: Phase 1 notification GraphQL schema.
- Produces: generated documents `NotificationAutomationSettingsDocument`, `SaveNotificationAutomationSettingsDocument`, `MyCelebrationPreferencesDocument`, and `UpdateMyCelebrationPreferencesDocument`.

- [ ] **Step 1: Make the gateway contract test fail**

Add the two queries and two mutations to `REQUIRED_CLIENT_FIELDS`, update the complete-schema fixture, and assert an older notification schema reports all four missing fields.

- [ ] **Step 2: Run the focused gateway test**

Run:

```powershell
Set-Location D:\work\heliorventures\hrms-gateway
npm test -- --test-name-pattern="required client fields"
```

Expected: FAIL until the fixture and contract are updated together, then PASS.

- [ ] **Step 3: Add exact schema-extension types and operations**

Add the GraphQL types/inputs from Task 5. Add four named operations selecting every field required by the two cards. Keep existing operation names unchanged.

- [ ] **Step 4: Regenerate typed GraphQL artifacts**

With the local gateway schema available at the configured schema URL, run:

```powershell
Set-Location D:\work\heliorventures\hrms-ui
npm run codegen
```

Expected: generated Phase 1 document/type exports with no duplicate operation names. If the gateway is unavailable, stop this step and report the runtime dependency; do not hand-edit generated files.

- [ ] **Step 5: Run gateway build and duplicate-operation scan**

Run:

```powershell
Set-Location D:\work\heliorventures\hrms-gateway
npm run build
Set-Location D:\work\heliorventures\hrms-ui
rg -n "query (NotificationAutomationSettings|MyCelebrationPreferences)|mutation (SaveNotificationAutomationSettings|UpdateMyCelebrationPreferences)" src
```

Expected: gateway build PASS and one authored definition per operation. Do not commit.

### Task 8: Add isolated employee celebration preferences

**Files:**
- Create: `hrms-ui/src/modules/notifications/celebrationPreferences.ts`
- Create: `hrms-ui/src/modules/notifications/CelebrationPreferencesCard.tsx`
- Create: `hrms-ui/src/modules/notifications/CelebrationPreferencesCard.test.tsx`
- Modify: `hrms-ui/src/modules/profile/components/NotificationsTab.tsx`
- Create: `hrms-ui/src/modules/profile/components/NotificationsTab.test.tsx`

**Interfaces:**
- Consumes: generated self-consent documents.
- Produces: an independently loading card whose failure cannot erase or disable the existing notification-preference form.

- [ ] **Step 1: Write failing component tests**

Test that both consent flags default from the query, unchecked is preserved, save sends only two booleans, no employee ID is sent, success is announced with `role="status"`, error is actionable, and a consent query failure leaves the existing mute/save controls usable.

- [ ] **Step 2: Implement the adapter and card**

Expose:

```ts
export interface CelebrationPreferencesState {
  shareBirthday: boolean;
  shareWorkAnniversary: boolean;
}

export async function loadCelebrationPreferences(client: GraphQLClient): Promise<CelebrationPreferencesState>;
export async function saveCelebrationPreferences(client: GraphQLClient, value: CelebrationPreferencesState): Promise<CelebrationPreferencesState>;
```

The card copy states that company sharing is opt-in, private reminders may still go to the employee and reporting manager, and birth year/age are never shared.

- [ ] **Step 3: Compose without merging failure state**

Add `CelebrationPreferencesCard` below the existing notification preference card. Add `{ id: 'celebration', label: 'Celebrations', hint: 'Birthday and work-anniversary alerts' }` to `TOPICS`. Do not rewrite the existing load/save behavior.

- [ ] **Step 4: Run focused UI tests**

Run:

```powershell
Set-Location D:\work\heliorventures\hrms-ui
npx vitest run src/modules/notifications/CelebrationPreferencesCard.test.tsx src/modules/profile/components/NotificationsTab.test.tsx
```

Expected: focused tests PASS. Do not commit.

### Task 9: Add isolated Admin/HR automation settings

**Files:**
- Create: `hrms-ui/src/modules/admin/notificationAutomation.ts`
- Create: `hrms-ui/src/modules/admin/components/NotificationAutomationSettingsCard.tsx`
- Create: `hrms-ui/src/modules/admin/components/NotificationAutomationSettingsCard.test.tsx`
- Modify: `hrms-ui/src/modules/admin/AdminNotificationsPage.tsx`
- Modify: `hrms-ui/src/modules/admin/AdminNotificationsPage.test.tsx`

**Interfaces:**
- Consumes: generated Admin settings documents and existing Admin Notifications permission gate.
- Produces: compact settings UI isolated from announcement and direct-notification state.

- [ ] **Step 1: Write failing validation and containment tests**

Cover both enable toggles, company-sharing toggle, local delivery time, four templates, unsupported token rejection, 500-character title limit, 4,000-character message limit, save success, refresh-after-save failure wording, and proof that a settings query failure does not hide or disable existing announcement/direct-notification controls.

- [ ] **Step 2: Implement validation adapter**

Export `validateNotificationAutomationSettings` returning field-keyed errors. Allow `{employee_name}` everywhere and `{service_years}` only in anniversary templates. Reject all other `{token}` forms before the mutation.

- [ ] **Step 3: Implement and compose the settings card**

Render one compact card above existing composers. Use visible labels, native time input, accessible inline errors, `role="status"` success, `role="alert"` failure, and retain loaded values when a save or refresh fails. Do not add new page-level scrolling or duplicate the existing page error state.

- [ ] **Step 4: Run focused UI regressions**

Run:

```powershell
npx vitest run src/modules/admin/components/NotificationAutomationSettingsCard.test.tsx src/modules/admin/AdminNotificationsPage.test.tsx
```

Expected: new settings tests and all existing Admin Notifications tests PASS. Do not commit.

### Task 10: Document and verify Phase 1 without live mutation

**Files:**
- Modify: `hrms-documentation/docs/module-completion-status.md`
- Verify all Phase 1 files in `hrms-database`, `hrms-svc`, `hrms-gateway`, and `hrms-ui`

**Interfaces:**
- Consumes: completed Phase 1 implementation.
- Produces: reviewable diffs and truthful verification evidence, with live migration/deployment/browser gaps explicitly recorded.

- [ ] **Step 1: Update completion documentation**

Record implemented behavior, permission contract, opt-in privacy, leap-day rule, idempotency key, focused test commands/results, and remaining live migration/worker/browser checks. Do not mark deployment complete.

- [ ] **Step 2: Run focused database and Rust verification**

Run:

```powershell
Set-Location D:\work\heliorventures\hrms-database
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\test-automated-employee-notifications.ps1
Set-Location D:\work\heliorventures\hrms-svc
cargo test -p kabipay-notification --lib
cargo check -p kabipay-outbox-worker
```

Expected: all focused checks PASS.

- [ ] **Step 3: Run focused gateway and UI verification**

Run:

```powershell
Set-Location D:\work\heliorventures\hrms-gateway
npm test
npm run build
Set-Location D:\work\heliorventures\hrms-ui
npx vitest run src/modules/notifications/CelebrationPreferencesCard.test.tsx src/modules/profile/components/NotificationsTab.test.tsx src/modules/admin/components/NotificationAutomationSettingsCard.test.tsx src/modules/admin/AdminNotificationsPage.test.tsx src/modules/notifications/useNotificationBoard.test.tsx src/components/layout/NotificationDropdown.test.tsx
```

Expected: gateway suite/build and focused UI notification regressions PASS. The UI production build and full UI suite are not run without additional approval.

- [ ] **Step 4: Check all repository diffs without touching unrelated work**

Run:

```powershell
git -C D:\work\heliorventures\hrms-database diff --check
git -C D:\work\heliorventures\hrms-svc diff --check
git -C D:\work\heliorventures\hrms-gateway diff --check
git -C D:\work\heliorventures\hrms-ui diff --check
git -C D:\work\heliorventures\hrms-documentation diff --check
git -C D:\work\heliorventures\hrms-database status --short
git -C D:\work\heliorventures\hrms-svc status --short
git -C D:\work\heliorventures\hrms-gateway status --short
git -C D:\work\heliorventures\hrms-ui status --short
git -C D:\work\heliorventures\hrms-documentation status --short
```

Expected: no whitespace errors; Phase 1 files are distinguishable from pre-existing attendance, leave, seed, and deployment changes.

- [ ] **Step 5: Review checkpoint without committing or deploying**

Report focused test evidence and the remaining gaps: migration not applied to any tenant, worker not run against live tenant data, no signed-in browser acceptance, no deployment, and no broad suite unless separately approved.
