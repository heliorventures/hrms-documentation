# Payroll Tax Projections and Draft Cycles Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. The user previously selected native execution in the current checkouts; preserve that method. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver configurable future payroll, honest annual tax projections and repeatable draft calculations while preserving imported September amounts and locked history.

**Architecture:** Expose pure tax calculations from the existing tax crate, use shared tenant-scoped repositories for settings/history, and orchestrate them from payroll without circular crate dependencies. Separate draft calculation snapshots from final financial records. Keep Solvian raw-file conventions in its converter and use the standard importer for normalized data.

**Tech Stack:** Rust, SeaORM, async-graphql, PostgreSQL/Liquibase, Python XLSX conversion, React/TypeScript/Vitest and Pencil `.pen` designs.

**Spec:** [Approved design](../specs/2026-10-04-payroll-tax-projections-and-draft-cycles-design.md).

## Global Constraints

- September 2026 reproduces the reviewed Excel amounts; Solvian's automatic mode begins October 2026 through configuration, not a tenant/date branch in calculators.
- Tax years run April–March. A May joiner projects through March, not the next April.
- 'Earlier TDS remains Not provided; do not substitute zero or estimated deductions into an actual-history field.'
- 'No UI wording such as tax paid, paid to government or tax remitted.' Use projections and recorded payroll deductions consistently, including exports and tours.
- Flat-percentage and custom contribution overrides require an HR reason and effective period; percentage basis does not redefine statutory taxability.
- 'Draft calculations can be repeated. Finalized/locked cycles cannot be recalculated or edited.'
- 'Projected amounts never populate recorded deduction history.' Missing optional import sections remain independently reportable.
- Company-level slip visibility remains presentation-only. Advances remain settlement, outside salary components and deduction totals.
- Update `hrms-ui/designs/ui-review.pen` and relevant tours with each UI deliverable. Preserve unrelated frames, existing tokens/components, and tenant/user tour state. Tours must not calculate, finalize, save or submit data.
- Use existing tenant/employee authorization scopes. Employee declarations cannot control authoritative TDS results.
- Work in current checkouts; inspect dirty state before edits and preserve other work. No automatic staging/commits, live operations, deployment, network code generation or Dart/Flutter commands.
- Prefix shell commands with `rtk`. Use existing focused local validation delegation; separate disposable/synthetic checks from live acceptance.
- Keep files cohesive; split new financial logic from large legacy services. Do not introduce a second payroll engine or arbitrary executable formula language.
- Native implementation is followed by one independent final review. If Astra is used, first use a dedicated GPT-6.1 Sol summarizer for execution evidence and pass only relevant AST/targeted source. Do not spawn agents for this planning self-review.

## Review Focus

1. Opening totals partially overlap September imports: reject/deduplicate overlap rather than increasing earnings or TDS twice (Tasks 3, 4, 6).
2. A declaration save or later proof approval races with a reviewed payroll draft: preserve HR results and invalidate stale finalization (Tasks 3, 7).
3. Join/exit midmonth, salary revision, March/April boundary or leap February: respect effective dates and company proration, with no future-year leakage (Tasks 4, 5).
4. Two finalizers run concurrently, or inputs change while finalizing: exactly one financial outcome, all-or-nothing allocations, stable retry behavior (Task 7).
5. Tenant/employee changes while UI requests are pending, or a tour runs with restricted access: no stale financial exposure or business mutation (Tasks 8–10).

## File and dependency map

Paths below are relative to `D:/work/heliorventures`. New directories/files are explicitly marked in tasks. Existing module registries, crate dependencies and tenant changelog include files must be updated together with their owned deliverable.

