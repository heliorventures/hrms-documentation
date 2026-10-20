# Delivery and scheduler retirement inventory

Date: 2026-10-19. Scope: static, targeted workspace source audit using the Rust skill. No product changes, builds, tests, live database access, deployment, or external Finance checkout inspection. Paths and line numbers identify the current source snapshot; runtime destinations and backlog counts are NOT DEMONSTRATED.

## Decision

Do not drop `outbox_event`, `webhook_delivery_log`, or `employee_finance_outbox`, or remove their workers, until replacement delivery, historical evidence, pending work, and scheduling have independent acceptance evidence. The existing organization Kafka pipeline is a projection/history pipeline and currently has no external delivery consumer. Its source exporter does not export these three tables.

## Verified legacy producers and consumers

All Rust paths below are relative to `hrms-svc/crates/`.

| Source | Events / behavior that must survive | Evidence |
| --- | --- | --- |
| `kabipay-leave/src/services/leave_service.rs` | `leave_request.approved`; same transaction as approval and annual balance movement. Payload v1: `leave_request_id`, `employee_id`, `leave_type_id`, `approver_user_id`, `from_date`, `to_date`, decimal-string `days_requested`, `is_half_day`, `status`. | 1092–1123 |
| `kabipay-expense/src/services/expense_service.rs` | `expense.approved`; transactional approval event. Payload v2: `expense_id`, `employee_id`, `expense_category_id`, `approver_user_id`, decimal-string `amount`, optional decimal-string `approved_amount`, `currency`, `expense_date`, `status`, `payment_status`, `title`. | 618–650 |
| `kabipay-employee/src/services/profile_change_service.rs` | `employee_profile_change_request.submitted`, `.cancelled`, `.approved`, `.rejected`. Transactional audit plus outbox insertion; payload v1: `request_id`, `employee_id`, `request_type`, `status`, `actor_user_id`. Notification writes are separate business effects in the same service and must remain. | helper 30–88; calls 544, 750, 837; notification helper 90 and review notification 855 |
| `kabipay-employee/src/services/profile_record_service.rs` | `employee_education.approved/rejected`, `employee_work_experience.approved/rejected`; payload v1: `record_id`, `employee_id`, `status`, `reviewer_user_id`; audit and employee notifications accompany review. | helper 32–78; callers 829, 901 |
| `kabipay-common/src/due_offboarding.rs` | `employee.offboarded`, aggregate `separation`; payload v1: `separation_id`, `employee_id`, `offboarded_at`. Conditional separation update gates employee deactivation, user deactivation, session revocation, and insertion in one transaction. | 26–129 |
| `kabipay-outbox-worker/src/main.rs` | Only production writer found for `webhook_delivery_log`; consumer of `outbox_event`; claims, stale recovery, webhook fanout, status transitions. | delivery log 193–225; claim 248–287; completion/failure 289–346; delivery 349–437; reclaim 440–473 |
| `kabipay-analytics/src/services/analytics_service.rs` | `outbox_event` list and manual requeue; webhook subscription CRUD; webhook delivery log list. Requeue allows FAILED or PROCESSING, resets claim but retains retry count. | 99–168, 203–231, 297–384 |
| `kabipay-analytics/src/resolvers/query.rs`, `mutation.rs`, `types.rs` | Tenant-scoped GraphQL inspection/requeue, subscription administration, DTO conversion. HR/directory authorization. Entitlement filtering on list/log reads must carry into replacements. | query 364–500; mutation 25–40; types 179, 292 |
| `hrms-ui/src/api/documents/clientOperations.graphql` | `AnalyticsWebhookDeliveryLogs` returns payload/response/attempt information. UI health and module probes also depend on this query, so dropping it breaks health tooling even without an outbox page. | 1228; `moduleHealth.graphql`:108; `moduleProbes.graphql`:318; `modules/admin/moduleHealthProbes.ts`:136 |

Generated tenant entities (`d0030_outbox_events`, `d0026_integrations`, `d0106_loan_exit_coordination`), analytics entity re-export/DTOs, and `kabipay-employee/examples/organization_fixture_source.rs`:183,189,290 also refer to these tables. Retiring runtime persistence requires updating fixture/schema generation without conflating those references with additional live producers.

### Existing webhook wire contract and delivery gaps

