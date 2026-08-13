# Employee Directory and Self-Service Profile Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver a tenant-wide safe employee directory and org chart plus secure, persistent employee self-service for personal details, identity evidence, education, and prior work experience without full-page reloads.

**Architecture:** Keep existing scoped employee APIs intact and add an allow-listed organization-directory projection for all authenticated tenant employees. Add normalized tenant tables for profile records and auditable sensitive change requests, enforce self-versus-HR authorization in Rust, and reconcile returned section DTOs into React state instead of refetching the entire profile bundle.

**Tech Stack:** PostgreSQL, Liquibase XML, Rust, SeaORM, async-graphql, React 18, TypeScript, graphql-request, GraphQL Code Generator, Tailwind CSS.

## Global Constraints

- Do not run unit tests; the user will run them and share output.
- Do not run Dart or Flutter commands.
- Do not create commits.
- Preserve unrelated dirty files in every repository.
- Do not edit historical Liquibase changesets; add migration `0050` after `0049`.
- Directory APIs must never expose private employee, identity, login, document, bank, compensation, role, or permission data.
- Server-side authorization is authoritative; React visibility is not a security boundary.
- Existing scoped `employees` consumers retain their current authorization behavior.

---

### Task 1: Tenant schema and SeaORM entity contract

**Files:**
- Create: `hrms-database/changelog/migrations/0050_employee_self_service/employee_self_service.xml`
- Modify: `hrms-database/changelog/tenant.changelog-master.xml`
- Modify: `hrms-svc/crates/kabipay-db-entities/src/tenant/d0007_employee_core.rs`
- Modify: `hrms-svc/crates/kabipay-db-entities/src/tenant/d0008_document_system.rs`
- Create: `hrms-svc/crates/kabipay-db-entities/src/tenant/d0050_employee_self_service.rs`
- Modify: `hrms-svc/crates/kabipay-db-entities/src/tenant/mod.rs`
- Modify: `hrms-svc/crates/kabipay-employee/src/entities/mod.rs`

**Interfaces:**
- Produces: `employee.personal_phone`, `employee.current_address`, `employee.permanent_address`.
- Produces: SeaORM modules `employee_education`, `employee_work_experience`, `employee_profile_change_request`, `employee_education_document`, and `employee_work_experience_document`.
- Produces: `document_type.system_key: Option<String>` and tenant-unique system document keys.

- [ ] **Step 1: Add schema-shape tests for the new entity fields**

Add compile-time construction coverage under each new entity module using `Model` field initialization so a missing column mapping fails compilation. Add validation tests later at the service layer; do not run them in Codex.

- [ ] **Step 2: Add Liquibase changesets**

Create ordered changesets for contact columns, document `system_key`, default system document types, education, work experience, change requests, and evidence junctions. Use explicit checks/FKs/indexes/triggers/rollbacks. Use these status checks:

```sql
verification_status IN ('UNVERIFIED','PENDING','VERIFIED','REJECTED')
status IN ('PENDING','APPROVED','REJECTED','CANCELLED')
request_type IN ('LEGAL_NAME_OR_DOB','PAN','AADHAAR','BANK_ACCOUNT')
```

Use a partial unique index for one pending request:

```sql
CREATE UNIQUE INDEX uq_profile_change_pending
ON "${schema}".employee_profile_change_request (tenant_id, employee_id, request_type)
WHERE status = 'PENDING';
```

- [ ] **Step 3: Include migration `0050` in the tenant master changelog**

Append the include after `0049_user_must_change_password`.

- [ ] **Step 4: Mirror the schema in SeaORM entities**

Add exact Rust fields matching nullability and types. Re-export the new module through tenant and employee entity modules.

- [ ] **Step 5: Perform allowed static verification**

Run `git diff --check` separately in `hrms-database` and `hrms-svc`. Do not run migration tests or unit tests.

---

### Task 2: Safe organization directory and complete org-chart APIs

