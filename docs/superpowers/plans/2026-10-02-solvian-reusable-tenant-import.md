# Solvian reusable tenant import implementation plan

> **For agentic workers:** Use `superpowers:executing-plans` for native execution or `superpowers:subagent-driven-development` if the user selects delegation. Steps use checkbox syntax. User instructions override skill defaults: no automatic commits and no agent-run tests/builds without delegation.

**Goal:** Convert the two reviewed September workbooks into a reusable import package, configure employee salary/leave/period inputs, and provide an operator-run preview/reset/import utility for actual client schemas.

**Architecture:** A Python standard-library converter reads XLSX without editing it. A local Rust `kabipay-tenant-import` CLI consumes a versioned JSON contract and uses application-domain functions through library targets; it does not add a deployed service. Shared payroll/leave modules support imported records and later HR edits consistently, with monthly-input provenance and replay protection.

**Tech stack:** Existing Python 3, Rust workspace dependencies (`serde`, `rust_decimal`, SeaORM/PostgreSQL, `sha2`, `chrono`, `uuid`), Liquibase XML, React/TypeScript and existing GraphQL authorization. No new framework, workbook-authoring package or network service.

**Spec:** `../specs/2026-10-02-solvian-reusable-tenant-import.md`

**Evidence:** `../../client-onboarding/2026-10-02-solvian-import-audit.md`

## Global constraints

**3 October execution update:** The user delegated local tests/checks/builds to the agent and requested completion of Step 2. This supersedes user-owned local validation gates below. Actual client-schema operations, migrations and deployment remain operator-run. The old fixed-roster onboarding workflow/tests have been retired at the user's request. Advances are settlement adjustments only. HR/Admin controls component visibility once per company; employer contributions are hidden by default and never change earned salary or employee deduction totals.

- No automatic commit, live execution, deployment, or Dart/Flutter command is part of implementation.
- User-run validation remains the default unless explicitly delegated. Provide RTK-prefixed commands and wait for results at required verification boundaries.
- Only the two explicit original workbook paths are client input; similarly named copies are excluded.
- Opening is 2025 carry-forward; Allotted is the 2026 grant.
- AF-AI proportions are 50%, 25%, 12.5%, 12.5% for all 37 reviewed rows. Apply them to contractual Monthly Fix gross for recurring salary.
- Excel component bases/formulas govern this client configuration. LWP divisor 31 remains editable.
- Annual gross and annual employer PF are separate inputs to annual CTC. Advances/incentives are period data, not recurring salary.
- Additional deductions require an HR-entered reason. SBL AU11 must retain a missing-reason issue until the actual reason is supplied.
- Preserve exact reviewed admin accounts, passwords, MFA, roles and employee linkage; retain tenant/subscription and migration/permission foundations.
- Exact tenant/database identity, salary effective date, leave as-of date, code/login mappings and write-pause/backup locations are operator inputs, not guessed defaults.
- No migration, real-schema preview, reset, import or payroll run is performed merely by implementing the utility.
- At execution start, inspect applicable instructions/isolation and dirty state. Do not stash, reset, overwrite or commit unrelated work. The user subsequently requested cleanup of superseded database scripts: the old Consultancy seed/test and workbook reset/reader/README are retired with recovery copies outside the repository. Retain multi-company provisioning/management tools, migration utilities and their tests/docs.

## Review focus

1. Corrected-file replay or an uncertain commit duplicates historical LWP, advances or salary assignments: Task 7 verifies persisted domain identity and reconciliation.
2. A negative year-to-date balance is charged again as September LWP: Tasks 1, 5 and 6 verify historical/period separation.
3. Adding employer PF to CTC changes gross-based component amounts: Task 3 verifies explicit annual-gross calculations and legacy compatibility.
4. Tenant reset drops a retained login, grants broader permissions or clears another schema: Task 8 verifies account identity/roles, FK boundaries and rollback.
5. Missing optional data or an unknown deduction reason becomes zero/verified/ready: Tasks 1, 6 and 9 verify field/section outcomes and finalization gates.

## Contract and file boundaries

All repository paths below are relative to `D:\work\heliorventures`.

The converter and CLI agree on `format = "hrms-tenant-import"`, `version = 1`, snake_case JSON fields, decimal strings and ISO dates. JSON schema and synthetic examples live in `hrms-database/import-templates/v1/`. The Rust package mirrors the schema in `crates/kabipay-tenant-import/src/contract.rs`; changing the contract requires updating both implementations and their compatibility cases.