`kabipay-outbox-worker/src/main.rs`:178–188 builds JSON `{schema_version:1,outbox_id,tenant_id,aggregate_type,aggregate_id,event_type,payload,created_at}`. `outbox_id` is the stable receiver deduplication candidate; no receiver agreement or explicit idempotency header is demonstrated. Destinations are each active tenant `webhook_subscription.endpoint_url` whose `event_name` equals the event case-insensitively or `*`, then optional platform `OUTBOX_WEBHOOK_URL` (349–437). Actual configured endpoints and receiver implementations are unknown. No destination response schema is enforced: any HTTP 2xx counts as success.

The current worker is at least once, with additional avoidable duplicate paths:

- One event status covers all destinations. A later destination failure retries already successful destinations. The platform destination has no corresponding subscription delivery log.
- No matching subscription and no platform URL still produces PROCESSED. That state cannot prove external delivery.
- `mark_failure` returns a row directly to PENDING. The processing loop immediately claims again, so the comment promising backoff is not reflected in a durable next-attempt time (314–346, 487–505). Exhaustion defaults to five failures.
- PROCESSING recovery uses age/claimed_at, but completion is not fenced by a claim generation. A slow former worker can complete after another worker reclaims a row. Created-at ordering plus SKIP LOCKED does not serialize aggregates across workers, and equal timestamps have no deterministic ID tie-breaker.
- HTTP success followed by crash or log-write failure has an uncertain outcome. Log insert failures are warned and delivery can still mark PROCESSED (391–403). Logs cannot independently prove complete fanout.

Security findings from `analytics_service.rs`:297–336 and worker 104–166, 193–224, 349–437:

- Subscription validation checks an `http(s)://` prefix only. No host/IP egress policy, DNS rebinding check, private/link-local/metadata exclusion, or explicit redirect denial is present in the inspected delivery path. SSRF protection is NOT DEMONSTRATED.
- Subscription secrets are SHA-256 hashes, unavailable for outbound HMAC signing. The worker optionally signs all destinations with one platform environment key; malformed HEX silently produces no signing key. Headers are `X-KabiPay-Timestamp` and `X-KabiPay-Signature: v1=<hex HMAC-SHA256(key,"timestamp.body")>`.
- Response text is read without a bound, then a 4000-byte snippet is stored with full outbound payload. Byte slicing can panic on UTF-8 boundaries; errors have similar slicing. Receiver text and endpoint URLs can enter logs/errors. Shared delivery must use bounded reads, character-safe truncation, structured error codes, retention/access controls, and secret references rather than raw credentials.

### Offboarding integrity blocker

`hrms-database/changelog/migrations/0066_lifecycle_validation_integrity/lifecycle_validation_integrity.xml`:8–39 stores a non-null paired offboarding marker and a deferred RESTRICT FK from `separation.offboarding_event_id` to `outbox_event.id`. Existing and future marker identity must remain verifiable after retirement; neither deleting referenced rows nor dropping the FK without replacement preserves the contract.

`kabipay-common/src/entitlements.rs`:81–86 permits leave, expense, profile-change, education, and work-experience aggregates, but omits `separation`. The offboarding emitter therefore creates a known aggregate that the current worker never claims and analytics does not list. This is a verified producer/allowlist mismatch; current live backlog impact is NOT DEMONSTRATED. A replacement must explicitly specify entitlement policy for offboarding delivery rather than silently discard these pending records or expand unrelated permissions.

## Private Finance delivery is an active business protocol

This is Employee-to-Payroll coordination inside HRMS, separate from arbitrary tenant webhooks and from the external Finance dashboard checkout. No external Finance receiver source is present in the inspected workspace top-level projects; outside-workspace receiver changes require a separate scoped inspection.

`kabipay-employee/src/services/finance_operation.rs`:139–166 atomically records a terminal `employee_exit_operation` and inserts one `employee_finance_outbox` row keyed uniquely by `(tenant_id,operation_id,event_type)`. Event kinds are `EXIT_APPROVAL_COMMITTED` and `EXIT_APPROVAL_CANCELLED`; stored payload is `{operationId,separationId,reviewId,authorizationId,payloadHash}`. Commit comes from `exit_approval.rs`:205; cancellation comes through `finance_operation::cancel`, separation edit/cancel flows (`separation_service.rs`:99,107,149), and the cancellation resolver (`resolvers/mutation.rs`:1475). Terminal operation and private event immutability triggers and tenant/operation FK exist in migration 0106, lines 117–153. A generic DELETE backfill will fail its guard and must never disable that guard just to drain work.

