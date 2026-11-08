# Employee Loan Management Implementation Plan

> **For agentic workers:** Use `superpowers:executing-plans` to implement this plan task by task in this session. Do not delegate without explicit authorization. Do not commit automatically. The user's approval-before-token-expensive-work rule applies before execution.

**Goal:** Implement employee loans, recorded payments, configurable salary recovery, payslip evidence and pre-approval resignation financial review using the approved screens.

**Architecture:** Separate Loans, Payroll and FNF financial modules share the existing Payroll service. Loans alone accesses loan storage through a transaction-aware module API. Employee owns resignation and clearance, coordinating financial authorization through a private Finance API and durable operation records.

**Tech Stack:** Existing Rust/async-graphql/SeaORM/PostgreSQL/Decimal services, Liquibase migrations, stitched GraphQL gateway, React 18/TypeScript and generated TypedDocumentNode clients.

**Spec:** [Approved functional design](../specs/2026-10-07-loan-management-design.md); [approved UI review](../../../../hrms-ui/designs/ui-review.pen).

**Status:** Phase A implementation approved on 8 October 2026. User confirmed one tenant is one company and delegated focused local tests/checks. At the user request, implementation now lives in the current service/database/UI/gateway/documentation checkouts on `feat/employee-loan-management`; temporary loan worktrees were removed after hash-verified transfer. No commits.

**Current verification (9 October):** Loans runtime database tests pass 17/17, domain tests 21/21, library tests 4/4, focused new-crate Clippy and storage boundaries pass. Generated Loan clients typecheck against exported Payroll SDL. Full Payroll tests still flag one unchanged payslip-address assertion; the whole UI typecheck flags a concurrent feedback-hook error. No live migration or browser acceptance has occurred. Detailed evidence and remaining Phase A coverage are recorded in [execution ledger](../../../../.loan-implementation/progress.md). The complete feature requires the later phases below.

## Global constraints

- Payments happen outside HRMS; record disbursements and receipts rather than initiating transfers.
- HR/Admin controls approved terms, future deduction amounts, period overrides/skips and exit recovery within configured authority.
- Do not supply assumed company rates, limits, jurisdiction rules or historical balances. Required policy values block activation until configured.
- Use Decimal and decimal strings plus currency; reject unsupported precision and currency mismatch. Never use binary floating point for financial calculations.
- Only posted financial events reduce balances. Approval, quotes, schedule items and resignation authorization are not repayment.
- Preserve unrelated edits: `hrms-documentation/deploy/.env.example`, the existing functional design changes and the approved Pencil file.
- No automatic commits, deployment, live migration, real payment, tenant enablement or opening-balance import.
- The user explicitly delegated focused tests, lint, typechecks, builds and available browser checks for this implementation. Run native executables, record actual results and preserve unrelated work. No automatic commits or deployment.
- Keep existing Payroll binary/port and gateway subgraph. Loans still has independent module entitlement and capabilities.
- Implement existing shared UI components, compact controls, keyboard support, responsive/dark appearance and generated GraphQL clients; no handwritten production operations.

## Decisions required before dependent work

1. **Employer identity — confirmed:** One tenant is one company. Tenant identity owns the loan receivable and policy; employee/lender relationships remain bound to that tenant.
2. **Interest convention:** The written spec proposes ACT/365 Fixed; the approved screen also illustrates monthly annual-rate/12. Implement these as explicitly selected, versioned policy conventions, with no default that silently chooses either. Monthly conventions require explicit period boundaries and treatment of mid-period transactions before policy publication. This is mechanism support, not adoption of a company policy.
3. **Correction rule — confirmed:** HR owns both Loans and Payroll. An issued payslip remains unchanged. HR approves a fingerprint-bound historical correction preview; the loan ledger appends the linked reversal and any recalculated principal/interest adjustment at the current company date. Original occurrence dates and frozen Payroll/FNF source allocations remain evidence. Credit refunds and waivers require separate authority.
4. **Activation:** Approvers, exposure/tenure limits, allocation order, short-salary protection, skip accrual, excess credit, early settlement and applicable tax/set-off treatment are required configuration. Their absence prevents activation, not development of the configurable module.

## Review focus

