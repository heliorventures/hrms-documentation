# Independent retirement security and correctness review

19 October 2026. Read-only source review of the foundation, source adapter, pending migration, private worker and bounded PostgreSQL guard surface. This report was written without changing implementation, running builds/tests, using live services or reading full execution logs. The execution summary and approved design were the initial context; their reported successes are not fresh runtime evidence from this review.

## Findings

### RSEC-1 — P1 — Terminal receipt immutability prevents durable broker ownership acknowledgement

**Location:** `hrms-database/changelog/migrations/0125_private_event_source/private_event_source.xml:198`; interacting callers: `hrms-svc/crates/kabipay-employee/src/services/private_ownership.rs:170-174`, `hrms-svc/integrations/organization-events/src/private/worker.mjs:51-54`, and `hrms-svc/crates/kabipay-tenant-maintenance/src/migrate_legacy.rs:265-269`.

The receipt trigger rejects every changed field once `OLD.status='DELIVERED'`. The first ownership acknowledgement nevertheless always updates `broker_owned_at`, `broker_owner_id`, `broker_receipt_sha256` and `updated_at`, without a terminal-status exception. The worker always invokes that acknowledgement after publishing executable intent work and before committing the original source offset.

This fails deterministically for migrated webhook destinations whose exact legacy HTTP acknowledgement was reconciled: migration creates their encrypted intent frames and marks their receipt DELIVERED before the collector sees those frames; broker ownership is still NULL. The collector's ownership write then raises `Stale or terminal private receipt`, so its source offset cannot advance. The same ordering is possible with multiple delivery consumers when a work consumer completes egress before the source collector acknowledges ownership. Duplicate work can be repeatedly published on restart, while the original source record remains blocked.

**Required fix:** Make the two independent state machines compose. Permit one validated initial broker ownership tuple on a delivered receipt while preserving all immutable identity and receiver-acceptance fields, and keep an existing ownership tuple immutable. Alternatively introduce a signed terminal-receipt response which the collector explicitly recognizes as sufficient to advance without a broker ownership mutation. Merely swallowing ownership failures would remove the durable handoff guarantee for genuinely pending work.

**Focused regression:** Use the actual receipt trigger with a DELIVERED receipt whose broker fields are NULL; perform first acknowledgement and duplicate acknowledgement and assert receiver status/acknowledgement/accepted_at never change. Also exercise migrated acknowledged fanout through collector ownership, plus two-consumer execute-before-own ordering. Assert source offsets can advance and no receiver resend occurs. These executions were not run by this reviewer.

### RSEC-2 — P1 — Audit records and counts are not restricted to the physical source whose coverage was authorized

**Location:** `hrms-svc/integrations/organization-events/src/private/clickhouse.mjs:33-39`; authority boundary: `hrms-svc/integrations/organization-events/src/private/query.mjs:27-28`.

The service obtains database/schema from its trusted tenant binding and verifies archive coverage for that physical source. It then calls `readAudit(f)`, which restricts records only by scope, tenant, source kind and user filters. Neither the rows query nor the total query includes `source_database` or `source_schema`. Thus a record stored for the same tenant under a different physical database/schema is returned under the authorized source's coverage. Source identity is already part of record storage identity, so both physical sources can legitimately coexist in protected storage.

A wrong-source archive can therefore add audit rows and counts to the current source reader without the required coverage for that archive. Equal original UUIDs across sources can also produce duplicate logical audit IDs or conflicting row contents at the Rust merge boundary, yielding HISTORY_UNAVAILABLE instead of the authorized source history. Tenant isolation alone does not satisfy the configured source provenance contract.

**Required fix:** Pass the trusted binding's database/schema into `readAudit`; validate them and add parameterized predicates to both rows and count queries. If historical source lineage is intentionally supported, authorize an explicit lineage set with corresponding coverage rather than reading every physical source sharing a tenant UUID. The untrusted request must not select these identities.

**Focused regression:** Store accepted audit records under two database/schema identities sharing the same tenant and original record UUID. Authorize coverage only for source A and assert A's records and total exclude B; include conflicting B content and a different B record ID. Confirm client-selected identity fields cannot override the trusted binding. These executions were not run by this reviewer.

## Reviewed boundaries and limits

Targeted source inspection covered common Rust envelope validation/AAD/key selection/publication; audit history source pending overlay and signed response binding; webhook fanout/configuration versioning; source delivery proof, lease and HTTP execution; ownership proofs and acknowledgement; pending migration classification/ack correlation; maintenance company binding; Node crypto/history/store/query/coordinator/worker/runtime; and the source/control DDL generation, legacy fence, capture, cleanup and retirement guard functions. No additional P0/P1/P2 issue is asserted from those inspected slices.

The source authority bootstrap is already tracked as an open implementation gate in the execution summary and was not treated as an independently discovered finding here. The reviewed DDL creates a checked authority table but its installation alone does not establish a source binding. Provider delivery-history/analytics work in progress and renderer/HTML integration were excluded. No full feature acceptance, production activation, real remote mTLS exchange, receiver idempotency, composed Kafka/ClickHouse restore, or deployment claim follows from this report.