- `hrms-database/scripts/tenant_specific/solvian/imports/`: source conventions only.
- `hrms-svc/crates/kabipay-tax/src/domain/` (new): shared DTOs and pure tax-year/projection/rate calculations.
- `hrms-svc/crates/kabipay-tax/src/services/`: settings, declaration and opening-history repositories; no dependency on payroll crate.
- `hrms-svc/crates/kabipay-payroll/src/services/`: contribution calculation, draft preparation and atomic finalization. This crate may depend on tax's new library.
- `hrms-svc/crates/kabipay-tenant-import/src/`: calls the same settings/history services, with existing savepoint/report/replay behavior.
- `hrms-database/changelog/migrations/0093_tax_projection_configuration/` and `0094_payroll_draft_calculation/` (new): tenant migrations and matching entity companions. Recheck number availability immediately before implementation.
- `hrms-ui/src/modules/payroll/`: HR settings, draft review, employee projections and statement presentation, using existing common UI components.
- `hrms-ui/designs/ui-review.pen`: update existing frames `b4ghOM` (Payroll Processing), `XMmPw` (Tax Settings), `b2PC0` (Salary Setup), and `u4G7K` (Payslips & Tax); add adjacent state frames only where needed.
- `hrms-ui/src/modules/payroll/guidance/`: the four existing payroll tours; tests live in `hrms-ui/src/guidance/payrollExpenseTours.test.tsx`.

## Task 1: Normalize the confirmed Solvian leave conventions

**Files:** Modify `hrms-database/scripts/tenant_specific/solvian/imports/solvian_salary_leave.py`, `solvian_profile.py` and `hrms-database/tests/tenant_specific/solvian/unit/test_converter.py`. Keep standard importer leave validation unchanged unless a normalized contract defect is demonstrated.

**Interfaces:** Preserve `leave_snapshot(row, options) -> (leave_opening, historical_lwp)` and the existing version-1 normalized shape. Produce explicit zero values, normalized usage and source-convention issue codes, retaining original states/references.

- [x] Add regression tests: `all_blank_leave_is_zero` asserts all paid values zero; `negative_taken_without_entitlement_is_historical_lwp` asserts 7.5 unpaid/zero paid; `positive_taken_with_zero_balance_is_lwp` asserts 6 unpaid; `blank_opening_reconciles_grant` asserts opening 0, grant 5, used 2, remaining 3. Preserve unknown pending/planned statuses and a genuine unrelated contradiction as deferred.
- [x] Run `rtk proxy py -3 -m unittest discover -s tests/tenant_specific/solvian/unit -p test_converter.py` from `hrms-database`; observe behavioral failures before changing conversion logic.
- [x] Implement the confirmed normalizations, log each blank/sign convention once, and derive historical usage without generating dated leave requests or payroll deductions. Bump the Solvian conversion-profile revision so new interpretations have distinct provenance.
- [x] Run the same tests to PASS. Convert only the two exact original workbooks into new private local output directories; do not overwrite earlier evidence. Verify all 15 previously flagged conventions reconcile and report any remaining exception without guessing.

## Task 2: Define reusable tax/rule contracts and tenant storage

**Files:** Create `hrms-svc/crates/kabipay-tax/src/lib.rs`, `src/domain/mod.rs`, `src/domain/contracts.rs`, `src/domain/settings.rs`, `src/domain/history.rs`; wire `src/main.rs` to shared modules. Create `hrms-database/changelog/migrations/0093_tax_projection_configuration/tax_projection_configuration.xml` and `hrms-svc/crates/kabipay-db-entities/src/tenant/d0093_tax_projection_configuration.rs`; modify `tenant.changelog-master.xml` and entity `mod.rs`. Create `hrms-svc/crates/kabipay-tax/tests/configuration_contract.rs`.

**Interfaces:** Export `TaxRegime { Old, New }`, `WithholdingMethod { AnnualProjection, PercentageOverride }`, `EvidenceKind { ImportedActual, FinalizedPayroll, HistoricalEstimate, FutureProjection }`, `CoverageStatus { Complete, Incomplete }`, `TaxSettingsInput`, `TaxSettings`, `TaxHistoryEntry`, `TaxProjectionInput` and `TaxProjection`. Use `Decimal` for arithmetic and explicit decimal strings at transport boundaries. Missing historical TDS is `Option<Decimal>`, not a numeric default.

