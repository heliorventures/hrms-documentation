# Asset Management Completion Implementation Plan

> **For agentic workers:** Execute this plan inline, task by task. Steps use checkbox (`- [ ]`) syntax for tracking. Do not dispatch subagents for this workspace.

**Goal:** Complete the tenant-scoped asset category, inventory, assignment, return, and history lifecycle across Liquibase, Rust GraphQL services, generated client operations, React UI, and completion documentation.

**Architecture:** Extend the existing `kabipay-assets` subgraph and `/workplace/assets` route. Add non-destructive lifecycle fields and database constraints, expose compatible paged GraphQL operations, enforce RBAC and tenant isolation in Rust, and split the React workspace into focused typed components.

**Tech Stack:** PostgreSQL/Liquibase, SeaORM, Rust/async-graphql, GraphQL Code Generator, React 18, TypeScript, Vitest.

## Global Constraints

- Do not run unit tests; record focused commands for the user to run.
- Do not run automatic commits or destructive Git commands.
- Preserve unrelated dirty work in every repository.
- Never accept a tenant ID from GraphQL input.
- Retire categories/assets; never hard-delete referenced lifecycle data.
- Do not expose raw SQL/database errors, PII, asset values, or condition/remarks in logs.
- Do not mark the module Complete without runtime browser, migration, authorization, and database evidence.

---

### Task 1: Tenant migration and SeaORM entity contract

**Files:**

- Create: `hrms-database/changelog/migrations/0057_asset_management_lifecycle/asset_management_lifecycle.xml`
- Modify: `hrms-database/changelog/tenant.changelog-master.xml`
- Modify: `hrms-svc/crates/kabipay-db-entities/src/tenant/d0022_assets.rs`

**Interfaces:**

- Produces category fields `is_active`, `retired_at`, `retired_by`.
- Produces asset fields `retired_at`, `retired_by`.
- Produces case-insensitive asset tag/serial uniqueness and one-return-per-allocation integrity.

- [ ] **Step 1: Add migration assertions to the static review checklist**

```text
asset_category lifecycle columns exist with safe defaults
asset lifecycle audit columns exist
asset status is restricted to AVAILABLE, ASSIGNED, RETIRED
asset tag and serial number are tenant-scoped and case-insensitively unique
asset_return_log permits one row per allocation
all rollback statements remove only 0057 objects
```

- [ ] **Step 2: Create migration 0057**

Use `addColumn` for lifecycle columns, normalize existing status/text rows, add foreign keys to tenant `user(id)`, and install these SQL invariants:

```sql
ALTER TABLE "${schema}".asset
  ADD CONSTRAINT chk_asset_status
  CHECK (status IN ('AVAILABLE', 'ASSIGNED', 'RETIRED'));

CREATE UNIQUE INDEX uq_asset_tenant_asset_tag_ci
ON "${schema}".asset (tenant_id, UPPER(asset_tag))
WHERE asset_tag IS NOT NULL AND BTRIM(asset_tag) <> '';

CREATE UNIQUE INDEX uq_asset_tenant_serial_number_ci
ON "${schema}".asset (tenant_id, UPPER(serial_number))
WHERE serial_number IS NOT NULL AND BTRIM(serial_number) <> '';

CREATE UNIQUE INDEX uq_asset_return_log_allocation
ON "${schema}".asset_return_log (tenant_id, asset_allocation_id);
```

- [ ] **Step 3: Include migration 0057 in the tenant master**

Add exactly:

```xml
<include file="migrations/0057_asset_management_lifecycle/asset_management_lifecycle.xml" relativeToChangelogFile="true"/>
```

- [ ] **Step 4: Extend SeaORM models**

Add fields matching database nullability and types:

```rust
pub is_active: bool,
pub retired_at: Option<DateTimeUtc>,
pub retired_by: Option<Uuid>,
```

- [ ] **Step 5: Perform permitted static verification**

Run XML parsing and `git diff --check`; do not execute Liquibase against a tenant database.

