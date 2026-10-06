# Company-wide Payslip Templates Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans for native execution, or superpowers:subagent-driven-development if the user selects delegation. Steps use checkbox syntax for tracking.

**Goal:** Let the company admin select Existing Format or Table Format for every employee's payslip preview, print and PDF download.

**Architecture:** Persist `EXISTING` or `TABLE` in the existing company payroll-compliance setting. Return the effective identifier with the authorized payslip presentation response so every document entry point shares one selection. Use focused browser and PDF template renderers that consume the same existing payroll data.

**Tech Stack:** React 18, TypeScript, jsPDF 4, Rust, async-graphql, SeaORM, PostgreSQL, Liquibase, Vitest.

**Spec:** [Approved design](../specs/2026-10-06-company-payslip-templates-design.md).

## Global Constraints

- The company administrator selects a payslip template that applies to every employee in that company.
- Stable identifiers are `EXISTING` and `TABLE`.
- There is no employee preference or override.
- Both formats render existing application data.
- Omit tax regime and sample-only fields.
- Preserve existing company component-visibility decisions, persisted totals, settlement information and access scopes.
- Preserve unrelated worktree changes. Do not auto-commit, deploy, run live migrations or execute Dart/Flutter commands.
- The user owns test, lint, typecheck and build execution unless explicitly delegated.
- Token-expensive implementation approval was requested with the spec and received on 2026-10-06; execution-method selection remains pending.

## Review Focus

- An older settings writer omits the new field: preserve the company's saved selection.
- A settings read fails or returns an unsupported identifier: report failure instead of silently selecting another layout.
- Hidden component rows do not sum to persisted totals: use persisted gross, deductions and net pay.
- Long names and uneven component counts: retain every authorized row and avoid overlapping totals on later PDF pages.
- Employee or tenant context changes: clear stale presentation state and retain existing read authorization.

## Task 1: Persist and expose the company template

**Files:**
- Create `hrms-database/changelog/migrations/0099_company_payslip_template/company_payslip_template.xml`; 0096–0098 were occupied, so implementation uses 0099.
- Modify `hrms-database/changelog/tenant.changelog-master.xml`.
- Modify `hrms-svc/crates/kabipay-db-entities/src/tenant/d0012_payroll.rs`.
- Modify `hrms-svc/crates/kabipay-payroll/src/resolvers/types.rs` and `resolvers/mutation.rs`.
- Modify `hrms-svc/crates/kabipay-payroll/src/services/payroll_service.rs` and `services/payslip_presentation.rs`.
- Create `hrms-svc/crates/kabipay-payroll/src/services/payslip_template.rs`; register it in `services/mod.rs`.

**Interfaces:**
- Persist `payroll_compliance_setting.payslip_template`, non-null, default `EXISTING`, constrained to `EXISTING` or `TABLE`.
- Add `payslipTemplate: String!` to the company-setting output and `payslipTemplate: String` to its update input.
- Add `template: String!` to `PayslipPresentation`.
- Define `resolve_payslip_template(current: Option<&str>, requested: Option<&str>) -> KabiPayResult<String>`: a supported explicit request wins; omitted requests retain the supported current value; absence of both yields `EXISTING`; unsupported values return validation errors.
- Append `payslip_template: Option<String>` to the existing settings service signature; keep omitted updates from overwriting the stored column.

- [x] Add focused resolver/service tests: initial default, both valid identifiers, rejected unknown identifier, omitted update preserves TABLE, tenant isolation and forbidden employee writes.
- [x] Give the user `rtk cargo test -p kabipay-payroll payslip_template` from `hrms-svc`; await output for the initial test stage if tests have not been delegated.
- [x] Add the migration and entity column, then wire the input/output and existing authorized settings write.
- [x] In presentation loading, read the company's template using the same tenant connection; absence of a settings row means EXISTING, while read errors or invalid stored identifiers propagate.
- [x] Keep the existing component filtering and monetary data intact.
- [x] Give the user the focused Rust command again and await results. Migration source inspection is not migration-execution proof.

## Task 2: Add typed template routing and the table document

**Files:**
- Create `hrms-ui/src/modules/payroll/payslipTemplates.ts`.
- Create `hrms-ui/src/modules/payroll/components/PayslipTableSheet.tsx`.
- Create `hrms-ui/src/modules/payroll/utils/payslipTablePdf.ts`.
- Modify `payslipPresentation.ts`, `components/PayslipDocument.tsx`, `components/PayslipSheet.tsx`, `utils/payslipPdf.ts` and `utils/payslipPdfLayout.ts` under the same module.
- Extend `components/PayslipDocument.presentation.test.tsx`; create `components/PayslipDocument.template.test.tsx` and `components/PayslipDocument.template.test.tsx`.

**Interfaces:**
- Export `type PayslipTemplateId = 'EXISTING' | 'TABLE'` and a registry containing `Existing Format` and `Table Format` labels.
- Export `resolvePayslipTemplate(value: string | null | undefined): PayslipTemplateId`; omitted values support existing fixtures/older responses as EXISTING, explicit unknown values fail visibly.
- Export the existing `SheetProps` as a reusable type, or extract it into a focused document-types file if needed.
- `PayslipTableSheet(props: SheetProps)` consumes exactly the existing authorized document inputs.
- `createTablePayslipPdf(branding: PayslipPdfBranding, slip: PdfPayslipPayload): jsPDF` consumes the same data as Existing Format; extend its payload with optional UAN and ESIC values already present in the browser model.
- Existing `createPayslipPdf` dispatches using `slip.presentation.template`; existing callers retain their public signature.