`ImportPackage` contains `source` (hash/path label/profile), `tenant_code`, `salary_effective_from`, `leave_as_of`, `period` (2026/9 for these inputs), `employees`, `configuration`, and `issues`.

Each `ImportEmployee` contains `source_ref`, `employee` (code or reviewed mapping key, name parts, joining date and optional profile data), optional identity/bank sections, `recurring_salary`, `leave_opening`, `historical_lwp`, and `period_input`. `SourceRef` carries file hash, sheet, row and field-to-cell references. A missing required employee code is represented as an issue and needs a reviewed code map; row position is not a persistent employee identity.

`ImportIssue` contains `code`, `severity` (`WARNING`, `DEFER_SECTION`, `BLOCK_EMPLOYEE`, `BLOCK_TENANT`), `section`, `source_ref`, `field`, and a safe message. No credential/full identifier appears in messages.

`ImportEmployee.clear_fields` is an explicit list of supported nullable field names. Omitted/null source values preserve existing data during normal updates; only that list requests deletion. Clearing required identity/bank fields is rejected. This avoids collapsing absent versus explicit-clear intent during JSON deserialization.

`PeriodInput` contains period identity, gross calculation rule, fixed gross, paid/proration-day inputs, LWP inputs, variable allowance/OT, Other Payable incentive, externally paid advance, additional deductions with optional source reason, contribution/tax overrides, expected earned components and expected statement totals. Source-only/hardcoded monthly values are explicit overrides, never hidden permanent eligibility decisions.

The imported period is a draft until required calculation/reason inputs are resolved. Basic employee import can succeed independently of this readiness state.

## Task 1: Versioned template and read-only Solvian converter

**Files:** Create `hrms-database/import-templates/v1/tenant-import.schema.json`, `example.synthetic.json`; shared `convert-client-workbook.py`, `workbook_xml.py`, `normalize.py`, `private_output.py` under `hrms-database/scripts/reusable/imports/`; the `solvian_profile.py`, `solvian_layout.py`, `solvian_period.py`, `solvian_salary_leave.py` client modules under `hrms-database/scripts/tenant_specific/solvian/imports/`; `hrms-database/tests/tenant_specific/solvian/unit/test_converter.py`. The root database README is the only project README after the user-approved 3 October reorganization.

**Interfaces:** `read_workbook(path: Path) -> WorkbookRows`; `convert_solvian(rows, profile, options) -> dict`; `ConversionOptions` requires tenant code, salary effective date, leave as-of date and optional reviewed employee-code mappings. CLI writes the package and masked issue report to a protected output directory.

- [x] Add synthetic tests for both header layouts, totals/footer exclusion, textual/serial dates, numeric identifiers, missing optional bank/DOB data and invalid required identity.
- [x] Add salary test: fixed gross `30000`, earned gross `27000`, AF-AI `13500/6750/3375/3375` must normalize recurring components to `15000/7500/3750/3750`, while retaining earned components separately.
- [x] Add tests that NA, blank and zero remain distinct; source LWP usage and opening/history never populate September days by inference; Other Deduction without a reason becomes `DEFER_SECTION` for period finalization.
- [ ] User runs from `hrms-database`: `rtk proxy py -3 -m unittest discover -s tests/tenant_specific/solvian/unit -p test_converter.py -v`; expected red failures before implementation, then passing cases after implementation.
- [x] Implement XML ZIP reader, explicit SCL/SBL profiles, Decimal normalization and JSON schema/example. No arbitrary formula execution, filename glob or workbook write.
- [ ] Provide a read-only real-workbook conversion command with required explicit dates/codes; operator validates 19 SCL and 18 SBL rows and masked source reconciliation. Do not generate private client packages in tracked documentation. Commands are now in `hrms-database/README.md#tenant-import-template-v1`; source acceptance remains user-run after the synthetic suite passes.

## Task 2: Add storage and shared domain library targets

