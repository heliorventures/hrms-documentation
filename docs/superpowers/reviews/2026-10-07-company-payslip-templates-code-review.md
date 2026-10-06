# Company payslip templates: requested code review

## Result

The independent reviewer found one Important issue: payslip output could silently omit configured company branding when company-setting or signed-logo requests were pending or failed. The issue was fixed, and the reviewer confirmed the revised source resolves it. No outstanding Critical, Important, or Minor findings were identified in the reviewed scope. Nothing was declined as outside the specification.

This is approval of the reviewed source, subject to verification and the existing release blockers below. It is not authenticated runtime, migration, or deployment acceptance.

## Reviewed snapshot

The reviewed head includes uncommitted changes and new files relative to:

- `hrms-ui`: `6995b5b9a518699fd04589054864479fd82585c7`
- `hrms-svc`: `0d8129fcce074c8d09bc32e29b81db13a1e64e82`
- `hrms-database`: `aa13c5d52417afe0b2dcf0c31030cda5282c2429`

Scope: company-wide template persistence and authorization, settings code generation, selector/neutral preview, employee and managed payslip flows, browser/print/PDF routing, company branding, component visibility and persisted totals, pagination, and migration/release ordering. Unrelated service changes and migrations 0096–0098 were preserved.

The implementation preserves omitted template updates, rejects unsupported identifiers, propagates settings-read failures, and filters company reads by tenant. Both formats consume existing authorized presentation rows and supplied totals. The generated settings contract and Table PDF row splitting/repeated headings are consistent with the approved design.

## Important finding and resolution

**Trigger:** presentation and calculation details finished loading before the separate company-settings or signed-logo request, or that branding request failed. A settings-save refresh recreated this window. Employee output could use the fallback tenant name or omit a configured logo; managed output could omit the logo. The failure was hidden.

**Resolution:**

- `usePayslipBranding.ts` exposes settings/URL readiness, error, and retry. A successful absent settings row or no configured logo remains valid.
- `usePayslipLogo.ts` centralizes guarded signed-logo loading and retry for both employee and managed views.
- `EmployeePayslipPanel.tsx` propagates branding state. `EmployeePayslipDetails.tsx` shows errors/retry and includes branding in the existing output-readiness gate.
- `ManagedPayslips.tsx` gates output on logo readiness and includes lookup failures in its existing visible retry flow.
- The employee details/status section is separated from period navigation; selected period, identity, presentation rows, and unpaid-leave behavior are preserved.

The follow-up reviewer read these deltas and the regression cases and found the original finding resolved with no additional material defects. The reviewer made no edits and ran no tests/builds.

## Verification after the fix

Four employee branding/readiness regression cases failed before implementation, demonstrating the missing loading/error/retry handling. After implementation, the initial affected run passed 16 tests across five files.

The expanded focused suite contains 39 cases across 11 files. Its final broad run passed 38 cases; the new managed retry case had an incorrect assertion expecting the raw exception rather than the application's sanitized user message. That assertion was corrected while retaining checks for visible failure, blocked output, and successful retry. The managed rerun then passed all three tests, validating all 39 focused cases across the final runs.

Targeted ESLint passed for the nine files implementing/testing the review fix, with unused-disable reporting enabled. The separately checked tab retains only the pre-existing complexity finding described below.

TypeScript was rerun after correcting the new test's mock return type. Only the four previously reported errors outside this feature remain: two request-mock tuple errors in `EmployeeUanCard.test.tsx`, the missing `EmployeePrivateProfileQuery` name in `mapBundleToModel.ts`, and unsupported `replaceAll` in `ClaimTravelReportFilters.tsx`.

The affected employee tab's pre-existing complexity finding is reduced from 25 at HEAD to 17. Its import/format issues were corrected and its document/status section extracted. The existing board-action length/complexity findings remain. No lint suppression was added for this review fix.

`rtk git diff --check` passed for the UI changes. Backend and migration source were not changed by this review fix, so their previously recorded verification was not rerun.

## Remaining release limits

The wider UI build remains blocked by the four unrelated TypeScript errors. The previously reported two payroll authorization-page expectation failures also remain outside this fix. Tenant migration, authenticated admin/employee/managed flows, print/download browser acceptance, and deployment are pending. Changes remain uncommitted.

See [implementation handoff](2026-10-06-company-payslip-templates-handoff.md) for the migration and release sequence.
