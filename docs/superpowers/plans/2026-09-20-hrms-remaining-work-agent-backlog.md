# HRMS remaining work: multi-agent task backlog

Prepared 20 September 2026. Status: source review and implementation approved; bounded performance and permission-service tasks executing. The user confirms prior runtime acceptance, migrations and release validation are complete for existing implemented features. New implementation still requires focused verification.

**Latest execution rules after interruption:** User will run tests, lint, typechecks and builds and share results. Agents perform coding only and provide unrun verification commands. Use Terra/Luna at high reasoning and default speed, a dedicated Luna summariser for logs/history, bounded relevant-file prompts, and RTK shell commands. Read lint constraints before coding; do not create oversized files and postpone decomposition. These rules supersede earlier agent-run verification steps below.

**Goal:** Close verified HRMS gaps without rebuilding implemented features or confusing local checks with runtime acceptance.

**Execution:** Current selected model owns source review, design, task contracts, coordination, security review and integration. Initial bounded coding used `gpt-5.6-luna` with medium reasoning. After review exposed UI state-management failures, the coordinator assigned corrective coding and stronger backend tests to `gpt-5.6-terra` with high reasoning; Luna handles isolated component extraction. Model escalation remains within the user's lower-model coding instruction. Shared source files have one owner.

**Stack:** Rust services, React/TypeScript UI, GraphQL gateway and Liquibase/PostgreSQL.

**Inputs:** `hrms-documentation/docs/HRMS-REMAINING-WORK-2026-09-08.md` and `docs/superpowers/reviews/2026-09-10-d5-gap-review.md`, relative to workspace root. Read their later verification records before relying on older findings.

This is a task-dispatch backlog, not a source-verified implementation specification. Paths below are confirmed entry points; reported defects must be reproduced against the current checkout before coding. Exact contracts and affected tests belong in the coordinator's task brief after T0.

## Current evidence and constraints

- The handoff records the original enhancements, entitlements, surveys and configurable attendance day as implemented. The user's 20 September confirmation closes their prior runtime, migration and release backlog; older unchecked release items are historical. This session does not independently recheck deployment.
- UI, service and gateway worktrees were clean at inspection. Database has existing README/migration README and seed-script changes. Documentation has existing handoff, deployment environment example and attendance verification changes. Preserve them; capture status again before execution.
- No automatic commits, deployments, migration execution, emails or live tenant writes. Do not run Dart or Flutter commands.
- MFA/login/password recovery remains excluded. Statutory payroll, email-service architecture and optional product expansion need separate scope decisions.
- Existing source implementation must not be removed simply because an old checklist is unchecked.
- Ask before token-expensive execution. Approval of the review does not authorize the entire optional product backlog.

## T0 — Reconcile backlog against current source (priority 0)

**Owner:** Current model. **Dependency:** Approval for deeper review. **Deliverable:** Evidence matrix and bounded implementation briefs.

- [ ] Read final attendance, entitlement, survey, appraisal-validation and appraisal-concurrency records linked from the handoff.
- [ ] Trace each reported performance defect through resolver, transaction/service and UI; record file/line evidence and current regression coverage.
- [ ] Inspect relevant repository instructions and scripts before selecting validation commands.
- [ ] Classify each item as implemented/local verification pending, confirmed code gap, runtime acceptance pending, product decision required, or excluded.
- [ ] Resolve stale handoff directions: D1 is already resolved, entitlement implementation is already recorded, and the migration checklist stopping at 0080 omits later recorded changes through 0087. Inspect actual changelogs before proposing execution order.
- [ ] Produce a coding brief per confirmed gap with allowed files, existing business rules, exact API contract, negative cases and pass criteria. Do not invent a mutation or migration to fill a documentation gap.

**Done when:** Every approved coding task has source evidence and an independently reviewable acceptance contract. Historical test counts are labelled historical.

## T1 — Goal correction workflow (priority 1, conditional coding)

**Owner:** Luna coding agent A; current-model design/review. **Dependency:** T0 and agreed edit/remove/manager authority rules.

**Entry points:**
- `hrms-svc/crates/kabipay-performance/src/resolvers/mutation.rs`
- `hrms-svc/crates/kabipay-performance/src/services/performance_workflow.rs`
- `hrms-svc/crates/kabipay-performance/src/services/performance_lifecycle.rs`
- `hrms-ui/src/modules/workplace/performanceLifecycleQueries.ts`
- `hrms-ui/src/modules/workplace/PerformanceLifecyclePanel.tsx`
- `hrms-ui/src/modules/workplace/PerformancePage.test.tsx`

- [ ] Reproduce the reported inability to correct an over-100 goal total; check whether newer source already resolves it.
- [ ] Coordinator defines permitted stages, edit/delete ownership, behavior for approved goals, and whether manager goal creation is in scope. Preserve current authority until a change is explicitly agreed.
- [ ] Implement the approved correction flow with tenant/role checks and transactional stage validation, preserving the cycle-lock ordering used by proposal/approval and stage advancement.
- [ ] Verify correcting an excessive total, unauthorized and cross-tenant attempts, disallowed stages, failed-write rollback and concurrent stage advancement. Real database race checks must be identified separately from unit tests.
- [ ] Provide changed-file list, root cause, focused test results and remaining runtime gates to the coordinator.

**Done when:** An authorized actor can correct goals within agreed stages; invalid edits cannot bypass approval or race stage advancement; coordinator approves the source and tests.

## T2 — Appraisal acknowledgement and closure (priority 1, conditional coding)

**Owner:** Luna coding agent A, after T1 (shared files). **Dependency:** T0 and explicit acknowledgement/closure policy.