- Concurrent external repayment and payroll/FNF finalization cannot recover the same principal twice; prove with database concurrency tests in Tasks 3, 5 and 7.
- A company with Loans disabled retains existing payroll behavior; an enabled module with unavailable loan state must fail visibly rather than deduct zero; prove in Task 5.
- Resignation approval committed while its response/event is lost must remain discoverable and must never release a guard based solely on timeout; prove in Task 6.
- Legacy FNF drafts and finalized records retain amounts, IDs and evidence when ownership moves; generic recovery must not become loan recovery automatically; prove in Task 7.
- Partial funding, sub-minor-unit accrual and a reversal of an earlier effective-date payment must reconcile without rewriting posted history; prove in Tasks 2 and 3.

## Current source anchors

- Payroll finalization: `hrms-svc/crates/kabipay-payroll/src/services/payroll_finalize.rs` validates draft revision/fingerprint, persists payslips and processes the cycle within one transaction.
- Payroll input freezing: `hrms-svc/crates/kabipay-payroll/src/services/payroll_fingerprint.rs` locks an explicit sorted input set. Loans must contribute through its interface, not by adding loan SQL to this file.
- Payroll preparation: `prepare_payroll.rs`, `imported_payroll.rs`, `automatic_payroll.rs` and `payroll_draft.rs` in the same services directory.
- Employee approval: `hrms-svc/crates/kabipay-employee/src/services/separation_service.rs::resolve_separation` currently creates FNF and clearance after approval and can immediately offboard a due employee.
- FNF: `hrms-svc/crates/kabipay-employee/src/services/offboarding_fnf_service.rs` currently contains financial writes and clearance reads/writes. Split these responsibilities; do not move clearance ownership.
- Gateway: `hrms-gateway/src/subgraphs.ts` already routes Payroll to port 4016. There is no new Loans subgraph.
- UI navigation: `hrms-ui/src/navigation/navigationModel.ts`, `navigationWorkspaces.ts`, `workplaceDestinations.ts`, `auth/permissionCapability.ts` and `routes/appRouteConfig.tsx`.
- Migration baseline: the current checkout already contained 0102. Loan migrations use 0103–0104, Phase B payslip loan evidence uses 0105, and proposed exit coordination is 0106.

## Phase A — Financial foundation and loan lifecycle

### Task 1: Loan schema, catalog and ownership

**Files:** Create `hrms-database/changelog/migrations/0103_employee_loans/employee_loans.xml`, `0104_loan_module_catalog/loan_module_catalog.xml`, `hrms-database/tests/migrations/test-employee-loans.ps1`; modify both changelog masters. Generate `hrms-svc/crates/kabipay-db-entities/src/tenant/d0103_employee_loans.rs` with the existing `hrms-svc/scripts/generate_db_entities.py` workflow, plus its generated module registration.

**Interfaces:** Produces loan policy/request/account/terms/schedule/override, disbursement/receipt, posting/ledger/allocation, excess-credit, employee revision, command receipt/audit and private outbox/consumer records from spec section 10. Exit review/guard records are introduced in Task 6. Catalog exposes Loans independently of the hosting service.

- [ ] Resolve employer identity before assigning ownership keys. Reserve migration numbers against the current checkout.
- [ ] Write constraint fixtures for cross-tenant foreign keys, duplicate source identities, request versions, active-policy overlap, period overrides and ledger deletion restrictions.
- [ ] Add additive schema with fixed-precision money, required currency, source/value/audit dates, immutable terms and ledger, scoped indexes and no financial cascade deletion. Require complete posted groups and balanced allocations.
- [ ] Add the Loans catalog and capabilities through current control-plane/tenant catalog conventions. Do not auto-subscribe tenants or broadly grant permissions. Preserve SELF and authorized management scopes.
- [ ] Generate entities from Liquibase rather than editing generated models manually. Supply migration validation and entity-generator commands after checking their current CLI arguments; validation must target a disposable test database, not production.

### Task 2: Domain calculations and versioned policies

**Files:** Create `hrms-svc/crates/kabipay-loans-domain/Cargo.toml`, `src/lib.rs`, `money.rs`, `terms.rs`, `interest.rs`, `allocation.rs`, `schedule.rs`, `state.rs` and `tests/calculations.rs`; modify `hrms-svc/Cargo.toml`.

**Interfaces:** Produces `LoanTerms`, `InterestConvention`, `AccrualInput`, `AccrualResult`, `AllocationInput`, `AllocationResult`, `ScheduleInput`, `LoanSchedule` and `LoanDomainError`. Functions: `accrue_interest(input: &AccrualInput) -> Result<AccrualResult, LoanDomainError>`, `allocate_repayment(input: &AllocationInput) -> Result<AllocationResult, LoanDomainError>`, `project_schedule(input: &ScheduleInput) -> Result<LoanSchedule, LoanDomainError>`.

