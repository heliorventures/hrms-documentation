# Unpaid-leave calculation and payroll locking

**Spec:** ../specs/2026-09-08-hrms-enhancements.md, Phase 2.

**Goal:** Implement the confirmed monetary calculation and ensure payroll execution cannot alter a closed or concurrently processed cycle.

**Architecture:** Decimal arithmetic calculates basic salary / configured divisor * approved unpaid days. The pay-run transaction locks its tenant-qualified cycle before checking DRAFT state. Policy storage and deduction placement will follow the pending business-rule response.

**Constraints:** Preserve current dirty work. No commits, deployment, live database execution, or Dart/Flutter commands. This core alone does not enable deductions.

## Task 1: Monetary calculation

Files: `hrms-svc/crates/kabipay-payroll/src/services/unpaid_leave_calculation.rs`, `services/mod.rs`.

Interface: `calculate_unpaid_leave(basic: Decimal, divisor: Decimal, unpaid_days: Decimal) -> KabiPayResult<Decimal>`.

- [x] Test configured divisor, half days, zero leave, invalid/negative inputs, and final monetary rounding. Example: basic 30000 / 30 * 1.5 days = 1500.
- [x] Observe failing assertions before implementation.
- [x] Use checked Decimal operations and round only the final deduction to two decimal places. Reject zero/negative divisors, negative basic/days and arithmetic overflow; never substitute a default divisor.
- [x] Run focused payroll tests.

## Task 2: Pay-run transaction boundary

File: `hrms-svc/crates/kabipay-payroll/src/services/payroll_service.rs`.

- [x] Move tenant-qualified payroll-cycle lookup into the transaction and acquire an exclusive row lock before validating DRAFT status.
- [x] Keep all payslip writes and cycle status transition in that same transaction.
- [x] Verify closed-cycle rejection and inspect existing payroll mutation access tests; run scoped payroll tests.

## Policy decisions pending

- Unpaid-leave placement relative to statutory calculations: question sent to user.
- Comp-off limit dimensions and authoritative weekly-off schedule: questions sent to user.

No dependent policy choice is inferred from elapsed time or missing answers.

## Verification record

- Payroll tests: 27 passed after observing three monetary regression failures and the transaction-order regression failure before implementation.
- Scoped git diff --check passed. Independent read-only review found no material defects.
- Proxy tests establish query/transaction ordering, not live PostgreSQL concurrency or rollback proof.
- No payroll deduction is enabled by this core; configuration, per-period leave allocation, snapshots and UI remain pending integration.
- No commits, migrations, live database writes or deployment were performed.

