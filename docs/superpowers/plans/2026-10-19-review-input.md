# Bounded implementation evidence for independent review

This is a mid-execution summary, not feature completion or independent verification. It was produced from the completion plan, four 2026-10-19 progress ledgers and native `git status --short --branch` only. No implementation sources, broad repository/history, existing company data, tests or builds were inspected by this summariser. Root and tenant work continue; refresh the named ledgers before review.

## Authorization and preserved state

The plan records authorization for remaining organization features, focused checks and two independent lower-model reviews during 2026-10-18 18:56 UTC to 2026-10-19 02:56 UTC. No commits, deployment, production migrations, Dart/Flutter or unrelated cleanup. Native commands supersede older RTK guidance. All five checked repositories remain on `feat/organization-cross-company-management` with uncommitted changes. Status does not establish commit hashes; the completion ledger says preserve database HEAD `80fb0c7` and unrelated loan changes, which were not independently HEAD-verified here.

Dirty scope: service workspace/Cargo and Auth/common/Employee/Leave/Attendance/Performance/Payroll plus new organization crates, fixtures/infrastructure/integrations; database migrations 0111–0116 and masters; UI organization module/generated contract/navigation; gateway header/subgraph/server files; documentation architecture/runbooks/plans. Existing loan changes remain visible in service/database/docs. Do not reset, overwrite or attribute every dirty file to this execution.

## Evidence and limits by workstream

**Root orchestration/security:** completion ledger at 19:47 UTC records shared service credentials and mandatory identity/link/membership epochs with 11 security tests passing. Company credentials are exact-service/tenant restricted, signing route/body/audience/type. Directory/global graph orchestration, source installation acknowledgements, minimal command intents and live policy are authored. Verification-only company RSA browser mode is authored; legacy client HMAC is refused when organization transport is enabled. At that checkpoint RSA checks, integrated schema/browser and reviews were pending. Parent coordination reports ongoing legacy graph import/transition and reload recovery, so do not treat these paths as reviewed or final.

**Source tenant:** fixed-company command boundary, raw body limit, exact delegation intent and independently authenticated live policy are authored. Receipts bind command/hash/actor/membership and status requires current authority. Grant/relationship installation and actor references are transactional, with post-commit ACK. Business adapters retain workflow/version/balance/template/payroll/loan rules; metadata events exclude private bodies. Canonical primary assignments supersede legacy TEAM/workflow authority, including foreign/future managers; bounded persistent bootstrap and directory tombstones are authored.

Executed source evidence: focused all-target compilation passed before later canonical-manager/directory hardening; five tenant unit tests passed before a sixth credential regression was added. Synthetic PostgreSQL executed actual 0112/0115 SQL with nine canonical facts covering corrections/date moves/deletion/privacy/version propagation/rollback. Rust bootstrap test passed for bounded batches/cursor/COMPLETE/privacy before later canonical-manager coverage. Populated rollback refused and empty rollback passed. Canonical-manager TEAM regression first failed as intended, implementation followed, green rerun pending in ledger. These are source SQL/fixture results, not full Liquibase upgrade or complete HTTP-chain evidence.

**Event/report pipeline:** ledger records completed synthetic worker/CDC acceptance and final dependency/image checks. Eleven Node tests pass; worker syntax check passes; exact pinned pg8.23.1/KafkaJS2.2.4 lockfile audited with zero vulnerabilities. Isolated real Kafka4/PostgreSQL16/ClickHouse25 acceptance covers replay, version corrections/date move, tombstone, private-data-free quarantine, sticky PARTIAL, sink failure rollback and offsets blocked until DLQ recovery. Real Debezium captures committed corrections and excludes rollback; restricted CDC role cannot SELECT business table. Actual 0116 capture gates reject premature acceptance/invalid partition, bind membership version/history_from and deny worker private/status writes. Live authority rejects suspended/expired/deleted membership.

