# SDD ledger — plan: 2026-10-19-organization-gap-closure.md

User approved closing the gaps identified by the recorded-architecture conformance review. This is a continuation of the approved feature, including focused validation/lower-model reviews; it does not authorize production changes or commits. Start 2026-10-19 02:45 UTC.

## Preflight

- Verified all five repositories remain on `feat/organization-cross-company-management`; prior implementation and unrelated loan changes remain dirty and must be preserved.
- Frozen exact earlier workspace requirements copy in `docs/superpowers/specs/2026-10-19-organization-recorded-baseline.html`, SHA256 AE0E0AA8DF303F62CE6CD85E840204E76C251B37F73265F65570792BDC2EF1E4. It contains earlier implementation annotations plus recorded proposal text; do not mislabel it pristine v5.
- Original requirements and user approval resolve the skill design gates. No repeat approval is needed for already authorized architecture/implementation. No automatic skill commits/worktree switches.
- Shared interfaces/ownership conflicts are ruled in the plan table. Root controls operation enum, central policy, shared transport and master migrations. Agents must coordinate those edits.
- Unknown business metrics/retention cannot be fabricated. Reuse actual source definitions; configurable policies default to preserving history and refusing destructive execution until accepted.

## Tasks

- [x] A: source employee/account/workflow/exit administration, including real login provisioning and current source discovery.
- [x] B: durable source payroll jobs and exact fresh execution policy.
- [x] C: independent consumers, source/CDC/all-role capture freshness, supported facts, genuine history export, encrypted archive and guarded cleanup/cutover workflows.
- [x] D: protected central APIs, authoritative generated clients and integrated application UI.
- [x] E: recorded-requirement conformance, two independent reviews with corrections closed, focused synthetic acceptance and documentation handoff.

## Final evidence

All identified engineering gaps are implemented. No finding remains open in the two scoped reviews. This is not production or browser acceptance.

| Area | Executed evidence |
| --- | --- |
| Source HR and workflow | Employee94passed/2existing S3ignored; Workflow5passed. Final real HTTP68271 passed employee create/edit/employment/login provisioning, initial-password non-retention, self/last-admin guards, workflow history, separation/clearance, exact replay/version checks and current-grant revocation. |
| Payroll |5focused unit tests;14authority mutation cases in1tenant helper test; actual PostgreSQL crash/claim/active-cycle/commit-time lease regression1passed. HTTP68271 passed ACCEPTED versus completion, cancellation, reviewed PayrollDetail, actual1000 gross/net payslip, source restart exactly once, stale fingerprint and revoked authority. |
| Central and tenant |Final organization/Tenant unit run80144:28+11passed,1+2explicit PG cases ignored by default; the organization reporting PostgreSQL case then ran separately24403 and passed. Protocol1passed. Existing special Tenant PG cases are not relabelled executed by these runs; full HTTP separately exercises lifecycle. |
| Separate-database integration |Final `node scripts/test-organization-execution.cjs`68271 exit0. Actual migration SQL, three separate PostgreSQL databases, real source Auth/central/source services, all HR/payroll/report/history/archive/revocation/lifecycle cases. Reporting capture/grants are explicit fixture seeds; this is not claimed as CDC capture proof. All owned fixture resources cleaned. |
| Events and capture |45Node tests passed; real PG/Kafka/ClickHouse/Debezium/Connect fixture passed independent sink outage/replay, exact heterogeneous envelopes, source-owned legacy export, all-partition barriers, retired/unavailable Connect historical acknowledgement, durable unknown quarantine, same-group resume epoch3/source bootstrap health and detached barriers. Separate PG recovery/timestamp and company/control cleanup fixtures passed. Only two proven synthetic outbox rows were deleted. |
| Reports and archives |Actual central HTTP plus real ClickHouse/AES sidecar passed exact/null attendance, whole-request leave, project time and ordinary time totals, curated administration history, encrypted export/retrieve, wrong archive, incomplete partition and revoked access. Actual query smoke passed all three supported views on ClickHouse25.8. Source archive/body/hash checks and source private legacy backup boundary remain explicit. |
| UI |Authoritative SDL/client generation, production TypeScript, scoped ESLint, caller audit and organization-enabled Vite build passed. Full suite28files/93tests; subsequent targeted payroll/login/API tests8passed and exit subject tests2passed. These overlapping counts are not summed as unique tests. |
| Compilation/lint |Affected Employee/Workflow/Payroll all-target `cargo check`33633 passed (existing dead-code/schema-example warnings). Five organization crates strict Clippy with `--no-deps --all-targets -- -D warnings`98645 passed. The first broader dependency-inclusive strict run was blocked by9existing common lint findings; it is not claimed clean. Existing proc-macro future incompatibility and UI chunk/Browserslist warnings remain. |
| Reviews |Dedicated GPT6.1sol evidence compression preceded two independent scoped reviews. G1 account lock order and G2 payroll detail contract were fixed and independently closed. R2-C1 historical coordinator replay and R2-C2 sticky historical checkpoint were fixed and independently closed, including the residual Connect ordering case. |
| Documentation |Canonical HTML v7 adds exact source workflows, independent-consumer diagram, payroll lifecycle, database migration/relationship map and history/cleanup boundaries. Structural DOM check passed unique IDs, internal anchors and SVG accessible labels; this is not visual/browser proof. Frozen baseline hash remains AE0E0AA8DF303F62CE6CD85E840204E76C251B37F73265F65570792BDC2EF1E4. |

