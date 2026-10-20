# Legacy audit and delivery retirement implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development. Track each task and its focused verification; user forbids automatic commits.

**Goal:** complete the remaining legacy migration and remove obsolete runtime code/storage only through verified replacements and guarded forward retirement.

**Architecture:** one existing CDC boundary, separately routed encrypted private streams, protected external history/delivery processing and source-owned compact business/receipt state. No shared company DB credentials, guessed legacy successes or silent historical loss.

**Tech Stack:** existing Rust/SeaORM/Axum, Node22/KafkaJS, PostgreSQL16, Debezium3.2, Kafka4, ClickHouse25.8, current Docker/Caddy/PowerShell deployment.

**Spec:** `../specs/2026-10-19-legacy-retirement-design.md`; existing architecture v8 phase7 and three bounded source inventories.

## Global constraints

- User explicitly approved full local migration/reviews/focused checks. No commits/live migration/deployment; native commands, no RTK/Dart/Flutter. Preserve unrelated dirty work.
- PostgreSQL DDL only hrms-database; ClickHouse schema only hrms-clickhouse; Kafka installation/operations only hrms-kafka. Keep original migration checksums/frozen HTML.
- Required business state/notifications/receipts/jobs remain; remove transport polling, duplicate histories and obsolete callers, not their active business responsibilities.
- Interfaces below are shared contracts. Agents own separate files; coordinator integrates overlapping profile/leave/analytics files and shared manifests.

## Review focus

1. Private bytes must never reach general reporting topics/roles, diagnostics or arbitrary destinations; cross-tenant/key/purpose tampering is rejected.
2. Old workers, expired leases, replay and delayed responses cannot repeat acknowledged destinations or authorize a stale Finance transition.
3. Full raw unknown/oversized/history rows and pending intent ownership survive cutoff, partial export, restore and detachment.
4. Survey read-your-write, offboarding FK identity, notification read/dedupe and every source maintenance job survive the old worker's removal.
5. Missing evidence, unexpected dependencies, unfinished private coverage or ambiguous old delivery stops retirement without data deletion.

## Tasks and interfaces

- [x] **1. Foundation/crypto.** New common `private_events/{mod,crypto,types}.rs`, public `append_audit`, `enqueue_delivery`, `read_audit_history` ports and Node `private/{contract,crypto}.mjs`. Exact AES-GCM associated-data and source-row hash contract; keyring scoped by tenant/purpose, bounded framing/rotation, synthetic cross-language vectors. RED wrong-scope/tamper/partial-frame tests, then implement and run focused common/Node tests. Coordinator owns exports/Cargo dependencies.
- [x] **2. Schema and stream infrastructure.** Forward0124–0127 ownership as spec; company event_stream default company/private-only nullable organization; metadata operator stream; compact survey/domain/delivery receipts; full export/cutover/retirement gates. CH0005+ private schemas/chunks/grants. Kafka fixed routing/topics/separate private principals/groups. RED provision/catalog/gate/ACL/isolation tests, then isolated migration and actual CDC proof. Exclude private rows from old company cleanup until separate coverage.
- [x] **3. Audit application.** Convert calendar/attendance/notification/survey producers, local survey business state and protected history readers; coordinator converts overlapping employee/profile/leave/analytics helpers. `append_audit<C:ConnectionTrait>(db:&C, AuditRecordInput)->KabiPayResult<Uuid>` preserves actor/raw JSON/time/transaction. History port uses signed fixed private RPC plus pending atomic-outbox merge, exact tenant/RBAC/filter/order and source unavailability semantics. RED transaction/savepoint/survey/API/unknown-payload tests then focused Rust/UI compatibility checks.
- [x] **4. Source maintenance and delivery adapter.** Move all listed source schedules to `kabipay-tenant-maintenance`; remove the old transport claim/retry loop. Replace Finance pending producer/loop with immutable intents and source operation adapter. `enqueue_delivery<C:ConnectionTrait>(db:&C, DeliveryIntentInput)->KabiPayResult<Uuid>` writes intent hash/compact destination receipts and encrypted stream atomically. Fixed HTTPS `/internal/private-events/delivery` validates source tenant, service proof, intent/destination/fence, reconstructs source Finance signatures or pinned webhook egress, and returns bounded signed outcomes. RED scheduling/offboarding/Finance/fanout/SSRF/fence/ack-loss tests before implementation.
- [x] **5. Private history and broker delivery.** New Node purpose-specific workers/query API: encrypted stream validation, duplicate/conflict-safe CH commit/checkpoint; durable broker retry/DLQ and per-destination execution with fixed source API clients. Historical replay is non-executable. Protected source-bound history RPC supplies existing DTOs. RED isolation/crash/retry/order/expired-proof/receipt/oversize tests; actual separate-company PG/Kafka/CH lifecycle and receiver failure fixture. No source DSNs.
- [x] **6. Full backfill and accepted cutover.** New source-owned restartable raw-row exporter and migration CLI with immutable manifests/chunks/source hashes; every five-table kind, unknown fields/actions, nullable ops tenant, original IDs and microsecond timestamps. Separate archive-only records from reconciled executable pending intents; verify restored full rows and receipt/FK/cutoff parity. Guard source generation, resume and policy evidence before0126/0127 retirement. RED incomplete/ambiguous/raced/conflicting/no-restore gate tests then isolated full populated rehearsal.
- [x] **7. Caller/entity/deployment cleanup.** Remove obsolete entities, direct table references, finance delivery loop and old worker crate/binary after all replacements/tests. Keep supported GraphQL/health APIs through new providers. Update current deployment/company endpoint/key/env/Kafka/CH/archive wiring, scripts/Caddy and source fixtures. No active manifest references to retired binaries/tables. Run caller searches, focused configuration/compile checks and build artifacts once the final source is stable.
- [x] **8. Independent review and final evidence.** Separate correctness/security and lower-model DRY/SOLID review; bounded GPT6.1 execution/evidence summary for the coordinator. Fix verified findings with regression tests. Update architecture HTML/mirrors, phase/cleanup audit, release/rollback/evidence runbooks; keep production/browser/receiver/restore gates explicit. Check exact owned process/container exit and all repository branches/diffs; leave work uncommitted for manual review.

## Execution ledger

See `2026-10-19-legacy-retirement-progress.md`. Each task records red/green commands, ownership, changed interfaces, findings, rulings and limitations. No full release compile per small change; focused checks first and stable-source image verification last.

Local execution complete; final proof and production acceptance limits are in the execution ledger. Live cutover/retirement is not authorized by this implementation completion.