`TaxSettingsInput` contains regime, method, optional fractional percentage, selected component codes, effective date, optional end date and required override reason. `TaxHistoryEntry` contains employee, FY, inclusive covered period, employer/source identity, actual earnings/components, optional TDS, completeness, source key and reason/provenance. `TaxProjectionInput` contains tax-year rules, dated earnings/assignments, declaration inputs, verified deductions and coverage. `TaxProjection` contains month evidence, annual amounts, selected withholding, completeness, optional remaining withholding and limitations.

- [x] Add tests that preserve `None` vs zero TDS, reject an override without a reason/rate/basis, reject invalid rates/dates and retain an explicit zero confirmed deduction.
- [ ] Run `rtk proxy cargo test -p kabipay-tax --test configuration_contract --offline` from `hrms-svc`; record RED, then implement the shared typed contracts and wire the library without duplicate binary module compilation.
- [x] Add append-only versions/audits for company calculation rules and employee tax settings, a separate declaration record, and versioned opening-history entries. Enforce tenant/employee ownership, stable source keys and coverage bounds; use database locks for overlap checks that span multiple history rows. Do not invent historical declarations or deductions from old aggregate computation fields.
- [ ] Add disposable migration tests in `hrms-database/tests/integration/payroll/tax-projection-storage.integration.cjs` using the established local-only fixture helper pattern. Repeated migration must succeed; cross-tenant references, overlapping history and invalid revisions must fail. Run only against an explicitly created synthetic loopback database.
- [x] Run the contract test to PASS and validate the migration/entity mapping. Record migration number and exact schema contracts for dependent tasks.

## Task 3: Separate declarations from HR-controlled settings and opening history

**Files:** Create `kabipay-tax/src/services/tax_settings.rs`, `tax_history.rs`, `tax_declarations.rs`; modify existing `tax_service.rs`, service registry, and tax resolver `query.rs`, `mutation.rs`, `types.rs`. Create `kabipay-tax/tests/settings_authorization.rs`, `history_coverage.rs`, `declaration_isolation.rs`.

**Interfaces:** `save_tax_settings<C: ConnectionTrait>(db: &C, tenant: Uuid, actor: Uuid, employee: Uuid, input: TaxSettingsInput, expected_revision: Option<i32>) -> KabiPayResult<TaxSettings>`; `save_tax_history<C: ConnectionTrait>(db: &C, tenant: Uuid, actor: Uuid, employee: Uuid, entry: TaxHistoryEntry, expected_revision: Option<i32>) -> KabiPayResult<TaxHistoryEntry>`. Loaders take tenant, employee, FY and as-of date explicitly. Resolvers use existing `tax:manage:ALL` for settings/history and existing self-submit scope for declarations.

- [ ] Write tests: self declaration/proof changes leave computed TDS unchanged; direct self API attempts to set calculated fields fail; HR cannot affect another tenant; stale settings/history revisions fail; duplicate history source keys replay unchanged; overlapping September coverage is rejected.
- [ ] Run `rtk proxy cargo test -p kabipay-tax --test settings_authorization --test history_coverage --test declaration_isolation --offline`; establish RED.
- [x] Route declaration writes and approved-proof totals into declaration state only. Keep a compatibility adapter for the old declaration mutation, rejecting supplied calculated fields while accepting old clients' omitted/null calculated fields without clearing HR results. Add scoped HR settings/history APIs and server-owned projection DTOs.
- [x] Keep computed results separate from editable inputs. Ensure effective-dated changes cannot mutate an existing locked statement. Return clear scope/revision/coverage errors; preserve all source and actor metadata.
- [ ] Run the tests to PASS. Add service GraphQL contract coverage to `kabipay-tenant-import/tests/api_contract.rs` for new input/output documents without requiring a live gateway.

## Task 4: Implement pure financial-year tax projection and allocation

