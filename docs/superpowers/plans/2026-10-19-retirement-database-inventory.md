# Retirement database inventory — 2026-10-19

Scope: source inspection only; no database connection, implementation, tests or builds. Existing dirty work was preserved. Paths below are relative to the workspace. Live catalog dependencies, deployed migration state, actual history completeness and delivery parity are **NOT DEMONSTRATED**.

## Verified source contracts

Database migration paths below abbreviate `hrms-database/changelog/migrations/` as `M/`.

| Source | Schema, dependencies and state that retirement must preserve |
|---|---|
| Tenant `audit_log` | `M/0027_communication_audit/communication_audit.xml:72-95`: UUID identity, tenant/user, entity/action, before/after JSON, IP, user agent, creation time; user FK `SET NULL`; tenant/time and entity indexes. `M/0051_employee_self_service_readiness/employee_self_service_readiness.xml:44-55`: mutation guard/function rejects UPDATE and DELETE. The FK's SET NULL action can therefore encounter that guard. `M/0121_organization_source_history/organization_source_history.xml:5-8` adds sequence-backed history position and unique index. |
| Ops `operator_audit_log` | `M/0001_operator_plane/operator_plane.xml:155-177`: operator/user FK `RESTRICT`; nullable tenant; entity/action/before/after/IP/time; user/tenant/entity indexes. No mutation trigger is defined for this table in the searched migration references; its append-only comment is not an enforced constraint. There is no separate ops `audit_log` in this migration inventory. |
| Tenant `outbox_event` | `M/0030_outbox_events/outbox_events.xml:11-30`: event identity/aggregate/type/payload, status/retry/error, created/processed times; status/time and aggregate indexes. `M/0034_outbox_claimed_at/outbox_claimed_at.xml:10-14` adds `claimed_at`. `M/0066_lifecycle_validation_integrity/lifecycle_validation_integrity.xml:10-43`: separation holds unique `offboarding_event_id` with deferred FK **RESTRICT** to this table and a check coupling it to `offboarded_at`. A durable compact receipt must replace this reference before table retirement. |
| Tenant `webhook_delivery_log` | `M/0026_integrations/integrations.xml:57-77`: subscription FK **CASCADE**, subscription index, updated-at trigger calling shared `kabipay_ops.set_updated_at()`. Each row contains event name, full payload, HTTP status/body, success, attempt and delivered/created/updated times. `delivered_at` defaults NOW even for failed attempts; it is not proof of successful delivery. |
| Tenant `employee_finance_outbox` | `M/0106_loan_exit_coordination/loan_exit_coordination.xml:21-31,123-153`: private immutable event binding, operation FK `(tenant_id,operation_id)` to `employee_exit_operation`, unique `(tenant_id,operation_id,event_type)`, event allowlist/object payload/attempt checks; due index on available time/id where undelivered. Trigger/function forbids DELETE, any modification after delivery and any binding/payload changes. Retry metadata remains operational authority until receiver acknowledgement. Do not retire `employee_exit_operation`, finance authorization/review/guard state or their invariants. |
| Tenant `notification` | `M/0027_communication_audit/communication_audit.xml:44-64`: user FK CASCADE, user index, updated-at trigger; recipient/title/message/action URL and **live read state** (`is_read`,`read_at`). `M/0074_automated_employee_notifications/automated_employee_notifications.xml:55-84`: occurrence FK CASCADE to notification and unique `(tenant_id,event_type,employee_id,event_date,recipient_user_id)`, employee/recipient FKs and tenant/date plus recipient/date indexes. Deleting notifications currently cascades away deduplication evidence. Notification settings/templates are business configuration and remain. |

No additional source-referenced views or table-specific production grants for these legacy tables were found by the scoped dependency search. A deployment must additionally inspect `pg_depend`, foreign keys, triggers, routines, views/materialized views, policies, publications, table/column/default privileges and ownership; source inventory does not prove a live catalog is clean. Shared `set_updated_at()` must remain.

## Canonical capture and history constraints

- `M/0115_organization_tenant_runtime/organization_tenant_runtime.xml:47-53` defines company event outbox; `M/0121_organization_source_history/organization_source_history.xml:29-41` gives deterministic identity and conflicting-content rejection. Positions/markers and compact cleanup receipts are at 0121:5-27. The canonical outbox remains the atomic business handoff, with bounded accepted cleanup; it is not the history store.
- Existing **legacy audit export is lossy**: 0121:152-162 maps unknown entity/actions to UNMAPPED, retains selected statuses and a source hash, but omits before/after bodies, IP and user agent. 0121:189-191 exports this transformed envelope. A hash cannot recover discarded data. Its COMPLETE state and manifests cannot authorize full legacy-table retirement.
- 0121:124-136 stores restartable export metadata/chunks; 138-175 locks the source and captures cutoff; 178-204 limits batches to 200 and rejects changed membership/version. Preserve these authority fences, but create an independent full-fidelity source export contract. Detachment must retain scoped historical access rather than require an ACTIVE membership to resume every historical migration.
- `M/0120_organization_capture_lifecycle/organization_capture_lifecycle.xml:46-67` checks current accepted capture, membership/epoch, freshness and per-role/partition barriers. 0120:133-177 defines archive manifests, restore/retention evidence, delivery-cutover offsets, policies disabled by default and control cleanup receipts. These records do not themselves verify external history or delivery.
- `hrms-database/provisioning/organization/cdc-source.template.sql:9-38` and `cdc-boundary-guard.sql:29-34` restrict company publication/identity to **exactly company outbox plus marker**; ops publication is only `kabipay_ops.organization_outbox`. PostgreSQL has no publication ACL; unrelated publications also break isolation. Keep production SQL in hrms-database.
- `hrms-clickhouse/migrations/0001-company-history.sql:4-30` uses ReplacingMergeTree; logical reads require FINAL; history and reporting have separate tables. TTL is disabled by `DELETE WHERE 0`. `0002-control-history.sql:4-24` preserves nullable-organization security events. `grants/0003-company-history.sql` permits projection readers company business history; `0004-control-history.sql` protects global security access. Raw audit/private finance must not enter those broader reader paths. Full-fidelity protected history and private delivery history need their own grants/storage contract, owned by hrms-clickhouse.
- `hrms-kafka/scripts/admin.mjs:13-18,34-59` gives separate reader identities/groups but history/inbox/reporting consume the company topic. `connectors/connector.template.json:16-18,28-36` selects only canonical outbox/marker and routes company outbox events. New sensitive streams require separate explicit topics, publishers, consumers, quarantine paths and literal ACLs in hrms-kafka; do not widen existing public event payloads.