**Files:**
- Create: `hrms-svc/crates/kabipay-employee/src/services/directory_service.rs`
- Modify: `hrms-svc/crates/kabipay-employee/src/services/mod.rs`
- Modify: `hrms-svc/crates/kabipay-employee/src/resolvers/types.rs`
- Modify: `hrms-svc/crates/kabipay-employee/src/resolvers/query.rs`
- Modify: `hrms-svc/crates/kabipay-employee/src/services/employee_service.rs`

**Interfaces:**
- Produces: `EmployeeDirectoryEntryDto` with only `employee_id`, `employee_code`, `full_name`, `department_name`, `designation_title`, `reporting_manager_id`, `reporting_manager_name`, `employment_type`, `date_of_joining`, and `status`.
- Produces: `EmployeeDirectoryPageDto { rows, next_cursor, has_more }`.
- Produces: queries `employeeDirectoryPage(limit, after)` and `organizationDirectoryChart`.

- [ ] **Step 1: Add failing service tests without running them**

Cover projection field allow-listing, exclusion of deleted/terminated employees, stable `(employee_code,id)` cursor ordering, and full hierarchy visibility independent of private `employee` resource scope.

- [ ] **Step 2: Implement cursor encoding and directory queries**

Use an opaque base64 JSON cursor containing `employee_code` and `id`. Clamp page size to `1..=100`. Require client claims and tenant ID; do not call `data_scope_employee` for these safe projections.

- [ ] **Step 3: Implement hierarchy enrichment**

Load department/designation/manager names in bounded set-based queries. Do not expose linked user fields or private employee columns in DTOs.

- [ ] **Step 4: Keep existing scoped APIs unchanged**

Do not modify `employees`, `employee(id)`, `employeeDocuments`, compensation, attendance, payroll, or other resource-scope behavior.

- [ ] **Step 5: Perform allowed static verification**

Run targeted Rust formatting only on changed files if it does not touch unrelated paths, then `git diff --check`. Do not run Rust tests.

---

### Task 3: Private profile capabilities and direct/sensitive personal changes

**Files:**
- Create: `hrms-svc/crates/kabipay-employee/src/services/profile_change_service.rs`
- Modify: `hrms-svc/crates/kabipay-employee/src/services/mod.rs`
- Modify: `hrms-svc/crates/kabipay-employee/src/services/employee_service.rs`
- Modify: `hrms-svc/crates/kabipay-employee/src/services/profile_extras_service.rs`
- Modify: `hrms-svc/crates/kabipay-employee/src/resolvers/scope.rs`
- Modify: `hrms-svc/crates/kabipay-employee/src/resolvers/types.rs`
- Modify: `hrms-svc/crates/kabipay-employee/src/resolvers/query.rs`
- Modify: `hrms-svc/crates/kabipay-employee/src/resolvers/mutation.rs`

**Interfaces:**
- Produces: `EmployeeProfileAccessDto { directory_entry, is_self, can_view_private_profile, can_edit_personal_profile, can_manage_organization_fields, can_review_profile_changes }`.
- Produces: direct mutation `updateEmployeeSelfServiceProfile(input) -> EmployeeDto` accepting only phone, addresses, gender, nationality, blood group, and emergency contacts.
- Produces: `submitEmployeeProfileChange`, `cancelEmployeeProfileChange`, and `resolveEmployeeProfileChange`.
- Produces: list query `employeeProfileChangeRequests(employeeId, status)`.

- [ ] **Step 1: Add authorization and validation tests without running them**

Cover self access, HR-in-scope access, ordinary-user denial for another private profile, forbidden organization fields, one-pending-request conflict, reviewer-self denial, and canonical values remaining unchanged before approval.

- [ ] **Step 2: Add reusable profile access resolution**

Resolve viewer employee ID once. Compute capability flags from `is_self`, `can_manage_employee_directory`, and existing data scope. Return public access DTO even when private access is false.

