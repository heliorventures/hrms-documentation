# HRMS remaining work — continuation handoff

Prepared: 8 September 2026. Workspace: `D:\work\heliorventures`.

## Read this first tomorrow

The original enhancements largely have source implementations. Most remaining work is release validation and deployment preparation. Comp-off decision D1 was resolved by the user and recorded on 10 September 2026 below. The pasted reviewer report predates several changes: do not restart unpaid leave, comp-off, video, reports or pre-joining from scratch.

This handoff was checked against current source and the verification records from today's work. No new tests, builds, migrations, live requests, emails or deployment were run for this documentation review. Earlier passing results are identified as recorded evidence, not freshly rerun results. The broader product-depth list was checked at entry-point level; it is not a full audit of every workflow.

The project's [completion rule](../hrms-documentation/docs/module-completion-status.md) requires role-specific browser journeys, real service/database integration, applied migrations and storage verification. These are still missing for the changed features, so **source implemented / QA pending** is the correct status. This does not establish that every existing module is broken or missing.

Preserve all uncommitted work across the separate repositories. Do not auto-commit, deploy, apply migrations, send emails or modify live tenant data. Do not run Dart/Flutter. Ask before new token-expensive work; existing approvals covered today's scoped implementation checks and builds. This document does not authorize implementation of every optional enhancement below.

## Recommended continuation order

1. Capture current Git status in each relevant repository and read the verification records linked below. Preserve unrelated concurrent changes.
2. Use resolved decision D1 below and verify its regression coverage. Do not introduce a leave approval-date restriction.
3. Address the confirmed module-entitlement gap as a separately scoped security implementation before claiming subscription enforcement.
4. Prepare a reviewed test-environment release: migration status, permissions, service/proxy configuration, storage and email adapter. Obtain the appropriate execution authorization before applying or sending anything.
5. Run the role-based acceptance journeys against the gateway, services and test tenant. Record screenshots, request results and database state transitions. Fix actual failures without rebuilding existing features.
6. Close the remaining lint/regression issues and update stale completion documentation with evidence.
7. Scope MFA, statutory payroll, automation/performance/survey closure and product-depth additions individually. Do not treat broad suggestions as approved implementation requirements.

## A. Original 13 requests

| Original item | Verified status | Remaining work |
|---|---|---|
| 1. Monthly average attendance hours | Implemented: backend full-month summary, completed segments only, stored workdate for overnight shifts; independent of pagination. | Test real multi-page months, open-only days, completed-plus-open segments, overnight September/October boundary and tenant timezone behavior. |
| 2. Reduce empty space | Compact attendance/timesheet/leave and priority form layouts implemented. | Signed-in desktop/tablet/mobile visual acceptance at 100% zoom; fix any observed overflow, excessive scrolling or inaccessible controls. |
| 3. Notification videos | External links and private in-app uploads/playback implemented, initial 50 MB limit. | Apply/configure media changes; test actual upload limits, permission/audience boundaries, seeking, download/playback failure and storage cleanup. |
| 4. Timesheet visibility | Compact controls and narrow-screen agenda implemented. | Employee/manager/HR browser testing, calendar visibility, submission/edit locks and keyboard/mobile behavior. |
| 5. Better popups | Shared modal sizing/footer behavior and priority forms updated. Pre-joining dialogs also split into focused components. | Inventory and visually review the remaining popups; the work has not established that every popup in the product is finished. |
| 6. Compact leave screen | Balances/history prioritized; reference sections collapsed. | Role, balance, request, cancellation and responsive acceptance against real data. |
| 7. Useful HR insights | Period-based punctuality, generated payroll, employee movements and pending-workload charts implemented. | Reconcile metrics to real records. Current chart actions open all period records; clicking an individual bar to apply that category/month is not implemented. Decide whether that richer interaction is required. Salary is labelled generated, not paid, because payment is external. |
| 8. Additional downloadable reports | Ten report choices plus separate pre-joining pipeline CSV implemented. Full server-filtered exports are independent of preview pagination. | Reconcile totals/permissions/filters; test large datasets and CSV escaping. Current export paths materialize data in memory: measure before claiming large-tenant scalability. Scheduled delivery/saved filters are future enhancements. |
| 9. Suggest missing/value-adding features | Priorities documented; this was a recommendation and gap-review request. | Optional implementation backlog appears in section E. A complete module-by-module product audit remains separate work. |
| 10. Candidate pre-joining | Private link without candidate login; configured fields/documents; staging, corrections, approval and atomic Confirm joined conversion implemented. | Migration0080, dedicated permission grants, invitation signing/origin configuration, email adapter and actual conversion/document/account browser journeys. |
| 11. Unpaid leave in payroll | Opt-in basic-pay/divisor configuration, company-selected treatment and closed-payroll protection implemented. | Validate approved unpaid leave, half days, cross-month dates, calculation snapshot and immutable closed cycle against actual tenant data. This does not remove statutory-processing gaps in section D. |
| 12. Comp-off requests/approval | Half/full-day requests for any worked date, manager/HR decisions, separate balance and policy precedence implemented. | Verify real permissions, duplicate approval prevention, caps, concurrency and leave-credit reservation/consumption. Manager determines worked-day eligibility; do not add a Saturday/Sunday restriction. |
| 13. Configurable comp-off expiry | Approval-date-based validity, limits and expiry-aware credit allocation implemented. D1 resolved below. | Verify expiry, delayed approval, cancellation, reserved credits and business-date boundaries in the running system. |

