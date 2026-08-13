# Employee Directory, Org Chart, and Self-Service Profile Design

Date: 2026-08-12

Status: Approved design, awaiting written-spec review

## Objective

Complete the Employee experience across the tenant database, Rust employee subgraph, GraphQL client operations, and React UI so that:

- every authenticated employee can browse safe basic information for all current employees;
- every authenticated employee can see the tenant reporting hierarchy;
- employees can maintain their own permitted personal information without changing organization-controlled fields;
- sensitive statutory and payroll-related changes remain pending until HR approval;
- employees can maintain education and prior-work-experience records with supporting documents;
- saving one profile section does not reload or blank the entire Employee page.

## Current root causes

1. `employees` and `orgChart` both consume the `employee` resource scope. A normal employee without an explicit wider scope defaults to `SELF`, so both queries return only the viewer's employee row.
2. The existing employee DTO contains private and operational fields. Widening its scope to `ALL` would expose data that does not belong in a company directory.
3. The profile bundle hook exposes a single `refetch()` operation. Every section calls it after a mutation, which sets shell-level `loading` and replaces the whole page with its initial skeleton.
4. Education and prior work experience exist only as UI model arrays. The bundle mapper always supplies empty arrays, Education is rendered with `readOnly`, and neither domain has tenant tables or GraphQL CRUD operations.
5. PAN and Aadhaar number mutations exist, but the Identity tab only exposes an evidence-upload action for Passport. Generic document upload also depends on tenant `document_type` rows that are not guaranteed to exist.
6. Personal phone and addresses are represented in React state but do not exist in the employee database/entity/API contract.

## Architecture decision

Use separate public-directory and private-profile contracts.

The existing scoped employee APIs remain unchanged for HR, payroll, attendance, workflow, and other operational consumers. New directory APIs return an explicitly allow-listed projection and are available to any authenticated tenant employee. This prevents an organization-directory requirement from weakening sensitive employee data authorization.

## Authorization and visibility

### Organization-visible fields

The directory and org chart may return only:

- employee ID, needed for links and reporting relationships;
- employee code;
- full name;
- department name;
- designation title;
- reporting manager ID and name;
- employment type;
- date of joining;
- current employment status.

They must not return linked user IDs/usernames/emails, DOB, gender, nationality, blood group, phone, addresses, emergency contacts, bank details, statutory identity values, documents, compensation, roles, permissions, or change requests.

The public directory contains current, non-deleted employees. `TERMINATED` employees are excluded from ordinary employee directory and org-chart responses. HR continues to use the existing scoped administrative employee query to see historical or terminated employees.

### Private profile access

- An employee may read and mutate their own private profile.
- An HR/directory administrator may read and mutate an employee that is within their existing employee data scope.
- An ordinary employee opening another employee receives the public organization profile only. Private tabs are not queried or rendered.
- Server-side authorization is authoritative. React visibility is usability only and must never be the security boundary.

### Organization-controlled fields

Self-service mutations must never accept:

- designation;
- department;
- reporting manager;
- employment type or status;
- employee/application roles and permissions;
- compensation.

These remain on existing HR-authorized mutation paths.

## Database design

Add a new tenant Liquibase migration after `0049`. Do not edit historical changesets.

### Employee contact fields

Add nullable fields to `employee`:

- `personal_phone VARCHAR(50)`;
- `current_address TEXT`;
- `permanent_address TEXT`.

Existing demographic and emergency-contact fields remain on `employee`.

### Education

Create `employee_education` with:

- UUID primary key and tenant/employee foreign keys;
- `education_level` with allowed values `SECONDARY`, `HIGHER_SECONDARY`, `DIPLOMA`, `UNDERGRADUATE`, `POSTGRADUATE`, `DOCTORATE`, `CERTIFICATION`, `OTHER`;
- qualification/degree, field of study, institution, and board/university;
- optional start date, required completion year, optional grade/score, and description;
- verification status `UNVERIFIED`, `PENDING`, `VERIFIED`, or `REJECTED`;
- reviewer, reviewed timestamp, and rejection reason;
- standard soft-delete and audit timestamps.

Create tenant/employee and tenant/status indexes. Enforce completion year between 1900 and the current calendar year, and reject a start date later than the end of that completion year.

### Prior work experience

Create `employee_work_experience` with:

- UUID primary key and tenant/employee foreign keys;
- company, role/title, employment type, and location;
- start date, optional end date, and `is_current`;
- description/responsibilities;
- verification status, reviewer, reviewed timestamp, and rejection reason;
- standard soft-delete and audit timestamps.

Enforce that current employment has no end date and completed employment has an end date on or after its start date. Duration is derived from dates and is not persisted as user-entered years.

### Sensitive profile change requests

Create `employee_profile_change_request` with:

- UUID primary key and tenant/employee/requester foreign keys;
- request type `LEGAL_NAME_OR_DOB`, `PAN`, `AADHAAR`, or `BANK_ACCOUNT`;
- validated requested payload stored as JSONB;
- status `PENDING`, `APPROVED`, `REJECTED`, or `CANCELLED`;
- optional supporting employee-document ID;
- reviewer, reviewed timestamp, and rejection reason;
- audit timestamps.

Only one pending request for the same employee and request type is allowed. Approval revalidates the payload and applies it transactionally to the canonical employee, PAN/Aadhaar, or bank tables. Rejection leaves canonical values unchanged.

### Document types and evidence links

Add nullable `system_key` to `document_type`, with a tenant-scoped unique constraint for non-null keys. Backfill a matching existing row where possible and insert a missing active type for:

- `PAN_CARD`;
- `AADHAAR_CARD`;
- `PASSPORT`;
- `EDUCATION_CERTIFICATE`;
- `EXPERIENCE_LETTER`.

Create normalized link tables between `employee_document` and education/work-experience records. Each link must carry `tenant_id`, enforce foreign keys, and prevent the same document from being linked twice to the same record. Sensitive change requests reference their supporting document directly.

## GraphQL and service design

### Directory

Add a dedicated `EmployeeDirectoryEntry` projection and a cursor page ordered by employee code and ID. The React directory repeatedly requests pages until all current employees are loaded for local search. The API authenticates the client JWT and tenant but intentionally does not use the private employee resource scope.

Add a dedicated organization-chart query using the same safe projection. It returns all current non-deleted employees needed to construct the reporting graph. Existing manager-cycle validation remains mandatory for HR assignment writes.

### Viewer capabilities

The profile response exposes viewer capabilities derived on the server:

- `isSelf`;
- `canViewPrivateProfile`;
- `canEditPersonalProfile`;
- `canManageOrganizationFields`;
- `canReviewProfileChanges`.

The UI uses these flags instead of inferring HR access from route visibility alone.

### Personal profile mutations

Split direct and reviewed changes:

- Direct self-service mutation: phone, addresses, gender, nationality, blood group, and emergency contacts.
- Sensitive request mutation: legal first/last name, DOB, PAN/Aadhaar, and bank details.
- HR may continue to use authorized direct administrative paths where required, but all changes remain auditable.

Every mutation returns the updated section DTO or change-request DTO so React can reconcile local state without a profile-wide refetch.

### Education and work-experience CRUD

Add list, create, update, and soft-delete operations. A normal employee may act only on records whose `employee_id` is their own. HR may act on employees in its existing scope. Updating a verified record resets it to `UNVERIFIED`; attaching employee-uploaded evidence moves it to `PENDING`. HR verification or rejection records reviewer metadata.

### Documents

Reuse the existing private object-storage upload path. Add a required evidence context to section-specific upload operations and validate that the target record belongs to the same tenant and employee. Preserve PDF/PNG/JPEG validation and configured size limits. Employee evidence uploads begin as `PENDING`; authorized HR uploads may be approved immediately under the existing rule.

## React design

### Directory and org chart

- Replace `ClientOpsEmployeesDirectory` on the employee-facing page with the safe paginated directory operation.
- Keep search client-side after all pages are loaded for the current tenant.
- Build the org chart from the safe full hierarchy response.
- Track visited IDs while rendering so corrupt legacy cycles cannot cause recursive rendering.
- Show employees with no valid in-dataset manager under an "Unassigned reporting line" group.
- Preserve links to employee routes; the destination renders public-only or private tabs from server capabilities.

### Profile shell state

Replace the single reload token with section-aware state reconciliation:

- initial shell load controls only the initial full-page skeleton;
- `updatePersonal`, `updateIdentity`, `updateBank`, `replaceEducation`, `replaceWorkExperience`, and `replaceDocuments` merge mutation results into the existing model;
- section components own their busy/error state;
- failed mutations preserve form input;
- an explicit Refresh action may perform a full background reconciliation without unmounting the current profile.

### Personal information

Render direct-edit and review-required fields separately. Saving direct fields updates only that card. Sensitive fields show their canonical value plus any pending request and its status. Organization-controlled fields appear read-only with explanatory text.

### Identity

Show PAN, Aadhaar, and Passport evidence actions in their respective cards. PAN/Aadhaar number changes and evidence are submitted as reviewed change requests. Mask statutory identifiers in all query responses.

### Education

Remove the forced `readOnly` behavior for self and authorized HR users. Provide add/edit/delete dialogs using the defined education levels and optional evidence upload. Show verification status and rejection reason.

### Work experience

Provide add/edit/delete dialogs for previous employment. Use start/end dates and a current-role checkbox, display calculated duration, and allow optional evidence upload. Show verification status and rejection reason.

## Error handling and security

- Validate every tenant, employee, record, and document relationship server-side to prevent IDOR and cross-tenant linking.
- Reject empty names, invalid dates, future completion dates, invalid PAN/Aadhaar formats, invalid IFSC/account payloads, unsupported MIME types, and oversized files.
- Do not expose raw database or storage errors in GraphQL responses.
- Apply sensitive approvals in a database transaction and retain rejected/cancelled requests for audit.
- Prevent ordinary users from approving their own requests or documents.
- Do not use organization-directory access as permission to read private profile sections.

## Acceptance criteria

1. A normal authenticated employee sees every current employee's safe directory card, regardless of private employee data scope.
2. The org chart displays all valid reporting relationships, multiple roots, and unassigned employees without recursive failure.
3. Another employee's route exposes organization-visible information only.
4. The viewer can directly save permitted self fields and only the active section shows a saving state.
5. Designation, department, reporting manager, employment status/type, roles, permissions, and compensation cannot be changed through self-service APIs.
6. Legal name, DOB, PAN/Aadhaar, and bank changes remain pending until HR approval and do not replace canonical values early.
7. PAN, Aadhaar, Passport, education certificate, and experience-letter uploads are discoverable in their relevant sections.
8. Education and prior work experience persist after a browser reload and support add, edit, soft delete, evidence, and verification status.
9. Employee-uploaded evidence is pending; HR can approve or reject it with audit metadata.
10. Existing HR-scoped employee consumers retain their current authorization behavior.

## Verification constraints

Codex will not run unit tests or Dart/Flutter commands. Implementation verification may use static inspection, targeted formatting where safe, generated-diff review, and `git diff --check` in each changed repository. The user will run and share unit/integration test output. No commits will be created by Codex.