---

### Task 2: Asset domain types, normalization, and page contracts

**Files:**

- Modify: `hrms-svc/crates/kabipay-assets/src/resolvers/types.rs`
- Create: `hrms-svc/crates/kabipay-assets/src/services/asset_rules.rs`
- Modify: `hrms-svc/crates/kabipay-assets/src/services/mod.rs`

**Interfaces:**

- Produces `UpsertAssetCategoryInput`, `UpsertAssetInput`, `AssetCategoryPage`, `AssetInventoryPage`, and `AssetAllocationPage`.
- Produces normalization functions used by mutation services.

- [ ] **Step 1: Write Rust rule tests before production rules**

Add tests asserting:

```rust
assert_eq!(required_text("  Laptop  ", "name").unwrap(), "Laptop");
assert_eq!(category_code(" lap-top ").unwrap(), "LAP-TOP");
assert_eq!(optional_identifier(Some(" tag-1 ".into())), Some("tag-1".into()));
assert!(required_text("   ", "name").is_err());
assert!(validate_purchase_value(Some(Decimal::new(-1, 0))).is_err());
```

User-run red command:

```powershell
cargo test -p kabipay-assets asset_rules
```

- [ ] **Step 2: Implement normalization and validation rules**

Use trimmed required text, uppercase category codes, blank-to-null optional identifiers, and non-negative purchase values. Return `KabiPayError::Validation` with stable field-specific messages.

- [ ] **Step 3: Extend DTOs and input objects**

Category DTOs include lifecycle fields. Asset DTOs include category labels, location ID, and lifecycle fields. Allocation DTOs include employee labels and optional return details while retaining purchase-value masking.

- [ ] **Step 4: Add page objects**

Each page type has:

```rust
pub rows: Vec<T>,
pub page_info: PageInfo,
```

Use `kabipay_common::{PageInfo, PageInput}` rather than a parallel pagination model.

---

### Task 3: Tenant-scoped paged query services

**Files:**

- Modify: `hrms-svc/crates/kabipay-assets/src/services/asset_service.rs`
- Modify: `hrms-svc/crates/kabipay-assets/src/resolvers/query.rs`

**Interfaces:**

- Produces `list_category_page`, `list_asset_page`, and `list_allocation_page`.
- Retains `asset_categories`, `assets`, and `asset_assignments` for compatibility.

- [ ] **Step 1: Write query-construction tests before query implementation**

Tests cover normalized search terms, status allowlists, page clamping, and self-view target selection. User-run command:

```powershell
cargo test -p kabipay-assets query_
```

- [ ] **Step 2: Implement category paging**

Filter every query by tenant ID, optionally filter active categories, search name/code case-insensitively, count before page limiting, and order by normalized name then ID.

- [ ] **Step 3: Implement asset paging**

Join category labels without dropping historical retired categories. Filter by category/status/search and order by name then ID.

- [ ] **Step 4: Implement allocation paging**

Join assets, employees, and optional return logs. Search asset/employee labels, filter status and employee, and preserve self-view purchase-value masking.

- [ ] **Step 5: Add paged resolvers with authorization**

Tenant-wide pages require `assets:read` or `assets:manage`. A non-manager allocation query must require `assets:self`, resolve the authenticated employee, and override any cross-employee request.

---

### Task 4: Category, asset, assignment, return, and retirement transactions

**Files:**

- Modify: `hrms-svc/crates/kabipay-assets/src/services/asset_service.rs`
- Modify: `hrms-svc/crates/kabipay-assets/src/resolvers/mutation.rs`

**Interfaces:**

- Produces `upsert_asset_category`, `retire_asset_category`, `upsert_asset`, and `retire_asset`.
- Hardens existing `assign_asset` and `return_asset` transaction behavior.

- [ ] **Step 1: Write lifecycle tests before mutation implementation**

Cover these behaviors individually:

```text
retired category cannot be updated
category with non-retired assets cannot be retired
assigned asset cannot be edited or retired
retired asset cannot be assigned
expected return cannot precede allocation date
return cannot precede allocation date
duplicate assignment maps to Conflict
duplicate return maps to Conflict
```

User-run command:

```powershell
cargo test -p kabipay-assets lifecycle_
```

- [ ] **Step 2: Implement category lifecycle mutations**

Create/update active rows with normalized name/code. Retirement counts non-retired tenant assets and records `is_active=false`, `retired_at`, and `retired_by` atomically.

- [ ] **Step 3: Implement asset lifecycle mutations**

Create assets as `AVAILABLE`. Update only `AVAILABLE` assets under active tenant categories. Retire only assets with no active tenant allocation and record audit fields.

- [ ] **Step 4: Harden assignment concurrency**

Lock the tenant asset row for update, require `AVAILABLE`, validate an active employee, insert the allocation, and set `ASSIGNED` in one transaction. Translate the active-allocation unique violation to `Conflict`.

- [ ] **Step 5: Harden return concurrency**

Lock the tenant allocation row for update, require `ACTIVE`, insert one return log, set allocation `RETURNED`, and set asset `AVAILABLE` in one transaction. Translate the return-log unique violation to `Conflict`.

- [ ] **Step 6: Expose lifecycle mutations**

Every new mutation requires `assets:manage`, takes no tenant ID, and maps UUID parsing and service errors through the established GraphQL error contract.

---

### Task 5: GraphQL client contract and generation checkpoint

**Files:**

- Create: `hrms-ui/src/api/schema-extensions/hrms-assets.graphql`
- Modify: `hrms-ui/codegen.ts`
- Create: `hrms-ui/src/api/documents/assets.graphql`
- Generated by user: `hrms-ui/src/api/graphql/*`

**Interfaces:**

- Produces generated documents and types for all Asset Management pages and mutations.

- [ ] **Step 1: Add the assets schema extension**

Mirror the Rust GraphQL names and nullability for page objects, lifecycle fields, inputs, paged queries, and mutations. Do not redefine existing scalar or base types.

- [ ] **Step 2: Register the extension in `codegen.ts`**

Add `hrms-assets.graphql` to the schema array after the other HRMS extensions.

- [ ] **Step 3: Add named client operations**

Create operations:

```text
AssetCategoriesPage
AssetInventoryPage
AssetAllocationsPage
AssetsEmployeeOptions
UpsertAssetCategory
RetireAssetCategory
UpsertAsset
RetireAsset
AssignAssetToEmployee
ReturnEmployeeAsset
```

- [ ] **Step 4: Hand off code generation**

User runs, with the gateway/schema source available:

```powershell
npm run codegen
```

Do not hand-edit generated files. Continue React integration only after generated document/type names match the operations.

---

### Task 6: React Asset Management workspace

**Files:**

- Modify: `hrms-ui/src/modules/workplace/AssetsPage.tsx`
- Create: `hrms-ui/src/modules/workplace/assets/assetTypes.ts`
- Create: `hrms-ui/src/modules/workplace/assets/assetValidation.ts`
- Create: `hrms-ui/src/modules/workplace/assets/useAssetsWorkspace.ts`
- Create: `hrms-ui/src/modules/workplace/assets/AssetInventorySection.tsx`
- Create: `hrms-ui/src/modules/workplace/assets/AssetCategorySection.tsx`
- Create: `hrms-ui/src/modules/workplace/assets/AssetAllocationsSection.tsx`
- Create: `hrms-ui/src/modules/workplace/assets/AssetHistorySection.tsx`
- Create: `hrms-ui/src/modules/workplace/assets/AssetCategoryModal.tsx`
- Create: `hrms-ui/src/modules/workplace/assets/AssetModal.tsx`
- Create: `hrms-ui/src/modules/workplace/assets/AssetAssignmentModal.tsx`
- Create: `hrms-ui/src/modules/workplace/assets/AssetReturnModal.tsx`
- Create: `hrms-ui/src/modules/workplace/assets/AssetRetireDialog.tsx`
- Test: `hrms-ui/src/modules/workplace/assets/assetValidation.test.ts`

