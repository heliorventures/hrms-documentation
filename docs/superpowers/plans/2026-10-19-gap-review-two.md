# Independent review two: event lifecycle and production boundaries

Date: 2026-10-19. Read-only source review with a small in-memory Node reproduction; no source edits, deployment, production mutation, full test suite or production acceptance operation was performed by this reviewer.

Review input: `2026-10-19-gap-review-input.md` and the current event ledger, followed by narrowly selected integration modules, infrastructure configuration and migrations 0120/0121. This pass does not repeat the first review's employee lock-order or payroll detail contract findings.

## Findings at review snapshot

### R2-C1 — High: queued capture marker becomes a permanent retry while its company is suspended or detached

Locations: `hrms-svc/integrations/organization-events/src/capture.mjs:39`, `capture.mjs:40`; `src/capture-worker.mjs:23`, `src/capture-worker.mjs:25`.

Scenario: a legitimate source marker is written while the membership is active. Before its raw Debezium record reaches the coordinator, an administrator suspends or detaches that company. Classification now returns `HISTORICAL`. `coordinateMarker` rejects every classification except `ACTIVE`, so the consumer never reaches its offset commit. Its crash handler exits, and the production restart policy consumes the same marker again. A detached company may never become active again. The coordinator instance cannot advance through that record; other bindings served by the instance can also lose fresh capture coverage.

Direct reproduction: call the existing `coordinateMarker` twice with a valid source/database/schema/topic-bound CDC marker, a successful Connect checkpoint confirmation, and a metadata client returning `HISTORICAL`. Both calls throw `CAPTURE_MEMBERSHIP_INACTIVE`; neither sends barriers. This used existing production functions and in-memory adapters, without a broker or database. Consumer replay follows directly from the offset commit being after the rejected call.

Required correction: handle a recognized historical marker as a terminal, safely acknowledged historical observation, without advertising active coverage or publishing current barriers. Keep invalid provenance, unavailable policy and unrecognized records fail closed with durable metadata handling. Exercise a marker queued before suspension/detachment and later current markers for another binding.

### R2-C2 — High: successful historical delivery permanently prevents healthy capture after resume

Locations: `hrms-svc/integrations/organization-events/src/consumers.mjs:31`, `src/consumers.mjs:44`; `src/store.mjs:42`; `hrms-database/changelog/migrations/0120_organization_capture_lifecycle/organization_capture_lifecycle.xml:11`, `:58`, `:59`.

Scenario: an event queued while active is delivered after suspension. Inbox intentionally avoids creating a current projection; history/reporting successfully retain the genuine event. All three roles nevertheless write `PARTIAL/HISTORICAL_MEMBERSHIP`. The checkpoint upsert preserves every existing `PARTIAL` or `QUARANTINED` state forever. Its primary key has no membership epoch, and no scoped recovery/reset path exists in these modules. After accepted resume, fresh bootstrap and all new role/partition barriers cannot change that checkpoint to `READY`. `organization_capture_healthy` requires `READY`, so reports, archive export and guarded retention continue to reject otherwise complete resumed coverage.

Direct reproduction: call the existing `processConsumerRecord` with a valid directory event, `HISTORICAL` classification, successful identity fence and inbox role. It returns `{historical:true}` and writes a `PARTIAL/HISTORICAL_MEMBERSHIP` checkpoint at the consumed offset. The permanent state follows from the actual checkpoint SQL and capture-health predicate; this reviewer did not execute that SQL in a database.

Required correction: distinguish successful historical processing from unresolved missing/conflicting data. Allow current coverage to recover after accepted resume while preserving genuine invalid-record and version-conflict quarantine. A role delivery checkpoint can acknowledge successfully handled history without granting active access, because current membership, current epoch, accepted bootstrap and every barrier are already separate health predicates. Existing historical-only partial checkpoints need a narrowly defined recovery behavior as well.

## Reviewed boundaries without an additional confirmed finding

- Inbox, history and reporting have separate group IDs, PostgreSQL role checkpoints and sink acknowledgement paths; inbox does not construct a ClickHouse client.
- Capture checks native Debezium source identity/LSN, persisted Connect `lsn` and `lsn_commit`, broker partition configuration and per-role/per-partition barriers. Capture freshness uses source marker time and current installed membership.
- Source export keeps fixed company credentials at the source, preserves immutable chunk manifests and original event IDs, and records publication only after broker acknowledgement. Genuine legacy export maps a closed metadata whitelist and source-row hash; private audit before/after bodies remain source local.
- Archive transport requires mTLS plus exact tenant/route/body-bound public-key service proof. Archives authenticate the immutable scope/range/event hashes using AES-GCM; writes are serialized by archive ID and protected against overwrite. Current central end-user authority remains a separate required check at the caller.
- Retention defaults dry-run, requires accepted persisted policy plus trusted operator enable configuration, and locks/verifies exact outbox candidates before deletion. No consumer DELETE privilege is introduced. History TTL deletion remains disabled. These statements are source observations, not production acceptance.