**Files:** Create migrations `hrms-database/changelog/migrations/0090_payroll_period_configuration/payroll_period_configuration.xml`, `0091_leave_import_history/leave_import_history.xml`, `0092_tenant_import_tracking/tenant_import_tracking.xml`; corresponding `d0090_payroll_period_configuration.rs`, `d0091_leave_import_history.rs`, `d0092_tenant_import_tracking.rs` under `hrms-svc/crates/kabipay-db-entities/src/tenant/`; update `tenant/mod.rs` and `hrms-database/changelog/tenant.changelog-master.xml`.

Create `src/lib.rs` in `kabipay-payroll`, `kabipay-leave`, `kabipay-employee`; update their `main.rs` module imports. Employee library retains its existing `entities` adapter module. Existing HTTP/resolver binaries and ports stay intact.

**Storage:** Add nullable `annual_gross` and `annual_employer_pf` to employee salary assignment. Add tenant/employee payroll-rule configuration, employee/month period inputs, itemized period adjustments, and payslip statement snapshots. Add dated leave-opening metadata and historical LWP usage. Add import run/record tracking. In 0092 also add nullable bank account-holder/branch and employee confirmation-date fields so these source values have supported profile destinations. Update existing calculation-basis CHECK constraints in the new migration to admit PERCENT_OF_GROSS while retaining legacy values. All employee/period references are tenant-scoped; unique domain keys prevent duplicate period/section entries.

**Interfaces:** Libraries expose `services`; existing resolver module visibility supports their current binaries. Domain operations that the CLI must compose accept a supplied transaction instead of opening independent nested transactions.

- [ ] Recheck that 0090-0092 remain unallocated before adding changesets. Preserve existing migrations; do not rewrite applied checksums.
- [ ] Add migration assertions and synthetic disposable-schema checks for nullable legacy fields, tenant-scoped unique keys/FKs, required reason/readiness state and retained import-run metadata.
- [ ] User-run migration fixture verification uses a new `hrms-database/tests/migrations/test-tenant-import-storage.ps1` that accepts only disposable test schema names and refuses any ops-mapped client schema. No automatic execution.
- [ ] Implement storage/entities/library wiring. Library extraction must not alter authentication, resolver composition or duplicate test compilation through both library and binary module declarations.
- [ ] User runs from `hrms-svc`: `rtk cargo check -p kabipay-payroll -p kabipay-leave -p kabipay-employee`; expected success before later tasks consume the libraries.

## Task 3: Explicit gross-based salary and configurable client payroll rules

**Files:** Create `kabipay-payroll/src/services/salary_rules.rs`, `payroll_rules.rs`; modify `payroll_service.rs`, `unpaid_leave_policy.rs`, `unpaid_leave_calculation.rs`, `services/mod.rs`, and salary/rule GraphQL types and mutations under `src/resolvers/`.

**Interfaces:** `calculate_recurring_salary(rules: &SalaryRules, annual_gross: Decimal, employer_rule: &EmployerPfRule) -> KabiPayResult<RecurringAmounts>`; `calculate_period_rules(input: &PeriodCalculationInput, rules: &EmployeePayrollRules) -> KabiPayResult<CalculatedPeriod>`; `resolve_lwp_basis(lines, policy) -> KabiPayResult<Decimal>` supports an explicitly configured component set/gross basis. Retain existing BASIC single-component behavior for older policies.

- [ ] Add fictional uncapped-rule tests: monthly gross `30000` yields `15000/7500/3750/3750`; PF base using Basic + Conveyance + Other is `22500`; configured employer 13% yields monthly `2925`, annual PF `35100`, annual gross `360000`, CTC `395100`.
- [ ] Verify adding employer cost does not change recurring gross/split; legacy PERCENT_OF_CTC without annual_gross retains current behavior; PERCENT_OF_GROSS requires an explicit gross value.
- [ ] Verify LWP `30000 / 31 * 3` rounds once to `2903.23`; multi-component before-statutory reductions reconcile components and gross without reducing a single BASIC line by the entire gross-based deduction.
- [ ] Test explicit eligibility/ceilings and source-only overrides; a zero contribution or missing UAN must not silently create a permanent exemption or select global stub calculations.
- [ ] User runs `rtk cargo test -p kabipay-payroll salary_rules` and `rtk cargo test -p kabipay-payroll payroll_rules` for red/green evidence.
- [ ] Implement pure Decimal functions and effective tenant/employee policy selection. Existing tenants keep their current paths; imported client policy uses the explicit new configuration. Final money rounding and source-specific whole-unit rounding are configuration fields.