- [ ] Write exact-value tests: interest-free 60,000 / 5,000; partial one-time percentage 6,000 × 10% = 600; ACT/365 10,000 × 12% × 30/365 = 98.63; monthly 12,000 × 12%/12 = 120 and payment 1,100 leaves principal 11,020.
- [ ] Cover leap dates, half-open value-date intervals, same-day sequence, fixed-charge tranche residue, short/zero repayments, earned versus projected interest and non-amortizing arrangements.
- [ ] Implement typed calculations with high-precision carry and explicit policy/calendar/rounding versions. Monthly and daily policies cannot be interchanged silently. Reject incomplete conventions, invalid rates, missing intervals and unsupported currency precision.
- [ ] Keep this crate free of database, HTTP, Payroll and Employee dependencies. Include allocation ordering, excess credit and early payoff as selected policy inputs.
- [ ] User validation: from `hrms-svc`, `cargo test -p kabipay-loans-domain`.

### Task 3: Loans module and private repository

**Files:** Create `hrms-svc/crates/kabipay-loans/Cargo.toml`, `src/lib.rs`, `api.rs`, `contracts.rs`, `policy_service.rs`, `request_service.rs`, `payment_service.rs`, `deduction_service.rs`, `repository/mod.rs`, focused repository files and `tests/ledger.rs`; register the crate in the workspace and Payroll dependencies.

**Interfaces:** Consumes Task 1 storage and Task 2 domain types. Exposes `LoanModule`, `LoanActorScope`, `RecoveryQuoteInput`, `RecoveryQuote`, `PostRecoveriesInput`, `PostingResult` and `LoanModuleError`. `LoanActorScope` is constructed from validated session/service authorization, never browser-supplied roles.

Transaction-aware asynchronous operations:

- `lock_recovery_inputs(tx: &DatabaseTransaction, tenant: Uuid) -> Result<(), LoanModuleError>`;
- `quote_recoveries(tx: &DatabaseTransaction, input: &RecoveryQuoteInput) -> Result<RecoveryQuote, LoanModuleError>`;
- `validate_recovery_quote(tx: &DatabaseTransaction, quote: &RecoveryQuote) -> Result<(), LoanModuleError>`;
- `post_payroll_recoveries(tx: &DatabaseTransaction, input: &PostRecoveriesInput) -> Result<PostingResult, LoanModuleError>`;
- `post_fnf_recoveries(tx: &DatabaseTransaction, input: &PostRecoveriesInput) -> Result<PostingResult, LoanModuleError>`.

Public request/payment/policy commands receive validated scope, expected version and an idempotency key. They return typed results containing authoritative versions and references.

- [ ] Write database tests for duplicate commands with same/different payloads, funding ceiling, concurrent exposure checks, receipt allocation, overpayment credit, source uniqueness, guards and cross-tenant access.
- [ ] Implement immutable approved snapshots, policy activation validation, workflow approval bindings, no self-approval, partial funding, recorded external receipts, future deductions and explicit skips.
- [ ] Accrue earned interest to the posting value date under a locked watermark before allocating repayment. Reuse the same path for scheduled accrual and postings; overlapping intervals must fail.
- [ ] Standardize a tenant financial synchronization lock before other financial locks, then deterministic per-employee/account locking. All Loans/Payroll/FNF financial writers follow the same order. Quotes include revision evidence even for an employee with no existing accounts.
- [ ] Storage stays private to `kabipay-loans`. The transaction-aware API cannot commit, open another connection or make network calls. Add a boundary check preventing loan entity imports/loan SQL in Payroll and Employee source.
- [ ] Implement linked reversals, historical value-date reconciliation and audit classification; never mutate posted entries. Supply targeted ledger/database tests once disposable database setup is confirmed.

### Task 4: Authorized public API and generated clients

**Files:** Create `hrms-svc/crates/kabipay-payroll/src/loans/{mod.rs,query.rs,mutation.rs,types.rs,authorization.rs}`, `hrms-ui/src/api/documents/loans.graphql`; modify Payroll `lib.rs` and resolver roots, common `entitlement_graphql.rs`/`entitlements.rs` and canonical permission registration as required; extend gateway `schemaContract.test.ts`.

**Interfaces:** Exposes spec section 10 queries/commands with decimal strings, currency, cursor connections, `expectedVersion` and mutation idempotency keys. Generated operations feed the UI. Internal recovery contracts exclude private purposes, medical attachments and management notes.