### D1 — resolved business decision (recorded 10 September 2026)

- [x] Credit enters the employee's comp-off bucket only when Manager/HR approves the worked-day claim. Validity starts on that approval business date, not the worked date or claim submission date.
- [x] Expiry is exclusive. Example: worked 14 September, requested 15 September, approved 20 September, with 30-day validity gives expiry 20 October; leave on 19 October qualifies and leave on 20 October does not. Validity remains configurable in days, not an assumed calendar month.
- [x] Leave using already-reserved eligible credit may be approved after its leave date and after credit expiry. Employee/Manager/HR manage timely requests and decisions; there is no additional approval-date restriction.
- [x] Selecting Comp-off reserves and consumes only comp-off credit. Missing configuration or insufficient credit must not fall back to normal leave balances.
- [x] Rejection/pending cancellation releases the reservation with its original expiry. Release after expiry does not make the credit spendable again. Existing restrictions for cancellation of already-approved leave remain unchanged.

The inspected reservation/final-approval paths already follow this decision. See the [10 September continuation record](superpowers/reviews/2026-09-10-compoff-release-security.md) for new regression evidence and the scoped entitlement audit. Runtime acceptance remains pending.

## B. Reconciliation of the other reviewer's findings

| Reviewer claim | Current verdict and evidence | What belongs in the remaining backlog |
|---|---|---|
| No module can be marked fully complete | Missing release evidence supports withholding Complete for these changed flows. It is not proof that every existing module lacks implementation. See the project's completion rule. | Capture runtime evidence per module. |
| Phase1 core exists; lint/route/browser work remains | Partly current. [Phase1 verification](superpowers/reviews/2026-09-08-phase1-verification.md) records later UI checks than the pasted 28-test snapshot. Later route/navigation/export checks passed with a 30-second timeout. | Browser acceptance and lint closure remain. Default full-suite timing stability is not established by scoped timeout-adjusted passes. |
| Birthday/anniversary notifications fail compilation with six missing symbols and need all layers built | The reported missing-symbol state is superseded by today's recorded 39 passing notification tests and successful notification/outbox Cargo check. [Settings](../hrms-svc/crates/kabipay-notification/src/services/automation_settings.rs), [generation](../hrms-svc/crates/kabipay-notification/src/services/automated_events.rs), worker calls, Admin settings and employee consent UI now exist. | Validate migration0074, configuration/consent, recipient selection, tenant-local scheduling, retries and duplicate prevention in the running worker. Do not recreate existing layers. |
| Subscription/feature-flag enforcement | The former unused pass-through has been removed. Approved shared GraphQL, capability-route, report and worker enforcement is now present locally; verification is recorded in the [10 September entitlement record](superpowers/reviews/2026-09-10-module-entitlements.md). | Complete authorized runtime acceptance. Local source/tests do not prove deployed subscription enforcement. See D2 below. |
| Unpaid leave and comp-off are essentially missing | Outdated. Services, policies, ledgers, UI, reports and migrations0077/0078 exist. [Phase2 final notes](superpowers/reviews/2026-09-08-phase2-payroll.md). | Runtime QA using resolved D1 and deployment. |
| Reports use capped client lists; insights are only succession catalogues | Outdated for the new HR report/insight paths. [Phase4 verification](superpowers/reviews/2026-09-08-phase4-ui.md), [report service](../hrms-svc/crates/kabipay-analytics/src/services/hr_reports.rs), and [insights page](../hrms-ui/src/modules/insights/AnalyticsPage.tsx). | Live data reconciliation, export scaling and optional saved/scheduled reports. Do not assume every legacy export elsewhere was audited. |
| Video and pre-joining are absent; attachment limits prevent them | Outdated. Video has a dedicated media path; the older generic attachment limit does not describe it. Pre-joining has a separate private document/form path. | Runtime/storage/proxy/email acceptance, migrations0079/0080. See [video review](superpowers/reviews/2026-09-08-phase3-video-ui.md) and [pre-joining review](superpowers/reviews/2026-09-08-prejoining-ui.md). |
| Appraisals/surveys only have designs; no lifecycle/subgraph | Outdated as an absence claim. Lifecycle services, review mutations, worker integration, migrations0075/0076, UI and survey subgraph now exist. Gateway source includes survey registration/contracts. | Completion against their original specs remains to be verified. Audit actual operation contracts and role/privacy behavior, then runtime test; do not infer lifecycle completeness from file existence. |
| MFA returns501; self-service reset absent | Confirmed. [Auth handlers](../hrms-svc/crates/kabipay-auth/src/handlers.rs) still call not_implemented for both MFA endpoints. [ForgotPasswordPage](../hrms-ui/src/modules/auth/ForgotPasswordPage.tsx) gives HR/admin reset guidance; it is not a self-service reset-token flow. | MFA implementation; product decision and separate implementation for self-service recovery. Keep working admin reset/change-password behavior. |
| Statutory payroll is simplified | Confirmed source limitation: [statutory_india](../hrms-svc/crates/kabipay-payroll/src/services/statutory_india.rs) and [payroll service](../hrms-svc/crates/kabipay-payroll/src/services/payroll_service.rs) retain explicitly labelled simplified/stub calculations and export paths. | Specialist-validated rules, effective dating, calculation fixtures and filing/export acceptance. This review checked source limitations, not current law or legal compliance. |
| Broad HR modules are mostly catalogues | Partially supported, but the list is too broad to accept wholesale. Recruitment exposes job-posting setup, compensation exposes cycles/bands, learning setup exposes skills/courses. Benefits already has enrollment; grievances already have submission; performance now has a lifecycle. | Audit missing transitions and role journeys before specifying additions. Keep the concrete review checklist in section E; do not label every workflow absent. |