## Task 4: Audited employee/month inputs and statement settlement

**Files:** Create `kabipay-payroll/src/services/payroll_period_input.rs`, `payroll_settlement.rs`; resolver modules `period_inputs.rs` and `period_input_types.rs`; update existing resolver roots/`services/mod.rs`, `payroll_service.rs` and payslip detail DTOs.

**Interfaces:** `save_period_input<C: ConnectionTrait + Sync>(db: &C, tenant: Uuid, actor: Uuid, input: SavePeriodInput) -> KabiPayResult<PeriodInputState>`; `calculate_settlement(earned_gross, incentive, statutory_total, additional_total, advance_paid) -> KabiPayResult<StatementSettlement>`; `load_period_input<C>(db, tenant, employee, year, month) -> KabiPayResult<Option<PeriodInputState>>`.

`StatementSettlement` contains earned gross, incentive, statutory deduction total, additional deductions, net earned, advance already paid, remaining payable and any excess advance credit. Existing `payslip.net_salary` and payment/export behavior represent remaining payable; snapshot DTO exposes net earned separately. Incentive stays separate from source AE earned gross.

- [ ] Test `30000 + 500 - 4000 - 100 = 26400` net earned; advance `5000` gives remaining `21400`; advance does not change gross or CTC.
- [ ] Test excess advance as explicit outstanding credit, not negative bank payable; source Total Deduction decomposition never subtracts advances twice.
- [ ] Reject new manual additional deductions without a nonblank reason. Imported unknown-reason items remain draft/needs-review and preserve source amount. Add tenant/permission tests using existing `PERM_PAYROLL_MANAGE` and read/self scope.
- [ ] User runs `rtk cargo test -p kabipay-payroll payroll_period_input` and `rtk cargo test -p kabipay-payroll payroll_settlement`.
- [ ] Implement actor/audit history, effective input version, source provenance and readiness. Locked/finalized snapshots cannot be edited through the period-input mutation.
- [ ] Extend pay-run preflight to report unresolved required inputs before financial writes. This may keep a cycle draft while employee import succeeds; do not report that as an import failure. Preserve cycle locks and existing closed-cycle protection.

## Task 5: Leave snapshot and historical LWP domain support

**Files:** Create `kabipay-leave/src/services/leave_import_history.rs`; update `services/mod.rs`, `leave_admin.rs`, `leave_service.rs`, `resolvers/query.rs`, `resolvers/types.rs`. Create `hrms-ui/src/modules/leave/leaveImportHistoryDocuments.ts`; modify `hooks/usePersonalLeaveBoard.ts`, `components/LeaveBalancesCard.tsx`, `components/validateLeaveApplication.ts`, and `hrms-ui/src/api/documents/clientOperations.graphql`'s LeaveBoard query if additive history fields are included there. Add `LeaveBalancesCard.test.tsx` and targeted unpaid-application cases.

**Interfaces:** `reconcile_opening(input: &LeaveOpeningInput) -> KabiPayResult<LeaveOpeningResult>`; `apply_opening<C>(db: &C, tenant, actor, employee, input: LeaveOpeningInput) -> KabiPayResult<LeaveOpeningResult>`. Input carries explicit as-of date, carry-forward, 2026 grant, source taken/balance and import identity; result separates EL paid usage, EL remaining, historical LWP and discrepancies.

- [ ] Test carry-forward `4` + grant `6`, total used `12` produces EL used `10`, EL remaining `0`, historical LWP `2` and zero September payroll units by default.
- [ ] Test negative Taken and inconsistent component totals produce explicit reconciliation issues instead of inverted signs or fabricated entitlement; unknown/NA grant stays unknown.
- [ ] Test snapshot replay preserves later requests/accrual and does not reserve or approve historical aggregates again. Reapplying the same opening returns unchanged; changing an opening after later activity requires reviewed reconciliation.
- [ ] Verify new unpaid requests still require the existing manager/workflow approval and overlap/date controls but do not require EL entitlement. No uniform annual policy is automatically granted.
- [ ] Test that LWP displays approval-based availability rather than zero paid entitlement, historical usage is distinct from September units, and unknown paid balances are visibly unprovisioned. Frontend and backend must agree on unpaid requests without a balance; do not configure a max-consecutive-days cap for this LWP type.
- [ ] User runs `rtk cargo test -p kabipay-leave leave_import_history`; implement transaction-aware opening/history operations and read DTOs after red evidence.