**Files:** Create `kabipay-tax/src/domain/tax_year.rs`, `projection.rs`, `income_tax.rs`, `withholding.rs`, `tax_rules_india.rs`; create `src/services/tax_projection.rs`. Create `kabipay-tax/tests/tax_projection.rs`, `india_tax_rules.rs`, `withholding.rs`; modify domain/service registries.

**Interfaces:** `calculate_projection(input: &TaxProjectionInput) -> KabiPayResult<TaxProjection>`; `load_projection_input<C: ConnectionTrait>(db: &C, tenant: Uuid, employee: Uuid, year: i32, month: u32) -> KabiPayResult<TaxProjectionInput>`. `year` is the fiscal start year in the projection contract; month inputs are calendar periods where named as such. Do not infer tax credits from estimated earnings.

- [ ] Test May 2026 join through March 2027 (11 employment months), pre-2026 join (12), midmonth join/exit, a salary revision, leap February and March/April boundaries. Assert imported September actuals replace that month's estimate and never add a second copy.
- [ ] Test incomplete history: earlier TDS `None`, remaining liability `None`, annual estimate divided by eligible payroll months as provisional monthly TDS, and explicit HR acknowledgement required for payroll use. Test complete-history allocation using Rs.621363 minus Rs.252400 over seven months equals Rs.52709; separate display rounding from legally prescribed rounding tests.
- [ ] Test current tax-year slab boundaries, standard deduction, rebate eligibility/limits, surcharge/marginal relief, permitted old/new deductions, optional previous-employer income and confirmed prior withholding. Test over-withholding produces an HR-review state without a fabricated refund. A percentage basis excluding incentive must not exclude that incentive from statutory taxable earnings.
- [ ] Run `rtk proxy cargo test -p kabipay-tax --test tax_projection --test india_tax_rules --test withholding --offline`; establish RED, implement the pure functions and typed date/evidence loader, then obtain PASS.
- [ ] Verify FY 2026-27 rules against the approved design's primary sources and applicable notifications at implementation time. Persist rule version/source and implement independently checked statutory rounding. Unsupported tax cases return explicit limitations/manual-review requirements rather than an approximate legal result.

## Task 5: Add reusable contribution formulas and automatic period calculation

**Files:** Create `kabipay-payroll/src/services/contribution_rules.rs`, `contribution_calculation.rs`, `automatic_payroll.rs`; modify `salary_rules.rs`, `payroll_rules.rs`, `payroll_period_input.rs`, `imported_payroll.rs`, module registry and `Cargo.toml` to depend on `kabipay-tax` by path. Create `tests/contribution_calculation.rs`, `tests/automatic_payroll.rs`.

**Interfaces:** Define `ContributionPolicy`, `ContributionInput` and `ContributionResult` in `contribution_rules.rs`; `calculate_contributions(input: &ContributionInput, policy: &ContributionPolicy) -> KabiPayResult<ContributionResult>`. Define `PreparedEmployeePayroll` and `EmployeePayrollInput` in `automatic_payroll.rs`; `calculate_employee_payroll(input: &EmployeePayrollInput) -> KabiPayResult<PreparedEmployeePayroll>`. Inputs include tax projection, earnings/proration, explicit deductions/overrides, contribution policy and settlement. Outputs include components, statutory amounts, tax evidence/acknowledgement needs, LWP and settlement.

- [ ] Add tests for source-preserved September, configured automatic October, exact percentage basis, reason-required overrides, 31-divisor LWP, an effective-date boundary and advances excluded from earnings/deductions. Missing eligibility must not use the global stub.
- [ ] Test ESI component inclusion/exclusion and the 50% add-back, eligibility separately from reduced actual month wages, contribution-period continuation, employee-share exemption, employer share and applicable rounding. Pin the verified standard rates (employee 0.75%, employer 3.25%) and Rs.21000 wage ceiling to versioned rule fixtures; verify applicable disability ceiling and daily-wage exemption notifications before enabling those branches. Demonstrate a structure where gross/2 differs from the statutory component result.
- [ ] Run `rtk proxy cargo test -p kabipay-payroll --test contribution_calculation --test automatic_payroll --test import_calculation --test period_validation --offline`; establish RED for new behavior.
- [x] Implement validated structured rules (component sum, rate, ceiling, rounding) and reasoned source overrides. Preserve old monthly `PeriodInput` source behavior; introduce an explicit calculation mode for reviewed source vs automatic rules with effective activation. Do not reuse September's expected totals as October targets.
- [x] Store source/client formula origin without certifying it as the statutory rule. Keep percentage withholding separate from annual regime calculation. Validate all financial inputs and exact totals using Decimal; then obtain PASS.