The relevant production reference discovered in this checkout is `hrms-svc/infrastructure/organization/compose.yaml`; no `compose.production.yml` was found by the bounded filename search. The reference requires private TLS materials, ACL provisioning, fixed database bindings and an external restricted Connect offsets proxy. Missing live acceptance evidence is not counted here as a newly reproduced code defect.

Root independently reported a real ClickHouse 25.8 operational-view query failure (`fact.1` unresolved across a view boundary) during this review and owns its correction and rerun. That diagnosis was not independently reproduced by this reviewer and is not included in the two findings above.

## Reverification status

R2-C1 and R2-C2 were sent to root for correction. This document records the original review snapshot; it must receive a dated correction/reverification addendum before these findings are described as closed.

## Reverification addendum - 2026-10-19

Independent review reread current `capture`, `capture-worker`, `consumers`, `store`, `worker`, the new exact-epoch classifier/operator recovery SQL, grants and lifecycle runbook. An in-memory harness exercised the actual current functions; no external service test or production operation was run by this reviewer.

**R2-C2: correction accepted.** All three current consumer roles now acknowledge successful historical handling as `READY` with no loss code. Inbox creates no current projection; history/reporting still require their own sink acknowledgement. The reviewer independently exercised all three roles and verified those outcomes. The checkpoint SQL preserves genuine invalid `PARTIAL` and `QUARANTINED` states, and a new real error replaces an obsolete historical-only detail instead of hiding it. Legacy historical partial state is never cleared automatically.

The administrator-only recovery function requires the exact offset and full PostgreSQL acknowledgement timestamp, an accepted current epoch with source bootstrap, a fresh latest marker, every role/partition barrier and its covering delivery checkpoint, an operator quarantine-review SHA256 and principal. It records reconciliation before changing the historical-only state. Genuine invalid partial or quarantined rows are rejected; real faults hidden by the old implementation require explicit operator review through the fenced offset. `PUBLIC` cannot execute recovery and the worker grants do not grant it. These SQL/grant conclusions are source verification. Root supplied separate fresh PostgreSQL recovery evidence and a 43-test Node pass; this reviewer did not rerun those suites.

**R2-C1: partly corrected; one reproduced dependency remains open.** Exact membership ID/version classification correctly distinguishes current, recognized older/suspended/detached and unrecognized/future epochs. With Connect confirmation available, historical raw markers now return terminal success on repeat without marker insertion or barrier publication. Independently exercised registered historical barriers also return historical success without inserting current proof. Unknown raw markers produce only code/hash quarantine metadata.

However, `coordinateMarker` still calls `confirmCapture` before querying the exact membership classifier. A genuine historical marker for a detached source whose connector has been retired or is unavailable therefore still fails before reaching historical handling. The independent harness supplied a valid historical marker, a metadata adapter configured to return `HISTORICAL`, and `confirmCapture: async () => false`; the result was `CONNECT_CAPTURE_NOT_CONFIRMED` with zero metadata queries. The same ordering delays terminal unknown-marker quarantine when Connect is unavailable. No current capture proof is needed for either terminal metadata-only outcome. Require Connect ordering confirmation for active registration/fanout after exact classification, retaining current-epoch revalidation around external I/O. Root was informed before this addendum.

Root also supplied real Kafka suspended-marker offset advancement and resumed-epoch/source-bootstrap healthy coverage observations, with a final fixture partition-order assertion rerun still pending at the time of this addendum. Those observations do not cover the retired-Connect residual above. This addendum makes no whole-feature completion or production acceptance claim.

## Final correction reverification - 2026-10-19

**R2-C1: correction accepted and closed. R2-C2 remains closed.** This status supersedes the earlier open residual above for the reviewed current source.

The current coordinator performs source-bound parsing and a short exact-policy classification transaction before Connect I/O (`capture.mjs:37`, `:45`, `:56`). Historical records terminate without current marker registration or barrier publication. Unrecognized membership records require durable metadata-only quarantine and also bypass Connect. Only an active marker proceeds to persisted Connect confirmation after releasing policy locks; a fresh transaction then rechecks the exact membership/epoch before current registration (`:58`, `:59`).

The reviewer independently executed an in-memory harness against the current `coordinateMarker`, with these assertions all passing:

- Historical and unknown markers both terminate on repeated delivery with a throwing retired-Connect adapter; Connect is called zero times, no current marker is inserted and no barrier is published. Unknown-record quarantine contains only code and SHA256.
- Active confirmation runs outside the policy transaction. An `ACTIVE` to `HISTORICAL` transition during that I/O is reclassified and produces no current insertion/barrier.
- Failed confirmation for an active marker denies current insertion/barrier.
- An active marker with valid confirmation receives two exact-policy reads, is registered and publishes every configured partition barrier.

Combined with the previous independent checkpoint/barrier/reconciliation inspection, neither R2 finding has a remaining confirmed defect in the reviewed current implementation. Root and the event workstream separately report eight focused capture tests, 45 Node tests, fresh PostgreSQL checkpoint recovery and timestamp fixtures, plus a completed earlier extended real Kafka/Connect fixture. The newest real-worker fixture adding unavailable Connect was still running when this addendum was written; those external test reports were not independently rerun by this reviewer. Whole-feature HTTP acceptance and production release operations remain outside this closure claim.