- [ ] **Step 3: Narrow direct self-service updates**

Move legal first/last name and DOB out of the direct self-service input. Validate phone length, trim nullable strings, and return the updated employee DTO.

- [ ] **Step 4: Implement sensitive request persistence**

Validate each typed payload before storing JSONB. Mask PAN/Aadhaar/bank values in response DTOs. Do not mutate canonical tables at submission time.

- [ ] **Step 5: Implement transactional approval/rejection**

Lock the pending request, prohibit requester self-approval unless the requester is operating through an HR-authorized administrative flow for another employee, revalidate payload, update the canonical table, update review metadata, and commit atomically.

- [ ] **Step 6: Perform allowed static verification**

Run targeted formatting and `git diff --check`; do not run unit tests.

---

### Task 4: Education, work experience, and evidence APIs

**Files:**
- Create: `hrms-svc/crates/kabipay-employee/src/services/profile_record_service.rs`
- Modify: `hrms-svc/crates/kabipay-employee/src/services/mod.rs`
- Modify: `hrms-svc/crates/kabipay-employee/src/services/document_file_service.rs`
- Modify: `hrms-svc/crates/kabipay-employee/src/resolvers/types.rs`
- Modify: `hrms-svc/crates/kabipay-employee/src/resolvers/query.rs`
- Modify: `hrms-svc/crates/kabipay-employee/src/resolvers/mutation.rs`

**Interfaces:**
- Produces: `EmployeeEducationDto` and `EmployeeWorkExperienceDto` including verification and evidence metadata.
- Produces: list/create/update/soft-delete mutations for both record types.
- Produces: `uploadEmployeeEducationEvidence`, `uploadEmployeeWorkExperienceEvidence`, and review mutations.

- [ ] **Step 1: Add service validation tests without running them**

Cover education levels, completion year `1900..=current year`, start-date ordering, work current/end-date consistency, self ownership, cross-tenant denial, verified-record edits resetting verification, and evidence attachment moving status to `PENDING`.

- [ ] **Step 2: Implement normalized CRUD services**

Trim required strings, convert empty optional strings to `None`, use soft delete, scope every query by tenant and employee, and order education by completion year descending and experience by start date descending.

- [ ] **Step 3: Implement evidence linkage**

Reuse `document_file_service::upload_employee_document`, choose document types by stable `system_key`, and create the junction row in the same database transaction as verification-state transition. Reject mismatched employee or tenant IDs.

- [ ] **Step 4: Implement HR review**

Reuse the existing directory-admin gate, reject self-review, record reviewer/reason/time, and update both linked document and record verification state consistently.

- [ ] **Step 5: Perform allowed static verification**

Run targeted formatting and `git diff --check`; do not run unit tests.

---

### Task 5: GraphQL client documents and generated contracts

**Files:**
- Modify: `hrms-ui/src/api/schema-extensions/hrms-employee-profile.graphql`
- Modify: `hrms-ui/src/api/documents/clientOperations.graphql`
- Generated: `hrms-ui/src/api/graphql/graphql.ts`
- Generated: `hrms-ui/src/api/graphql/gql.ts`
- Preserve existing user changes: `hrms-ui/src/api/graphql/index.ts`
- Preserve existing user changes: `hrms-ui/src/api/graphql/fragment-masking.ts`

**Interfaces:**
- Consumes: all GraphQL types and operations from Tasks 2–4.
- Produces: typed Documents and query/mutation result types used by Tasks 6–8.

- [ ] **Step 1: Extend the local schema**

Declare the exact DTOs, page types, capabilities, inputs, queries, and mutations from Tasks 2–4 so codegen can work before a gateway restart.

- [ ] **Step 2: Add named operations**

Add directory paging, hierarchy, profile access, direct update, change requests, education/work CRUD, evidence upload, and review operations to `clientOperations.graphql`.

- [ ] **Step 3: Protect dirty generated files**

