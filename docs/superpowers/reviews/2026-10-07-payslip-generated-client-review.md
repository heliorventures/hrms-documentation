# Payslip generated client and production readiness review

## Result

The payslip UI now consumes the main generated GraphQL documents and inferred operation types. Independent backend/UI review has no outstanding Critical, Important, or Minor source findings in the company-template scope. Production acceptance remains conditional on tenant migration and authenticated admin/employee/managed browser checks. Changes remain uncommitted; no migration or deployment was performed.

## Changes and review

Eight existing presentation, unpaid-leave, component-visibility, and managed-payslip operations now live in `hrms-ui/src/api/documents/payslipOperations.graphql`, preserving selections and limits. Hooks/components import their documents from the main generated client. Settings, save input, and signed-logo reads use that client too. The isolated payroll-settings generator/client and package command were retired. Future updates use `rtk npm run codegen`; generated files were regenerated without manual edits.

Generated settlement JSON is decoded against the eleven fields emitted by the service's `CalculatedPeriod` writer. An absent historical statement remains valid; malformed data exposes an error and blocks output. Unpaid-leave policy decoding preserves the domain treatment union.

**Important finding resolved:** hiding a salary component updated its checkbox but left a retained payslip/PDF using the previous rows. Successful visibility writes now dispatch the shared refresh to reload mounted authorized presentations. Company switches/unmounts suppress stale write results; duplicate writes are blocked; rejected writes retain saved state.

**Minor finding resolved:** effect restarts could accept a superseded component read. An effect-local active flag now invalidates both outcomes. The reviewer verified both fixes and the regression tests; the reviewer ran no checks.

Backend review confirmed tenant/employee-scoped presentation reads; tenant-scoped settings/logo/snapshot lookup; company-wide payroll-management permission for writes; supported-template validation; preservation of omitted template updates; and propagation of database/read errors. Existing calculations, totals, and employer/component filtering are unchanged. The decoder matches the production statement writer; partial historical/manual JSON has no guaranteed contract and is rejected. The earlier branding-readiness/retry fix remains in place.

Four existing build errors were corrected in two UAN test assertions, a missing generated employee-profile type import, and an ES2020-incompatible report label method. Other concurrent edits were preserved.

## Verification

- `rtk npm run codegen`: passed against the configured gateway.
- Read-only gateway introspection: HTTP 200; settings/presentation template fields present and non-null, mutation template input optional, settlement scalar JSON, and settings/presentation/unpaid-leave/logo queries present. This is schema evidence only.
- Main generated-client/template suite: 48 tests passed across 13 files.
- Component lifecycle suite: four passed. The stale-presentation/company-switch cases failed before implementation and passed afterward; added cases cover superseded reads and rejected writes.
- UAN tests: seven passed. Report filters: two passed. Payroll workspace/board authorization: seven passed. Total: 68 unique tests across 18 files.
- Scope-wide ESLint checked 50 payroll files: only three prior findings remain (employee tab complexity 17, board-action length 145, cycle-creation complexity 13). Final focused lifecycle/component/decoder lint passed; no new suppression added.
- Final `rtk npm run build`: passed (TypeScript and Vite production bundle). Existing non-blocking Browserslist-age and large-chunk warnings remain.
- UI/service/database `rtk git diff --check`: passed.
- Backend source was unchanged in this follow-up. Earlier template tests passed eight and the library run reported 50; these were not rerun for UI-only changes.

Concurrent changes to codegen configuration and unrelated UI files produced intermediate type-check failures. The final build result is recorded separately above.

## Release requirements

Apply migration 0099 to intended tenant schemas before dependent service/gateway/UI release. Verify admin preview/save/reload, isolation/permissions, employee and managed output, both print/PDF formats, configured/removed logos, and visibility changes with an already-open payslip. Local UI ports 5173/4173 were unavailable, so authenticated browser acceptance was not exercised. The two previously reported compensation/tax navigation expectation failures were outside this follow-up.

Rollback must remove dependent UI/service use before dropping the column, which discards company selections. See [implementation handoff](2026-10-06-company-payslip-templates-handoff.md) for release ordering and prior layout/PDF evidence.
