# Retirement execution evidence summary

19 October 2026. Bounded handoff for independent review; local uncommitted work only. This summary compresses the foundation, source, audit-application, infrastructure, tools and providers reports, `2026-10-19-legacy-retirement-progress.md` and `.codex-tmp/private-fixture-bindings.json`. Coordinator updates below are attributed separately. The dated progress ledger contains older checkpoints; later owner reports supersede their counts/status. No tests, builds, migrations or live operations were run to prepare this summary.

## Implemented boundaries requiring review

- Common Rust and Node private contracts use bounded AES256-GCM frames, authenticated source identity/generation and exact original-byte hashes. Source producers query and lock explicit source authority; absent/stale registration fails closed. Audit actor existence/tenant and generation are checked in the publication statement. Delivery receipt plus frames are atomic; duplicate identities must match immutable metadata/hash.
- Business audit callers preserve their original transactions/savepoints. Survey lifecycle state and offboarding identity have compact source-owned replacements. Audit history uses signed fixed-endpoint mTLS transport plus authenticated source pending overlay; archive access is durable/revocable rather than tied to destructive authorization expiry.
- A separate tenant-maintenance binary owns existing source business schedules, explicit company binding and no delivery polling. Source delivery executes only fixed configured destinations under signed tenant/generation/hash/version/lease proofs. Exact-next claims, durable accepted receipts and UNCERTAIN ambiguity prevent blind resends. Finance retains authoritative Employee/Payroll signed reconciliation. Webhook DNS/address/HTTPS/proxy/redirect policy is source-owned; legacy password hashes never become signing secrets.
- Analytics outbox/log providers merge protected original history with source pending frames and compact current receipts. Delivery history has distinct signed domains/path and three accepted original archive identities. Source-authorized replay locks receipts, restores authenticated original payload if necessary, audits the actor and emits a fresh bounded reference command while preserving original intent/base lease. Parent owns broker replay integration.
- Forward PostgreSQL preparation is separate from explicit destructive retirement entrypoints. Source-owned export/capture/accept helpers retain exact raw rows and dependencies. Retirement requires full restore, current scope/generation, source digest/catalog equality, pending destination ownership, business/reader switches and current complete capture; DROP has no CASCADE. Cleanup retains nonterminal delivery payloads and locks receipt state against replay races.
- Kafka routes audit/delivery/operator streams separately while preserving company/control topics and publication pair. Private principals/groups and work/retry/DLQ/history ownership are separated. ClickHouse physically separates private record/chunk/checkpoint/coverage tables, validates byte hashes/framing and grants no private access to reporting. FINAL/application conflict checks remain required; ReplacingMergeTree is not uniqueness enforcement.
- Export/restore tools preserve PostgreSQL raw JSON UTF8 bytes, UUIDs and microseconds without numeric reserialization. Historical exports are nonexecutable. Pending migration requires explicit classifications/destinations and source-validated broker ownership acknowledgements; broker ownership does not assert receiver success.

## Evidence ledger and freshness

### Actual isolated infrastructure execution

- PostgreSQL16: **34 scenarios passed** with final standalone fixture functions, including destructive negatives/exact drops, generation/restore/catalog/pending/business/reader/capture gates, legacy writer/TRUNCATE fencing, survey ordering/rollback, UTC bytes, cleanup and the reproduced two-connection cleanup/replay race.
- ClickHouse25.8: **10 scenarios passed** against final schema, covering record/hash/chunk/role denial/source identity/coverage. Separate loader offline validation and nine migration tests passed.
- PostgreSQL16 + Kafka4 + Debezium3.2: **5 CDC scenarios passed**, covering two-company private routing, company/marker bypass, strict NULL-organization metadata parity, NULL-original-tenant operator routing and publication pair. This isolated rehearsal uses plaintext; production TLS/ACL denial is unproven.
- Infrastructure Node checks: **35 passed** across Kafka admin11, private streams3, SQL contracts3, routed control3, existing control6 and migration9. These are distinct from actual infrastructure scenarios.

### Fresh Rust execution versus compile-only evidence

