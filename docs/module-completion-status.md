# HRMS Module Completion Status

This is the one-module-at-a-time completion register for the HRMS product.

## Completion rule

A module may be marked **Complete** only when all of the following are verified:

1. The React UI flow works for each supported role.
2. GraphQL operations reach the intended Rust resolver and service.
3. Authorization and tenant/data scoping are enforced server-side.
4. Required database migrations and seed/configuration changes are applied.
5. File/object-storage behavior works for the configured storage mode.
6. Success, validation, and failure states are visible and actionable in the UI.
7. The documented browser journey passes against the running gateway, services, and tenant database.

Static code, a generated GraphQL client, a successful compile, or a UI that renders is not sufficient for **Complete**.

## Status meanings

| Status | Meaning |
|---|---|
| **Complete** | End-to-end runtime flow verified and no known blocking issue remains. |
| **In progress** | Required implementation, defect fixing, or integration work is still being done. |
| **QA** | Implementation is complete enough for validation; browser/runtime, migration, role, or regression verification remains. |
| **Todo** | The capability is not implemented or is not reachable from the product flow. |

## Module queue

| Order | Module | Status | Completion evidence |
|---:|---|---|---|
| 1 | Timesheet | **QA** | UI and Rust validation/workflow paths exist; browser and tenant-runtime verification are pending. |
| 2 | Attendance | **QA** | UI and Rust attendance/policy paths exist; role, overlap, reporting, and runtime verification are pending. |
| 3 | Leave | **QA** | Accrual, balance, overlap, and workflow logic exist; migration and browser verification are pending. |
| 4 | Notifications and announcements | **QA** | Notification and private attachment paths exist; role and download journeys are pending runtime verification. |
| 5 | Employee profile and documents | **QA** | Profile/document implementation is wired end to end; browser, role, migration, and storage verification remain. |
| 6 | Organization/company documents | **QA** | UI, Rust service, and Liquibase migration exist; migration application and download smoke test remain. |
| 7 | Expenses and travel | **In progress** | Submit and approval paths exist; receipt upload and remaining role-workflow implementation remain. |
| 8 | Authentication, tenant session, and RBAC | **QA** | Login, password, tenant, and scope paths exist; inactive-user and session browser journeys remain. |
| 9 | Payroll and tax | **QA** | Payslip/pay/tax paths exist; statutory outputs contain documented stub scope and need runtime verification. |
| 10 | Workplace modules | **QA** | Asset Management now has category, inventory, assignment, return, history, and retirement implementation; runtime verification remains module-specific. |
| 11 | Admin reporting and settings | **QA** | Reports and policy screens exist; reporting correctness and role verification remain. |
| 12 | Browser regression coverage | **Todo** | No durable browser E2E suite is currently available. |

## Module 1: Timesheet acceptance checklist

Sources: `test/Issues_15-Aug.docx`, `test/Issues_Admin-Timesheet,Leave-8-Aug.docx`, `test/Issues_Attendance_5Aug.docx`, `test/Issues_Attendance_6Aug.docx`, and the timesheet items in the earlier issue documents.

### Entry and editing

- [ ] Add Entry requires Project and Task Type.
- [ ] A single entry cannot exceed 24 hours.
- [ ] A day's combined entries cannot exceed 24 hours.
- [ ] A week's combined entries cannot exceed 40 hours.
- [ ] Submitted or approved entries cannot be edited unless the configured policy explicitly permits approved-row editing.
- [ ] Entries from outside the configured editable-week span cannot be edited or submitted.
- [ ] Adding time to an already submitted or approved week shows a specific user-facing message and does not mutate data.
- [ ] Delete requires confirmation and only deletes an allowed draft/rejected entry.
- [ ] Custom date entry does not reset while the user is typing a valid date.
- [ ] Decimal hours such as `0.25` display and total correctly.

### Calendar, controls, and feedback

- [ ] Calendar remains visible below a report/load error.
- [ ] The weekly option is labelled clearly as a weekly view.
- [ ] Submit success feedback is visible and the refreshed state is correct.
- [ ] CSV column names use the required human-readable casing and spacing.

### Approval workflow

- [ ] A manager/HR user cannot approve or reject their own timesheet.
- [ ] Approvers can open the timesheet details before deciding.
- [ ] Employee names and row details are correct for manager and HR views.
- [ ] Reject opens the reason dialog above the details dialog.
- [ ] Reject success feedback is visible.
- [ ] Rejected rows appear under the appropriate status filter and can be resubmitted.
- [ ] The employee receives the rejection notification.
- [ ] Submitting a rejected timesheet gives a specific, actionable error.

### Evidence to record before completion

| Evidence | Result / link |
|---|---|
| UI browser run by role | Pending |
| GraphQL gateway operation trace | Pending |
| Rust service/resolver verification | Static implementation present; runtime pending |
| Tenant Liquibase status | Pending |
| Database row/state verification | Pending |
| Browser screenshots or recording | Pending |
| Regression test reference | Pending; do not mark complete without this evidence |

