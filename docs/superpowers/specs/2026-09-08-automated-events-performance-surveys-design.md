# Automated Employee Events, Performance, Appraisal, and Surveys Design

## Status and Delivery Boundary

This design covers three coordinated but independently deployable capabilities:

1. automatic birthday and work-anniversary notifications;
2. recurring performance, feedback, and appraisal cycles; and
3. anonymous employee surveys with aggregate reporting.

The work spans `hrms-database`, `hrms-svc`, `hrms-gateway`, `hrms-ui`, and
`hrms-documentation`. Each repository remains independently versioned. Database migrations are
forward-only and are not applied automatically. Deployment, live tenant writes, commits, and
remote operations require separate user action.

The existing notification, tenant business clock, employee hierarchy, performance service, and
RBAC patterns are extended. Existing unrelated worktree changes are not modified.

## Product Decisions

- Automatic notifications are in-app notifications in the first release. Email, SMS, Slack, and
  Teams delivery are outside this design.
- A birthday or anniversary may be shared company-wide only after that employee opts in. Without
  opt-in, reminders are private to the employee and their current reporting manager.
- Birthday messages never expose birth year or age.
- The tenant business timezone determines event dates, cycle transitions, and survey schedules.
- Performance feedback and appraisal share one lifecycle and one participant record. Continuous
  feedback remains a distinct record and never changes a rating automatically.
- Managers may evaluate only authorized subordinates. A reporting relationship is snapshotted when
  a participant enters a cycle so a mid-cycle manager change does not silently transfer a submitted
  appraisal.
- Survey analytics are aggregate-only. No GraphQL operation exposes a respondent identity or a raw
  response to Admin, HR, managers, or department viewers.
- A survey aggregate or comment set is returned only when at least five submitted responses are in
  the authorized cohort.
- Published questionnaire and survey versions are immutable. Corrections create a new version.

## Alternatives Considered

### Recommended: module-owned domains with a shared durable scheduler

Performance remains in `kabipay-performance`, notifications remain in
`kabipay-notification`, and surveys use a new `kabipay-survey` subgraph. The existing outbox worker
hosts the tenant-aware scheduling loop but calls domain-owned library functions. Each domain owns
its state transitions and idempotency constraints.

This preserves clear authorization boundaries, reuses deployed worker infrastructure, and avoids
putting business logic in the gateway or UI.

### One combined employee-engagement service

A single new service could own celebrations, performance, and surveys. This reduces the number of
processes but couples unrelated privacy, workflow, and retention rules. A survey defect could affect
appraisals, and performance changes would require redeploying celebration processing. This option
is rejected.

### Database cron jobs, functions, or triggers

The database could generate scheduled events and transition cycles. This would hide business logic
from application tests, complicate tenant-timezone behavior, and make retries and notification
delivery harder to observe. This option is rejected. Database constraints enforce integrity, while
Rust services own business state transitions.

## Shared Scheduling and Idempotency

The existing outbox worker already resolves active tenants, loads each tenant's business clock, and
performs retryable sweeps. It will call three new domain jobs after resolving a tenant database:

- due employee celebration generation;
- due performance-cycle creation and stage transitions; and
- due survey opening and closing.

The worker supplies the tenant ID and current tenant-local date/time. Domain jobs do not read the
host machine timezone. Each job is safe to run repeatedly and concurrently.

Every generated occurrence has a database uniqueness boundary. A transaction claims or inserts the
occurrence and creates its resulting records atomically. A worker restart, duplicate poll, or second
worker instance therefore cannot create duplicate notifications, cycles, assignments, or stage
transitions. Failed jobs retain structured error context and are retried without weakening the
uniqueness constraint.

The existing webhook outbox remains a delivery mechanism and is not used as the source of truth for
scheduled business state.

## Automatic Birthday and Work-Anniversary Notifications

### Configuration and consent

Tenant notification automation settings contain:

- birthday enabled;
- work anniversary enabled;
- local delivery time;
- private birthday and anniversary templates;
- company birthday and anniversary templates; and
- company-sharing availability.

Templates support only a controlled placeholder set: employee display name and completed service
years for anniversaries. Birthday age and birth year are not supported placeholders.

Each employee has independent `share_birthday` and `share_work_anniversary` consent flags. Both
default to false. Employees may update only their own flags. Admin/HR may view whether consent is
present for operational support but may not enable company sharing on an employee's behalf.

Automation settings require `notification:manage=ALL`. Reading and changing one's own celebration
consent requires the existing `notification:read` permission; the mutation always resolves the
employee from the signed-in user and does not accept an employee ID, so a wider read scope cannot
broaden the write. Company-recipient selection uses the existing notification-read authorization
contract and never grants notification access by itself.