## Task 6: Connect September inputs to ordinary payroll and reconcile

**Files:** Create `kabipay-payroll/src/services/payroll_reconciliation.rs`; update `payroll_service.rs`, `unpaid_leave_policy.rs` and pay-run tests.

**Interfaces:** `reconcile_statement(expected: &ExpectedStatement, actual: &CalculatedPeriod) -> Vec<ReconciliationIssue>`; `preflight_period<C>(db, tenant, cycle) -> KabiPayResult<PeriodReadiness>`. Consume salary rules (Task 3), period inputs/settlement (Task 4) and leave attribution (Task 5).

- [ ] Add tests for FIXED_MINUS_LWP, PAID_DAYS_PLUS_OT and explicit source-only earned-gross rules. Gross-based LWP and paid-day proration must never both charge the same source reduction.
- [ ] Verify row-level earned components, PF/ESI wages/contributions, PT/TDS, additional deductions, incentive, advance and remaining payable against synthetic expected source amounts.
- [ ] Verify monthly imported LWP is consumed once; linked future dated requests cannot also charge units already represented by the same period input; unrelated cumulative historical LWP is excluded.
- [ ] Verify no imported-policy calculation silently falls back to the global statutory stub. Missing-rule/reason issues remain visible and keep finalization unavailable until HR resolves them.
- [ ] User runs `rtk cargo test -p kabipay-payroll payroll_reconciliation` and `rtk cargo test -p kabipay-payroll payroll_run`; implement integration preserving cycle row locks, atomic writes and immutable snapshots.
- [ ] September generation remains an explicit operator action after import/reconciliation; do not auto-run payroll as part of reset.

## Task 7: Reusable local importer, preview and replay-safe section writes

**Files:** Create `hrms-svc/crates/kabipay-tenant-import/Cargo.toml`, `src/main.rs`, `lib.rs`, `cli.rs`, `contract.rs`, `tenant_target.rs`, `preview.rs`, `apply.rs`, `employee_import.rs`, `salary_import.rs`, `leave_import.rs`, `report.rs`; register the crate in `hrms-svc/Cargo.toml`. Add `tests/contract.rs`, `preview.rs`, `replay.rs`, `tenant_isolation.rs` under the new crate.

**Interfaces:** `preview_import(ops_db, package: &ImportPackage, options: &ImportOptions) -> KabiPayResult<ImportPlan>`; `apply_import(target: &VerifiedTenantTarget, plan: &ImportPlan, options: &ExecutionOptions) -> KabiPayResult<ImportReport>`. `ImportPlan` has immutable source/config/target digests, action list, source issues, per-section readiness and preservation manifest. Report outcomes are created/updated/unchanged/partial/deferred/failed and are committed facts.

- [ ] Test schema-contract compatibility with Task 1's synthetic package, decimal-string precision and version rejection.
- [ ] Resolve tenant ID/schema/database through real ops mapping using fail-closed common DB resolution; reject derived fallback, identity disagreement, missing migrations and actor not authorized for the reviewed operation. No client-specific UUID or column letter appears in importer code.
- [ ] Test optional-field omission preserves existing values, explicit clear is honored only for nullable supported fields, and invalid bank/DOB sections do not undo valid independent core data. Required identity defers dependent sections.
- [ ] Test corrected file with stable domain identity updates rather than duplicates; same committed run returns unchanged; uncertain commit is reconciled before retry.
- [ ] User runs `rtk cargo test -p kabipay-tenant-import --test contract --test preview --test replay --test tenant_isolation` against synthetic/proxy fixtures.
- [ ] Implement CLI default preview, supplied transaction domain calls, masked logs, protected package/report paths and persisted run/record provenance. Execution accepts only the reviewed digest/target; it does not create tenants or run migrations automatically.

## Task 8: Transactional tenant reset, verified backup and preserved logins

**Files:** Create `kabipay-tenant-import/src/reset.rs`, `backup.rs`, `credentials.rs`, `tests/reset.rs`; create `hrms-database/scripts/reusable/imports/import-tenant.ps1` as an operator wrapper with explicit modes and paths.