## Proposed forward migrations and graph

Numbers are proposals: tenant master currently includes through 0121; ops master includes 0123; 0122 directory is absent. Coordinate reservations before implementation.

`CH protected history + Kafka isolated streams` → `0124 ops retirement authority/evidence` → `0125 tenant durable handoff + compact receipts + restartable exports` → `application producer/consumer/read cutover + verified drain` → `0126 tenant retirement` → `0127 ops retirement`.

Use CH forward files 0003/0004 for new protected history/grants. All production PostgreSQL DDL, functions, grants and prerequisite checks belong in hrms-database; CH schema/grants in hrms-clickhouse; topic/ACL/connector operations in hrms-kafka. Do not alter applied 0027/0030/0051/0106/0121 changesets.

Required compact operational state:

- Event receipt: original event UUID, tenant, kind/aggregate, immutable content hash, authority/producer generation and durable handoff/terminal acknowledgement references; preserve separation marker FK.
- Notification receipt/read projection: original notification UUID, tenant/recipient, event/content reference and hash, created time, read time/version, deletion policy; retain occurrence unique delivery key and repoint its FK before retirement.
- Webhook/finance delivery authority: event+destination/operation identity, unique dedupe key, payload hash, current state, attempts, next eligible time, lease/fence token/expiry, durable destination acknowledgement and accepted time, bounded error code. Pending payload remains transactionally available in a private handoff until accepted; a hash alone cannot support redelivery. Store complete attempts/payloads/responses in protected history.

## Lossless cutover and fail-closed retirement

1. Inventory actual source schema/dependencies and scope each export by source database/schema/table, tenant and original UUID. Preserve every original column/type/time and canonical full-row hash; add immutable source position under a producer fence. Capture finite cutoffs without losing transactions committed out of sequence. Resume by committed chunks with durable manifest, row count, hashes and destination acknowledgements; retries must reject conflicting same-identity content.
2. Install atomic replacement handoffs and enforce database-visible writer/worker generations so old binaries cannot resume legacy writes or sends after cutover. Migrate outstanding claims/retries and recipient/subscription identity without resetting dedupe. Fence stale workers before receiver side effects; receiver idempotency must tolerate acknowledgement loss.
3. Verify complete source-ID/hash parity through the final cutoff, protected history query parity and restore exercise. Require no gaps/quarantine, exact expected partitions, current authority/epoch and independently acknowledged replacement consumers. Verify every pending delivery is either accepted into durable replacement ownership or terminally acknowledged; zero legacy backlog alone is insufficient.
4. Record signed/reviewed evidence bound to source cutoff, migration/producer generation, current authority and history/delivery digests. Retirement preconditions HALT on missing, expired, mismatched or revoked evidence; lock authority and source objects while checking. Repoint FKs, remove legacy routines/triggers explicitly, then retire exact tables without CASCADE. Recheck the catalog dependency allowlist. Keep compact receipts and canonical outbox/marker/cutover/restore evidence. Rollback before destruction uses accepted generation rollback; restoration after destruction requires verified full archive, never empty-table recreation.

## Focused verification matrix for implementation

| Area | Required evidence |
|---|---|
| Full fidelity | Unknown audit actions/entities, full before/after/IP/agent, nullable ops tenant; exact raw row hash roundtrip; original timestamp precision. |
| Restart/concurrency | Crash before/after destination insert/chunk acknowledgement; duplicated chunk; conflicting identity/hash; concurrent commit beyond cutoff; old worker after fence; membership/authority change. |
| Business integrity | Offboarding FK survives; notification unread counts/read updates and occurrence dedupe survive; finance operation/event unique constraint survives; private event immutability remains. |
| Delivery | Pending/in-flight/retry/terminal rows, subscription deletion, destination timeout/ack loss, receiver duplicate; attempt parity and no extra sends. |
| Fail closed | Missing/expired/revoked archive/restore/cutover evidence; stale epoch/marker, partition gaps/quarantine, unrelated live dependencies, old writer generation; zero deletion on every failure. |
| Access/retention | Cross-company/topic denial; reporting cannot read raw audit/private finance; org-null operator history denied to app; TTL remains disabled until accepted policy/restore evidence; production SQL absent from application runtime. |

These are proposed checks, not executed results.