Root reporting ledger evidence includes organization all-target check, strict clippy, 14 ordinary tests passing/one ignored fixture then explicitly passing, real PostgreSQL authorization fixture, and exact SQL against ClickHouse. Checks cover ALL versus SELF, explicit/default company scopes, separate history permission, pending/revoked/suspended authority, typed date/UUID cursor, correction total 1800, actor provenance and exact 18014398509481982 seconds. UI/root use decimal strings/BigInt. Fresh SDL exported and UI confirmed codegen. Final image manifest recorded as `sha256:d19e015829032e57b514b6a265da0943b1f47ebe9ae84306cf8be37803653b94`.

Pipeline production limits remain: TLS/ACL deployment, collector export, restore, historical backfill/rollout unverified. Single-host reference has no host-failure availability. Idle source freshness intentionally fails until a separately reviewed heartbeat/barrier rollout. Synthetic infrastructure temporarily retained for tenant fixtures; coordinate cleanup.

**UI:** separate feature-flagged `/organization-workspace`, source-company login header, explicit target selection, identity/invitation/grant/directory/relationship management, approvals/team/feedback/appraisal, owner reports/history and scoped payroll are authored. Query ownership and command payloads stay in memory; stale/revoked responses are discarded. Exact command identity/payload/version survives uncertain transport while workspace remains open; uncertainty never means business success. Ledger records focused Vitest 10 files/26 tests passing in `.superpowers/organization-ui-tests.log`, proving synthetic helper/hook behavior only. Earlier type inference fixed; ledger still leaves authoritative contract/type/lint/browser integration pending, while later pipeline ledger confirms SDL/codegen. Resolve this timestamp mismatch before claiming UI validation complete. Reload recovery is still in progress per parent coordination.

## Prioritized review entrypoints

1. Trust boundary: shared protocol/security, Auth/common JWT/browser source-company handling, live policy and service credentials; gateway source header forwarding. Trace current epoch/eligibility and wrong-company/resource/body/route rejection.
2. Source boundary: tenant command parsing/receipt replay, source policy-before-query, installation ACK/version fences and business adapters. Trace canonical primary authority through local legacy TEAM/workflow/queue, future manager snapshots and legacy import/transition. Check bootstrap, module subscription and payroll loan attribution against existing callers.
3. Command lifecycle/UI: command intent persistence and status authorization, uncertain outcomes, reload recovery, revoked/private payload pruning, immutable payroll revision/fingerprint and source-confirmed feedback. Verify generated SDL and actual UI contract before inferring browser correctness.
4. Projection/reporting: worker required-history ACK ordering, provenance/hash/version fences, membership capture gates and report live authority; verify stale/missing source handling and large integer exactness. Separate synthetic acceptance from production TLS/restore/backfill.
5. Regression/integration: complete source HTTP chain and current focused checks; ordinary local workflows, Finance/webhook endpoints, tenant isolation and source login semantics. Two review passes and confirmed fixes are still outstanding in the completion ledger.

## Exact evidence locations

All ledger paths below are under `D:/work/heliorventures/hrms-documentation/docs/superpowers/plans/`:

- `2026-10-19-organization-completion.md`: authorized scope, architecture contract, ownership and validation gates.
- `2026-10-19-organization-completion-progress.md`: root checkpoint and unfinished phase checklist.
- `2026-10-19-tenant-execution-progress.md`: source implementation and superseded/current check limits.
- `2026-10-19-event-pipeline-progress.md`: synthetic real infrastructure, reporting/capture/actor evidence and production limits.
- `2026-10-19-organization-ui-progress.md`: UI semantics, focused synthetic tests and outstanding validation.

Architecture specification named by plan: `hrms-documentation/docs/architecture/2026-10-18-organization-cross-company-management.html`. Pipeline heartbeat design named by ledger: `heartbeat-coverage.md` (resolve within owned pipeline docs before reading). Earlier prerequisite ledgers were deliberately not reopened.