`kabipay-employee/src/main.rs`:85 starts `finance_worker.rs`, which polls every 30 seconds, resolves bound/active tenants in pages of 100, and calls `finance_outbox::deliver_due`. This is independent of `kabipay-outbox-worker`.

`finance_outbox.rs`:11–70 claims at most five rows using a one-minute lease and incremented attempt fencing. COMMITTED maps to `ConfirmExitApproval` expecting `CONFIRMED`; CANCELLED maps to `CancelExitApproval` expecting `CANCELLED`. It sends only `{operationId}` with no client claims and marks delivered only for matching response operation ID and expected state. Failed/uncertain replies retain delivery and retry exponentially from 60 seconds up to 3600 seconds, without a terminal retry cap/DLQ. An unrecognized event aborts the current batch; schema constraints currently prevent the two-kind mismatch.

`kabipay-common/src/finance_transport.rs`:6–104 sends a signed envelope to fixed `KABIPAY_FINANCE_PAYROLL_URL` or `KABIPAY_FINANCE_EMPLOYEE_URL`, path `/internal/finance`, with no caller-selected destination, credentials/query/fragment/custom path, redirects, or implicit retries. It uses 3-second connect/10-second total timeout, 128 KiB request and 1 MiB response limits. HTTP is permitted, so deployment network confidentiality remains unproven.

`finance_contract.rs`:47–99,132–179,207–306 defines exact request `{version:1,caller,recipient,issued_at,request_id,tenant_id,action,client_claims,input}` plus `signature`. Response is `{version:1,caller,recipient,tenant_id,request_id,action,issued_at,result}` plus `signature`. HMAC uses separate request/response domain prefixes and a dedicated service secret of at least 32 bytes. Response verifies tenant, caller/recipient inversion, request ID, action, signature, and 60-second age/5-second future skew. Every retry has a new transport request ID; business idempotency is the persisted operation identity. Never enqueue an already signed request for delayed retry, as its timestamp expires; sign freshly in the source-bound adapter.

`kabipay-payroll/src/fnf/http.rs`:24–27,126–194 exposes the receiver. It rereads authoritative Employee `OperationStatus`, checks returned operation ID, and applies reconciliation. A cancelled operation without authorization returns `{operationId,state:"CANCELLED",cancelledWithoutAuthorization:true}`. `fnf/coordination.rs`:114–146 maps operation bindings, reconciles guarded loans, verifies confirmed authorization identity, and creates a draft FNF only after confirmation, in one transaction. `fnf/worker.rs`:20–55,70–126 independently reconciles pending exit guards against Employee; unknown/unavailable status keeps guards held. This recovery function must survive even if outbox delivery is centralized. Related loan reconciliation in the same worker is unrelated dirty-work scope and must remain intact.

## Scheduler work currently packaged inside the legacy outbox binary

`kabipay-outbox-worker/src/main.rs`:545–657 is a general tenant scheduler as well as a webhook dispatcher. Rehost these functions in a source-bound scheduler before removing the binary:

| Function | Existing call | Preservation requirement |
| --- | --- | --- |
| Due employee separation | 556 | Deactivate access and revoke sessions on tenant business date; retain transactional marker/idempotency. |
| Attendance expiry | 571 | Entitlement-gated bounded sweep with tenant clock. |
| Survey lifecycle | 580 | Open/close due surveys; preserve notifications and retry-safe transition behavior. |
| Birthday/work anniversary | 588 | Tenant local time/date, employee privacy preferences, recipient permissions, occurrence deduplication. `kabipay-notification/src/services/automated_events.rs`:353–399,436–498 persists notification/occurrence ledger. |
| Performance cycles | 612 | Due cycle and participant generation. |
| Performance stage deadlines | 626 | Advance/block stages with existing domain rules. |
| Expired company upload stages | 639 | Bound 25; preserve cleanup/recovery and staged file privacy. |
| Expired announcement video stages | 642 | Bound 25; preserve upload cleanup. |
| Private file cleanup tasks | 645 | Bound 25; execute source-local storage deletion/retry safely. |

Global worker shutdown, restart, fairness, and high-volume tenant backlog must not prevent these jobs. Currently the unbounded `process_tenant_outbox` loop runs after scheduler work and before the next tenant (476–505,648); separate scheduling removes that starvation coupling. Do not route raw notification content or storage credentials through an organization topic merely to rehost scheduling.