**Interfaces:**

- Consumes generated Asset Management GraphQL documents.
- Produces a role-aware workspace for `assets:manage`, `assets:read`, and `assets:self`.

- [x] **Step 1: Write validation tests before UI validation code**

Tests assert required category/asset labels, non-negative purchase value, return/allocation date ordering, and whitespace normalization. User-run command:

```powershell
npm test -- src/modules/workplace/assets/assetValidation.test.ts
```

- [x] **Step 2: Implement pure validation helpers**

Return field-keyed validation messages so each modal can render accessible inline feedback without duplicating rules.

- [x] **Step 3: Implement `useAssetsWorkspace`**

Maintain independent page/filter state for categories, inventory, active allocations, and history. Start independent initial requests concurrently, retain previous rows on refresh errors, prevent duplicate mutation submission, and refresh only affected datasets.

- [x] **Step 4: Implement category and inventory sections**

Use labeled search/filter controls, semantic tables, page navigation, empty-state creation actions, and manager-only edit/retire actions. Show category labels rather than IDs.

- [x] **Step 5: Implement allocation and history sections**

Display employee code/name, asset label/tag/serial, dates, conditions, and status. Managers can initiate returns from active rows; employees see only data returned by their server-restricted self query.

- [x] **Step 6: Implement focused modals/dialogs**

Category and asset modals support create/edit. Assignment modal validates dates. Return modal is the confirmation surface and captures returned date, condition, and remarks. Retirement dialog explains why the action is non-destructive.

- [x] **Step 7: Reduce `AssetsPage.tsx` to route composition**

Remove inline GraphQL and hand-written API result contracts. Compose role-appropriate sections from the hook, keep visible success/error feedback, and do not discard loaded data when one request fails.

- [x] **Step 8: Hand off UI verification commands**

User runs:

```powershell
npm test -- src/modules/workplace/assets/assetValidation.test.ts
npm run lint
npm run build
```

---

### Task 7: Completion register and runtime acceptance evidence

**Files:**

- Modify: `hrms-documentation/docs/module-completion-status.md`
- Modify: `hrms-documentation/kabipay-feature-matrix.csv`
- Modify: `hrms-documentation/STATUS.md`

**Interfaces:**

- Produces an Asset Management-specific QA checklist and removes stale read-only/deferred wording.

- [x] **Step 1: Add the Asset Management acceptance checklist**

Include unchecked browser journeys for manager create/edit/assign/return/history/retire, employee self-view, permission denial, tenant isolation, validation, duplicate conflict handling, and retained-data error states.

- [x] **Step 2: Add runtime evidence fields**

Record explicit Pending entries for tenant Liquibase status, GraphQL traces, database state transitions, role-based browser runs, screenshots/recording, and regression command output.

- [x] **Step 3: Correct stale status wording**

Replace documentation that equates “page present” with implementation and remove the old “assign/return deferred” statement.

- [x] **Step 4: Set the honest status**

After implementation and permitted static checks, mark Asset Management **QA**, not Complete. Runtime verification remains the user's gate.

---

## Final Static Review

- [ ] Confirm every database and service query filters tenant ID.
- [ ] Confirm every mutation enforces `assets:manage` server-side.
- [ ] Confirm self-service ignores/rejects cross-employee IDs.
- [ ] Confirm no hard-delete mutation was introduced.
- [ ] Confirm no inline GraphQL remains in the asset page.
- [ ] Confirm no raw employee ID is the primary UI label.
- [ ] Parse changed XML files.
- [ ] Run `git diff --check` in each changed repository.
- [ ] Do not claim tests, migration application, build, or browser flows passed until the user supplies their output.

---

## Review Remediation (2026-08-18)

### Task 8: Transactional asset lifecycle and authorization

**Files:**

