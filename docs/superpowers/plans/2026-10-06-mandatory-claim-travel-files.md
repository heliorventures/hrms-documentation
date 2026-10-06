# Mandatory Claim and Travel Files Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. The user selects the method before execution.

**Goal:** Require supporting files for every new expense and travel request, and let authorized viewers retrieve the evidence.

**Architecture:** Share required-file validation between the two submission services, retain nullable historical associations, and reuse tenant upload/storage infrastructure. Business-record authorization precedes attachment metadata and byte access.

**Tech Stack:** React 18, TypeScript, GraphQL, Rust, SeaORM, PostgreSQL, Liquibase, existing local/S3-compatible storage.

**Spec:** [Approved design, Workstream 1](../specs/2026-10-06-claims-locations-and-guidance-design.md).

## Global Constraints

- Enforce presence, same-tenant ownership, and uploader ownership inside the submission transaction before creating the business record/workflow.
- Never invent or backfill historical files.
- Do not expose raw storage URLs or internal IDs as report download links.
- Preserve the draft and successfully uploaded file ID on submission failure so retry does not unnecessarily upload again.
- No automatic commits; `rtk` commands; user-owned validation; preserve unrelated work. Shared execution/rollout constraints are in [the plan index](2026-10-06-claims-locations-and-guidance.md).

## Review Focus

1. Upload succeeds but submit fails: reuse the same file ID on retry; Task 2 asserts one upload and two submission calls.
2. User/tenant changes during upload: the old completion cannot submit into the new owner; Task 2 asserts zero stale submit callbacks.
3. Foreign, missing, unsupported, or empty evidence: submission writes no record/workflow; Task 1 checks transaction state.
4. Approver-only access or a retired employee: attachment access follows the existing parent-request scope; Task 3 checks scope parity.
5. Provider configuration changes after upload: LOCAL files remain readable and S3 reads use the recorded bucket; Task 3 checks metadata-based reads.

## Task 1: Persist and enforce new submission evidence

**Files:** Create `hrms-database/changelog/migrations/0096_travel_supporting_file/travel_supporting_file.xml`; modify `hrms-database/changelog/tenant.changelog-master.xml`; regenerate `hrms-svc/crates/kabipay-db-entities/src/tenant/d0033_travel_request.rs`; create `hrms-svc/crates/kabipay-expense/src/services/request_file_service.rs` and `request_file_tests.rs`; modify expense `services/{mod.rs,expense_service.rs,travel_request_service.rs}` and `resolvers/{types.rs,mutation.rs}`.

**Interfaces:**
- Produce `require_submission_file<C: ConnectionTrait + Sync>(db: &C, tenant_id: Uuid, uploader_user_id: Uuid, file_id: Option<Uuid>) -> KabiPayResult<file_storage::Model>` in `request_file_service.rs`.
- Add nullable `travel_request.supporting_file_storage_id: Option<Uuid>`; travel submission receives `uploader_user_id: Uuid` and `supporting_file_storage_id: Option<Uuid>` and validates unconditionally. Both GraphQL submission ID fields remain nullable at schema level to provide a clear service validation error to older callers; successful new submissions always have an ID.
- Both effective expense-hint branches produce `receipt_required: true`, even without a policy. Historical DTO attachment IDs remain nullable.

- [ ] Add regression tests named `submission_requires_owned_file`, `mandatory_receipt_ignores_optional_policy`, and `legacy_travel_without_file_remains_readable`. Assert absent/foreign/other-uploader/empty/unsupported files fail; valid PDF/JPEG/PNG up to 6 MiB succeeds; no failed submission leaves a request or workflow. Use current SeaORM proxy patterns for pure authorization/lookup tests and a disposable PostgreSQL fixture for persisted transaction assertions.
- [ ] Obtain the failing output for `rtk cargo test -p kabipay-expense request_file` and record whether DB-dependent cases require the disposable fixture.
- [ ] Add the nullable travel column and foreign-key association; verify same-tenant ownership in service logic. Append the forward migration. Generate with `rtk proxy py -3 scripts/generate_db_entities.py --only 0033_travel_request` from `hrms-svc`; inspect the generated diff.
- [ ] Move existing expense file-ownership logic into the shared validator. Check positive size, allowed metadata type, and permitted provider using existing upload limits; upload already validates bytes/type, so do not introduce a new acceptance policy. Validate within each transaction before inserting a request/workflow. Pass the authenticated user ID from the travel resolver.
- [ ] Update resolver tests so authorization failures are still tested with otherwise-valid inputs; add a direct-GraphQL missing-file assertion. Obtain focused passing output and disposable DB read-back showing no historical file backfill and correct persisted associations.

## Task 2: Required file forms and reliable upload retries

