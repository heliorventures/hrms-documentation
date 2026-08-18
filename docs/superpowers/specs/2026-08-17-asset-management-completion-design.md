# Asset Management Completion Design

**Date:** 2026-08-17

**Status:** Approved architecture; implementation under review remediation

## Objective

Complete the existing HRMS Asset Management module as a tenant-scoped core asset lifecycle. Managers must be able to maintain asset categories and inventory, allocate and return assets, and inspect allocation history. Employees must be able to view only assets allocated to their own employee record.

The module moves to **QA** only after the implementation is wired across React, GraphQL, Rust, Liquibase, and generated client documents. It moves to **Complete** only after the documented role-based browser journeys and tenant database state are verified at runtime.

## Scope

### Included

- Create, edit, list, search, filter, paginate, and retire asset categories.
- Create, edit, list, search, filter, paginate, and retire assets.
- Allocate an available asset to an active employee.
- Record allocation date, expected return date, and condition at allocation.
- Return an active allocation with confirmation, return date, condition, and remarks.
- Display active allocations and historical returned allocations.
- Display employee code/name and category name rather than raw identifiers.
- Enforce tenant isolation and role permissions in every resolver and service operation.
- Prevent duplicate active allocations, duplicate returns, duplicate asset tags, and duplicate serial numbers.
- Add generated GraphQL operations and focused React components/hooks.
- Add regression test source and an executable manual browser acceptance checklist.

### Excluded

- Procurement and purchase-order workflows.
- Vendor management.
- Accounting depreciation schedules.
- Warranty and maintenance scheduling.
- Asset attachments or photographs.
- Barcode/QR label generation.
- Bulk import/export.

These capabilities require separate product designs and must not be represented as part of this module's completion.

## Chosen Architecture

Extend the existing `kabipay-assets` tenant subgraph and the `/workplace/assets` UI route. The page becomes a role-aware workspace instead of introducing a parallel admin-only route.

- Users with `assets:manage` see Inventory, Categories, Active Allocations, and History, with lifecycle actions.
- Users with `assets:read` see tenant inventory and allocation history without mutations.
- Users with only `assets:self` see their own active and returned allocations.
- All ownership and permission enforcement remains server-side. UI visibility is convenience, not authorization.

Existing list queries remain available for compatibility. New paged queries provide the production UI contract.

## Data Model and Migration

A new tenant Liquibase migration will extend the existing `asset_category`, `asset`, `asset_allocation`, and `asset_return_log` model.

### Asset category

Add:

- `is_active BOOLEAN NOT NULL DEFAULT TRUE`
- `retired_at TIMESTAMPTZ NULL`
- `retired_by UUID NULL`, referencing tenant `user(id)` with `ON DELETE SET NULL`

Category `code` remains unique per tenant. Category names and codes are trimmed. Codes are normalized to uppercase before persistence. A retired category remains queryable for historical display and cannot be selected for a new asset.

A category can be retired only when it has no non-retired assets. A referenced category is never physically deleted.

### Asset

Add:

- `retired_at TIMESTAMPTZ NULL`
- `retired_by UUID NULL`, referencing tenant `user(id)` with `ON DELETE SET NULL`

Supported persisted statuses for this scope are:

- `AVAILABLE`
- `ASSIGNED`
- `RETIRED`

Add a database check constraint for these values. Existing rows are normalized before the check is installed.

Add partial tenant-scoped unique indexes:

- `(tenant_id, UPPER(asset_tag))` where `asset_tag` is non-null and non-blank.
- `(tenant_id, UPPER(serial_number))` where `serial_number` is non-null and non-blank.

Asset tags and serial numbers are trimmed before persistence. Matching is case-insensitive. An asset can be retired only while it has no active allocation. Retired assets remain queryable for history and cannot be allocated.

### Allocation and return integrity

Retain the existing partial unique index allowing only one `ACTIVE` allocation for each tenant/asset pair.

Add a unique index on `(tenant_id, asset_allocation_id)` in `asset_return_log`, ensuring one return record per allocation.

Assignment and return operations lock the affected asset/allocation rows inside their database transaction. Status changes and audit inserts commit atomically.

## GraphQL Contract

### Paged queries

Add stable page objects using the repository's existing `PageInput` and `PageInfo` conventions:

- `assetCategoriesPage(page, search, activeOnly)`
- `assetInventoryPage(page, search, categoryId, status)`
- `assetAllocationsPage(page, search, employeeId, status)`

Search is case-insensitive:

- Categories: name and code.
- Assets: name, asset tag, and serial number.
- Allocations: asset name/tag/serial and employee code/name.

Stable ordering uses a human-readable key followed by `id` as a deterministic tie-breaker.

### Category mutations

- `upsertAssetCategory(input: UpsertAssetCategoryInput!): AssetCategory!`
- `retireAssetCategory(assetCategoryId: ID!): AssetCategory!`

The upsert input contains optional `id`, required `name`, and required `code`. Updating a retired category is rejected.

### Asset mutations

- `upsertAsset(input: UpsertAssetInput!): Asset!`
- `retireAsset(assetId: ID!): Asset!`

The upsert input contains optional `id`, required category ID/name, optional asset tag/serial number/purchase value/purchase date, and optional location ID. Status is controlled by lifecycle operations rather than accepted as arbitrary client input.

### Allocation mutations

Retain:

- `assignAssetToEmployee(input: AssignAssetInput!): AssetAssignment!`
- `returnEmployeeAsset(input: ReturnAssetInput!): AssetAssignment!`

Return input requires allocation ID and returned date. Condition and remarks remain optional. The UI must no longer force these fields to `null` without presenting them.

### Returned fields

Inventory rows include category name/code and lifecycle fields. Allocation rows include employee code/name and optional return details. `purchaseValue` is returned only to users with tenant-wide asset-read permission, preserving the existing self-view masking rule.

## Rust Service Design

The service remains organized into resolver types, query/mutation resolvers, and tenant-scoped service operations.

- Parse and validate GraphQL IDs at the resolver boundary.
- Normalize text and enforce business rules in service functions.
- Apply `assets:manage` to all category and asset mutations and all allocation/return mutations.
- Apply `assets:read` or `assets:manage` to tenant-wide pages.
- Apply `assets:self` with the authenticated user-to-employee link for self allocation pages.
- Never accept tenant ID from GraphQL input.
- Return `Validation`, `NotFound`, `Conflict`, or `Forbidden` errors with actionable messages; do not expose raw database errors.
- Map unique constraint failures to stable conflicts for category code, asset tag, serial number, active allocation, and duplicate return.
- Do not log employee PII, asset values, or free-text condition/remarks.

Queries joining employees, categories, assets, allocations, and returns remain tenant-filtered at every relation boundary.

Lifecycle validation and writes execute in transactions with a consistent category-before-asset lock order. Conditional lifecycle updates verify their affected-row count so concurrent assignment or retirement cannot commit a stale edit.

## React Design

`AssetsPage.tsx` becomes a small route/container. Focused units will own the UI responsibilities:

- `useAssetsWorkspace`: permission-aware server requests, filters, paging, refresh, and mutation feedback.
- `AssetInventorySection`: inventory table, search/filter controls, page navigation, and manager actions.
- `AssetCategorySection`: category table and create/edit/retire actions.
- `AssetAllocationsSection`: active allocation table and allocation action.
- `AssetHistorySection`: returned allocation history.
- `AssetCategoryModal`: create/edit category form.
- `AssetModal`: create/edit asset form.
- `AssetAssignmentModal`: allocate asset form.
- `AssetReturnModal`: explicit confirmation plus return fields.
- `AssetRetireDialog`: reusable confirmation for category or asset retirement.

The page uses generated GraphQL document nodes from `.graphql` operation files and generated TypeScript result/input types. No new inline GraphQL strings or duplicated hand-written API row contracts are introduced.

Independent initial requests start concurrently. Mutations refresh only affected pages where practical. Buttons remain disabled while their action is pending, and repeated submission is prevented.

Category and employee choices use option queries that are independent from the visible management-table page. Employee choices are server-searchable, deterministically paged, and limited to `ACTIVE` employees. Asset mutations require the explicit `assets:manage` permission; role names do not grant an undocumented bypass.

All form controls have visible labels, validation messages, keyboard-accessible modal behavior, and actionable success/failure feedback. Raw employee IDs are never used as the primary display value.

## Lifecycle Rules

### Category

