# Company payslip templates: implementation handoff

Implemented in `hrms-ui`, `hrms-svc`, and `hrms-database`. Changes remain uncommitted. No live migration or deployment was performed.

## Behaviour

- The company administrator selects **Existing Format** or **Table Format** under payroll company settings. The choice applies to every employee and to historical payslips when reopened, printed, or downloaded.
- Existing companies default to Existing Format. The selector previews neutral example data using the real renderer; previewing does not save.
- Both layouts consume existing authorized presentation rows and persisted totals. Payroll calculations, component visibility, employer contributions, and stored salary amounts are unchanged. Optional available UAN/ESIC values are shown; sample-only fields and tax regime are omitted.
- Browser, print, and downloaded PDF route through the company template identifier. Table PDFs wrap descriptions and repeat headings across pages. Narrow browser screens provide a keyboard-accessible horizontally scrolling component table.
- New layouts can be added to the typed template registry and corresponding PDF routing without creating employee preferences.

## Review and fixes

An independent static review and a focused follow-up found no outstanding Critical or Important findings in this scope. This is not production-runtime certification.

- Company-wide payroll-management permission protects template writes; reads use the existing authorized payslip/tenant context.
- Omitted template updates preserve the stored selection. Unsupported explicit identifiers are rejected. Settings read errors do not silently become a saved default.
- Save is blocked until settings load, for unauthorized users, and while the same owner's save is pending. A completion from an old company cannot update the new company's UI or trigger its reload.
- Saving company settings refreshes mounted payslip presentation and branding. Removed logos clear, and managed payslips retain the selected period when it still exists.
- Unknown templates disable output. Empty/unequal component lists, other authorized component types, hidden rows, settlement details, persisted totals, and long multipage PDFs are covered by focused tests.

## Verification

- Initial UI regression run demonstrated four expected failures before implementation. The branding-refresh regression also failed with the old header before its fix. The initial Rust run overlapped source rebuilding and is not claimed as a clean red-stage result.
- `rtk cargo test -p kabipay-payroll payslip_template`: **8 passed**.
- `rtk cargo test -p kabipay-payroll --lib`: **50 passed**, as reported by RTK.
- Nine focused UI test files: **29 passed**. The two expanded renderer files subsequently passed all **13 tests**, adding four cases for **33 focused tests total**. Those cases cover settlement in both templates and empty/other component data.
- `rtk npm run codegen:payroll-settings`: passed using the actual Rust-exported payroll SDL. The main gateway was unavailable at localhost:4009; the isolated generated client follows the repository's existing service-client pattern.
- Targeted lint across 35 changed payroll files exposed two existing findings in `usePayrollBoardActions.ts`: function length and cycle-creation complexity. Checking the committed version confirmed both already existed. New-feature lint findings were corrected; the scroll region has an explained keyboard-access exception.
- `rtk git diff --check`: passed in the three implementation repositories.
- New migration and tenant changelog XML parse successfully. No database execution was used to validate migration behaviour.
- Neutral Existing and Table PDFs were generated and inspected. A 90-row long-description Table PDF spans seven pages; first/last pages were inspected and all extracted words stayed within page bounds.
- Isolated headless Edge rendered the neutral Table browser fixture at desktop and mobile sizes. At a measured 390px viewport, document/body widths were also 390px. This is fixture-level visual verification, not an authenticated application test.

## Wider workspace blockers

`rtk proxy npx tsc --noEmit` and `rtk npm run build` both fail before Vite packaging on four errors outside this feature:

1. `EmployeeUanCard.test.tsx:47` and `:121`: request mock tuple has no element at index 1.
2. `employee-profile/lib/mapBundleToModel.ts:209`: missing `EmployeePrivateProfileQuery` name.
3. `reports/ClaimTravelReportFilters.tsx:34`: `replaceAll` is unavailable under the configured TypeScript library target.