## Update protocol

When implementation work is finished, move the module to **QA**. After the complete runtime journey passes, update only that module's row and checklist, add the runtime evidence links, and record the verification date. Do not mark a module complete because another module's UI or backend work is complete.

## Module 5: Employee profile and documents acceptance checklist

### Profile and authorization

- [ ] Self profile resolves from the authenticated user-to-employee link.
- [ ] Directory viewers receive only the safe employee projection; private tabs remain unavailable outside the server-authorized scope.
- [ ] Self-service contact/demographic edits persist and show actionable success/error feedback.
- [ ] Legal name/date-of-birth, PAN, Aadhaar, and bank changes follow the HR review workflow and show pending/approved/rejected state correctly.
- [ ] Profile mutations remain visible after switching tabs or refreshing the profile.
- [ ] HR employment status, role/reporting, and compensation changes persist with the correct scoped authorization.

### Documents and evidence

- [ ] Employee, education evidence, work evidence, and company documents use the same private storage abstraction.
- [ ] S3/R2 is preferred; unavailable object storage falls back to tenant/user-scoped local storage unless fail-closed mode is explicitly configured.
- [ ] Document bytes are returned only through authorized GraphQL attachment reads and converted to a browser Blob; no public storage URL is exposed.
- [ ] Upload validation, preview/download, approval/rejection, and failure feedback work for employee and HR roles.
- [ ] Supporting-document linkage is tenant- and employee-scoped and compensates failed record linkage.
- [ ] Company-document uploads return only an opaque, purpose-bound stage ID; document creation claims that stage atomically before expiry.
- [ ] Failed or abandoned company-document uploads cannot delete or expose storage records owned by another feature.
- [ ] Expired unclaimed company-document stages are swept by the shared worker and their private objects are retried until physical deletion succeeds.
- [ ] Archiving retains the company document and file for audit; permanent deletion atomically removes the record and creates a durable private-file cleanup task.
- [ ] Announcement lists expose only attachment-presence flags; bytes load only after an authorized preview/download action.

### Evidence to record before completion

| Evidence | Result / link |
|---|---|
| Self-service browser run | Pending |
| HR/admin browser run | Pending |
| GraphQL gateway operation trace | Pending |
| Rust resolver/service verification | Static implementation present; runtime pending |
| Tenant Liquibase status | Pending |
| Local and S3/R2 storage smoke test | Pending |
| Private attachment authorization test | Pending |

## Module 10: Asset Management acceptance checklist

Implementation status: **QA**. The React workspace, authored GraphQL operations, Rust lifecycle service/resolvers, and Liquibase migrations are present. Generated GraphQL output and runtime evidence must be refreshed before this module can be **Complete**.

### Manager lifecycle

- [ ] Create and edit an asset category; duplicate normalized codes show actionable conflict feedback (category names may repeat).
- [ ] Create and edit an available asset with category, tag, serial number, value, date, and location.
- [ ] Inventory search, category/status filters, paging, and retained-row error behavior work.
- [ ] Search available assets and assign one to an active employee, including employees beyond the first result page.
- [ ] A second or concurrent assignment of the same asset is rejected without corrupting state.
- [ ] Record a return with return date, condition, and remarks; the asset becomes available again.
- [ ] Active assignments and returned history show employee and asset labels instead of raw IDs.
- [ ] Retiring an assigned asset is rejected; retiring an available asset preserves its history.
- [ ] Retiring a category with non-retired assets is rejected; an empty category can be retired.
- [ ] A successful mutation followed by a refresh failure closes the form, retains rows, and warns against repeating the action.

### Employee and security boundaries

- [ ] An `assets:self` user sees only their own active and returned assignments.
- [ ] An `assets:read` user can inspect inventory and history but cannot see mutation actions.
- [ ] Category, asset, assignment, return, and retirement mutations require `assets:manage` server-side.
- [ ] Cross-tenant category, asset, employee, and allocation identifiers are rejected.
- [ ] Purchase value is not shown in employee self-service views.

### Validation and evidence

- [ ] Required category, asset, employee, and allocation fields show inline validation.
- [ ] Negative purchase values and invalid allocation/return date ordering are rejected in UI and service.
- [ ] Tenant migrations `0057_asset_management_lifecycle`, `0058_asset_management_integrity`, `0059_file_upload_stage`, and `0060_private_file_cleanup` are applied successfully in order.

| Evidence | Result / link |
|---|---|
| Focused TypeScript asset workspace check | Pending rerun after review remediation |
| GraphQL code generation | Pending regeneration after final schema changes |
| Validation unit test | Pending user run |
| Manager browser lifecycle | Pending |
| Employee self-service browser run | Pending |
| Read-only role browser run | Pending |
| GraphQL gateway operation trace | Pending |
| Tenant Liquibase status | Pending |
| Database state-transition verification | Pending |
| Screenshots or recording | Pending |