Inspect the current diff for `index.ts` and `fragment-masking.ts`. Run codegen only if it can preserve those user-owned changes; otherwise update only `graphql.ts` and `gql.ts` through the generator output and restore no user content.

- [ ] **Step 4: Generate contracts without running tests**

Use `npm run codegen` only when the live gateway/schema source is available. If unavailable, report generated-contract verification as pending rather than inventing hand-written generated types.

- [ ] **Step 5: Perform allowed static verification**

Run `git diff --check` in `hrms-ui`. Do not run unit tests.

---

### Task 6: React directory, org chart, and public employee profile

**Files:**
- Modify: `hrms-ui/src/modules/organization/OrganizationEmployeesPage.tsx`
- Modify: `hrms-ui/src/modules/organization/OrgChartPage.tsx`
- Modify: `hrms-ui/src/utils/orgChartTree.ts`
- Create: `hrms-ui/src/modules/organization/employee-profile/PublicEmployeeProfile.tsx`
- Modify: `hrms-ui/src/modules/organization/employee-profile/EmployeeProfileShell.tsx`
- Test: `hrms-ui/src/utils/orgChartTree.test.ts`

**Interfaces:**
- Consumes: `EmployeeDirectoryPageDocument`, `OrganizationDirectoryChartDocument`, and `EmployeeProfileAccessDocument`.
- Produces: full safe directory, cycle-safe hierarchy, and public-only profile rendering for another employee.

- [ ] **Step 1: Write cycle/orphan tree tests without running them**

Add fixtures for one root, multiple roots, missing manager, and `A -> B -> A`. Assert the builder emits finite roots/unassigned groups and never recursively revisits an ID.

- [ ] **Step 2: Replace the scoped directory operation**

Fetch cursor pages until `hasMore` is false, deduplicate by employee ID, retain client-side search, and show an explicit partial-load error if a later page fails.

- [ ] **Step 3: Render a complete resilient org chart**

Use the safe hierarchy query. Pass an ancestor set through recursive rendering and render a data-warning node rather than descending into a repeated employee ID.

- [ ] **Step 4: Add public/private route branching**

Load profile access first. Render `PublicEmployeeProfile` when private access is false; only then load private bundle data for self or HR.

- [ ] **Step 5: Perform allowed static verification**

Run formatting through the project formatter only on changed files if available, then `git diff --check`. Do not run Vitest.

---

### Task 7: React section-local profile reconciliation and reviewed changes

**Files:**
- Modify: `hrms-ui/src/modules/organization/employee-profile/hooks/useEmployeeProfileData.ts`
- Modify: `hrms-ui/src/modules/organization/employee-profile/lib/mapBundleToModel.ts`
- Modify: `hrms-ui/src/modules/organization/employee-profile/types.ts`
- Modify: `hrms-ui/src/modules/organization/employee-profile/EmployeeProfileShell.tsx`
- Modify: `hrms-ui/src/modules/organization/employee-profile/tabs/PersonalInfoTab.tsx`
- Modify: `hrms-ui/src/modules/organization/employee-profile/tabs/BankingTab.tsx`
- Modify: `hrms-ui/src/modules/organization/employee-profile/tabs/IdentityTab.tsx`
- Modify: `hrms-ui/src/modules/organization/employee-profile/tabs/DocumentsTab.tsx`
- Create: `hrms-ui/src/modules/organization/employee-profile/components/ProfileChangeStatus.tsx`

**Interfaces:**
- Produces: hook methods `mergeEmployee`, `replaceBank`, `replaceIdentity`, `replaceDocuments`, `replaceEducation`, `replaceWorkExperience`, and `refreshInBackground`.
- Consumes: capability flags and change-request DTOs.

- [ ] **Step 1: Refactor initial load versus background refresh state**

Keep `initialLoading` separate from `refreshing`. Do not set `model` to null during background refresh. Expose immutable functional merge methods.

- [ ] **Step 2: Wire direct personal fields**

