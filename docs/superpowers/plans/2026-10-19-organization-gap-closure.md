# Organization architecture gap closure implementation plan

> For agentic workers: use subagent-driven-development for owned subsystems and executing-plans for root integration. User explicitly authorized closing the audited gaps and focused validation. Do not repeat already completed foundation work.

**Goal:** deliver the missing recorded organization features and independent failure domains without narrowing the requirements to match existing code.

**Architecture:** retain separate company databases and fixed source services. Extend the explicit command allowlist and source-owned domain adapters; use durable source payroll jobs with fresh authorization; separate Kafka consumer groups/checkpoints; add source capture barriers, reporting facts and reconciled history/archive/cleanup workflows. Production deployment and destructive existing-data operations remain release gates.

**Tech stack:** existing Rust/Axum/SeaORM/GraphQL, React/TypeScript, PostgreSQL, Kafka/Debezium, ClickHouse, Node and OTel. Reuse locked dependencies where possible.

**Spec:** `docs/superpowers/specs/2026-10-19-organization-recorded-baseline.html`, frozen from the earlier workspace copy before gap closure, SHA256 `AE0E0AA8DF303F62CE6CD85E840204E76C251B37F73265F65570792BDC2EF1E4`. This is an exact captured requirements reference, not a claim of pristine original-v5 bytes. The conformance review and original user instructions resolve ambiguity; queued business decisions remain optional.

## Global constraints

- Existing feature branch in all five repos; preserve unrelated loan edits. No automatic commits, pushes, deployment or existing-company migrations.
- Native commands only; no RTK, Dart or Flutter. Focused tests/checks and lower-model implementation/review remain authorized by the user's continuation.
- Shared services never receive arbitrary source-company credentials. Endpoint/topic/key/storage roots are deployment-bound, never browser-selected.
- Company business grants are explicit; organization management is not payroll, account or employee administration authority. Foreign actors never become fake local users/employees.
- Source domain validation, tenant scope, expected version, live grants, transactional receipts and attribution remain mandatory, including job execution and archive/export reads.
- Do not delete business records, receipts or unconfirmed history. Implement bounded automated cleanup with verified coverage/restore/configuration gates, and execute only in disposable fixtures.
- Unknown/unreconciled data remains incomplete, not zero or invented historical transitions. Policy defaults retain history until explicitly configured/accepted.
- Final completion is per requirement with source and executed evidence, not all-checkbox rewriting of a prior plan.

## Review focus

1. A ClickHouse outage must not stall current inbox ingestion; independent consumer offsets and capture coverage must still prevent false complete reporting.
2. An HR/account/workflow grant cannot bypass the corresponding source domain restrictions, last-admin/self guards, inactive-account checks or sensitive-field restrictions.
3. A queued payroll job must survive restart, run once, recheck exact current authority, and refuse revoked grants before business commit.
4. Idle source health requires all expected partition barriers and source capture evidence, never worker uptime or one connector heartbeat.
5. Historical export, archive retrieval and cleanup must verify IDs/hashes/ranges and current access; wrong tenant, partial sink, expired lease or damaged archive must fail closed.

## Ownership and shared interfaces

Root owns `kabipay-organization-protocol`, organization service policy/APIs, shared tenant transport edits, Cargo workspace/lock coordination, migration master includes, UI integration, conformance HTML and final reviews. Agents send exact contract needs before shared edits. Scoped business service manifests may be changed by their owner using existing dependencies.

| Task | Produces / consumes | Shared-file ruling |
| --- | --- | --- |
| A: source HR administration | Typed Employee/account/workflow commands and source results; consumes private verified authorization | Root publishes operation/service/capability/resource mappings; owner does not edit central policy/protocol |
| B: durable payroll | Source-owned job state/worker and current-policy refresh; consumes original immutable command intent | Root owns central job authorization route and wire DTO; job owner owns Payroll and its SQL |
| C: independent events/report/history lifecycle | Independent worker modes/offsets, barrier/fact contracts, archive/reconciliation and cleanup executables | Root coordinates protocol/source emitter changes and central APIs; C owns Node/infrastructure and assigned migrations |
| D: central APIs/UI | Explicit admin grants, job status, richer report/history/export/archive UI | Root consumes A/B/C result contracts; no raw GraphQL/SQL proxy or caller URL |
| E: acceptance/review/docs | Conformance matrix with each remaining gate | Reviewers read bounded summaries/current files, not full repository/log dumps |

Migration reservations: source HR0118; source payroll jobs0119; ops consumer/capture/archive state0120; source expanded facts/barriers/backfill0121. Root integrates master streams. Add further numbered migrations only after checking current inventory.

### Task A: shared HR administration

Files: Employee adapter and new cohesive admin module; actual account-management owner and Workflow service adapter/startup; corresponding service tests; source0118. Root updates operation enum/policy/resource locks and UI after contract handshake.