## Task 6: Extend the standard import for rules, tax settings and opening history

**Files:** Modify `hrms-database/import-templates/v1/tenant-import.schema.json`, `example.synthetic.json`, the import section of `hrms-database/README.md`, Solvian `solvian_profile.py`/`solvian_period.py`; create `kabipay-tenant-import/src/tax_import.rs`; modify `contract.rs`, `configuration.rs`, `import_sections.rs`, `preview_actions.rs`, `validation.rs`, `reset.rs`, `Cargo.toml`; create `tests/tax_import.rs` and update existing contract fixtures.

**Interfaces:** Add optional `tax_settings` and `tax_history` employee sections and optional versioned company payroll-rule configuration to the version-1 template. Old packages retain behavior through omission defaults; strict validation of present fields remains. `import_tax_sections<C: ConnectionTrait>(db: &C, tenant: Uuid, actor: Uuid, employee: Uuid, settings: Option<TaxSettingsInput>, history: &[TaxHistoryEntry]) -> KabiPayResult<TaxImportResult>` calls Task 3 services. `TaxImportResult` has per-section action/status/reason without PII.

- [ ] Test old packages unchanged, missing tax history reported without blocking employee/salary sections, duplicate history idempotence, partial section rollback and conflicting coverage. Test blank ESI is a September source value, not a permanent eligibility switch.
- [ ] Run `rtk proxy cargo test -p kabipay-tenant-import --test contract --test tax_import --offline`; establish RED, then implement optional contract and savepoint/report wiring.
- [x] Configure the Solvian source formula and October activation as data with imported notes. Formula-bearing 10% source rows establish that formula only; constant TDS amounts must not be converted into guessed percentage or regime assignments. Leave unconfirmed settings explicit for HR review.
- [x] Extend preview fingerprints and the exhaustive reset manifest for the new owned tables, respecting audit retention and preserved administrators. No automatic reset/import/finalization is introduced.
- [ ] Obtain PASS and validate normalized packages offline. Print only aggregate results; keep source records in private output directories.

## Task 7: Separate draft calculation from atomic finalization

**Files:** Create `hrms-database/changelog/migrations/0094_payroll_draft_calculation/payroll_draft_calculation.xml`, matching entity companion `d0094_payroll_draft_calculation.rs`; modify tenant changelog/entity registry. Create `kabipay-payroll/src/services/payroll_draft.rs`, `payroll_finalize.rs`, `payroll_fingerprint.rs`; modify `payroll_service.rs`, `imported_payroll.rs`, `imported_lwp.rs`, `arrear_service.rs`, period-input service, resolver files and module registry. Create `tests/draft_calculation.rs`, `tests/finalization.rs`.

**Interfaces:** `calculate_payroll_cycle(db: &DatabaseConnection, tenant: Uuid, actor: Uuid, cycle: Uuid, expected_revision: Option<i32>) -> KabiPayResult<PayrollDraft>`; `finalize_payroll_cycle(db: &DatabaseConnection, tenant: Uuid, actor: Uuid, cycle: Uuid, draft_revision: i32, fingerprint: &str, acknowledgement: FinalizeAcknowledgement) -> KabiPayResult<PayrollFinalization>`. Define these DTOs in `payroll_draft.rs`; the acknowledgement binds employee/provisional-tax decisions to the reviewed draft. Task 5 produces employee calculations; this task owns persistence and transaction boundaries.