- [ ] Write resolver tests proving SELF queries derive employee identity from the session, management scopes constrain every detail/list/mutation/export, and Loans entitlement is enforced independently of Payroll entitlement.
- [ ] Compose Loans query/mutation fields into the existing Payroll schema, preserving tenant resolver and audit mechanisms. File access uses existing authorized private storage.
- [ ] Translate typed financial errors without leaking internal records; schema stitching must reject duplicate authoritative fields and unauthorized internal coordination entry points.
- [ ] Regenerate Payroll SDL and gateway/UI contracts using existing tools. User checks: `cargo test -p kabipay-payroll`, gateway `npm test`, UI `npm run codegen` and `npm run graphql:check`.

## Phase B — Payroll and immutable payslip evidence

### Task 5: Quote, capacity and atomic payroll posting

**Files:** Modify Payroll `services/{prepare_payroll.rs,payroll_draft.rs,payroll_fingerprint.rs,payroll_finalize.rs,imported_payroll.rs,automatic_payroll.rs,payroll_rules.rs,payslip_presentation.rs}`. Create `services/loan_recovery.rs`, `tests/loan_recovery.rs` and the additive payslip/source evidence migration needed for finalized loan snapshots.

**Interfaces:** Consumes Task 3 `RecoveryQuote` and posting API. Produces prepared per-loan principal/interest recovery lines and immutable `PayslipLoanSnapshot` with opening, recovered and closing balances, source IDs, value date and terms/calculator versions.

- [ ] Write tests for import and automatic paths, supplement cycles, no salary/LWP, multiple loans, overrides, skipped periods, final payoff cap, shortage policy and finalized-period locks.
- [x] Obtain loan recovery through the module API during preparation. Apply reviewed policy capacity after applicable deductions and show deferred amounts explicitly; require known loan state for each eligible employee when Loans is enabled.
- [x] Combine the Loans revision contribution with the existing payroll fingerprint without reading loan tables here. Obtain the financial synchronization lock before existing input locks, then call `lock_recovery_inputs` in the agreed order.
- [x] Revalidate the quote inside finalization, persist payslip evidence and post repayments in its existing transaction. A posting failure rolls back payslips, loan entries and cycle status together. Test a concurrent external receipt and finalization.
- [x] Store loan recovery distinctly from salary-already-paid settlement, employer PF, statutory deductions and taxable benefit assessments. Historical imports do not invent loan repayment evidence.
- [ ] Protect cancellation/reversal with source-linked compensating entries and closed-period rules. User checks: `cargo test -p kabipay-payroll --test loan_recovery` plus existing draft/finalization/import tests affected by the change.

**2026-10-09 execution checkpoint:** Phase B and focused checks were explicitly authorized. Migration 0105 stores immutable Payroll-owned evidence and protects its issued payslip and statement. Draft payment dates can be corrected only against the current reviewed revision and input fingerprint; editing requires recalculation. Existing payslip templates, print/PDF and draft review now display loan evidence. Loans retains generic currencies; payroll recovery fails closed outside the existing INR/two-decimal payroll engine. No FX or payroll cancellation/reissue capability was introduced. The user selected preview now and finalization on/after the payment date in the company timezone. Payroll now rechecks date readiness during calculation, draft reads and finalization; the existing Loan future-posting guard is retained. Focused evidence and deferred acceptance work are recorded in `.loan-implementation/progress.md`; this is not production release acceptance.

## Phase C — Resignation coordination and FNF ownership

### Task 6: Durable financial review authorization

**Files:** Create Loans `src/exit_review.rs`, `exit_authorization.rs`, `tests/exit_authorization.rs`; Payroll `src/finance_api/{mod.rs,authorization.rs,routes.rs}`; Employee `src/services/{finance_client.rs,separation_approval_operation.rs}`; private dispatcher/reconciliation handlers. Add `0106_loan_exit_coordination/loan_exit_coordination.xml` and generated records for exit review/guard, HR operations and private delivery evidence.

**Interfaces:** Finance operations `prepareExitApproval`, `confirmExitApproval`, `cancelExitApproval`, plus bound operation-status queries. Requests bind tenant, employee, separation, HR operation, actor and reviewed loan/separation/decision versions. No generic browser token is sufficient to invoke internal commands.

**State contract:** HR operations are `REGISTERED`, `COMMITTED` or `CANCELLED`. Finance authorizations are `AUTHORIZED`, `CONFIRMED`, `CANCELLED` or `RECONCILIATION_PENDING`. A pending/unreachable HR status never implies cancellation. All commands are idempotent and bind their payload hashes.

