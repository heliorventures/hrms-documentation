# Loan review fixes implementation plan

> **For agentic workers:** Use superpowers:subagent-driven-development for independent tasks, with coordinated Cargo verification and final review. No automatic commits or additional worktrees.

**Goal:** Resolve the eight findings from the 11 October production-readiness review and prove the corrected behavior with regression tests.

**Architecture:** Keep Loans storage private within the Payroll service. Persist contractual repayment dates independently of finite forecast rows; use shared calendar-period accrual rules and dated arrangements in projections. Expose workflow stage and employee-visible decisions through scoped APIs. Proposed deduction changes use read-only server previews and existing optimistic versions.

**Tech Stack:** Rust, PostgreSQL/Liquibase, async-graphql, React/TypeScript, Vitest.

**Spec:** ../specs/2026-10-07-loan-management-design.md

## Global constraints

- Tracking only, one company per tenant; preserve issued payslip/FNF records and historical financial evidence.
- Decimal money, explicit company policies, transaction-aware module boundaries, exact permission scopes.
- Work on existing feat/employee-loan-management branches; preserve unrelated documentation changes.
- No commits, deployments, live migrations, Dart/Flutter, or rtk commands.
- Coordinate all Cargo commands through the parent; disposable PostgreSQL only.

## Review focus

- Skips/short salary and pre-funding arrangements must not silently remove future recovery obligations.
- Pauses spanning calendar months must produce identical preview/posting interest and rounding carry.
- Future arrangements and month-end anchors must appear in projections with correct effective dates.
- Intermediate approvals must not submit final financial terms; returned reasons and withdrawal remain visible.
- Proposed-change previews must be read-only, permission checked, validated like writes, and invalidated when inputs change.

## Task 1: Financial schedule and accrual correctness

- [x] Add failing domain/database regressions for review findings 1, 3 and 4.
- [x] Correct recurring schedule eligibility, retaining explicit first-due dates even before funding, with additive migration if needed.
- [x] Share accrual interval/pause calculations and project across dated arrangements.
- [x] Run domain and disposable database tests; review changes.

## Task 2: Request workflow and employee feedback

- [x] Add failing tests for intermediate/final approval payloads, returned decision reason and UNDER_REVIEW withdrawal.
- [x] Expose authoritative final-stage metadata and employee-visible reason; preserve server authorization.
- [x] Adapt approval form and request table/actions; verify service and UI contracts.

## Task 3: Proposed arrangement/override review

- [x] Add failing tests for explicit skip mapping and required proposed-change previews.
- [x] Add read-only previewLoanDeduction and previewLoanPeriodOverride queries using existing input DTOs and Loans validation/calculation.
- [x] Wire editors to server previews, with an explicit AMOUNT/SKIP action and no ambiguous blank-to-skip conversion.
- [x] Verify no preview writes, stale-version rejection, input-change refresh and financial summary display.

## Task 4: Integration and completion

- [x] Export actual service SDL and regenerate isolated Loan client; update gateway ownership contract.
- [x] Run affected Rust, PostgreSQL, UI and gateway tests, builds, migration checks and storage-boundary checks.
- [x] Independently review the complete fix diff and address confirmed regressions.
- [x] Update execution evidence/runbook as needed; report remaining deployed-environment acceptance gates honestly.

Local verification and residual release gates are recorded in [the runbook](../../runbooks/employee-loans.md#11-october-review-corrections). All eight findings and additional date/completion regressions are resolved in source and covered by the local checks. Pencil synchronization remains pending editor access; full tenant upgrade and authenticated deployed acceptance are separate release gates. No commit or deployment was performed.

## Coordination

Task 1 owns Loans arrangement/recovery/projection/domain and its migration. Task 2 owns request read DTOs and request UI. Parent owns new preview API/query endpoints and schema generation. Task 3 owns paymentEditor UI and tests, consuming preview queries. Shared exports/tests are coordinated rather than overwritten. Existing specification supplies behavior; repayment beyond an approved policy limit must require HR review rather than silently disappearing.