- Audit report supersedes the foundation report's older failed test-import build and earlier four-test success: fresh common/survey/attendance test executables were built successfully, then **68 tests passed**: common21, survey9, attendance19, attendance policy18, and common isolated PostgreSQL atomicity1.
- The last test used actual PG16 TEMP tables inside a transaction rolled back at completion. It proves savepoint rollback, actor tenant rejection/acceptance, generation fencing, delivery dedupe/conflict and receipt rollback on frame failure. It does not prove full migrated schema/cutover, real concurrent generation scheduling or remote signed history.
- Common/survey/attendance/analytics/expense library/test targets passed coordinated Cargo check. A later SQL-only archive TTL predicate change is covered by static RED/GREEN evidence; full signed SQL/mTLS history runtime remains unrun.
- Source owner previously passed Employee/maintenance Cargo check and two Employee proof/key-config tests, plus deterministic native policy tests (egress1, delivery3). Later fixture/source changes require final compilation/tests. A frozen JSON request/response test and adapted ignored Finance integration tests were not in that tested binary.
- Providers added raw-hash/scope/u64 and ignored PG replay tests. **Their focused latest common/analytics compile and test execution remain pending**; formatting is not compilation.

### Node, source checks and in-memory boundaries

- Foundation private crypto: **8 passed**, including frozen cross-language vector, immutable-head tamper, framing, key rotation and strict config/calendar checks. Common fresh Rust tests also cover the vector.
- Audit static source contract: **6 passed**; source maintenance static checks2 and provider source checks2. These prove inspected caller boundaries, not deployed runtime behavior.
- Tools: legacy12 and capture2 passed using in-memory protected-store substitutes. Actual PostgreSQL export/publish/accept rehearsal covered all five populated legacy table kinds, **8 raw rows / 9 frames**, exact replay IDs and independent restored-byte digests; wrong generation/hash rejected. The real private processor ran, but protected persistence was in memory. This is not Kafka-to-real-ClickHouse restore proof.
- Provider delivery history5, existing query4 and audit source6 passed. Delivery history tests use a store double and SQL contracts; real ClickHouse grouping/cursor/log SQL and mTLS remain unrun.
- Coordinator reports the latest individual Node suites passed: crypto8/history5/query4/delivery6/ownership2, plus separate source-identity5. The last combined run was23 before two new regressions; **do not claim a combined25 pass until rerun**. Worker CLI syntax passed. Full worker end-to-end remains unrun.
- Coordinator reports source pending migration/ownership **actual Rust compilation GREEN**; no-run build86907 remains in progress. New source-pending/ownership PostgreSQL fixtures are written but not executed. This supersedes the tools report's earlier compilation-pending statement without claiming runtime acceptance.
- An older broad foundation Node snapshot was 61 passed/5 failed during parallel WIP; it is neither a current suite pass nor proof that all those failures remain. Acceptance/schema/launcher/process-tree issues require current focused reconciliation.

## Held fixture and operating constraints

The shared synthetic PG16 fixture is loopback **62831**, container `private-retirement-sql-ad53a1a928554e23b894132e2720cdcf`, terminal55266; root coordinates cleanup. Audit released its claim; root/tools release is still required. Do not reproduce fixture credentials into deploy configuration.

It is FENCED and archive accepted, with retirement flags false. **Installed retirement/cleanup/guard function bodies predate final broker-owned waiver and receipt-lock correction. Refresh canonical0125 functions before any held-fixture cleanup/retirement acceptance.** Fresh standalone 34-scenario evidence uses final functions. Earlier native fixture shutdown cause is NOT DEMONSTRATED.

## Critical remaining gates

1. Explicit trusted source authority bootstrap for every company and metadata installation, including fresh/verified-empty installs; review exact invoker table/lock/default grants. Preparation DDL alone does not authorize production producers.
2. Latest providers/common/analytics Rust compilation and new unit/PG replay execution; final source/maintenance/ownership runtime tests and adapted Finance/offboarding tests. Ownership/source-pending compilation passed, but build86907 and actual PG fixtures remain pending. Reconcile source drift against executable provenance rather than old build success.
3. Full real private worker chain: source encrypted publication → Kafka collection/work ownership → signed HTTPS source execution → durable outcome → real ClickHouse history → independent restore/capture/replay. Demonstrate offsets, retries/DLQ, restart/ack-loss behavior, authentic capture completeness and protected history SQL/mTLS. Separate infrastructure tests do not establish this composition.
4. Real signing-key reconciliation, production Kafka TLS principal denial, source/receiver DNS and redirect fixtures, authoritative Finance receiver acceptance, concurrency/restart scheduling and receiver idempotency. No exactly-once receiver effect is demonstrated.
5. Workspace/runtime/Docker/deployment reference completion after old worker removal; deployment and HTML/operator documentation; explicit release sequence and independent reviews. Providers report targeted removed-entity imports/callers absent, but coordinator must finish obsolete binary/caller/config searches across final owned scope.
6. Guarded migration/export/pending ownership/business/reader/capture acceptance for actual sources before destructive retirement. No live migration, production deployment, destructive shared retirement, browser acceptance or automatic commit is claimed. Missing proof must keep retirement closed.