## C. Release and QA work still pending

- [ ] Prepare and review tenant migration status for0074–0080. These files are included in the master changelog; they were not applied during this work. Do not blindly rerun against a tenant without inspecting its changelog state.
- [ ] Confirm required service startup/deployment configuration and gateway composition. Validate operations against the running schema; offline SDL validation does not prove live routing.
- [ ] Grant dedicated permissions intentionally. In particular,0080 creates pre-joining permission catalog entries, not automatic role grants.
- [ ] Configure private video storage/proxy and pre-joining origin/signing key. Pre-joining documents are private tenant-database bytes (10 MiB per document; separate from the 50 MB video limit).
- [ ] Configure the trusted HTTPS email delivery adapter for system invitations; verify recipient receipt and copy-link recovery. Adapter acceptance alone is not inbox-delivery proof.
- [ ] Run Employee, Manager, HR/Admin and unauthorized-user journeys; include cross-tenant and expired/revoked link/document attempts.
- [ ] Run desktop/tablet/mobile checks at100% zoom: actual records visible, controls reachable, no horizontal clipping, usable touch targets, modal focus/keyboard/validation and busy-state behavior.
- [ ] Exercise real transaction/race behavior: duplicate comp-off approvals, competing credit consumption, payroll closure, pre-joining conversion replay and failure rollback.
- [ ] Validate notification and performance workers against tenant business dates; retry a run to prove idempotency.
- [ ] Close existing UI lint debt. The final new pre-joining/route/navigation scoped lint passed; whole-repository lint is not clean. Shared permission-service complexity/function-size/loose-null findings and older Phase1 findings remain to be assessed and fixed.
- [ ] Establish a stable default regression gate and durable browser E2E coverage. Do not rerun every passing check solely because the old reviewer said all code was moving; select checks according to changes since their last verified state.

The browser tool failed during bootstrap with unavailable kernel assets. No successful browser connection, screenshots or signed-in acceptance were obtained. Restore that environment or use an approved working browser-test setup.

For pre-joining's exact operational checklist, use [runtime acceptance](superpowers/reviews/2026-09-08-prejoining-runtime-acceptance.md) and [user workflow](superpowers/reviews/2026-09-08-prejoining-user-workflow.md).

## D. Confirmed additional implementation gaps

These are broader than the original13 enhancements. Scope each before implementation.

### D2 — server-side module entitlements — high priority