- [ ] Register the HR operation durably before requesting Finance authorization. Build current exposure/forecast with explicit pending FNF inputs; record source allocations, residual arrangement, responsible owner and evidence.
- [ ] Finance acquires a guard over reviewed inputs only after validating scope and versions. Loan mutations encountering it receive a typed retry/review conflict. The browser cannot authorize another employee or substitute a separation.
- [ ] Employee performs its guarded separation/clearance transition and records the operation result plus private confirmation event atomically. Call Finance before this transaction; no network wait holds database financial locks.
- [ ] Deliver confirmation/cancellation with durable per-consumer deduplication. Finance confirmation links/prepares the FNF draft without posting recovery. Private events cannot flow to wildcard webhooks.
- [ ] Reconcile lost replies, duplicate delivery, crash before HR commit, crash after HR commit, rejected approvals and expired reviews. Release guards only against authoritative terminal operation state. Test every transition and same-day offboarding ordering.

### Task 7: FNF financial module and coordinated single-writer transfer

**Files:** Create Payroll `src/fnf/{mod.rs,service.rs,allocation.rs,query.rs,mutation.rs,types.rs}`, `tests/loan_fnf.rs`; modify Employee `services/{offboarding_fnf_service.rs,separation_service.rs}` and resolver query/mutation/types files, Payroll resolver roots and gateway schema-contract tests.

**Interfaces:** FNF financial queries/mutations have one authoritative Payroll owner. Employee retains clearance and employment-state writes. FNF calls Task 3 `post_fnf_recoveries`; Finance API coordinates authorization from Task 6.

- [ ] Split existing FNF financial code from clearance code; preserve IDs and existing processed records. Remove Employee financial writes and replace any temporary compatibility entry point with authenticated Finance delegation.
- [ ] Introduce itemized loan recovery/source allocations separately from existing other recoveries. Existing generic recovery remains other recovery unless explicitly reviewed and reclassified; do not seed loan balances from it.
- [ ] Requote at settlement value date, subtract already posted payroll/receipt recovery, validate complete eligible payout sources and prevent duplicate final salary or loan allocations.
- [ ] Finalize settlement and loan postings in one Payroll transaction. Pin the example payoff 20,000, eligible payout 12,000, recovery 12,000, employee payout zero and residual debt 8,000.
- [ ] Test unchanged legacy finalized records, drafts with generic recovery, late receipt, stale review, unsupported set-off pools and residual external servicing after exit.
- [ ] Ship ownership transfer in a coordinated service/gateway release: there must never be two active FNF writers or ambiguous stitched fields. User checks: `cargo test -p kabipay-payroll --test loan_fnf`, affected Employee tests and gateway `npm test`.

## Phase D — Approved UI and release acceptance

### Task 8: Loans screens, permissions and navigation

**Files:** Create `hrms-ui/src/modules/loans/{MyLoansPage.tsx,LoanAdministrationPage.tsx,LoanPoliciesPage.tsx,loanTypes.ts,loanQueries.ts,loanActions.ts,loanValidation.ts}`; focused `components/`, `hooks/`, `guidance/` and tests. Modify `src/navigation/{navigationModel.ts,navigationWorkspaces.ts,workplaceDestinations.ts}`, `src/auth/{permissions.ts,permissionCapability.ts}`, `src/routes/{appRouteConfig.tsx,routeTypes.ts,RouteGuards.tsx}` only where required by the established capability mechanism.

**Interfaces:** Uses generated Task 4 operations and shared page workspace/task-selector patterns. Destinations `/loans/my`, `/loans/admin`, `/loans/policies`; account/request views remain loan workspace tasks. Loans root sits beside Pay & Benefits, filtered by subscription/capability.

- [ ] Implement the approved employee list/request/account history, management request review/approval, account list, payment recording, deduction arrangement and policy screens with small cohesive forms and hooks.
- [ ] Add UI tests for unauthorized direct routes, employee self visibility, complete decimal input, duplicate submit, stale review, partial funding, excess receipt, failed submission preservation and policy activation errors.
- [ ] Match `ui-review.pen` shared navigation/header, compact tables, information popovers, mobile stacked records, 44px touch controls and dark variables. Preserve keyboard focus and screen-reader field errors.
- [ ] Reuse current workflow inbox, authorized attachments, notifications and contextual tours. Do not expose confidential admin notes in employee pages.
- [ ] User checks: `npm test -- src/modules/loans src/navigation src/routes`, `npm run graphql:check`; then affected lint/typecheck after generated client changes.

