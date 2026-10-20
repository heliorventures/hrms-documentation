# Complete legacy audit and delivery migration

## Authority and intent

Implements the already recorded architecture's phase7 cleanup. On 19 October2026 the user explicitly authorized full migration of audit history, legacy delivery/webhooks, private Finance delivery, historical/pending-data tools, guarded retirement, independent review and focused checks. Existing organization/infrastructure decisions remain binding. Local source and isolated rehearsals are authorized; live migration/deployment and commits are separate. Preserve unrelated dirty work.

Success means every active producer/reader/scheduler has a supported replacement, historical records are recoverable without field loss, pending deliveries retain identity and ownership, and obsolete runtime callers/binaries/entities can be removed. Retirement SQL must reject incomplete evidence. Merely installing infrastructure or renaming old log/queue tables is insufficient.

## Verified constraints

See the three `2026-10-19-retirement-*-inventory.md` reports and their dedicated GPT6.1 summary. Audit rows drive survey opening/failure deduplication. The outbox worker also hosts source business schedules. Offboarding has an immutable FK to old outbox IDs. Private Finance is internal Employee-to-Payroll confirmation/cancellation, with authoritative readback and signed receipts. The old export is lossy and does not cover legacy delivery tables. Notifications/read state/settings and operational receipts remain business state.

## Source and privacy boundary

1. Keep the exact existing company publication tables: company_event_outbox and organization_capture_marker. PostgreSQL publication access cannot be isolated by inventing another publication role. Do not publish raw private tables or widen reporting payloads.
2. Add a checked `event_stream` discriminator to the existing atomic company outbox: company (default), audit, delivery. Existing organization_id is mandatory for company events; private streams work independently of organization membership. Existing business event envelopes remain unchanged. Private payloads use authenticated AES256-GCM encryption before persistence/publication.
3. Debezium EventRouter routes by event_stream to organization.company.<UUID>, organization.audit.<UUID>, organization.delivery.<UUID>. Metadata outbox routes existing control events unchanged and operator audit to its own protected topic. Only fixed checked discriminator values determine routing. Marker predicates, exact schemas, roles, slots and private Connect proxies remain.
4. Separate Kafka audit/delivery/operator-audit principals and groups. No reporting/inbox principal receives private topics or keys. Company source producers get only their own company/purpose keys; private workers receive only the purpose-specific keys needed for their configured bindings. No source database credentials go to a shared worker.
5. Cipher envelopes have version, event/record IDs, tenant scope, purpose, source kind/resource hints, original time, key ID, nonce, source SHA256 and ciphertext. AES-GCM associated data binds all immutable head fields. Wrong tenant/purpose/key/ID/time/hash or modified ciphertext fails closed. Key rotation preserves old readers until evidence permits removal; no default production key, disabled TLS or caller-selected credential path.
6. Full raw legacy rows retain original UUID, table/schema/database identity, exact serialized row, timestamps, actor, before/after, IP/agent and hash. Unknown entity/actions are retained. Bounded chunk framing preserves oversized historical rows without truncation; incomplete/conflicting chunks cannot be accepted as complete history. Private archive restore streams verify the original byte hash.

## History and source business state

Protected ClickHouse schemas/grants are separate from business_history/reporting. Private consumers durably persist duplicate-safe records/chunks before committing offsets. Query APIs accept fixed typed filters and authenticated, tenant-scoped service proofs; never SQL, arbitrary URLs or browser-selected source identities. Existing analytics and survey permissions/DTOs/order remain, with no expansion of payload access to organization reporting. Source pending-outbox merging supplies read-your-write while external history catches up; history unavailability/gaps must remain visible rather than becoming a fabricated empty history.

Survey execution moves to compact local transactional lifecycle state, backfilled from exact old event order. It preserves one opening and failure deduplication under the same locks/transactions. Historical management events move to protected history. Notifications, read state, consent, templates and automated occurrence dedupe remain in the existing business tables.

Offboarding IDs move to immutable compact domain receipts before their FK changes. Existing IDs and timestamp pairing remain verifiable. The worker's source-only schedules move to an independently deployable `kabipay-tenant-maintenance` binary: offboarding/access/session revocation, attendance expiry, surveys, celebrations/privacy/dedupe, performance cycle/deadlines, staged upload/video expiry and private-file cleanup. This runner performs business sweeps; it does not poll a transport outbox.

## Delivery and Finance

Produce one immutable intent per event/destination inside the original business transaction. Preserve all11 webhook event names and both Finance terminal kinds. Stable original IDs and per-destination identity prevent partial fanout retrying acknowledged destinations. Compact source receipts retain only concurrency, dedupe, authorization and outcome state; payload copies, attempt history and retry schedules move to the private broker/history pipeline.