1. A manager creates a category with a tenant-unique code.
2. A manager may edit an active category.
3. Retirement is rejected while any non-retired asset references it.
4. Retired categories remain visible when displaying historical assets.

### Asset

1. A manager creates an asset under an active category.
2. A manager may edit an available asset.
3. Assigned assets cannot have category, tag, serial, purchase, or location data changed until returned.
4. An asset cannot be retired while actively assigned.
5. A retired asset cannot be edited or reallocated in this scope.

### Allocation

1. Only active employees and available assets can be selected.
2. Expected return date cannot precede allocation date.
3. The transaction verifies and locks the asset before inserting the active allocation.
4. The asset status changes to `ASSIGNED` in the same transaction.

### Return

1. Only an active allocation can be returned.
2. Return date cannot precede allocation date.
3. The manager confirms the action and may record condition and remarks.
4. One return log is inserted and the allocation becomes `RETURNED`.
5. The asset becomes `AVAILABLE` in the same transaction.
6. A repeated or concurrent return produces a stable conflict without inserting another log.

## Error and Empty States

- A list-query error remains visible without removing previously loaded data.
- Empty inventory gives managers a clear action to create the first category or asset.
- No available assets or employees disables allocation and explains why.
- Conflict errors identify the relevant category code, asset tag, serial number, assignment, or return rule without exposing SQL details.
- Successful mutations identify the completed action and refresh the relevant view.

Database and internal errors are logged server-side and exposed only as stable, sanitized GraphQL error codes/messages.

## Private File Remediation

- `file_storage` remains private implementation metadata. No local path, object key, bucket name, VPS URL, or signed object-store URL is returned to the client.
- Attachment bytes are fetched only through the owning business object after its authorization rules pass. A generic tenant-wide attachment read is not part of the public GraphQL contract.
- Announcement lists return only owning-record attachment-presence booleans; bytes are loaded lazily when the user previews or downloads one authorized attachment.
- Company-document upload returns an opaque, creator/purpose/expiry-bound staged-upload ID. Creating the document locks and claims that stage in the same transaction as the business record; the underlying `file_storage` ID is never public.
- Failed create/update operations compensate only operation-owned, unclaimed staged files. Successful replacement, clear, or permanent delete operations record durable cleanup only after the owning record no longer references the file. Company-document archive deliberately retains its referenced file for audit until permanent deletion.
- Local/S3 deletion is idempotent and retryable through a durable cleanup queue. Structured server logs contain only allowlisted error classes and correlation IDs, never storage details or raw provider errors.
- Expired unclaimed company-document stages are swept by the worker. Local fallback requires the worker profile and subgraph service to share the same private persistent mount; database and private-file backups use one coordinated recovery point.

## Verification Strategy

Test source will cover:

- Text normalization and date validation.
- Tenant filtering and permission enforcement.
- Category code and asset tag/serial uniqueness.
- Category and asset retirement guards.
- Assigned-asset edit guards.
- Concurrent/double assignment handling.
- Duplicate return handling and transaction state.
- Purchase-value masking for self-service users.
- React manager and employee visibility.
- Form validation, confirmation, mutation feedback, and retained-data error states.

Per repository instructions, Codex will not execute unit tests. The user will run the provided focused test commands and share failures.

The browser acceptance checklist requires manager and employee journeys against a running gateway, asset service, employee service, migrated tenant schema, and seeded or manually created tenant data. Runtime evidence must include the GraphQL result and resulting database state for create, edit, assign, return, history, and retire operations.

## Documentation and Status

- Update the feature matrix so `Implemented` does not mean merely that a page exists.
- Add a dedicated Asset Management acceptance checklist to `docs/module-completion-status.md`.
- Mark Asset Management **QA** only after implementation and permitted static checks are complete.
- Mark it **Complete** only after the user verifies the full browser journey, migration, authorization roles, and database transitions.

## Rollout Order

1. Add and review the tenant Liquibase migration.
2. Extend database entities for the new columns.
3. Implement Rust DTOs, paged queries, lifecycle mutations, authorization, and constraint error mapping.
4. Add GraphQL operation documents and regenerate the client.
5. Implement the React workspace and focused components.
6. Add test source and documentation.
7. User runs migrations, code generation where necessary, focused tests, and browser acceptance journeys.

No destructive data migration, hard deletion, automatic deployment, or source-control commit is part of this implementation.
