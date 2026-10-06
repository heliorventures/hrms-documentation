# Company-wide payslip templates

Date: 2026-10-06

## Approved intent

The company administrator selects a payslip template that applies to every employee in that company. Provide Existing Format and Table Format, with the latter following the supplied client's table arrangement. Both formats render existing application data. Unnecessary sample fields, including tax regime, may be omitted. There is no employee preference or override.

Reference: `ClientDocumenation/Pay Slip_Z12253_Jul-24.pdf`. Its one-page A4 layout has a company header, employee details grid, side-by-side earnings and deductions, totals, net pay and a separate days table. The reference provides layout guidance; its employee information, payroll amounts and company identity are not template defaults.

## Verified source context

- `hrms-ui/src/modules/payroll/components/PayslipDocument.tsx` coordinates preview, print and PDF download.
- `PayslipSheet.tsx` renders browser and print output. `utils/payslipPdfLayout.ts` renders the downloaded PDF separately.
- Company header and logo already come from `payroll_compliance_setting`.
- `hrms-svc/crates/kabipay-payroll/src/services/payslip_presentation.rs` supplies company-controlled display lines and existing settlement information.
- Existing company-setting writes use `require_payroll_manage_all`; payslip reads retain their employee-scope restrictions.

## Template setting

Persist one template identifier per company using the existing tenant payroll-setting infrastructure. Stable identifiers are `EXISTING` and `TABLE`. Existing companies without a selection retain Existing Format.

Expose the selection alongside company payslip branding with a preview of each format. Save through the existing company payroll-management authorization. Employees can see payslips in the selected format but cannot change the selection.

Reject unsupported identifiers on writes. Older API clients that omit the template field must preserve the saved selection. Loading or saving failures must remain visible; a failed settings read must not silently render a different company template.

The setting controls rendering when a payslip is opened, printed or downloaded, including existing payslips. It does not regenerate payroll records or replace previously downloaded files.

## Shared rendering contract

Resolve the company template once for each displayed payslip and pass that identifier to browser/print and PDF renderers. All employee and administrator payslip entry points must use it. Templates consume the same authorized presentation lines, totals, branding and settlement data.

Use a small typed template registry so another built-in layout can be added without introducing template selection logic into every entry point. Template definitions are application code; this feature does not include an arbitrary HTML editor or user-uploaded templates.

## Existing Format

Preserve the current arrangement and its displayed payroll information. Route it through the shared template-selection contract.

## Table Format

- Company name and configured logo at the top, followed by the pay period.
- A compact employee-details grid using existing authorized fields, starting with employee name and code; show available UAN and ESIC information consistently in preview, print and PDF.
- Earnings and deductions in adjacent tables with description and amount columns. Group by existing component types and preserve existing company component-visibility decisions.
- Existing gross, deduction and net-pay totals beneath the component tables. Never recompute totals from visible rows, because company settings can hide components.
- Existing unpaid-leave and settlement information where supplied, including advance already paid and remaining payable. The new arrangement must not discard information available in Existing Format.
- Keep the document readable on A4 and on smaller screens. Handle long names, uneven component counts and overflow onto additional pages without overlapping totals or losing rows.

Use fields already supplied by the existing payslip flow. Additional existing application fields may be mapped through authorized reads during implementation. Do not add payroll calculations, invent missing values or copy formulas from the reference PDF. Omit tax regime and sample-only fields. YTD columns and the sample's arrear/LOPR/day categories appear only if existing application values and meanings are already available; do not introduce those calculations to reproduce the sample.

## Boundaries and security

The change adds company template persistence and rendering. It preserves salary amounts, payroll processing, employer-contribution visibility and access scopes. No employee-specific settings, bulk payroll regeneration, live migration execution or deployment is included.

Previews must use neutral example data or an already authorized payslip. They must not embed the reference employee's personal information. Use the existing signed-logo flow and normal escaped text rendering.

## Acceptance and validation

1. A company admin can preview and save either template; the selection survives reload.
2. Every employee and administrator payslip view in that company uses the saved selection; another company's setting remains independent.
3. Employees cannot change the company selection, and existing payslip read scopes remain enforced.
4. Preview, print and downloaded PDF use the same selected layout, visible components, totals and settlement information.
5. An unset company retains Existing Format; unsupported writes fail; omitted fields from older clients preserve the saved value.
6. Table Format handles missing optional fields, empty or uneven component lists, long descriptions and page overflow.
7. Selecting a template does not change persisted payroll amounts or calculations.

Use focused persistence/authorization and rendering tests for these behaviors. The user owns test, lint, typecheck and build execution unless explicitly delegated. Supply exact RTK-prefixed commands in the implementation handoff. Browser and PDF visual checks are separate from static source review.

## Delivery constraints

Preserve unrelated worktree changes. Do not auto-commit, deploy, run live migrations or execute Dart/Flutter commands. Obtain approval before token-expensive implementation work. This specification records the approved intent and the concrete proposed integration for written review before implementation planning.