- [ ] Test repeated draft calculations replace the current draft/version and create zero published slips, actual TDS history, LWP allocations and applied arrears. Test all excluded/inactive/no-eligible-employee cases have an explicit preview outcome.
- [ ] Test input/settings/history/approved-leave changes invalidate reviewed drafts, including a concurrent declaration/proof change. Test duplicate/concurrent finalizers create exactly one set of slips and allocations; a mid-finalization failure rolls everything back.
- [ ] Run `rtk proxy cargo test -p kabipay-payroll --test draft_calculation --test finalization --offline`; establish RED. Add disposable PostgreSQL transaction tests in `hrms-database/tests/integration/payroll/payroll-finalization.integration.cjs` for actual locking/rollback evidence.
- [ ] Build draft snapshots from a consistent database view; fingerprint calculation inputs and exact rule versions. Finalization must lock/revalidate all relevant mutable inputs until commit, not merely compare a hash and then leave a race window. Use consistent lock order across input editors and finalizers.
- [x] Store immutable final statements with source evidence, projection limitations, acknowledgement and exact amounts. Preserve existing PROCESSED cycles as locked. Generated source slips and ordinary payroll must use the same finalization boundary.
- [x] Replace the old direct run entrypoint with an actionable API error/deprecation directing clients to calculate/review/finalize; it must not remain an alternate way to bypass review. Update all internal fixture callers. Locked cycles reject both old and new write paths.
- [ ] Obtain PASS, including the real concurrent fixture. Verify exports use finalized records only and advance settlement remains correct. A preview refresh must never emit final-payslip notifications.

## Task 8: Build HR rule, employee tax and history controls with design/tour updates

**Files:** Modify `hrms-ui/src/modules/payroll/PayrollTaxPage.tsx`, compensation sections, `payrollTaxTypes.ts`, `src/api/schema-extensions/tax-admin.graphql`; create `modules/payroll/components/EmployeeTaxSettings.tsx`, `TaxHistoryEditor.tsx`, `ContributionRuleEditor.tsx`, matching focused tests and `hooks/useEmployeeTaxSettings.ts`. Update `PayrollTaxPageTour.ts`, `PayrollCompensationPageTour.ts`, `src/guidance/payrollExpenseTours.test.tsx` and `designs/ui-review.pen`.

**Interfaces:** Use Task 3's authorized GraphQL APIs and revision fields; UI money remains strings. Company rule editing and employee settings are separate forms using the existing page tabs. Queries are keyed by tenant, employee, tax year and effective period, and ignore stale responses.

- [ ] Add UI tests for reason-required overrides, percent conversion, absent vs confirmed-zero history, coverage errors, effective dates, permission denial and employee/tenant switches while loading. Ensure declarations cannot submit calculated TDS fields.
- [ ] Run `rtk proxy npm test -- src/modules/payroll/components/EmployeeTaxSettings.test.tsx src/modules/payroll/components/TaxHistoryEditor.test.tsx src/modules/payroll/components/ContributionRuleEditor.test.tsx` from `hrms-ui`; establish RED.
- [ ] Update Pencil frames `XMmPw` and `b2PC0` for the forms, notes, source labels, loading/errors and unknown-history state, then implement those controls with existing accessible components. Use Pencil's available tools and inspect rendered frames; do not treat JSON validity as visual review.
- [ ] Add stable tour anchors and scope-aware explanatory steps for settings, source/custom rules and history. A tour must never save changes. Remove obsolete wording implying storage-only tax versions automatically calculate deductions.
- [ ] Obtain PASS for UI and `rtk proxy npm test -- src/guidance/payrollExpenseTours.test.tsx src/guidance/tourCoverage.test.ts`. Verify the actual service schema accepts the new documents without network codegen.

## Task 9: Build payroll calculation/review/finalization controls with design/tour updates

