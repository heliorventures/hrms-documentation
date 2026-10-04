# Performance completion and statutory payroll scope

Status: user approved the proposed performance scope and phased implementation on 22 September 2026. Payroll jurisdiction, effective dates, filing scope and statutory reference approver remain unanswered; payroll coding is not started.

## Objective and existing authority

Complete the seven listed performance workflows and separately replace payroll stubs within a confirmed statutory scope. Reuse the existing services, UI, permissions, scheduler, goals and participant snapshots. Preserve current uncommitted work.

The performance baseline is `2026-09-08-automated-events-performance-surveys-design.md`, especially Participants, Lifecycle, Continuous feedback and Audit. Its settled rules are retained: reasoned exclusion before self-review, prerequisite-gated automatic transitions, immutable closed submissions, audited reopening with preserved revisions, and calibration without overwriting employee/manager submissions. Current positive goal-weight bounds remain unchanged.

## Proposed performance delivery

| Task | Complete user flow | Dependency |
| --- | --- | --- |
| P1: calibration | HR opens submitted manager reviews, records a final rating/band and reason, reviews previous decisions, and finalizes calibration. Employee and manager answers remain separate and unchanged. | Revision/audit data contract |
| P2: reopen and correction | Manage-ALL actor chooses a permitted correction stage and records a reason. A new response revision is created; prior responses and decisions remain accessible as history. Resubmission and downstream completion gates apply again. | Revision/audit data contract |
| P3: exclusions and exceptions | HR excludes participants before self-review with a reason, sees blocked transitions and their causes, fixes prerequisites, and retries through the same idempotent domain operation. | Existing stage guards; P1/P2 for new prerequisites |
| P4: private HR feedback | Authorized HR creates explicitly private feedback; employee and manager APIs/UI never expose private entries. Existing employee-visible feedback remains unchanged. | Visibility enforced before DTO construction |
| P5: program archive | HR archives an active program, preventing new manual/scheduled cycles. Existing cycles and history remain accessible and continue under their recorded settings. | Scheduler and launch share archive guard |
| P6: population and KPIs | HR configures all eligible employees or selected departments, locations or explicit employees; launch snapshots the selected eligible population. Authorized users maintain goal KPIs with targets, units, actuals and evidence/comments. | Existing goal authority; immutable launch snapshot |
| P7: automatic stage transitions | HR configures deadlines; the scheduler advances due stages only when all prerequisites pass. Blocked stages produce deduplicated actionable exceptions; retry does not duplicate transitions. | P1-P3, P5-P6 and shared manual/automatic transition service |

## Proposed policy details requiring approval

- Calibration requires an explicit HR decision for every included participant before leaving the enabled calibration stage. No implicit acceptance of a manager rating.
- Reopening is an explicit exceptional action, including for a closed cycle. Preserve prior revisions; invalidate completion/acknowledgement downstream of the chosen correction stage in the new revision. Never rewrite historical submission evidence.
- HR-only means `performance:manage=ALL`; TEAM authority alone cannot read private feedback. No retroactive change to existing employee-visible feedback.
- Archiving does not cancel active cycles, remove participants or delete history. Unarchive is outside this initial scope.
- Population selections use one explicit mode initially, avoiding ambiguous AND/OR combinations. Eligibility restrictions still apply; later program changes affect future launches only.
- KPI target/unit changes belong to goal setting and invalidate affected goal approval. Actual/evidence submission follows the appropriate employee/manager review stage and revision locks. No automatic KPI-to-rating formula.
- Program deadlines are tenant-local day offsets from cycle start, snapshotted as cycle stage deadlines. A late scheduler advances at most one eligible stage per cycle per run; it never fabricates missing submissions or acknowledges for an employee.
- Legacy manager-written final ratings must retain their provenance. Migration must not manufacture historical HR calibration decisions or revision history.

These defaults are proposals, not inferred existing business requirements. A coding contract will freeze schemas, APIs and role/stage acceptance cases after approval.

## Payroll: scope required before implementation

Current code is India-oriented, but this does not establish the production jurisdiction or required registrations. Confirm:

1. Country, applicable states, employing entities, and effective financial year/date.
2. Required scope: payroll deductions/contributions and reconciliation, or also filing-ready outputs such as EPF/ESI returns, TDS returns and Form 16.
3. Who supplies or approves statutory reference examples and registration-specific rules.

Payroll delivery will inventory existing calculations and exports, research applicable official rules, define effective-dated calculation contracts, author reference-case tests, and implement the agreed calculation/export flows. Do not advertise prep CSVs as official filing outputs. Production acceptance requires approved reference cases and the user's execution results. No statutory rates or legal conclusions are assumed by this scope document.

## Execution and acceptance boundaries

- Recommended sequence: shared revision/audit design; P1/P2; P3/P4; P5/P6; P7. Payroll remains a separate workstream after its scope is confirmed.
- Use one Terra coding owner at high reasoning and default speed initially; add a second worker only for a genuinely disjoint task. Use Luna high for bounded extraction/summaries. Current selected model owns contracts, coordination and focused security review.
- Fresh bounded prompts, AST-selected relevant symbols, concise handoffs and a dedicated Luna log/history summariser. Read lint rules before implementation and design cohesive files within their limits.
- Agents may write regression tests and migration files but do not execute tests, lint, typechecks, builds or migrations. The user runs supplied commands and shares output.
- No commits, deployments, live writes, new infrastructure provisioning, Dart or Flutter commands. Shell commands use RTK.
- Existing September 20 performance UI remains awaiting user validation; preserve those changes and clearly distinguish subsequent results.
- Coding completion, user validation and production acceptance are separate statuses. No production-ready claim before the required evidence exists.