Enable phone/current/permanent address plus approved direct fields. Legal name and DOB submit reviewed requests and display pending/rejected status.

- [ ] **Step 3: Wire PAN/Aadhaar and bank reviewed requests**

Add evidence-upload controls beside PAN and Aadhaar, retain Passport upload, submit canonical replacements as pending requests, and merge request status locally.

- [ ] **Step 4: Remove profile-wide post-save refetches**

Each successful mutation merges its returned DTO. Keep the manual Refresh action, implemented through `refreshInBackground` so the shell remains visible.

- [ ] **Step 5: Perform allowed static verification**

Run `git diff --check`; do not run unit tests.

---

### Task 8: React education and work-experience management

**Files:**
- Modify: `hrms-ui/src/modules/organization/employee-profile/types.ts`
- Modify: `hrms-ui/src/modules/organization/employee-profile/lib/mapBundleToModel.ts`
- Modify: `hrms-ui/src/modules/organization/employee-profile/tabs/EducationTab.tsx`
- Modify: `hrms-ui/src/modules/organization/employee-profile/tabs/WorkExperienceTab.tsx`
- Modify: `hrms-ui/src/modules/organization/employee-profile/EmployeeProfileShell.tsx`
- Create: `hrms-ui/src/modules/organization/employee-profile/components/EvidenceUploadButton.tsx`

**Interfaces:**
- Consumes: education/work CRUD and evidence Documents from Task 5.
- Produces: persistent self/HR forms with local list reconciliation and verification-state display.

- [ ] **Step 1: Replace fallback arrays with GraphQL records**

Map server education/work records directly into the profile model, including evidence and review fields.

- [ ] **Step 2: Implement education add/edit/delete**

Use the approved education-level choices, require qualification/institution/completion year, support optional remaining fields and evidence, preserve modal values on failure, and merge returned records without refetch.

- [ ] **Step 3: Implement work-experience add/edit/delete**

Require company/role/start date, enforce current/end-date UI behavior, calculate display duration from dates, support description/location/employment type/evidence, and merge returned records locally.

- [ ] **Step 4: Respect viewer capabilities**

Show mutations only for self or HR. Public profiles receive no education/work private query and no edit controls.

- [ ] **Step 5: Perform allowed static verification**

Run `git diff --check`; do not run Vitest.

---

### Task 9: Cross-repository audit and user-run verification handoff

**Files:**
- Modify only if omissions are found: files changed in Tasks 1–8
- Review: `hrms-documentation/docs/superpowers/specs/2026-08-12-employee-directory-self-service-design.md`

**Interfaces:**
- Consumes: completed database, service, GraphQL, and React changes.
- Produces: evidence-backed completion report and exact user-run commands.

- [ ] **Step 1: Audit authorization and data exposure**

Trace every new query and mutation from React to resolver to service/entity. Confirm the public projection contains only approved fields and every private record path validates tenant, employee, viewer, and role.

- [ ] **Step 2: Audit migration/entity parity**

Compare every new Liquibase column with its SeaORM field type/nullability and confirm master changelog inclusion and rollback coverage.

- [ ] **Step 3: Review repository diffs**

Run `git status --short` and `git diff --check` independently in `hrms-database`, `hrms-svc`, `hrms-ui`, and `hrms-documentation`. Preserve and separately identify pre-existing dirty files.

- [ ] **Step 4: Provide user-run commands**

Ask the user to run and share output for:

```powershell
Set-Location D:\work\heliorventures\hrms-database
.\scripts\update-tenant-liquibase.ps1 -Schema tenant_e6d4fc13

Set-Location D:\work\heliorventures\hrms-svc
cargo test -p kabipay-common -p kabipay-auth -p kabipay-employee

Set-Location D:\work\heliorventures\hrms-ui
npm run codegen
npm run build
npm test
```

Codex must not run these unit-test commands. Report any compilation/codegen/build command that was also intentionally left to the user.