**Files:** Modify `modules/payroll/components/PayrollCyclesCard.tsx`, `PeriodEditor.tsx`, `PayrollPeriodInputs.tsx`, `hooks/usePayrollBoardActions.ts`, `payrollTypes.ts`, local payroll GraphQL documents and `src/api/schema-extensions/payroll-run.graphql`; create `components/PayrollDraftReview.tsx` and focused tests. Update `PayrollPageTour.ts`, payroll tour tests and `designs/ui-review.pen`.

**Interfaces:** Consume Task 7 operations and opaque revision/fingerprint values. UI actions are `Calculate`, `Recalculate` and `Finalize & Lock`; finalization submits the exact reviewed snapshot and required acknowledgement. Old run calls are removed from the current UI.

- [ ] Test draft calculation leaves the cycle editable; recalculation replaces results; stale inputs disable finalization and show a refresh action; provisional-tax acknowledgement is required; server-rejected races recover visibly; locked cycles have no calculate/edit action.
- [ ] Run `rtk proxy npm test -- src/modules/payroll/components/PayrollDraftReview.test.tsx src/modules/payroll/hooks/usePayrollBoardActions.test.tsx`; establish RED.
- [ ] Update Pencil frame `b4ghOM` and adjacent review/finalized/error states, then implement the UI. Show financial totals and unresolved inputs in product language without database field names, stub implementation text or claims of executing payments.
- [ ] Update processing tour copy and anchors to explain repeated draft calculation, HR review and locking. Exercise keyboard navigation, modal focus and read-only permissions; the tour must invoke zero calculation/finalization mutations.
- [ ] Obtain PASS for targeted UI/tour tests; inspect Pencil renders and the local browser with synthetic data for draft-to-finalized state behavior.

## Task 10: Show employee projections and preserve honest slip/export terminology

**Files:** Modify `components/PayrollIncomeTaxTab.tsx`, `EmployeeTaxCards.tsx`, `TaxComputationsCard.tsx`, `hooks/useEmployeeTaxSelfService.ts`, `components/PayslipSheet.tsx`, `PayslipSettlement.tsx`, `utils/payslipPdf.ts`; create `components/TaxProjectionSummary.tsx`, `TaxProjectionTimeline.tsx`, `TaxSlabBreakdown.tsx` and `hooks/useTaxProjection.ts` with tests. Update `PayrollPayPageTour.ts`, payroll tour tests and `designs/ui-review.pen`. Adjust payroll export headings where they claim remittance.

**Interfaces:** Consume Task 4 projection output and Task 7 immutable statements. Never infer evidence kind from whether a value is nonzero. Keep company visibility and existing target authorization intact in browser, print and PDF.

- [ ] Test incomplete/complete history, May-to-March bounds, actual/estimated/projected month labels, stale response isolation, hidden employer components and advance settlement. Assert 'tax paid', 'paid to government' and 'tax remitted' never appear as assertions in these product views/exports.
- [ ] Run `rtk proxy npm test -- src/modules/payroll/components/TaxProjectionSummary.test.tsx src/modules/payroll/components/TaxProjectionTimeline.test.tsx src/modules/payroll/components/TaxSlabBreakdown.test.tsx src/modules/payroll/hooks/useTaxProjection.test.tsx`; establish RED.
- [ ] Update Pencil frame `u4G7K` plus tax projection, history-incomplete, slab-detail and mobile states. Implement annual summary, monthly evidence timeline, recorded payroll TDS and the exact projection note from the spec. A partial known TDS total must be visibly partial; hide numeric remaining liability until coverage supports it.
- [ ] Update pay/payslip tour guidance to explain estimates and where to contact HR, without implying government payment. Ensure print/PDF use the same financial semantics and company component visibility as the browser.
- [ ] Obtain PASS, run relevant existing payslip presentation/authorization tests, inspect Pencil renders and test the local employee browser view with synthetic data at desktop and mobile widths.

## Task 11: Complete integration acceptance, documentation and independent review