- [ ] Trace existing employee creation/update/employment, account eligibility/roles and workflow-definition services. Return a compact operation table with exact existing capability and protected fields before editing shared contracts.
- [ ] Write failing tests for explicit ALL company grants, foreign/wrong-resource/readonly grants, invalid employment/account/workflow changes, last/self-admin restrictions, version conflict and exact replay.
- [ ] Implement specific typed source adapters that reuse domain validation/transactions and original principal attribution. No generic SQL/GraphQL forwarding, credential return or synthetic source user.
- [ ] Add source-owned versions/receipts for supported new resource kinds and future-safe creation identifiers. Existing same-company routes remain compatible.
- [ ] Verify focused source tests and actual separate-database HTTP cases for administration/revocation. Publish result payloads and a scoped ledger.

### Task B: durable source payroll jobs

Files: `kabipay-payroll/src/organization_jobs.rs` and small worker/state modules, Payroll startup and adapter; source0119. Root supplies a private source-service-authenticated authorization refresh endpoint using exact immutable central intent and original body hash.

- [ ] Write failing tests: accepted is not completed; same command creates one job; restart/lease recovery; revoked/replaced grant; stale fingerprint; crash before/after source commit; no cross-company job read.
- [ ] Queue draft/finalization in the same source transaction as the command acceptance receipt. Store bounded business job input/actor/reference, not reusable login/delegation tokens.
- [ ] Worker claims a bounded lease, refreshes current source-account/principal/membership/grant authority, validates it cryptographically, then holds current local fences through existing payroll business transaction and terminal job update.
- [ ] Expose protected paged job status and cancellation-before-execution; keep command acceptance and business completion distinct in UI. No automatic multi-company scheduling.
- [ ] Execute focused unit/PG/job-restart and full synthetic payroll HTTP acceptance.

### Task C: independent consumers, freshness, reporting and history lifecycle

Files: `integrations/organization-events/src`, its tests, `infrastructure/organization`, ops0120/source0121. Coordinate root-owned source emitter/service hooks before editing them.

- [ ] Reproduce coupled-sink behavior, then split current inbox, retained history and reporting into independently acknowledged groups/checkpoints. Test one failed sink while the other advances and replay without duplicate decisions/totals.
- [ ] Implement source-owned capture marker/barrier contract and coordinator evidence for all expected partitions. Keep source LSN/capture confirmation separate from source activity and retained history. Test idle healthy, missing partition, stale marker, resumed membership and quarantine.
- [ ] Add supported attendance/leave/project progress facts using actual existing source fields and definitions. No productivity inference from logged hours. Root expands protected reporting API/UI using exact integer quantities and explicit coverage.
- [ ] Implement resumable source-owned historical export/backfill with deterministic IDs, preserved provenance, contiguous range/hash manifests and conflict quarantine. Unsupported legacy actions remain a declared gap rather than reconstructed fiction.
- [ ] Implement protected encrypted archive write/verify/retrieve and authorized export integration. Keep source secrets and raw private fields out of general topics; operator-only legacy restore is a separate boundary where needed.
- [ ] Implement bounded execution of evidence-gated outbox retention and legacy delivery retirement/cutover. Default dry-run; require configured accepted capture/history/consumer/restore evidence and locked candidate identity/hash checks. No production execution.
- [ ] Run focused contracts plus isolated real PG/Kafka/ClickHouse outages/restarts/backfill/archive/cleanup acceptance; update exact deployment/runbook assets.

### Task D: central policy/API and existing application integration

- [ ] Publish shared operation mappings and fresh job-authorization DTO with exact original command/actor/membership/authority binding; deny arbitrary endpoint/resource substitutions.
- [ ] Add central entry points only for source-supported employee/account/workflow administration, durable payroll job status, richer reporting and protected archive/export. Revalidate identity/current grants before and after external reads.
- [ ] Update generated SDL/clients and source-labelled UI forms. Keep private payloads in memory, preserve current cancellation/recovery ownership and require fresh reads after authority changes.
- [ ] Add access, payload, job-state and stale-response UI tests; real browser fixtures use only isolated nonproduction services/accounts.

### Task E: final conformance and review

- [ ] Dedicated GPT6.1 sol summariser compresses execution evidence for independent reviewers; scoped lower-model review checks original requirements and concrete callers.
- [ ] Fix confirmed defects and run focused regressions. Perform a second independent final review of final changes as previously authorized.
- [ ] Run affected Rust all-target/strict changed-crate lint, generated GraphQL/TS/build/tests, SQL migration/restore fixtures and final real workflow HTTP/browser cases.
- [ ] Reconcile divergent HTML copies to one canonical implementation document while retaining the frozen baseline. Publish a requirement-by-requirement matrix with implemented/executed/production gates distinguished.
- [ ] Keep production deployment, real historical cutover, real retention deletion, TLS/ACL acceptance and production backup/restore as explicit release operations; do not mark those executed from synthetic proof.