## Existing Kafka/export integration: reuse transport, extend contracts

`hrms-kafka/connectors/connector.template.json`:17,28–36 captures only `company_event_outbox` and `organization_capture_marker`, keyed by aggregate ID, into source-bound organization topics. It does not capture `outbox_event` or private Finance delivery rows.

`hrms-svc/integrations/organization-events/src/events.mjs`:4–86 accepts exact organization envelopes and eight event categories: `approval.changed`, `timesheet.changed`, `administration.changed`, `legacy_audit.recorded`, `attendance.changed`, `leave.changed`, `project_time.changed`, `directory.changed`. None of the legacy webhook names or private Finance event kinds is accepted. Payloads/envelopes cannot simply be forwarded into this parser.

`consumers.mjs`:2–52 declares only inbox/history/reporting roles. Identity, membership classification, version conflict detection, checkpointing, quarantine, and archive handling are useful patterns; none creates external delivery intents or dispatches HTTP. `worker.mjs`:37–70 commits Kafka offsets after processing, using an independent consumer group per role. Adding delivery inline to these consumers would couple external availability to projection/history coverage and replay could repeat business effects.

`source-export-cli.mjs`:1–26 is already fixed to local company credentials, checked database identity and active membership, bounded chunks, restrictive export files, Kafka idempotent producer/acks-all, and manifest hashes. Its only kinds are OUTBOX and LEGACY_AUDIT. Migration 0121 `organization_source_history.xml`:138–153,164–207 shows OUTBOX reads `company_event_outbox`; LEGACY_AUDIT reads `audit_log`. It does not preserve old pending delivery intent, destination receipts, webhook responses, or private Finance outbox rows. A new source-owned export contract is required for all three legacy tables.

## Proposed shared delivery architecture

Proposal, not implemented or accepted runtime evidence:

1. Persist a typed delivery intent in the originating business transaction. Use distinct schemas and restricted topics for public webhook delivery and private Finance commands. The common envelope carries stable event/command ID, source tenant, aggregate/operation identity, ordering version, payload schema/version, creation time, destination reference, and content hash. Keep receiver-specific payloads encrypted or source-local where possible. Organization membership/history replay must not itself authorize an external side effect.
2. A delivery consumer with its own group validates immutable source-topic/tenant bindings and durably creates one job per destination in a dedicated delivery database. Unique key `(source_tenant_id,event_id,destination_id,contract_version)` and content-hash conflict detection fence replay. Commit the Kafka offset only after this transaction. Preserve the original event ID through migration; transport offsets and newly generated retry IDs are not business dedupe keys.
3. Each job has immutable destination/config version and bounded payload reference, state, next-attempt time, attempts, lease owner/generation, ordering key/sequence, and separate attempt/receipt evidence. Enforce generation on every update; renew long deliveries; serialize only aggregates/destinations requiring order. Broker retention must exceed recovery needs; durable job state owns retry scheduling.
4. An egress adapter performs webhook fanout with per-destination retries, bounded jitter/backoff, status classification (including 429/Retry-After), caps, DLQ, redacted diagnostics, and explicit uncertain outcomes. Stable receiver idempotency keys/receipts are required for exactly-once business effects; Kafka idempotent publishing does not supply this guarantee. No-destination, skipped/disabled, permanent failure, and delivered are distinct outcomes. Manual replay is permissioned, scoped, audited, and cannot replay acknowledged destinations silently.
5. A source-bound Finance adapter receives only private operation references and a typed allowed action, reconstructs/signs a fresh request using local service credentials, invokes the existing private receiver, validates the signed expected-state receipt, and durably publishes a minimal acknowledgment. The shared delivery service never receives arbitrary tenant DB credentials, client JWTs, Finance service secrets, raw loan/FNF payloads, or caller-selected URLs. Preserve authoritative Employee readback, authorization identity, conflict holds, and source-owned FNF transaction. Authenticate source-adapter requests and receipts against fixed tenant/service identities and command IDs.
6. Move scheduler functions into a source-bound runner using existing domain services and clock/entitlement/privacy gates, independently deployable from Kafka delivery. Do not implement business state transitions centrally.

Alternatives: retain source-owned durable Finance delivery initially while centralizing only public webhooks; this preserves its existing authority boundary with smaller cutover risk. Or centralize scheduling and queue operations while executing both webhook and Finance egress locally; central workers receive sanitized receipts only. Fully central private Finance egress requires explicit credential custody/network authorization and is not justified by the current shared projection architecture.

