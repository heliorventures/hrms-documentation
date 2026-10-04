# Performance Completion Implementation Plan

**Goal:** Complete the seven approved performance workflows while preserving existing submitted data and user-owned validation.

**Architecture:** Extend module-owned Rust services with transactionally shared manual/scheduled stage operations, explicit administration APIs, immutable revision/audit evidence and snapshotted program policy. React consumes a frozen GraphQL contract through focused components and hooks; existing employee/manager workflows remain integrated.

**Stack:** Rust, SeaORM/PostgreSQL, async-graphql, Liquibase, React/TypeScript.

**Spec:** `../specs/2026-09-22-performance-completion-and-payroll-scope.md`, approved by user.

**Completion checkpoint (22 September):** Source implementation and targeted source review are complete for P1-P7. Migration 0088 and focused regression cases are authored; no tests, lint, typechecks, builds or migrations have been executed by agents. The checklist below distinguishes implemented work from broader validation/coverage still required. See `../reviews/2026-09-22-performance-validation-handoff.md` for user-run commands and role journeys. Statutory payroll remains outside this completed source scope pending its required scope answers.

## Constraints

- User executes tests, lint, typechecks, builds and migrations. Agents may author regression cases and migration files but must not execute validation commands.
- No commits, deployments, live writes, dependency installation, Dart or Flutter commands.
- Use RTK shell commands, UTF-8 reads/writes, relevant-file context and Luna summaries. Coding uses Terra/Luna high reasoning without a speed override; coordinator retains planning/review.
- UI limits: 400 effective lines/file, 120/function, complexity 10, depth 3, statements 30; no suppressions. Split by responsibility before adding code.
- Preserve existing worktree changes. Existing validated feature branches are used in place; no branch reset or automatic worktree move.
- Payroll remains separately blocked on scope, without blocking performance work.

## Review focus

1. Tenant-scoped lookup before every write and explicit manage-ALL/private-feedback boundaries.
2. Cycle-before-participant lock ordering shared with submissions, calibration, reopen, exclude and automatic transitions.
3. Historical response/calibration/KPI evidence retained; no fabricated legacy calibration approval.
4. Archived programs cannot launch new cycles through either entry point; active cycles retain their snapshots.
5. Selection changes cannot route an old UI draft or response to a new participant. Mutations serialize conflicting operations and retain drafts on failure.

## Task 1: Freeze persistence and GraphQL contracts

- [x] Map existing 0075/0018 tables, latest migration identifier, worker integration and root schema constructors.
- [x] Reuse existing revision, calibration, audit, exception and KPI structures where their semantics fit; add migration fields/tables only for actual gaps.
- [x] Record exact input/output field names in `hrms-documentation/docs/superpowers/reviews/2026-09-22-performance-api-contract.md` before UI implementation.
- [x] Freeze correction-stage behavior: reopening one participant returns the cycle to SELF_REVIEW or MANAGER_REVIEW, retains other participants' submissions, and invalidates only the reopened participant's downstream completion in the new revision.

## Task 2: Backend administration and evidence

**Owner:** One Terra worker, service and authored migration files. Coordinator reviews schema/API/security decisions.

**Files:** New focused modules under `hrms-svc/crates/kabipay-performance/src/services/administration/`; administration resolver/type modules under `src/resolvers/`; bounded integration changes in existing mutation/query/workflow modules. Liquibase append-only migration under `hrms-database/changelog/migrations/` using the verified next identifier. Update entities only where required by the chosen persistence contract.

- [x] Implement calibration decisions and finalization prerequisites without changing saved manager answers.
- [x] Implement revision-preserving reopen and restricted history access, including legacy provenance handling.
- [x] Implement reasoned participant exclusion/restoration before self-review and exception management/retry.
- [x] Implement private HR feedback through separate manage-only reads/writes; public detail stays filtered.
- [ ] Author focused role, stage, tenant and replay regression cases; do not execute them.

## Task 3: Program policy, KPIs and scheduling

**Owner:** Same backend owner; no overlapping service/migration edits.

- [x] Add archive guard to manual and scheduled cycle creation under the same program lock.
- [x] Implement one-mode population selection, tenant-valid identifiers, and immutable launch population snapshots.
- [x] Implement KPI target/unit CRUD during goal setting; invalidate affected goal approval. Actual/evidence changes respect employee/manager stage and submission/revision locks.
- [x] Store cycle-snapshotted tenant-local stage deadlines. Share prerequisite validation and writes between manual advancement, automatic advancement and exception retry.
- [x] Advance at most one stage per cycle/run. Deduplicate actionable exceptions and resolve them only after the corresponding prerequisite succeeds.
- [x] Integrate the existing worker caller and retain scheduled cycle creation behavior.
- [ ] Author meaningful concurrency/idempotency/permission regression cases without running them.

## Task 4: Complete the role-specific UI

**Owner:** Terra UI worker only after the API contract is frozen. Disjoint from backend files.

**Files:** Focused components/hooks/documents under `hrms-ui/src/modules/workplace/performance-admin/`; bounded integration in PerformancePage, program setup and review detail. Preserve the previous performance work and its tests.

- [x] Admin cycle/participant view exposes excluded participants and actionable exceptions, including empty-population cycles.
- [x] Calibration, revision history and reasoned reopen/exclusion dialogs with confirmation and clear downstream effects.
- [x] HR-only feedback interface uses only manage-authorized operations; TEAM/SELF never request it.
- [x] Program policy editor exposes population mode, identifier selection, deadlines and archive with explicit effects.
- [x] Employee/manager KPI controls obey the backend authority/stage contract.
- [ ] Add focused regression cases for denied access, failed writes, stale selection and each complete flow. Do not run them.

## Task 5: Integration and user handoff

- [x] Coordinator inspects targeted source/diffs selected by the compact source map; review the final API/schema/UI relationships without running validation.
- [x] Update gateway required-field contract and fixtures for new UI-required fields.
- [x] Update remaining-work and completion records with coded versus unverified status and migration prerequisites.
- [x] Provide exact user commands for validation plus role-based acceptance journeys. Do not label the implementation production-ready before the user supplies passing evidence.

Focused authored regressions cover reviewer draft transitions, unauthorized administration requests, stale KPI drafts, cursor validation, KPI stage authority, appraisal state/revision guards, deadline fallback/override and date overflow. The broader tenant/concurrency/replay and complete-flow coverage items above remain open; these require further evidence rather than being implied by the source review.

## Execution rulings

- Existing approval covers these performance tasks and ordinary implementation decisions within the written spec; no repeated per-task permission prompts.
- Historical revisions include sensitive appraisal content and therefore use the existing review authorization boundary; administrator audit/private feedback are manage-ALL only.
- Population mode chooses ALL, DEPARTMENTS, LOCATIONS or EMPLOYEES. No implicit intersection/union across different modes.
- Scope is complete user flows, not additional unrelated module features or a new scheduler infrastructure.