## Recorded-requirement conformance

- Configurable organization/company membership and explicit company roles remain generic; no SBL/SCL behavior is hardcoded. One real employer-company session serves authorized shared HR, managers and owners.
- Company databases remain separate. Shared services have metadata/ClickHouse access and fixed source HTTP routes, without arbitrary tenant credentials, cross-database joins or caller-selected endpoints.
- Bidirectional cross-company reporting, company acceptance, current installed assignments, cycle checks and lifecycle behavior remain in the foundation and final HTTP acceptance.
- Local HR permissions remain local. Organization configuration, employee administration, account administration, workflows, onboarding, payroll, analytics and history are separately grantable.
- Manager discovery is event-fed, but the source validates and commits approvals/reviews/feedback. A broker ACK is never business completion.
- Payroll jobs are durable source business state; original command acceptance remains immutable, while the job reports its own current lifecycle. No login/delegation token is persisted.
- Kafka, retained ClickHouse business history and diagnostics are separate. Independent consumers prevent a failed history/reporting sink from blocking inbox updates. Current reports require source capture proof rather than worker uptime.
- Actual source attendance/leave/project-time facts are delivered. Unsupported productivity/task-completion metrics are not invented.
- Source historical exports are resumable and retain genuine provenance. Unknown legacy labels/history stay UNMAPPED/UNKNOWN; private original audit snapshots remain in the protected source backup boundary.
- Archives are encrypted/authenticated and scoped. Cleanup/cutover is implemented, disabled by default and evidence-gated. Minimal source receipts/jobs and transactional outboxes remain necessary; no business/audit/receipt table was dropped.

## Release acceptance still pending

- Live browser acceptance: **NOT DEMONSTRATED**. CUA had no surfaces; Chrome, Edge and IAB each returned unavailable. Earlier mocked screenshots do not prove the new screens.
- Existing-company Liquibase upgrade/rollback/restore on representative data; production migration/deployment.
- Target VPS/private TLS/mTLS, broker ACLs, separate runtime/CDC/consumer/archive/operator grants and key custody/rotation acceptance. Synthetic loopback credentials are never deployment configuration.
- Real source legacy backfill and exact historical range acceptance, independent consumer cutover, off-host archive/private-source backup restore, accepted production retention policy and any real deletion.

No automatic commits, push, deployment or existing-company mutation occurred. All repositories remain on the existing feature branch; unrelated loan work is preserved.

## Evidence references

- `2026-10-19-gap-central-progress.md`
- `2026-10-19-gap-hr-progress.md`
- `2026-10-19-gap-payroll-progress.md`
- `2026-10-19-gap-events-progress.md`
- `2026-10-19-gap-review-one.md`, `2026-10-19-gap-review-two.md`
- `hrms-ui/docs/organization-workspace.md`