The wider payroll test run also has two failures in `PayrollAuthorizationPages.test.tsx`: it expects the former Employee Tax & History tab role and the former Salary Structure Template text. These refer to existing workspace navigation changes outside this task. No payslip-focused test failed in the final focused run. Unrelated analytics, expense, calendar/leave migrations, and UI-review work was preserved.

## Release order and remaining acceptance

1. Resolve the wider workspace build blockers before producing the UI release.
2. Apply tenant migration `0099_company_payslip_template/company_payslip_template.xml` to the intended tenant schemas through the normal reviewed migration process. Slots 0096–0098 were already occupied and were preserved.
3. Release the payroll service exposing `PayrollComplianceSetting.payslipTemplate`, its optional mutation input, and `PayslipPresentation.template`. Refresh/compose the gateway schema as required by the normal release process.
4. Release the matching UI. Do not deploy this UI before the API exposes its new selected fields. Older clients can omit the optional input without overwriting the choice.
5. In a running migrated environment, verify admin preview/save/reload, both employee and managed payslip views, company isolation, browser print pagination, both downloaded PDFs, configured logo behaviour, and refresh-time output buttons. The local application/gateway was unavailable, so this authenticated acceptance remains pending.

For rollback, remove dependent UI/service use before dropping the database column. Rollback discards the selected template value and must follow the normal reviewed release process.

## Focused rerun commands

From `hrms-svc`:

```powershell
rtk cargo test -p kabipay-payroll payslip_template
rtk cargo test -p kabipay-payroll --lib
```

From `hrms-ui`:

```powershell
rtk npm run codegen
rtk npm test -- src/modules/payroll/components/PayslipDocument.template.test.tsx src/modules/payroll/components/PayslipDocument.presentation.test.tsx src/modules/payroll/components/PayslipTemplateSelector.test.tsx src/modules/payroll/components/ManagedPayslips.test.tsx src/modules/payroll/hooks/usePayrollTemplateSettings.test.tsx src/modules/payroll/hooks/usePayslipPresentation.template.test.tsx src/modules/payroll/hooks/usePayslipBranding.template.test.tsx src/modules/payroll/hooks/usePayrollComplianceSave.test.tsx src/modules/payroll/hooks/usePayrollPayData.authorization.test.tsx
rtk npm run build
```

Use `rtk git diff --check` in each changed repository before committing manually.

## Requested follow-up review: 2026-10-07

The user explicitly requested the requesting-code-review workflow. A fresh independent source review found one Important issue: pending or failed branding/URL reads could silently omit company branding in employee or managed output. The root cause was corrected by propagating branding readiness/error/retry into the output gate through shared branding/logo hooks. The reviewer confirmed the fix and reported no additional material findings.

Final focused coverage is now 39 cases across 11 files. The broad run passed 38; one new managed assertion was corrected to expect the application's sanitized error message, and all three managed tests then passed. Targeted lint passed for the nine review-fix files. The employee tab's existing complexity finding fell from 25 to 17; the old board-action lint findings remain. Fresh TypeScript checking reports only the same four unrelated errors documented above. No service/migration changes, commit, or deployment were made in this follow-up.

See [requested code-review report](2026-10-07-company-payslip-templates-code-review.md) for the finding, resolution, and exact review limits.

## Main generated-client follow-up: 2026-10-07

The main gateway client now supplies payslip/settings/logo/unpaid-leave/component/managed-view documents and types. Eight operations are centralized in `src/api/documents/payslipOperations.graphql`; the isolated settings generator/client was retired. Future generation uses `rtk npm run codegen`. The running gateway exposes the required fields, superseding the earlier offline-gateway limitation.

Review resolved presentation invalidation after component-visibility writes and a superseded-read lifecycle issue. No source findings remain. The four earlier build errors were corrected. Current checks cover 68 unique passing tests across 18 files; the prior three payroll lint findings remain. See [generated-client readiness review](2026-10-07-payslip-generated-client-review.md) for final build/schema evidence and migration/authenticated acceptance requirements.