**Entry points:** Same performance resolver/services and UI lifecycle files as T1.

- [ ] Reproduce reported timestamp/comment overwrites and closure without acknowledgement.
- [ ] Coordinator confirms repeat-submission behavior and whether acknowledgement is mandatory for closure; define any HR override explicitly before implementation.
- [ ] Implement the agreed state transition transactionally, preserving permission checks and audit evidence.
- [ ] Verify repeat and simultaneous acknowledgements, unauthorized actors, premature closure and the approved override behavior if one exists.
- [ ] Run focused regressions for T1 and T2 together after the final shared-file change.

**Done when:** Acknowledgement and closure match the agreed policy, including replay/concurrency behavior, with coordinator review.

## T3 — UI lint and regression reliability (priority 1)

**Owner:** Luna coding agent B; current-model triage/review. **Dependency:** T0, approved check scope and disjoint file ownership.

**Entry points:** `hrms-ui/package.json`, `hrms-ui/src/modules/workplace/PerformanceLifecyclePanel.tsx`; discover current permission-service paths before assigning them.

- [ ] Coordinator establishes current failures from scoped lint/tests; historical lint failures are not automatically current defects.
- [ ] Extract cohesive UI units and fix confirmed causes without disabling lint rules or changing role behavior. Avoid broad unrelated refactoring.
- [ ] Work only on files outside agent A's ownership; defer performance-panel restructuring until T1/T2 finish.
- [ ] Investigate regression timing failures using the failing cases; do not treat a larger timeout as proof of stability.
- [ ] Run affected tests and lint, then the approved default regression gate once integration is ready.

**Known focused test command:** From `hrms-ui`, `npm test -- src/modules/workplace/PerformancePage.test.tsx`.
**Known backend command:** From `hrms-svc`, `cargo test --offline -p kabipay-performance --lib`.
These commands are candidates for approved execution, not checks performed during this review. A missing offline dependency is an environment issue to report.

**Done when:** Assigned lint failures are resolved without suppressions and relevant behavioral checks pass; full-suite status is reported accurately.

## T4 — Release acceptance pack (priority 0 planning, runtime execution gated)

**Owner:** Current model. **Updated status:** User confirmed this work complete for previously implemented features on 20 September. The checklist below is retained as historical scope, not a request to repeat release work. Verify new changes independently.

- [ ] Inventory included migrations and prerequisites, including later attendance/survey/permission migrations; prepare read-only migration-state checks before applying anything.
- [ ] Specify matched gateway/service/UI versions, dedicated permission grants, private media storage/proxy, invitation origin/signing and delivery configuration without copying secrets into evidence.
- [ ] Prepare Employee, Manager, HR/Admin and unauthorized-user journeys with expected data transitions and evidence locations.
- [ ] Cover entitlement revocation/expiry, tenant isolation, queued-work races; survey suppression and visibility; attendance boundaries/DST/incomplete punches; comp-off expiry/reservations; unpaid leave and closed payroll.
- [ ] Include video access/limits, pre-joining conversion replay/rollback, report reconciliation/CSV escaping, large-export measurement and worker retry/idempotency/consent.
- [ ] Include signed-in desktop/tablet/mobile, keyboard/focus and modal acceptance. Recheck browser availability rather than assuming the old bootstrap failure persists.
- [ ] Record unavailable environments as blocked runtime gates, not code failures or completed acceptance.

**Done when:** The acceptance pack names prerequisites, expected results and evidence per flow. Runtime closure requires actual authorized execution; source tests cannot satisfy it.

## T5 — Completion documentation (priority 2)

**Owner:** Current model, after evidence from T0–T4.

**Files:** `hrms-documentation/docs/HRMS-REMAINING-WORK-2026-09-08.md`, `hrms-documentation/docs/module-completion-status.md`, `hrms-ui/FEATURES.md`.

- [ ] Correct stale implementation claims and broken relative source/document links, preserving existing user edits.
- [ ] Record source implementation, local validation, runtime QA and deployment independently.
- [ ] Link current verification evidence and retain explicit blockers instead of checking every box.

**Done when:** The handoff gives the next developer an accurate continuation order with no instruction to rebuild already-completed work.

## Deferred product decisions

- Performance calibration records, HR-only feedback, audited reopen, exclusions/exceptions, program archive, population/KPI setup and automatic stage transitions need individual designs.
- Statutory payroll needs jurisdiction, effective-date and specialist-approved reference cases before implementation.
- Reusable queued email needs its own architecture, broker contract and threat model after existing release/security closure.
- Follow-up queues, payroll readiness, renewals, exit clearance, saved/scheduled reports, roster swaps, generic employee import, recruitment, LMS, compensation, benefits and grievances require workflow audits before declaring missing implementations.
- MFA/login/recovery remains excluded unless the user changes the boundary.

## Dispatch and integration rules

1. Current model completes T0 and freezes each task's scope before dispatch.
2. Agent A owns performance changes; agent B may work on confirmed disjoint UI defects. Shared files, generated GraphQL outputs and migrations have one owner at a time.
3. Give each coding agent only its task brief, relevant source paths, constraints and tests. No full-history fork for lower-model workers.
4. Each worker reports root cause, files changed, exact checks/results and unresolved issues. Coordinator reviews authorization, tenant isolation, transaction behavior and contract compatibility.
5. Run affected integration checks after combining changes; broaden checks only for material risk or observed failures. Do not claim browser/database acceptance from compile or unit-test results.
6. Leave all changes uncommitted for user review. Stop for missing business decisions or execution authority, while continuing independent approved work.