**Interfaces:** `prepare_reset(db, target, preserved_usernames) -> KabiPayResult<ResetManifest>`; `backup_locked_schema(txn, target, private_dir, pg_tools) -> KabiPayResult<VerifiedBackup>`; `apply_reset<C>(txn: &C, manifest: &ResetManifest) -> KabiPayResult<PreservedIdentitySet>`. CLI starts the outer transaction; domain section writers do not independently commit.

- [ ] Add synthetic integration cases for all four admin usernames, unchanged passwords/MFA/roles/employee IDs, staff recreation, preserved tenant subscriptions and import audit metadata. Missing account matches fail preview or require explicit reviewed absence, never replacement privileged users.
- [ ] Test malicious schema names and external FK dependencies fail closed; deletion uses the exact manifest and RESTRICT semantics, never cross-schema CASCADE.
- [ ] Require an operator write-pause assertion. Acquire per-tenant import lock and schema table locks blocking writers while allowing backup readers; export a repeatable-read snapshot for `pg_dump --snapshot`, verify backup via `pg_restore --list`, then upgrade locks for reset/recreation in the same transaction. Backup failure means no reset.
- [ ] Test reset/import failures roll back user/employee/config changes; repeat of a committed replacement run is unchanged rather than a second wipe. Commit uncertainty requires read-only run reconciliation.
- [ ] Generate new staff credentials only from the reviewed login/code manifest; use existing common password primitives, forced password change and protected credential output. No credential in ordinary logs; invalidate replaced sessions and document retained-user re-login behavior.
- [ ] User runs `rtk cargo test -p kabipay-tenant-import --test reset` for pure/proxy cases. A separately gated disposable PostgreSQL fixture is required for actual lock, backup and rollback acceptance; it must refuse schemas referenced by live ops mappings.
- [ ] Implement reset/backup/credential modules and wrapper. Provide executable dry-run and execution help with exact required arguments; do not execute the wrapper against actual client schemas.

## Task 9: HR period-input editing and readable salary statements

**Files:** Create `hrms-ui/src/modules/payroll/payrollPeriodDocuments.ts`, `payrollPeriodTypes.ts`, `hooks/usePayrollPeriodInputs.ts`, `components/PayrollPeriodInputsCard.tsx`, and associated tests; extend `PayrollPayPage.tsx`, `hooks/usePayrollBoardActions.ts`, `hooks/usePayrollPayData.ts`, `payrollTypes.ts`, `components/PayslipDocument.tsx`, `components/PayrollPayslipTab.tsx`; extend `PayrollCompensationSections.tsx`, `PayrollCompensationPage.tsx`, `payrollCompensationTypes.ts`, `components/PayrollSalaryTab.tsx`; add `hrms-ui/src/api/schema-extensions/payroll-period-inputs.graphql` and register it in `hrms-ui/codegen.ts`.

For Task 2's supported nullable profile fields, update `kabipay-employee/src/services/profile_extras_service.rs`, `employee_service.rs`, `resolvers/mutation.rs`, `resolvers/query.rs`, `resolvers/types.rs`; `hrms-ui/src/modules/organization/employee-profile/tabs/BankingTab.tsx`, `EmploymentManagementTab.tsx`, `hooks/useEmployeeProfileData.ts`, `lib/mapBundleToModel.ts`, and the corresponding employee profile GraphQL selections in `hrms-ui/src/api/documents/clientOperations.graphql`. Preserve existing verification flags and field permissions; do not add unrelated profile features.

**Interfaces:** `usePayrollPeriodInputs(client, authorizationOwnerKey, cycleId, canManage)` provides permitted employee/month draft values and save/retry. GraphQL documents use Task 4's DTOs and existing permission service. No new authorization hierarchy or generic upload UI.

