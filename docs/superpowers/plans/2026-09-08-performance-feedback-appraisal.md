# Performance, Feedback, and Appraisal Implementation Plan

**Goal:** Add reusable monthly, quarterly, yearly, and manual performance programs; immutable appraisal questionnaires; employee self-review; manager evaluation of snapshotted subordinates against goals and feedback; and auditable cycle stages.

**Architecture:** Extend the existing performance subgraph and `review_cycle` authority. A reusable program generates cycle instances. Published template versions and participant snapshots protect in-progress reviews from later organization changes. Rust services own stage transitions and authorization; the shared worker only invokes idempotent scheduled-cycle generation.

**Security invariants:**

- `performance:manage=ALL` controls programs, templates, cycle launch, and organization-wide status.
- `performance:evaluate=TEAM` additionally requires the participant's snapshotted manager ID to match the caller's employee ID.
- `performance:self=SELF` additionally requires the participant employee ID to match the caller's employee ID.
- Role names never authorize runtime requests.
- Submitted self and manager answers are immutable.
- Manager answers cannot overwrite self answers, and HR calibration cannot overwrite either submission.
- Every query and mutation is tenant-bound before reading or writing rows.

## Task 1: Database lifecycle contract

Create migration `0075_performance_appraisal_lifecycle` and a PowerShell contract test. Add:

- `performance_program` with cadence, anchor date, stage configuration, rating bounds, status, and active-template reference;
- versioned `appraisal_template`, ordered sections, questions, and stable options;
- `review_cycle` program, period, template, stage, and due-date columns;
- `performance_participant` with manager/department/designation/location snapshots and submission state;
- `appraisal_answer` with separate employee and manager answer/rating columns;
- `continuous_feedback` for manager/direct-report and HR evidence;
- `performance_admin_exception` for failed scheduled transitions;
- canonical `performance:evaluate` TEAM and `performance:self` SELF permissions and scopes.

Use uniqueness constraints for `(program_id, period_key)`, template version, participant per cycle/employee, answer per participant/question/revision, and manager feedback idempotency where applicable. Make the migration forward-only because it contains durable review responses.

## Task 2: Generated entities

Generate only migration 0075 entities and confirm the existing entity generation contract. Do not hand-edit generated database models.

## Task 3: Rust lifecycle service

Add pure validation tests before implementation for:

- supported cadence and deterministic period keys;
- legal cycle stage transitions;
- one-level question nesting and question-type/option rules;
- rating bounds;
- total approved goal weight exactly 100 before self-review;
- immutable submitted phases;
- manager relationship checks based on the participant snapshot.

Implement tenant-scoped transactions for program/template saving and publishing, cycle launch, goal upsert/approval, continuous feedback, self submission, and manager submission. Lock participant rows for final submissions and store audit actions without answer bodies.

## Task 4: GraphQL contract

Expose:

- Admin/HR: programs, templates, cycles, save/publish/launch operations;
- Employee: own participants/goals, goal proposal, self-review submission;
- Manager: team participants/goals/visible feedback, goal approval, feedback creation, manager-review submission.

Authorization must run before tenant database access where possible. Inputs for self and manager operations never accept a caller identity; identity comes from claims.

## Task 5: Scheduled cycles

Add the performance crate as a library and invoke an idempotent `process_due_performance_cycles` function from the existing outbox worker using the same tenant-local date used by other scheduled sweeps. Log counts only.

## Task 6: Gateway and UI schema

Add the new required client fields to the gateway fail-closed contract. Extend UI schema/documents without discarding concurrent attendance work. Use safe local operation documents until full codegen can run against a live gateway.

## Task 7: Permission-composed UI

Replace the performance catalog-only page with compact sections:

- Admin/HR: program cadence, cycle stages, appraisal questionnaire builder, and launch controls;
- Manager: team reviews with goals, feedback, employee answers, and manager ratings;
- Employee: own goals, questionnaire responses, self-ratings, submission, results, and acknowledgement.

Do not issue operations for sections the signed-in user cannot access. Final submissions require explicit user action and show validation failures.

## Task 8: Verification

Run migration contract, focused Rust tests, performance/outbox compilation, gateway schema tests, focused UI tests, TypeScript build, formatting checks, and diff review. Do not run migrations, deploy, or commit.