The delivery consumer owns configurable bounded backoff/retry topics, retry caps, DLQ and permissioned replay. Kafka offset acknowledgement follows durable broker state/history ownership; crashes and retries retain intent/destination IDs and content hash. Historical replay never becomes new executable work. No destination, disabled, delivered, retryable failure, permanent failure and uncertain outcome are distinct.

A fixed source adapter executes egress. It validates scoped service proof, current source generation, immutable intent hash, destination/config version and receipt lease before sending. It never accepts an arbitrary URL. Completion is fenced by lease generation. Webhooks preserve v1 payload/signature compatibility, add stable delivery/idempotency headers, use configured signing-key references, reject malformed keys, deny redirects/proxies, enforce explicit DNS/IP egress policy and bound request/response/diagnostics. Existing one-way subscription hashes cannot manufacture outbound secrets: cutover must reconcile real key references, rather than invent credentials. HTTP2xx retains the current at-least-once contract; exactly-once receiver effects require receiver deduplication/acknowledgement acceptance and are never inferred from Kafka acknowledgement.

Finance carries only immutable operation/action references. The source reconstructs a fresh signed Employee-to-Payroll request and validates the signed tenant/request/action/expected-state response. Keep authoritative Employee status readback, authorization binding, loan holds and transactional Payroll FNF creation/reconciliation. Source service secrets and client JWTs never enter Kafka or shared workers. Remove the finance polling loop only after all pending operation identities are safely transferred.

## Capture, migration and retirement

Private streams have their own durable checkpoints/coverage/archive acceptance. Existing company cleanup must exclude private records until private-specific evidence is accepted; ordinary reporting barriers cannot authorize their deletion. Source ownership/generation and bounded compact migration metadata are operational state, not an event archive.

Use restartable source-owned export and cutover tools. Fence old producers/workers, establish a commit-safe cutoff, export every row from tenant audit_log, ops operator_audit_log, outbox_event, webhook_delivery_log and employee_finance_outbox, and reconcile original identity/hash/count/restore. Export evidence separately from executable pending intents. PROCESSED/DELIVERED never becomes a new command. Uncertain or uncorrelatable webhook evidence remains explicitly unresolved and blocks destructive retirement unless an authorized reconciliation resolves it. Detachment does not erase local historical access.

Retirement requires source/version/generation-bound evidence, complete raw archives, restored hashes, pending-destination ownership/receipts, source business-state backfill and FK parity, private capture coverage, active reader/writer switch and exact dependency inventory. SQL locks the authority/source, validates all gates, and drops only exact obsolete routines/triggers/tables without CASCADE or trigger bypass. Missing/mismatched/revoked/stale/incomplete evidence halts without deletion. New empty installations need an explicit verified-empty path. Applied migrations and the frozen architecture baseline are immutable.

## Ownership and reserved forward resources

- hrms-database: PostgreSQL0124 control/checkpoints/cutover;0125 tenant private streams/business receipts/state/export;0126 tenant retirement;0127 ops retirement. Confirm uniqueness against masters before creation.
- hrms-clickhouse: new identities0005+;0001/0002 schemas and0003/0004 grants are already occupied. Own protected history/chunk schemas, grants and migration versioning.
- hrms-kafka: stream routing, exact topic/ACL/group provisioning, TLS bindings and independent deployment.
- hrms-svc: common private-event contracts/crypto, application producers/readers, maintenance, source adapter and private consumer/export/archive behavior.
- hrms-documentation: runtime manifests/Caddy/env/runbooks, immutable baseline plus current architecture/phase audit.

## Required verification

RED-to-GREEN tests for crypto cross-language vectors/tampering/rotation; transaction/savepoint rollback; survey state concurrency; offboarding FK identity; Finance confirmation/cancellation and signed mismatch/readback; per-destination fanout/retry/lease/ack loss; SSRF/redirect/DNS/size/UTF8/key errors; unknown/raw/oversized legacy row roundtrip and chunk restart/conflicts; pending-versus-history classification; detached sources; old worker fencing; private ACL/CH isolation; private cleanup exclusions and every destructive gate negative. Run focused Rust/Node/SQL tests and isolated Kafka/CH/PG rehearsals, then two independent source/security reviews and fix findings. Builds/config/mock/static proof remain distinct from live/browser/receiver/restore acceptance.

## Reference

Pinned Debezium3.2 supports explicit EventRouter routing fields and topic replacement: https://debezium.io/documentation/reference/3.2/transformations/outbox-event-router.html . AES-GCM implementation API: https://docs.rs/aes-gcm/0.10.3/aes_gcm/ . No package/runtime upgrades are implied.