- [x] Scoped implementation approved; active core modules need no separate subscription and existing role permissions remain required. The [implementation plan](superpowers/plans/2026-09-10-module-entitlements.md) records subscription dates, deny-flag precedence, dependencies and queued-work handling.
- [x] Shared evaluator and actual shared/custom GraphQL, capability HTTP, report and worker call sites implemented locally. The unused placeholder is removed; no long-lived entitlement cache is introduced.
- [x] Local verification: offline workspace compile and 29 focused common/ops/analytics/media/worker tests passed; independent source review found no blocking defect. See the [verification record](superpowers/reviews/2026-09-10-module-entitlements.md) for warnings and coverage limits.
- [ ] Authorized runtime acceptance of fail-closed access, revoked/expired subscriptions, tenant isolation, permission-plus-entitlement behavior, queued work and subscription transaction races. Do not treat local implementation as release closure.

### D3 — MFA and recovery

- [ ] Implement enrollment, challenge, verification, recovery-code lifecycle and appropriate rate limiting/audit behavior for the required account planes.
- [ ] Decide whether employee self-service password reset is required; if yes, implement a secure expiring, single-use reset workflow and delivery path.
- [ ] Keep admin reset and forced password change working; existing endpoints and guidance must not be mistaken for the missing self-service feature.

### D4 — statutory payroll production scope

- [ ] Agree applicable jurisdictions, supported rules, effective dates and filing/export requirements with a payroll specialist.
- [ ] Trace and replace the active simplified calculations/exports required by that scope; the separate unpaid-leave implementation is already present.
- [ ] Validate representative payroll results and external filing formats against approved reference cases before making compliance claims.

### D5 — automation, appraisals and anonymous-survey closure

- [x] Source comparison against the [automation plan](../hrms-documentation/docs/superpowers/plans/2026-09-08-automated-employee-notifications.md), [appraisal plan](../hrms-documentation/docs/superpowers/plans/2026-09-08-performance-feedback-appraisal.md), and [survey plan](../hrms-documentation/docs/superpowers/plans/2026-09-08-anonymous-surveys.md) recorded in the [10 September D5 gap review](superpowers/reviews/2026-09-10-d5-gap-review.md). This comparison does not close implementation or runtime acceptance.
- [ ] Verify actual schema operations, service deployment, migration state, scheduled generation and role-specific UI transitions.
- [ ] Preserve employee opt-in for company-wide celebrations and tenant enablement; test private delivery when consent is absent.
- [ ] Verify survey minimum-response suppression and department/team visibility; results must not identify respondents.
- [x] Concrete missing transitions and defects are listed in the [D5 gap review](superpowers/reviews/2026-09-10-d5-gap-review.md), including survey storage timestamp linkage, missing publication cohort snapshots, performance locking/acknowledgement issues and larger missing workflows. These broader modules are not fully complete.
- Current user boundary: no MFA/login/password-recovery work. Tenant/release validation is user-owned; local corrections do not authorize live actions.

### D6 — reusable queued email delivery service

- [ ] After the existing release/security issues are complete, design a standalone email-delivery service that can be reused by HRMS and other applications. Do not treat the current pre-joining HTTPS adapter as the final architecture.
- [ ] Define a durable broker contract in which producers enqueue a complete, immutable email job containing everything required for delivery: message/tenant/application IDs, recipients, reply-to, rendered subject, text and HTML bodies, approved attachment content or a deliberately designed broker-safe representation, selected provider profile, priority, timestamps and correlation/idempotency data. The delivery worker must not query an application database or call a producing application to complete a job.
- [ ] Keep SMTP/API/OAuth provider credentials out of queue messages. Store and rotate credentials only in the email service's secret configuration, and resolve the job's non-secret provider-profile identifier to SMTP or another supported provider adapter.
- [ ] Specify delivery semantics before implementation: transactional producer outbox or equivalent no-loss publication, schema versioning, idempotent consumption, bounded exponential retries with jitter, retry classification, visibility/lease recovery, dead-letter handling, duplicate-risk controls and explicit terminal outcomes.
- [ ] Publish delivery-status events containing safe identifiers and provider response metadata so applications can build their own status projections without the email service reading their databases. Define retention, replay, redaction and reconciliation procedures.
- [ ] Include security and operational controls: tenant isolation, producer authentication/authorization, queue encryption and ACLs, recipient/header validation, injection prevention, attachment/type/size limits, log redaction, rate limits, provider failover policy, health/readiness checks, metrics, tracing, alerting and auditable credential rotation.
- [ ] Compare broker and deployment options against the existing HRMS outbox/worker infrastructure, then produce an approved architecture specification, threat model, message schemas, provider interface, rollout/migration plan and end-to-end acceptance criteria before coding.