### Eligibility and audience

Only active employees with an associated active user are eligible. Birthdays require a date of
birth. Anniversaries require a joining date in a prior year and therefore begin after one completed
year.

On ordinary dates, month and day must match the tenant-local date. A 29 February birthday is
observed on 28 February in non-leap years. The occurrence stores the actual observation date so the
rule remains auditable.

Without company-sharing consent, recipients are the employee and current reporting manager, when
that manager has an active user. With consent and tenant company sharing enabled, every active user
with notification read access receives the company message. The occurrence ledger is unique per
event, employee, observation date, and recipient.

Notification types `EMPLOYEE_BIRTHDAY` and `EMPLOYEE_WORK_ANNIVERSARY` map to a new `celebration`
preference topic. Users may mute that topic without hiding leave, expense, travel, tax, or direct HR
notifications.

### Administration and employee UI

Admin/HR receives a compact automation-settings panel under Notifications. Employees receive two
clear consent controls in notification preferences. No public calendar exposes dates of birth.

## Performance, Feedback, and Appraisal Domain

### Reusable program and generated cycles

A `performance_program` is the reusable Admin/HR configuration. It defines:

- name and optional description;
- cadence: monthly, quarterly, yearly, or manual;
- anchor date and tenant-local schedule;
- participant population rules: all active employees, selected departments, selected work
  locations, or an explicit employee set;
- stage sequence and deadlines;
- rating scale;
- goal policy and total required weight; and
- the current published appraisal-template version.

Programs move through `DRAFT`, `ACTIVE`, and `ARCHIVED`. Activating a scheduled program makes it
eligible for automatic cycle creation. A uniqueness constraint on program and period prevents a
second cycle for the same period.

The existing `review_cycle` table remains the cycle-instance authority and gains a program
reference, period key, lifecycle state, and schedule metadata. Existing draft rows remain valid
manual cycles and can be migrated without fabricating a program.

### Appraisal template

An appraisal template contains ordered sections and questions. A question may have one optional
parent question within the same section, allowing one level of subquestion nesting. Supported
question types are:

- single-choice MCQ;
- multiple-choice MCQ;
- rating;
- short text; and
- long text.

Each question declares whether it is required, who answers it (`EMPLOYEE`, `MANAGER`, or `BOTH`),
and whether self-rating and manager-rating fields are enabled. Options have stable IDs and display
order. Publishing creates an immutable template version. Cycle participants reference the published
version so later template edits cannot alter an in-progress or closed appraisal.

### Participants, goals, and manager ownership

When a cycle launches, it creates one participant record per eligible employee and snapshots the
employee's manager, department, designation, and work location. Terminated employees are excluded.
Admin/HR can explicitly exclude a participant before self-review begins and must record a reason.

Goals remain employee- and cycle-specific. Admin/HR or the participant's authorized manager may
create and edit goals during `GOAL_SETTING`. An employee may propose a goal, but a manager must
approve it before self-review. Goal weights must be non-negative and total exactly 100 before the
participant can enter self-review. KPIs remain children of goals and contain target, unit, actual
value, and evidence/comment fields.

### Lifecycle

The default sequence is:

1. `GOAL_SETTING`
2. `SELF_REVIEW`
3. `MANAGER_REVIEW`
4. `HR_CALIBRATION` when enabled
5. `EMPLOYEE_ACKNOWLEDGEMENT`
6. `CLOSED`

Admin may omit calibration or acknowledgement when configuring the program. Stage transitions are
validated in Rust and use row locks to prevent double submission. Scheduled transitions run only
when prerequisite checks pass. If a prerequisite fails, the cycle remains in its current stage and
the system records an actionable administration exception rather than discarding responses.

Employee submission validates all required questions and self-ratings, then locks employee answers.
The snapshotted manager can see those answers only after submission. Manager submission validates
manager questions and ratings, then locks manager answers. HR calibration can set the final rating
and performance band without rewriting the employee or manager submissions. Employee
acknowledgement records acknowledgement and an optional comment; it does not mean agreement.

Closed-cycle submissions are immutable. Reopening requires `performance:manage=ALL`, a reason, an
audit entry, and creation of a new response revision while retaining the prior revision.

### Continuous feedback

Feedback is stored separately from appraisal answers. The first release supports manager-to-direct-
report feedback and Admin/HR-entered feedback. Feedback may reference a cycle or goal, includes an
observation date and comments, and has an explicit visibility of employee-visible or HR-only.