- [x] Add rendering tests for both identifiers, rejected identifiers, company-hidden components, persisted totals differing from visible row sums, missing optional fields, unequal lists and preserved settlement/unpaid-leave details.
- [x] Give the user `rtk npm test -- src/modules/payroll/components/PayslipDocument.presentation.test.tsx src/modules/payroll/components/PayslipDocument.template.test.tsx src/modules/payroll/components/PayslipDocument.template.test.tsx` from `hrms-ui`; await output if execution has not been delegated.
- [x] Add `template` to the presentation GraphQL selection and interface; route both browser/print and PDF through the template registry.
- [x] Implement Table Format: company header, employee grid, adjacent earnings/deduction columns, supplied totals, net pay and existing leave/settlement details. Preserve any other visible component types in a clearly labelled section rather than discarding them.
- [x] Render only available authorized fields; omit empty optional fields and unsupported sample columns. Do not calculate YTD or reference-specific day values.
- [x] Use jsPDF's existing font and wrapping facilities for table rows; paginate with repeated column headers and reserved space for totals/settlement. Do not add a dependency.
- [x] Verify long descriptions, enough rows to span pages, and zero rows. PDF tests should check the actual generated document for row preservation and page count.
- [x] Give the user the focused UI test command and await results.

## Task 3: Add the admin selector and safe previews

**Files:**
- Modify `hrms-ui/src/api/documents/clientOperations.graphql` and `src/api/schema-extensions/payroll-run.graphql`.
- Generate the isolated settings client under `hrms-ui/src/api/payroll-settings/` from the Rust-exported service SDL using `codegen:payroll-settings`; the gateway endpoint was unavailable.
- Modify `hrms-ui/src/modules/payroll/payrollTypes.ts`, `hooks/usePayrollBoard.ts`, `hooks/usePayrollBoardActions.ts` and `components/PayrollComplianceCard.tsx`.
- Create `hrms-ui/src/modules/payroll/components/PayslipTemplateSelector.tsx` and `PayslipTemplateSelector.test.tsx`.
- Create `hrms-ui/src/modules/payroll/payslipTemplatePreview.ts` for neutral example document data.

**Interfaces:**
- Add `payslipTemplateInput: PayslipTemplateId` to the compliance form state and initialize it from the loaded company setting.
- Include `payslipTemplate` in the company-setting query, mutation output and save input.
- `PayslipTemplateSelector({ value, disabled, onChange }: { value: PayslipTemplateId; disabled: boolean; onChange: (value: PayslipTemplateId) => void })` exposes accessible Existing Format and Table Format choices and corresponding neutral previews using the real renderers.

- [x] Add tests for initial company choice, disabled/loading state, changing selection, preview correspondence, saved selection after reload and employee lack of a write control.
- [x] Give the user `rtk npm test -- src/modules/payroll/components/PayslipTemplateSelector.test.tsx src/modules/payroll/hooks/usePayrollComplianceSave.test.tsx` from `hrms-ui`; confirm the actions test path exists at execution time and create it if needed for the save contract.
- [x] Extend schema/documents and regenerate clients without manually altering generated types. Preserve unrelated generated content.
- [x] Add the selector next to company branding and integrate it into the existing save behavior; disable saving while company settings are unavailable.
- [x] Use neutral company/employee preview values, never the reference employee's personal information. Preview choice must not persist until Save succeeds.
- [x] Keep template routing in the presentation response so employee, payroll-hub and managed-payslip entry points require no separate preference state.
- [x] Give the user the focused selector/save tests and await results.

## Task 4: Validate and hand off

**Files:**
- Create `hrms-documentation/docs/superpowers/reviews/2026-10-06-company-payslip-templates-handoff.md`.
- Update this plan's completed checkboxes using actual evidence.

- [x] Review only changed files for company scoping, existing API compatibility, component visibility, stale responses and renderer consistency.
- [x] Execute delegated focused Rust tests, the Rust library suite, focused UI tests, targeted ESLint, TypeScript/build checks, and repository diff checks. Record passing evidence separately from the unrelated workspace failures in the handoff. A separate cargo check was unnecessary after successful compilation and library tests.
- [x] Provide the migration and backend/client schema release ordering in the handoff. Do not execute live migrations or deployment.
- [ ] Once a local application is available, check company admin selection/save/reload, an employee view, managed payslips, print preview and both downloaded PDFs. Use authorized existing data or neutral fixtures.
- [x] Render both PDF outputs locally and inspect ordinary and overflowing documents. Record browser/PDF checks separately from source and automated checks.
- [x] Record remaining user-owned validation, changed repositories, migration requirement and preserved unrelated changes. Do not claim tests or runtime checks passed without output.
- [x] Leave all changes uncommitted for the user's review.

## Execution choice

Native execution in this session is recommended: these tasks share the company template and presentation contracts, and delegation would add repeated context cost. The user must review this plan and select native or delegated execution before product implementation, as required by the writing-plans workflow.

## Execution outcome (2026-10-06)

The user delegated test execution, implementation, review and fixes. Tasks 1–3 are implemented; source/automated/PDF-fixture review is complete. Nine focused UI files now cover 33 tests: the initial final run passed 29, and the two expanded renderer files then passed all 13 tests (four additional cases). Rust template tests passed 8; the library run reported 50 passed. The production UI build remains blocked by four unrelated TypeScript errors. Authenticated acceptance and live migration execution remain pending. See `../reviews/2026-10-06-company-payslip-templates-handoff.md` for precise evidence and release order. Changes are uncommitted.