- [ ] Add authorization tests proving employee/self scope cannot manage other employees' inputs, inaccessible tabs issue no privileged queries, and tenant/user switching invalidates stale input state.
- [ ] Add form tests for amount plus mandatory additional-deduction reason, source missing-reason review, immutable processed periods and visible section readiness.
- [ ] Add profile tests for imported account holder/branch/confirmation display, optional updates preserving omitted values, and unchanged bank/PAN/Aadhaar verification state. Self-service update permissions must not expand because import fields were added.
- [ ] Add statement tests showing annual gross/employer PF/CTC separately, LWP formula once, Other Payable separately, net earned, advance already paid and remaining payable. Existing net salary/export meaning remains compatible.
- [ ] User runs from `hrms-ui`: `rtk npm run test -- src/modules/payroll/components/PayslipDocument.unpaidLeave.test.tsx src/modules/payroll/components/PayrollPeriodInputsCard.test.tsx src/modules/payroll/components/PayrollSalaryTab.test.tsx`; use corresponding authorization tests as added.
- [ ] Implement concise forms using existing Card/Table/Button patterns and product labels. Record source provenance as expandable review information, not routine employee-facing implementation detail.
- [ ] User runs `rtk npm run codegen` after schema/document changes, then scoped tests, `rtk npm run lint` and `rtk npm run build`. Codegen may contact the configured gateway and write generated files; describe those effects before supplying it. Never overwrite generated federation code manually.

## Task 10: Operator delivery and acceptance handoff

**Files:** Add reusable import operator instructions to `hrms-database/README.md`; create `hrms-documentation/docs/client-onboarding/solvian-september-2026-import-runbook.md`, `hrms-documentation/docs/superpowers/reviews/2026-10-02-solvian-import-validation-handoff.md`; update package command documentation without replacing unrelated edits. Do not recreate separate database script/template/migration README or instruction files after consolidation.

- [ ] Publish commands for converter, importer preview, replacement execution, reviewed code/login maps, issue correction, reconciliation and separate September generation. Build the CLI through user-run `rtk cargo build -p kabipay-tenant-import --release` from `hrms-svc`.
- [ ] Provide a blank operator configuration/example containing no guessed tenant IDs, passwords or employee data. Effective date/as-of date are explicit required parameters. Defaults remain read-only; execution never runs migrations/deployment implicitly.
- [ ] Document prerequisite user deployment of updated payroll/leave/employee binaries, UI and composed gateway schema, plus user-applied tenant migrations. Verify actual runtime contract support before reset; a newly built local CLI must not populate fields that the running old application ignores. Deployment itself is outside this implementation execution.
- [ ] Record validation evidence separately: converter/source checks, library/API tests, migration/disposable DB checks, browser statements and actual tenant acceptance. Do not claim real-schema readiness from unit tests.
- [ ] Verify real-source normalization/reconciliation reports include all 37 rows, missing employee-code mappings, DOB conflicts, bank omissions and SBL AU11 pending reason. No optional omissions become silent zeroes.
- [ ] Complete source/diff review; provide per-repository RTK validation commands for the user. No automatic commits, formatting of unrelated files or live commands.
- [ ] Operator acceptance verifies exact preserved accounts, backup restoration evidence, actual target changelog/schema, employee/assignment/opening counts, September financial reconciliation and readable authorized statements before any actual reset/generation is reported successful.

## Execution and review handoff

This plan covers one coordinated import-to-payslip delivery; tasks share a single template and domain contract. Execute in order and stop at each user-owned red/green or required database/browser verification boundary until results are supplied or execution is delegated.

Recommended method: **native execution in this session**, because interfaces and transactions span the three domains and it avoids repeated worker contexts. A final independent review is required before reporting implementation ready. If the user chooses agents, use the mandated dedicated Luna summariser for logs/history before any Astra review and supply only narrowly selected source; do not spawn agents before that method is selected.

Approval of this plan authorizes the chosen implementation workflow, not live client-schema operations. Tests/builds and live execution keep their separate user ownership. Remaining unknown client fields are visible issues/operator inputs, not new approval gates for routine implementation decisions.

## Implementation status - 4 October 2026

The historical unchecked lists above are the original implementation plan, not the current status. The user delegated local tests/builds during execution. Tasks 1-9 now have implemented converter, storage, domain services, guarded native importer/reset, company presentation and HR monthly-editor paths. Task 10 operator instructions and independent review handoff are complete; changed-code checks passed and are recorded in the ledger and [validation handoff](../reviews/2026-10-02-solvian-import-validation-handoff.md). No live acceptance is implied.

Rulings: use the existing transaction domain APIs rather than legacy roster scripts; keep one database README and grouped reusable/client/test folders; preview linked sections as explicit RECONCILE actions rather than simulating domain writes; retain unknown optional source values and period-specific provenance; render/export only after company display settings resolve; imported salary commencement at any point in the month requires reviewed period input. Existing staged/unrelated changes are preserved, and no commits are created.