## E. Product improvements and deeper audits — not yet approved as a full build

| Candidate work | Known starting point | Next step |
|---|---|---|
| Follow-up queue, reminders and escalation | Pending-request report now exists. | Define owners, aging, deadlines, escalation and duplicate-send prevention. |
| Payroll readiness checklist | Payroll generation and unpaid-leave calculation exist. | Check unresolved punches/leave, missing salary setup and exceptions before cycle closure. |
| Document renewals | Existing document submission/review/download workflow. | Add configurable expiry reminders and expiring-document report if required. |
| Consolidated exit clearance | Separation/offboarding services already exist. | Bring assets, handover and outstanding tasks into a coordinated view. |
| Saved report filters/scheduled delivery | Current full CSV exports and permission checks. | Measure scale first, then design secure delivery and recipient authorization. |
| Shift/roster/swap management | Shift/roster entities and attendance shift settings exist. | Trace published rosters, assignment changes and swap approvals; identify actual UI/service gaps. |
| Custom fields and employee CSV import | Custom-field entities and client-specific import/seed scripts exist. | Verify reusable admin UI, validation, generic import preview/error handling and supported scope. Do not equate a seed script with a product import flow. |
| Recruitment pipeline | Job-posting setup is implemented. | Trace applications, stage transitions, interviews/offers and candidate conversion before defining missing work. |
| LMS enrollment/progress | Skill/course setup is implemented. | Trace enrollment, completion/progress and employee/manager journeys. |
| Compensation decisions | Review cycles and salary bands are implemented. | Trace individual proposals, approvals and payroll-effective changes. |
| Benefits lifecycle | Plan setup and an enrollment mutation exist. | Verify approval/change/termination journeys and employee UI; do not rebuild enrollment without checking it. |
| Grievance resolution | Case submission exists. | Verify assignment, investigation, confidential access, resolution and closure. |

## F. Documentation corrections

- [ ] Reconcile [FEATURES.md](../hrms-ui/FEATURES.md) with current source. Its missing attendance adjustment, leave cancellation and obsolete expense-form descriptions are stale.
- [ ] Update the [completion register](../hrms-documentation/docs/module-completion-status.md) with evidence-based statuses. Receipt upload exists, so it is not a reason by itself to keep Expenses/Travel In progress. Confirm remaining role paths before moving the entire module to QA.
- [ ] Preserve the distinction between Implemented, QA and runtime Complete. Do not check all acceptance boxes merely because code compiles.
- [ ] Reconcile older progress prose/unchecked plan lists with later final verification entries. The older value-priorities document still says pre-joining is outstanding; this handoff and the final pre-joining ledger supersede that statement.

## G. Recorded verification available for tomorrow

These are results from earlier work in this conversation, not reruns performed for this handoff.

| Area | Latest relevant recorded evidence |
|---|---|
| Attendance/Phase1 | Attendance70 tests; later scoped UI coverage recorded in [Phase1 verification](superpowers/reviews/2026-09-08-phase1-verification.md). Browser/lint limits remain explicit. |
| Payroll/comp-off | Payroll41 and leave46 tests, additional focused regressions, actual-SDL validation and UI build; [Phase2 final notes](superpowers/reviews/2026-09-08-phase2-payroll.md). |
| Notification video | Notification39 tests; notification/outbox check; Admin16 tests and root video tests; [video review](superpowers/reviews/2026-09-08-phase3-video-ui.md). The old six-missing-symbol compile failure is superseded. |
| Reports/insights | Analytics13 tests and check, UI/permission53 plus focused integration checks; [report review](superpowers/reviews/2026-09-08-phase4-ui.md). |
| Pre-joining | Employee59 passed/2 existing S3-environment tests ignored; final focused17; candidate16 plus2 recovery checks; Admin10; root route/navigation/export40; permission52;13 operations validated against actual SDL. [Final ledger](superpowers/reviews/2026-09-08-prejoining-progress.md). |
| Final assembled UI | TypeScript, scoped pre-joining/route/navigation lint and production build passed. Existing Browserslist-age/large shared-chunk warnings remain; whole-repo lint was not claimed clean. |
| Gateway/database older counts in pasted review | Historical evidence only. They are not a newly executed full-system gate for the final checkout. |

## Suggested first message tomorrow

> Read `docs/HRMS-REMAINING-WORK-2026-09-08.md` and the linked final verification records. Preserve all existing uncommitted work. Start with the open comp-off policy decision and the release/security priorities; do not rebuild already implemented features. Before expensive work, tell me the exact scope and obtain approval where required. Do not commit, deploy, run migrations, send emails or modify live tenant data without authorization.