Feedback appears as evidence to an authorized manager during evaluation, but no aggregation or
formula silently converts it into a manager or final rating.

### Performance authorization

The canonical permissions are:

| Permission | Scope | Authority |
| --- | --- | --- |
| `performance:manage` | `ALL` | Programs, templates, cycles, calibration, exceptions, and organization status |
| `performance:evaluate` | `TEAM` | Goals, feedback, and evaluations for snapshotted authorized subordinates |
| `performance:self` | `SELF` | Own goals, self-review, own submitted/final results, and acknowledgement |

Rust is the authority. Manager access requires both `performance:evaluate=TEAM` and a matching
snapshotted manager relationship. Role names never grant access. Tenant-wide goal queries are
replaced with scoped participant and goal queries so a manager cannot enumerate another manager's
team.

### Performance UI

The current Performance page becomes permission-composed:

- Admin/HR: Programs, Templates, Cycles, Calibration, and Exceptions.
- Manager: My Team Reviews, Goal Setting, Feedback, and Submitted Evaluations.
- Employee: My Goals, Self Review, Results, and Acknowledgements.

Pages remain compact and action-oriented. Each role loads only authorized operations. A denied route
does not issue its GraphQL request. Autosave is not used for final submissions; explicit submission
shows a confirmation and validation summary.

## Anonymous Survey Domain

### Survey configuration and lifecycle

A new `kabipay-survey` subgraph runs on port `4030`. Admin/HR can create a draft survey with:

- title and optional description;
- open and close times in the tenant timezone;
- target population by all employees, department, work location, or explicit employee set;
- ordered sections and questions; and
- an anonymous-results notice shown before submission.

Question types are single-choice, multiple-choice, rating, short text, and long text. Survey
definitions are versioned. Publishing freezes the version and participant population. Scheduled
surveys open and close through the shared worker. Manual open and close operations use the same
state-transition service.

### Anonymous storage

Eligibility and duplicate prevention are separated from answers:

- `survey_participant` records eligibility and whether a submission receipt exists;
- `survey_submission_receipt` records that the employee submitted; and
- `survey_response` and `survey_answer` store answers without employee ID or user ID.

The receipt and anonymous response are created in one transaction. Application queries cannot join
responses back to employees because the response has no participant foreign key. Responses store
only `department_id`, `work_location_id`, and `reporting_manager_id` as approved reporting
dimensions snapshotted at survey publication. They do not store employee code, designation, name,
email, user ID, or employee ID. Exact submission timestamps are not returned by analytics APIs.

The employee sees whether they have submitted but cannot retrieve or edit an anonymous response
after submission. Server-side draft saving is excluded because it would require a durable identity
link to unsubmitted answers.

### Aggregate analytics and comments

Analytics resolvers accept only server-defined dimensions and validate the caller's scope. They
return response counts, score distributions, averages, and approved comments only when the selected
authorized cohort has at least five responses. The threshold is applied after every permission and
dimension filter, including comments and answer options.

Comments are returned without author, employee metadata, or exact timestamp and in nondeterministic
display order. Employees are warned not to include identifying personal information. The first
release does not provide raw response export or arbitrary filter combinations because either could
defeat anonymity.

### Survey authorization

| Permission | Scope | Authority |
| --- | --- | --- |
| `survey:manage` | `ALL` | Draft, publish, schedule, close, and organization-level aggregate status |
| `survey:respond` | `SELF` | View assigned surveys and submit one anonymous response |
| `survey:analytics` | `TEAM` | Aggregates for authorized team snapshots only |
| `survey:analytics` | `DEPARTMENT` | Aggregates for the viewer's authorized department only |
| `survey:analytics` | `ALL` | Tenant-wide and permitted dimension aggregates |

Backend scope filtering occurs before threshold calculation. UI controls never substitute for this
enforcement.

Admin/HR manages surveys under Workplace > Surveys. Employees receive an Assigned Surveys page.
Managers and department viewers receive only aggregate dashboards authorized by
`survey:analytics`; no UI route or hidden operation can enumerate individual submissions.

## Database Migrations

Three forward-only tenant migrations follow the currently included `0073` migration:

- `0074_automated_employee_notifications`: automation settings, employee consent, occurrence
  ledger, notification source integrity, and preference topic support. It verifies the existing
  `notification:read` and `notification:manage` RBAC prerequisites without reassigning roles or
  revoking sessions because Phase 1 introduces no new permission.