### Task 9: Payroll, payslip and exit UI integration

**Files:** Modify Payroll workspace/draft review components and `components/{EmployeePayslipDetails.tsx,PayslipDocument.tsx,PayslipSheet.tsx,PayslipTableSheet.tsx}`, `src/utils/generatePayslipPdf.ts`, `src/modules/workplace/components/SeparationRequestsCard.tsx`; create Loans `components/{PayrollLoanReview.tsx,PayslipLoanBreakdown.tsx,ExitFinancialReview.tsx}` and focused tests. Extend existing Payroll/Employee operation documents discovered at implementation time, using generated exports.

**Interfaces:** Displays Task 5 immutable payslip snapshots and Tasks 6–7 reviewed authorization/FNF allocations. Payroll and Hiring & Exit retain their existing menu ownership.

- [ ] Add principal/interest/balance evidence to payroll review and both existing payslip templates, browser print and generated PDF; later receipts must not change finalized payslip numbers.
- [ ] Block payroll finalization for stale/unknown loan inputs; explain recalculation and capacity deferrals. Do not include employer PF in deductions/net pay or loan balance calculations.
- [ ] Show financial review before resignation approval, pending components, payoff forecast, recovery decision and residual arrangement; require refreshed reviewed versions after date/balance changes.
- [ ] Test unavailable Finance state, idempotent retry, disabled approval/finalization controls, repayment/payslip linking and final payroll versus FNF allocation without double counting.
- [ ] User checks: targeted Loans/Payroll/Separation UI tests, `npm run lint`, `npm run build`. Perform authenticated browser and PDF checks after runtime setup is available.

### Task 10: Reconciliation, rollout and acceptance evidence

**Files:** Create `hrms-documentation/docs/runbooks/employee-loans.md`, migration/permission reconciliation checks and focused service reconciliation tests; update the functional spec and UI review context only for approved implementation differences.

**Interfaces:** Reconciliation reports tie loan ledger totals to disbursements, receipts, payroll sources, FNF sources, excess credits and authorization operations. No automatic mutation repairs without reviewed authority.

- [ ] Exercise authorization, decimal calculation, concurrency, posting rollback, private event retry and legacy FNF migration in disposable databases. Record actual results separately from static/code inspection.
- [ ] Validate generated/stitched GraphQL schema ownership, module dependency readiness and UI navigation while preserving payroll behavior for tenants without Loans enabled.
- [ ] Prepare rollout order: additive schema/catalog → coordinated Payroll/Employee/private-consumer/gateway release → generated UI → configured policies/permissions → authenticated acceptance → explicit tenant activation.
- [ ] Reconcile existing FNF records and review baseline regression behavior before enabling loan recovery. Opening balances/imports remain a separate reviewed task.
- [ ] Review all approved screen flows, mobile/dark accessibility, both payslip outputs and resignation/FNF residual behavior. Document unresolved business configuration and deployment limits.
- [ ] Run `git diff --check` for changed repositories; provide user-owned test/build commands and results. No completion claim without the relevant runtime/concurrency evidence; no commits or live rollout here.

## Execution and review checkpoints

Execute inline in dependency order, without subagents unless explicitly authorized. Phase A creates the ledger and lifecycle; Phase B adds payroll; Phase C transfers FNF and coordinates HR; Phase D completes UI and acceptance. Each phase ends with reviewable code and focused validation evidence; partial phases are not a production-ready loan feature. A financial validation failure blocks progression into dependent finalization work.

The plan was self-reviewed against functional requirements R1–R8, spec sections 4–16 and all 17 approved screen examples. Full execution begins after the cost/execution approval required by the user's instructions; tenant/employer identity must be answered before dependent storage work.


**11 October implementation checkpoint:** The user authorized completing remaining implementation and local checks. Loans, employee/HR screens, configurable servicing, Payroll/payslip recovery, resignation coordination, FNF ownership/calculation and residual arrangements are implemented. Migration 0107 adds immutable financial reconciliation reports and evidence-backed recovery holds; 0108 extends posting validation for reviewed late external payments without changing issued Payroll/FNF allocations. HR/Admin pending-resignation funding exceptions require recorded reason and exact company HR/disbursement scopes. New late payments require both payment and correction ALL authority and a fresh fingerprint-bound review. Waivers/refunds remain outside the first-release command set under spec section 7. Detailed current validation evidence is in the execution ledger and runbook; authenticated browser, full Liquibase upgrade and deployment/configuration acceptance are release gates, not completed checks.