- Modify: `hrms-svc/crates/kabipay-assets/src/services/asset_service.rs`
- Modify: `hrms-svc/crates/kabipay-assets/src/resolvers/mutation.rs`
- Modify: `hrms-svc/crates/kabipay-common/src/error.rs`
- Test: focused asset service/resolver regression source

- [x] Write regression source for edit-versus-assign, edit-versus-retire, category-update-versus-retire, create-versus-category-retire, explicit permission enforcement, and sanitized conflicts. Execution remains a user-run verification step.
- [x] Put category and asset upserts in transactions. Lock category before asset and verify lifecycle state inside the transaction.
- [x] Require explicit `assets:manage` for every asset mutation and explicit `assets:read` or `assets:manage` for tenant-wide reads, without role-name fallback.
- [x] Return stable asset conflict codes while keeping database/internal details server-side.

### Task 9: Safe lifecycle migration

**Files:**

- Preserve: committed `hrms-database/changelog/migrations/0057_asset_management_lifecycle/asset_management_lifecycle.xml` byte-for-byte
- Add: `hrms-database/changelog/migrations/0058_asset_management_integrity/asset_management_integrity.xml`
- Add: migration verification SQL under `hrms-database/tests/`

- [x] Add bounded, actionable preflight failures for tenant-parent mismatches, retired/actively allocated contradictions, and normalized category-code, tag, serial, active-allocation, and return-log duplicates.
- [x] Normalize category codes and reconcile asset status from retirement and active-allocation truth only after preflight validation.
- [x] Keep ambiguous identity data fail-closed with remediation guidance; document that normalization is not data-reversible.

### Task 10: Independent option paging and resilient React interactions

**Files:**

- Modify: asset GraphQL resolver/types/operations and schema extension
- Modify: `hrms-ui/src/modules/workplace/assets/useAssetsWorkspace.ts`
- Modify: asset picker/modals/sections and `src/components/common/Modal.tsx`
- Test: asset hook/component/validation test source

- [x] Add deterministic, server-searchable, paged `ACTIVE` employee options protected by `assets:manage`.
- [x] Maintain category-option paging/search separately from the category management table.
- [x] Add a synchronous keyed in-flight guard and block modal dismissal while saving.
- [x] Move dialog focus inside, trap focus, and restore the opener on close.
- [x] Build date-only defaults from local calendar components.
- [ ] Remove the asset local schema extension after the running gateway exposes the contract; generated client files remain codegen-owned.

### Task 11: Private attachment lifecycle and lazy retrieval

**Files:**

- Modify: employee/company document and notification storage services/resolvers
- Modify: announcement and company-document GraphQL/UI operations
- Remove: unused generic tenant attachment read client/server contract
- Test: authorization, cleanup, replacement, and lazy-download regression source

- [x] Authorize every read through its owning business object; do not allow generic cross-module file reads.
- [x] Add operation-owned staged company uploads and idempotent compensation for failed create/update/link operations.
- [x] Record a durable cleanup tombstone in the same transaction that removes an owning reference and file metadata; retry physical deletion through the shared worker without persisting raw provider errors.
- [x] Lock announcements during update/delete and derive replaced attachment IDs inside that transaction so concurrent replacements cannot orphan intermediate files.
- [x] Sweep expired, unclaimed company-document upload stages through the same durable cleanup queue.
- [x] Archive company documents with their private file intact for audit; permanent delete removes the business record and durably schedules the file for deletion.
- [x] Fetch announcement bytes only on explicit preview/download, not in the announcement list query.
- [x] Keep local and object-store implementation details, storage IDs, keys, paths, and URLs private.

### Task 12: Documentation and user-run verification handoff

- [x] Correct `ACTIVE` employee and category-code uniqueness wording.
- [x] Keep Asset Management in QA until migration, Rust, UI, role, tenant, concurrency, and browser evidence is supplied.
- [x] Run only permitted static checks. Do not run unit tests; provide exact commands for the user.