## Required migration and retirement evidence

- Freeze/drain or transactionally fence old emitters before high-water export. Record every legacy ID, payload hash, status, retries/claims, timestamps, error metadata, offboarding reference, Finance operation binding, destination mapping, and acknowledgment. Export historical evidence separately from executable pending work. Never replay PROCESSED/DELIVERED records as fresh commands. Existing webhook successes may be incomplete fanout evidence; classify uncertainty for reconciliation.
- Record destination-set policy for old rows: current configuration at export, original configuration if recoverable, or explicit operator reconciliation. Legacy logs do not have a dedicated `outbox_id` column; derive only from the stored JSON envelope when present and verified. Preserve uncorrelatable logs as history rather than asserting a delivery receipt.
- Migration counts/hash/manifests must cover every source row and every pending destination job, including FAILED/PROCESSING/PENDING, offboarding events excluded by the current allowlist, and delivered/pending private Finance rows. Enforce typed tenant/event/operation uniqueness and retry generation. Preserve archived mapping from legacy IDs to new immutable evidence.
- Replace `separation.offboarding_event_id` integrity with a source-local immutable marker/evidence target through a forward migration. Keep historical IDs stable and paired timestamp constraints. Do not attach private Finance state to organization membership lifecycle or weaken immutable terminal operation guards.
- Replace GraphQL delivery inspection/requeue and health callers before removing old entities. Recheck exact tenant, entitlement, data scope, payload redaction, pagination, and replay permission boundaries.
- Stop old workers only after replacement scheduler ownership, new producer writes, Kafka ingestion checkpoints, per-destination jobs, receipts/reconciliation, backlog parity and archival retrieval have passed. A guarded retirement SQL script must fail closed if any one prerequisite is absent; no CASCADE/disable-trigger bypass. Production cutover is a separate operation.

## Acceptance checks required before implementation can be called complete

No checks below were executed in this audit.

1. Producer transaction rollback/commit, all 11 legacy public event names, both private Finance kinds, and an offboarding referential-integrity migration with existing references.
2. Duplicate export/chunk publication, consumer restart before/after durable job creation, hash/ID conflicts, wrong-tenant/topic/destination proofs, migration resumes, pending/history parity, and rejection of mutated manifest bindings.
3. Receiver success followed by timeout/crash, durable receipt write failure, two-worker claim expiry overlap, per-destination partial success, retry scheduling/cap/DLQ/manual replay, 429/5xx/4xx classification, absent destinations, and UTF-8/oversized response handling.
4. Preserve per-operation Finance semantics: signed receipt tenant/request/action mismatch, stale timestamp, unknown authorization, authoritative Employee unavailable/REGISTERED, COMMITTED/CANCELLED conflicts, cancellation without authorization, duplicate confirmation, and no premature loan guard release/FNF creation. Existing relevant suites are `kabipay-common/tests/finance_contract.rs` and `kabipay-employee/tests/exit_finance.rs`; extension and execution are separate approved work.
5. SSRF matrix: loopback/private/link-local/metadata IPv4/IPv6, DNS rebind, redirect, URL userinfo, credential leakage, request/response bounds, signing key rotation, malformed HEX fail-closed, and immutable endpoint config. Verify only allowed destinations receive private data and per-subscription keys.
6. Scheduler restart/concurrency, tenant clock boundaries, offboarding and access/session effects, survey open/close, birthday privacy and occurrence dedupe, performance cycle/deadline transitions, attendance expiry, and file/video cleanup retry semantics. Compare jobs before/after binary retirement.
7. Receiver staging acceptance with a real supported idempotency/receipt contract, broker/DB durability/recovery, archive restore/query, GraphQL/UI health compatibility, and fail-closed retirement SQL. Static source inspection proves none of these runtime outcomes.

## Decisions still requiring business/operations input

Which public receivers are currently configured and active; which accept a stable idempotency key; their accepted event schemas, responses, order guarantees and reconciliation APIs; public webhook retention/data minimization; whether HTTP is permitted; per-destination retry/expiry/DLQ ownership; policy for historically unconfigured/partially delivered events; private Finance broker/network/service-secret ownership; source adapter deployment boundary; archive retention/retrieval and scheduler deployment ownership. Resolve these before a destructive retirement or externally visible contract switch.
