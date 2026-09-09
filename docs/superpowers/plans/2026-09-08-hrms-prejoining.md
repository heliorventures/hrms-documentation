# Link-based pre-joining implementation plan

> For agentic workers: use superpowers:subagent-driven-development. No commits.

**Goal:** Candidate form without login, configurable required fields/documents, HR corrections/review, and atomic employee/account conversion on Confirm joined.
**Architecture:** Employee service owns candidate staging and exact-permission HR GraphQL APIs. A separate bearer-invitation HTTP API exposes only one candidate form. Candidate secrets are carried in the URL fragment and HTTP Authorization, never normal employee JWTs. No employee/user rows exist before confirmation.
**Stack:** Rust, SeaORM, Axum, GraphQL, Liquibase, React/TypeScript.
**Spec:** ../specs/2026-09-08-hrms-enhancements.md, Phase3; latest user approved no-password private form.

## Global constraints

- Preserve existing dirty work in the current feature checkouts. No commits, deployment, migrations/live writes or Dart/Flutter. Existing implementation and scoped test/build approval applies.
- Admin-configurable invitation expiry defaults48 hours. Expiry disables candidate access, not HR review or stored submissions. Rotate/revoke old links on correction/reissue and after conversion.
- Required employee identity fields remain mandatory where the existing employee schema requires them. Admin chooses optional personal fields and document requirements from supported employee fields/document types; do not silently discard submitted fields at conversion.
- Dedicated prejoining:manage ALL and prejoining:review ALL permission checks server-side. Manage config/invitations; review reads/reviews/confirms candidate. Confirmation must also enforce existing employee/login role-assignment privilege rules, preventing escalation via the new path.
- Status DRAFT, SUBMITTED, CHANGES_REQUESTED, APPROVED, JOINED, CANCELLED. Submission and review changes carry expected revision; reject stale decisions. Confirm joined only APPROVED, idempotently returns existing employee on repeat.
- Config is snapshotted per invitation so later admin edits do not change a submitted form. Candidate editable only DRAFT/CHANGES_REQUESTED; no edits after submit except authorized reopening.
- Candidate private uploads enforce configured document requirement, safe PDF/JPEG/PNG, server MIME/signature and <=10MiB per document (technical initial limit matching existing document patterns; UI must disclose). Stored files have no public URLs. HR/candidate download rechecks current authorization. Conversion links actual employee documents/file storage, not just retained JSON.

## Shared contract

Backend publishes exact GraphQL SDL and public JSON contract in `../reviews/2026-09-08-prejoining-contract.md` before UI integration. Root validates actual SDL, not invented generated types.
Public page `/prejoining#token=SECRET`, API same origin `/prejoining-api/form`, Authorization Bearer SECRET. GET form returns configuration, answers, status, revision, feedback, document metadata. POST submit accepts `{revision,answers}`. PUT draft optional if supported by final contract. POST document upload raw bytes with requirement ID and safe encoded filename; delete and download routes scoped to invitation. No public candidate list, employee query or login.
HR APIs must cover config get/save, candidate paginated list/detail, invite(copy or system email), reissue, request changes, approve, cancel, confirm joined, and authorized document download. Return action errors that UI can recover from; no secrets in list/detail responses. Invite/reissue returns private URL only to authorized actor.
Confirm joined collects HR-only employeeCode/dateOfJoining/organization assignment and normal employee username/initialPassword/role choices through existing setup validation; never accepts candidate-assigned roles or status. New login forces password change, as current employee setup does.

## Task1: Backend and persistence

Owner backend agent: `hrms-svc/crates/kabipay-employee/**`, new `hrms-svc/crates/kabipay-db-entities/src/tenant/d0080_prejoining.rs`, new `hrms-database/changelog/migrations/0080_prejoining/**`, own contract/review docs. Root registers shared modules/master and deployment config.
- [x] Read employee creation/login/document paths; write exact contract and validation/state-machine failing tests.
- [x] Persist config, candidate snapshot/answers, immutable submitted revisions/reviews, invitation digest/expiry/revocation, private document staging, converted employee ID with tenant-qualified constraints.
- [x] Implement candidate routes with high-entropy signed/digested invitations, strict tenant resolution, no-store/nosniff/referrer headers, bounded bodies, no secret logging; reject expired/revoked/converted access.
- [x] Implement HR GraphQL gates before database access, revision/state checks, safe invitation generation, email delivery with explicit configured transport and truthful failure state.
- [x] Convert approved candidate in one locked transaction: validate HR fields/roles, create account+employee via transaction-compatible existing services, map every supported answer/document, audit actor, revoke invitation, commit once. Rollback all on conflicts.
- [x] Test authorization/state/expiry/revisions/conversion replay and failure rollback; run scoped employee tests/check, export real SDL and report limitations. No migration execution.

## Task2: Candidate form UI

Owner public UI agent: ONLY `hrms-ui/src/modules/prejoining/public/**` (including own client/types/tests). Root registers route and proxy.
- [x] Wait for backend contract before network integration; build responsive labelled field/document primitives from configuration.
- [x] Read fragment secret without storing it in localStorage, cookies or normal auth; API Authorization header with no referrer/caching. Never expose normal navigation.
- [x] Render form, submitted/review/approved states, specific correction feedback, upload progress/errors, expired/revoked state and submit receipt; protect against duplicate/stale requests/unmount.
- [x] Test anonymous route component, required validation, completed submission lock, correction editing, errors/expired access and stale invitation responses. Scoped lint/tests only.

## Task3: HR configuration/review UI

Owner HR UI agent: ONLY `hrms-ui/src/modules/prejoining/admin/**` (own GraphQL documents/types/tests). Root registers permissions/route/navigation/schema.
- [x] Use final backend contract, compact tabs Config/Candidates, per-action permission controls and tenant/session ownership keys.
- [x] Configure required fields/documents/expiry; create invitation and expose Copy link/Send email with truthful delivery result.
- [x] Paginated candidate rows with status, detail drawer/modal, staged answers/document access, revision-based request corrections/approve actions and explicit Confirm joined form using normal employee setup validations.
- [x] Test permissions, correction/approve/confirmation separation, stale ownership, duplicate submit, email failure and conversion success/error. Scoped tests/lint only.

## Task4: Root integration and review

- [x] Register0080 and entity module, public/HR routes and dedicated permissions/navigation; use schema from actual backend.
- [x] Add employee-service proxy path and explicit public invitation/email configuration docs without live changes.
- [x] Add candidate pipeline CSV for HR review ALL permission (complete dataset, safe escaping), integrated with the new workspace/export or reports.
- [x] Independent source review of tenant/token/document/role/conversion boundaries; fix material findings.
- [x] Actual SDL validation, focused UI regressions, Rust check/tests, TypeScript/lint/build; document live migration/email/provider/browser acceptance gaps.

## Ledger

Approval: user approved the specified no-password form workflow on2026-09-08. Existing current feature worktrees retained because the new workflow integrates the already approved uncommitted features. Candidate login choice is resolved; no new approval gate required. No actual invitations/emails are sent during development.