**Files:** Create `hrms-ui/src/modules/expenses/hooks/useSubmissionFile.ts` and `.test.tsx`; modify `components/{SubmitExpenseModal.tsx,SubmitTravelModal.tsx}`, `types.ts`, `hooks/useExpenseActions.ts`, admin `components/ExpensePolicyModal.tsx`, `hooks/useAdminExpenseCategories.ts`, and `src/api/{documents/clientOperations.graphql,schema-extensions/hrms-expense.graphql}`; regenerate `src/api/graphql/`. Create modal regression tests beside each modal.

**Interfaces:** `useSubmissionFile(ownerKey: string, client: GraphQLClient)` returns `{ file: File | null, uploading: boolean, setFile(file: File | null): void, ensureUploaded(): Promise<string>, reset(): void }`. The owner key includes authenticated tenant/user identity. Changing a file or owner clears its upload ID. Consume Task 1's `supportingFileStorageId` travel input and unconditional expense hints.

- [ ] Add `requires_file_before_submit`, `reuses_upload_after_submit_failure`, `ignores_completion_after_owner_change`, and `replacing_file_invalidates_cached_id`. Assert empty, oversized (>6 MiB), and unsupported files show errors before upload; failed upload produces zero mutations; failed mutation retains all fields and reuses one successful upload; double click produces one active submit.
- [ ] Obtain failing output from `rtk npm test -- src/modules/expenses/hooks/useSubmissionFile.test.tsx src/modules/expenses/components/SubmitExpenseModal.test.tsx src/modules/expenses/components/SubmitTravelModal.test.tsx` in `hrms-ui`.
- [ ] Implement the hook through existing `validateTenantUploadFile` and `uploadTenantFile(..., isCurrentOwner)`. Add the required file control, field-level error and PDF/JPG/PNG, 6 MB helper text; use the shared modal lifecycle to block dismissal while busy. Keep the existing successful-submit callback behavior.
- [ ] Remove the optional receipt checkbox; retain policy editing for all other rules and display the mandatory requirement. Send effective `receiptRequired: true` when saving policies without modifying historical records in bulk. Regenerate clients against the matching schema with `rtk npm run codegen`; confirm this is generation, not build/test evidence.
- [ ] Obtain passing focused outputs and verify keyboard/error/progress behavior in the browser. Update the expense/travel tour wording so this deliverable does not ship contradictory receipt guidance.

## Task 3: Authorized evidence metadata and downloads

**Files:** Create `hrms-svc/crates/kabipay-common/src/private_file_reader.rs`; modify common `lib.rs`, employee `services/document_file_service.rs` and the relevant helpers under its existing `services/object_store/`; extend expense `services/request_file_service.rs`, `resolvers/{query.rs,types.rs}` and `main.rs` only if required to register byte responses. Create UI `components/RequestAttachmentButton.tsx` and `.test.tsx`; update `ExpenseClaimsTable.tsx`, `TravelRequestsTable.tsx`, and the expense GraphQL documents/extension. Add service `request_file_tests.rs` download cases.

**Interfaces:** Produce shared `read_private_file(db: &DatabaseConnection, root: &Path, row: &file_storage::Model) -> KabiPayResult<Vec<u8>>`, preserving existing DATABASE/LOCAL/S3-compatible behavior. Keep the employee reader as a compatibility wrapper. Produce GraphQL `expenseAttachment(expenseId: ID!): RequestAttachment` and `travelRequestAttachment(travelRequestId: ID!): RequestAttachment`, returning `{ fileName: String!, mimeType: String!, contentBase64: String! }` or null for a historical missing association. Add `hasSupportingFile` to both business DTOs so lists need not download bytes.

- [ ] Add `attachment_scope_matches_parent_list`, `attachment_rejects_foreign_parent_or_file`, `legacy_missing_attachment_is_null`, and reader tests for path traversal, recorded provider/bucket, unavailable bytes, and existing employee-document behavior. The exact parent expense/travel list-scope helper is the authorization reference, including approval scopes; do not weaken it to a generic tenant-file lookup.
- [ ] Obtain failing outputs for `rtk cargo test -p kabipay-expense request_file`, `rtk cargo test -p kabipay-common private_file_reader`, and focused employee-reader regression tests.
- [ ] Extract only shared read/config helpers needed by existing provider-aware reads, retaining byte-based upload validation and cleanup logic in their current owners. Look up and authorize the parent, then its tenant file; return bounded bytes with safe filename/type metadata. Parent lookup, not client file ID, selects the document.
- [ ] Implement the reusable attachment action with existing object-URL download conventions, disabled loading state, friendly errors and URL revocation. Missing historical evidence displays an explanatory state. Never retrieve all document bytes during list loading.
- [ ] Obtain focused passing output plus browser download proof for employee, assigned approver, ALL reader, and denied user. Run no live upload or migration automatically; record the coordinated rollout dependency in the handoff.

## Verification handoff

Provide UI focused test commands above, `rtk npm run lint`, `rtk npm run build`, and service `rtk cargo test -p kabipay-expense`, shared reader and employee regression commands. Disposable DB cases must cover migration rerun, historical nulls, failed-transaction read-back, and successful evidence association. No commits or deployment steps are executed by this plan.