**Files:** Extend `hrms-database/tests/integration/imports/native-import.integration.cjs`, `hrms-svc/crates/kabipay-tenant-import/tests/payroll_fixture.rs`, `tests/api_contract.rs` and new payroll integration fixtures. Update `hrms-documentation/docs/client-onboarding/solvian-september-2026-import-runbook.md`, existing database README import section, this plan's checkboxes, and create one focused evidence handoff at `docs/superpowers/reviews/2026-10-04-payroll-tax-projections-validation.md`.

**Interfaces:** This is acceptance of Tasks 1–10, not a second implementation. Use private conversion reports, schema-contract results, synthetic fixture outcomes and rendered UI/design evidence.

- [x] Reconcile the two real workbooks read-only: 37 salary structures, confirmed normalized leave conventions and unchanged September source financials. Do not claim missing employee codes or additional-deduction reasons have been resolved by tax work.
- [x] From `hrms-svc`, run `rtk proxy cargo test -p kabipay-tax -p kabipay-payroll -p kabipay-tenant-import --lib --tests --offline` (119 passed), then `rtk proxy cargo check -p kabipay-tax -p kabipay-payroll -p kabipay-tenant-import --offline` and build the required native binaries after final changes.
- [x] From `hrms-database`, run the expanded native disposable integration fixture, with finalization cases consolidated into its Rust payroll fixture; the dedicated tax-storage fixture also passed. Verified repeat migrations, import replay, retained-admin replacement, backup/restore, projection history, concurrent finalization and rollback. Final native evidence: `hrms-native-import-xUnx3e`. No `.env` target or live client schema was used.
- [ ] From `hrms-ui`, run `rtk proxy npm test -- src/modules/payroll src/guidance/payrollExpenseTours.test.tsx src/guidance/tourCoverage.test.ts`, lint only the changed owned source files, then `rtk proxy npm run build`. Do not rerun broad checks without new failures/changes.
- [ ] Render and inspect all changed Pencil frames and compare them with the local browser flows. Record browser cases separately from unit/build evidence; unavailable browser/Pencil verification must remain explicit, not marked passed.
- [ ] Verify tour coverage, permissions, keyboard flow and absence of business mutations during guidance. Update the runbook with September import/review/finalization, October calculation, provisional history and later future-only adjustments.
- [x] Use the approved native final-review workflow: dedicated GPT-6.1 Sol compresses bounded execution evidence; one independent reviewer receives the approved spec/plan summary and only relevant source selections. Resolve material findings and rerun affected checks.
- [x] Record outcomes and remaining live acceptance work in the validation handoff. Leave current-checkout diffs for manual review; do not stage, commit, migrate or deploy automatically.

## Plan self-review and handoff

Coverage check: confirmed leave conventions map to Task 1; settings/history and declaration isolation to Tasks 2–3; tax projection/allocation to Task 4; contributions and October automation to Task 5; standard imports/reporting to Task 6; draft/lock integrity to Task 7; UI/Pencil/tours to Tasks 8–10; integration and operator instructions to Task 11. Review Focus conditions each have explicit tests in their owning tasks.

Implementation was approved and completed natively in the current checkouts. Tasks 1–10 are implemented; Task 11 regression, disposable database acceptance, documentation and independent review are complete. See the [validation handoff](../reviews/2026-10-04-payroll-tax-projections-validation.md) for observed results and remaining acceptance. Unchecked composite steps are not blanket failures: some combine completed code/tests with browser validation or an exact originally proposed test command. Browser acceptance remains unverified because its runtime could not start; 24 preexisting UI lint findings remain in three legacy files. No live operations or commits were performed.

Execution adjustment: finalization transaction cases were added to the existing native import PostgreSQL fixture and its Rust payroll fixture rather than creating a duplicate database harness. Tax storage has a dedicated synthetic fixture. Focused test names/files follow the final cohesive implementation; no claim is made that every originally listed RED command was run verbatim. The final independent review found five important issues, which were corrected and passed final regression validation. The expanded database fixture additionally exposed PostgreSQL decimal padding; the corrected validator accepts trailing zeroes while still rejecting fractional paise, and the full fixture passed afterward.