- `0075_performance_appraisal_lifecycle`: performance programs, stages, template versions,
  participant snapshots, answers, response revisions, feedback visibility, lifecycle constraints,
  scoped permissions, indexes, compatibility upgrades for the existing `review_cycle`, `goal`,
  `kpi`, `feedback_response`, and `performance_rating` tables, bootstrap parity, and session
  revocation.
- `0076_anonymous_surveys`: survey/version/question/audience/participant/receipt/anonymous-response
  tables, uniqueness and anonymity constraints, scoped permissions, bootstrap parity, and session
  revocation.

Migration contract scripts verify exact permission/scope assignments and reject accidental manager
`ALL` grants. Existing applied migrations are not edited. Migration application remains dry-run
first and explicitly user-controlled.

## GraphQL and Gateway Contract

`kabipay-performance` exposes role-specific operations for programs, templates, participants,
goals, feedback, submissions, calibration, acknowledgement, and status summaries. Each resolver
uses the exact permission and scope before database access.

`kabipay-notification` exposes automation settings and employee-owned consent. Scheduled generation
is an internal library entry point, not a public mutation that an HR user must trigger.

`kabipay-survey` exposes management, self-response, and aggregate-only analytics operations. It does
not expose a raw response list or respondent lookup.

The gateway registers the survey subgraph on port `4030` and adds required-field contract checks for
all UI-critical operations. Production remains fail-closed when a required updated subgraph is
missing or schema-incomplete. Authenticated tenant and request headers continue through the existing
gateway forwarding boundary.

GraphQL client output is regenerated only after authored operations and schemas are updated. Source
`.graphql` files remain authoritative; generated files are not edited manually.

## Audit, Errors, and Observability

Audited actions include configuration changes, consent changes, program publication, cycle launch,
stage transitions, exclusions, submissions, reopening, calibration, survey publication, manual
closure, and scheduler exceptions. Audit payloads do not copy survey answers or birth dates.

Expected validation failures return stable domain codes and field-specific messages. Authorization
denial is `FORBIDDEN`; missing records are tenant-scoped `NOT_FOUND`; concurrency conflicts return a
retry-safe conflict code. Scheduler logs include tenant, job type, business date, counts, and stable
record IDs but exclude answer text, feedback comments, dates of birth, and notification message
bodies.

An administration exception view surfaces cycles or surveys whose scheduled transition could not
complete. Retrying uses the same idempotent domain service.

## Test-First Verification

Implementation follows red-green-refactor and includes:

- migration contract tests for tables, foreign keys, uniqueness, anonymous-storage separation,
  exact permission bundles, bootstrap parity, and session revocation;
- Rust unit tests for event-date calculation, leap-day handling, consent audiences, notification
  idempotency, recurrence periods, state machines, goal weight totals, required responses, manager
  snapshots, immutable submissions, survey threshold enforcement, and denial before database access;
- disposable PostgreSQL integration tests for concurrent worker sweeps, duplicate submission,
  scoped manager access, reopening revisions, and aggregate anonymity;
- gateway tests for survey registration and required schema contracts;
- React tests for permission-composed navigation, protected request suppression, compact workflows,
  question rendering, submission validation, retained data after refresh errors, and aggregate-only
  survey dashboards; and
- signed-in browser acceptance for Admin/HR, Manager, and Employee after deployment.

No Dart or Flutter command is part of verification. Broad, expensive suites require explicit
approval before execution. Static tests and builds do not substitute for tenant migration,
deployment, worker, or browser proof.

## Phased Implementation and Deployment

Implementation is split so each capability can be reviewed independently:

1. automated notification migration, Rust generation, preferences/settings UI, and worker wiring;
2. performance/appraisal migration, Rust lifecycle, GraphQL operations, and role-specific UI;
3. survey migration, new subgraph and gateway contract, response UI, and aggregate dashboards.

For each phase, authored migrations and source code land together, focused tests run first, and the
repository diffs are reviewed before progressing. No phase requires the following phase to be
deployed, although all use the shared worker process and RBAC conventions.

Production rollout order is database preflight, tenant migration, service images, gateway, UI,
worker restart, session refresh, focused API checks, and role-by-role browser acceptance. Migration
and deployment commands remain unexecuted until separately authorized.

## Out of Scope

- Email, SMS, Slack, or Teams notification delivery.
- Public birthday calendars or display of age/birth year.
- Peer or 360-degree reviewer nomination in the first release.
- Automatic rating calculation from feedback sentiment or survey answers.
- Payroll or salary changes based on appraisal results.
- Raw survey-response export, per-respondent reporting, arbitrary analytics filters, or server-side
  anonymous-response drafts.
- Editing applied migrations, committing changes, applying tenant migrations, or deploying without
  explicit authorization.
