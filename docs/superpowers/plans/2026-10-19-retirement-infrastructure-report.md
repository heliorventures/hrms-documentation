# Private-event infrastructure implementation report

Owner: retirement_infrastructure. Date: 2026-10-19. Local uncommitted implementation only. No live deployment, production migration, full Rust build, Dart/Flutter command or commit was performed by this agent. Existing dirty work was preserved.

## Forward ownership and retirement activation

- PostgreSQL identities 0124/0125 are registered only in the ops/tenant preparation masters. 0126/0127 are reachable only through the explicit `tenant-retirement.changelog.xml` / `ops-retirement.changelog.xml` entrypoints. Normal installation does not drop existing legacy data and is not blocked by missing retirement evidence.
- Existing applied changesets were not edited. 0121's lossy audit export is not accepted as full raw history. 0126 replaces the old export-next legacy branch with an explicit retired-path error while retaining its company export branch.
- ClickHouse migrations/grants 0005/0006 follow occupied 0001-0004 identities; the loader enforces unique identities/checksums.

## PostgreSQL preparation

`0124_private_event_control/private_event_control.xml` retains the single metadata publication table. It adds checked `control/operator_audit` routing, stored routed JSON and a strict versioned control wrapper containing the original ten control row fields. Global private operator events may have NULL original tenant/actor; normal control events still require both. Original control occurrence time is formatted as UTC ISO without losing microseconds. The wrapper never fabricates Debezium source/op fields.

`0125_private_event_source/private_event_source.xml` retains the exact existing company publication pair: `company_event_outbox` and `organization_capture_marker`. `event_stream` is checked `company/audit/delivery`, defaults to company and allows NULL organization only for private streams. Company membership and marker behavior are retained. Private inserts bind their authenticated envelope generation to a locked source authority; private rows cannot be changed into company rows or mutated. Ordinary cleanup and TRUNCATE cannot remove private records.

Compact business state includes:

- `private_survey_execution_state(tenant_id,survey_id,opened_at,last_transition_action,last_transition_at,last_transition_id)`. Opening existence and failure dedupe are backfilled using the original transition allowlist and exact `(created_at DESC,id DESC)` ordering. A temporary legacy audit trigger maintains this state transactionally until fencing/retirement.
- Immutable `private_domain_receipt` retains offboarding event UUID, tenant, event/aggregate binding, occurrence time and source hash. Existing separation IDs/timestamps remain. The deferred composite FK replaces the legacy FK. A temporary old-producer bridge creates receipts before a legacy offboarding event can be referenced.
- `private_delivery_receipt` retains immutable intent/destination/hash/version/generation, lease/fence and compact outcome state. Broker ownership proof is separate from actual delivery acknowledgement. Pending, processing, retryable and uncertain payloads remain in the source outbox even after broker ownership; terminal no-destination/disabled/permanent outcomes do not manufacture receiver acknowledgements. A `(tenant_id,source_kind,resource_id,created_at DESC)` index supports source status projection.
- Webhook subscription `signing_key_ref` remains NULL until explicit real-key reconciliation; `config_version` increments on configuration changes. Existing one-way hashes never become secrets.

## Source-owned migration and capture API

All production SQL remains in hrms-database. Helpers have PUBLIC execution revoked; source migration operators require explicit reviewed source-local grants. Shared private workers receive no source DSN.

| Helper | Contract |
|---|---|
| `private_fence_legacy(scope,generation)` | Locks legacy source tables and authority, then fences old writes/claims. |
| `private_legacy_export_start(scope,table,job,generation)` | Captures full raw row count, rolling source digest and actual catalog dependency digest under a fenced source. Restart rejects identity/hash drift. |
| `private_legacy_export_batch(scope,job,after_uuid,batch,byte_limit)` | Typed full-row JSONB UTF8 bytes, original UUID, original tenant, exact UTC six-digit occurrence time, byte hash/size and explicit historical/non-executable flags. UTC/date/float/bytea serialization is pinned. Finance uses actual `COALESCE(delivered_at,available_at)`, since it has no created_at. |
| `private_legacy_export_publish(scope,job,frames)` | Atomically publishes complete exact encrypted historical frames; validates original row hash/size/time, scope/generation, all indices and source table. Exact retries reuse event IDs/ciphertext; conflicting content fails. |
| `private_legacy_export_published_frames(scope,job,record)` | Reads source-owned canonical frames for restart. |
| `private_legacy_export_accept(scope,job,proof)` | Rechecks current source digest/count/catalog and independently supplied restore acceptance. Business/reader/pending flags are copied from source authority, not proof booleans. |
| `private_capture_tick(scope,generation)` | Waits for prior source outbox writers under a table lock; stores scope, generation, source LSN and through-position in compact source metadata. No publication table is added. |
| `private_capture_status(scope,marker,purpose)` | Returns exact retained frame count/digest, marker boundary and fixed slot flush status. |
| `private_capture_batch(scope,marker,purpose,after_position,batch)` | Bounded ordered `{position,event_id,envelope,raw_envelope}` rows. Continue until an empty result; a short batch is not EOF. |
| `private_capture_accept(scope,purpose,marker,proof)` | Requires exact source frame digest/count, marker identity, fixed slot flush plus connector LSN and commit LSN beyond the boundary, full partition0 coverage, zero quarantine and independently verified restore proof. |
| `private_cleanup_outbox(scope,purpose,evidence,batch)` | Bounded maximum200 deletion through accepted private coverage only, plus a compact cleanup receipt retained until accepted capture compaction. Delivery source payloads remain while nonterminal. Cleanup prelocks only bounded candidate receipts FOR SHARE before outbox rows, then rechecks status; the row guard also checks locked current status, preventing PERMANENT-to-PENDING replay from losing frames. This race was reproduced RED and fixed with an actual two-connection PostgreSQL test. Ops exposes the same typed operator-audit cleanup interface. |
| `private_capture_pulse_spec(scope,marker,purpose)` | Source-owned exact raw text, UTC6 occurrence time, safe numeric generation, prior event UUID, decimal-string published position and existing envelope (nullable until publication, and envelope nullable after accepted cleanup). Raw keys are exactly id,tenant_id,source_generation,purpose,through_position,source_lsn,created_at. The cutoff is a decimal string; LSN is uppercase PostgreSQL hex. |
| `private_capture_pulse_publish(scope,marker,purpose,frame)` | One standard encrypted capture_marker/private_capture_marker frame, record/resource UUID equal marker UUID. Checks exact seventeen fields, numeric types, source hash/size/time, canonical base64 bytes and generation; serializes the one marker/purpose receipt and binds the first immutable event/ciphertext hash. Identical retries return the original bigint position, including after source cleanup. A changed frame is rejected. The pulse must be after its marker cutoff. |
| `private_capture_prune(scope,purpose,freshEvidence,batch)` | At most200 total expired cleanup/evidence rows, settled pulse receipts and orphan operational markers per call, behind fresh current-generation accepted archive/restore. Retains live payloads, current proof/marker, revoked evidence and every remaining FK. A single per-scope/purpose private_capture_compaction row retains rolling SHA256/count/current-proof identity; this is bounded state rather than another append log. Markers/pulse receipts require at least one hour age. |

Raw legacy rolling digest: initial SHA256 of UTF8 `database + chr31 + schema + chr31 + table`; per original UUID order, SHA256 of previous digest bytes + UTF8 UUID + SHA256 of exact raw UTF8 row. Capture digest uses `database + chr31 + schema + chr31 + purpose`, then per source-position order previous digest + UTF8 decimal position + UTF8 event UUID + SHA256 of exact PostgreSQL envelope text. A source position or maximum Kafka offset alone is not completeness evidence.

Frames are bounded to 16MiB per raw source / 256KiB per frame / 64 frames by the common contract. A larger legacy row fails export without truncation and blocks retirement until a reviewed framing-limit change. Historical records cannot become executable pending work.

## Destructive gates

0126/0127 lock exact source tables and source authority and reject missing/mismatched/revoked/expired evidence, stale generation/version/database/schema, changed full-row digest/count, absent full restore, pending ownership gaps, reader/business backfill gaps, incomplete or stale private capture, or changed catalog inventory. Inventory hashes include relation privileges/owner, columns/defaults, dependent objects, FKs, trigger definitions/functions, policies, publications and indexes. Exact DROP operations have no CASCADE; an unexpected dependency rolls back the transaction.

`private_pending_migration` binds each pending/ambiguous legacy identity to its exact source row hash, export manifest/generation, reviewed classification, expected destination set and resolution acceptance. `private_pending_destination_owner` binds every expected destination to an immutable compact receipt/hash and durable broker ownership or receiver acknowledgement. Processed/delivered history cannot be transferred as a command. Every webhook attempt requires explicit reconciliation rather than inferring success from delivered_at. An unresolved mapping blocks deletion. Empty sources require explicit verified-empty acceptance; that exception cannot waive restore for a nonempty table.

Retirement authorization expiry stays short lived. Accepted raw archive identity/hash/restore facts remain durable and revocable for history reads after retirement; runtime readers must not reuse the destructive expiry as a history-access TTL. A generation change requires renewed scope-bound runtime acceptance.

## Kafka and ClickHouse

Kafka routes only checked discriminators to unchanged `organization.company.UUID`, `organization.audit.UUID`, `organization.delivery.UUID`; metadata control remains `organization.control.metadata`, private operator history uses `organization.operator_audit.metadata`. The company marker predicate bypasses EventRouter. `source_position` is a trusted CDC header. Metadata uses one JSON-string-preserving EventRouter payload; the strict decoder supports versioned routed JSON and the old native wire during transition. Expanding the inferred Connect JSON schema failed the NULL-organization parity rehearsal and was removed.

Three additional distinct principals/groups own audit, delivery and operator audit. No existing reporting/inbox/history/capture/control reader gets their private topics. Delivery work/retry1-3/DLQ/history names are fixed `organization.delivery.<stage>.UUID`; only the delivery worker reads/writes these, and it cannot write the CDC source topic. Existing certificate/TLS source/proxy requirements remain in production templates. The routing rehearsal uses explicitly isolated plaintext transport and does not prove production TLS/ACL rollout.

ClickHouse `private_history` has physically separate audit/delivery/operator record, chunk, checkpoint and coverage tables. Exact full source identity is in record keys; chunk keys include source kind, resource type and transport generation. Chunks store canonical base64 of authenticated decrypted bytes to preserve UTF8 splits. Database constraints check decoded frame hash/size, complete raw-row hash/size and framing bounds. FINAL reads and application conflict checks remain necessary; ReplacingMergeTree is not uniqueness enforcement. No reporting role gains private grants. Retention deletion is disabled.

`INITIAL_ARCHIVE` coverage is a durable revocable fact with NULL expiry. `LIVE_CAPTURE` requires current marker/LSN, partition0 completeness and a nonnull expiry within one hour. Initial archive acceptance does not authorize GC, and live capture does not substitute for historical backfill. See `hrms-clickhouse/PRIVATE-HISTORY-CONTRACT.md` for exact fields and role contracts.

## Verification ledger

- RED: new Kafka routing/role tests failed on aggregate-type routing and missing private principals; new SQL contracts failed before 0124-0127 existed.
- GREEN: `node hrms-kafka/test/admin.test.mjs` 11 tests; `node hrms-kafka/test/private-streams.test.mjs` 3 tests; `node hrms-database/tests/integration/organization/private-retirement.contract.test.cjs` 4 tests.
- GREEN: `node hrms-database/tests/integration/organization/private-retirement.integration.cjs --docker-fixture` 42 actual PostgreSQL16 scenarios, including exact drops and negative restore/generation/expiry/revocation/source/dependency/pending/business/reader/capture gates, legacy writer/TRUNCATE fencing, survey rollback/order, raw UTC stability, accepted private cleanup and capture digest parity.
- GREEN: strict routed control tests 3 and existing control tests6. Routed DTO/content-hash parity and wrong scope/topic/version/extra/private-field denial are covered; wrapped native input is rejected.
- GREEN: ClickHouse loader offline validation and9 migration tests. Final actual ClickHouse25.8 fixture passed10 record/hash/chunk/role-denial/source-identity/coverage scenarios with the complete final schema.
- Tools agent independently reported all five populated legacy table kinds /8 rows /9 encrypted frames through the actual source SQL publisher, real Node private processor with memory persistence, independent byte restore and source acceptance; bad generation/restore hash rejected. This is not a full real-ClickHouse broker proof.
- GREEN: `node hrms-kafka/test/private-cdc.integration.mjs` passed 8 actual PostgreSQL16/Kafka4/Debezium3.2 scenarios: two-company encrypted audit/delivery routing; company/marker bypass; strict NULL-organization metadata control compatibility; NULL-original-tenant encrypted operator routing; exact company publication pair; and three idle audit/delivery/operator capture-pulse proofs. The metadata NULL-field regression was reproduced and fixed before the final pass.

## Provisioning prerequisite

0124/0125 create source-authority tables but deliberately do not guess or seed tenant/metadata installation IDs. New and existing source provisioning must explicitly register the trusted source tenant or metadata scope in private_source_cutover before private producers are enabled. Missing registration fails closed. Runtime/provisioning wiring and exact role/default grants remain a coordinator review item; preparation DDL alone does not make an unregistered producer ready. All helpers are SECURITY INVOKER, so operator role table/lock privileges must also be reviewed, rather than granting EXECUTE alone.

## Fixture ownership and limitations

Current shared synthetic source fixture is recorded in `.codex-tmp/private-fixture-bindings.json`, loopback62831, owned container `private-retirement-sql-ad53a1a928554e23b894132e2720cdcf`, held terminal55266, Docker ID `f8128e99f69c3a90847efbfe74bd0fab77d6f945209b96fafc79c4ed8aaf2794`. Keep until root/tools release; audit has released its claim after its independent TEMP-table PG test. Synthetic credentials/keys are local fixture data only. The fixture is FENCED and archive accepted, with retirement flags still false; no shared source was retired. Its installed retirement function predates the final broker-owned pending waiver, and its cleanup/guard functions predate the receipt-lock replay fix, RSEC-1 first terminal ownership, encrypted pulses and operational compaction; replace those functions from canonical0125 before using this held fixture for retirement/cleanup acceptance. Fresh standalone fixtures use the final function and passed 42 scenarios.

An earlier native PostgreSQL17.6 fixture under `%TEMP%/hrms-private-retirement-c26b51d4632d498984d1280bab59b70b` stopped after logs reported missing `pg_logical/snapshots` and `postmaster.pid`. Cause is NOT DEMONSTRATED. It was replaced with owned PostgreSQL16 Docker fixtures. No conclusion about another agent/process is asserted.

Production deployment/catalog state, real private signing-key reconciliation, real Kafka TLS principal denial, receiver idempotency/acknowledgements and full broker-to-real-history-to-restore cutover acceptance remain separate release evidence. The database cannot independently prove external archive or receiver outcomes from booleans/hashes alone; source-local admission is restricted and requires actual verified proof import. Missing proof keeps retirement closed.

## Follow-up security review and idle capture liveness

RSEC-1 is corrected at the canonical SQL guard. DELIVERED remains immutable except for one first complete broker-ownership tuple, which must preserve every terminal/intent/destination/hash/version/lease/ack field and bind the locked current producer generation. A second ownership tuple or changed outcome is rejected. The actual PostgreSQL regression covers two delivered destinations, identical retry and illegal outcome/hash/lease/owner updates. The tools agent separately exercised the canonical guard through the actual signed Rust ownership service, including migrated ACK and execute-before-ownership destinations, different-offset duplicate proof, and returning the existing delivery ACK without source payload/URL access.

Idle capture uses the ordinary encrypted private stream, with no extra publication table or organization membership dependency. Its source_kind is capture_marker and its semantic history dataset/resource_type is private_capture_marker; the compact operational SQL table remains private_capture_source_marker. It is never executable delivery work or an employee audit action. A pulse follows the locked cutoff; the next capture includes that prior pulse. Retirement excludes only outbox rows matching a validated persisted pulse receipt/event/position/purpose/envelope SHA256 from the business-frame maximum, avoiding an endless cutoff loop. Unregistered rows with the same source_kind still require coverage. All pulses remain subject to normal archive/restore and private cleanup proof.

The shared 62831 fixture has not been changed for these follow-up functions. New standalone PostgreSQL/CDC fixtures load canonical SQL; the shared source requires coordinated helper replacement before exercising the follow-up APIs.

Final follow-up evidence: PostgreSQL 42/42 and source contract 4/4 passed on the final XML and envelope-SHA retirement binding. Both 0124/0125 also parsed as complete XML documents. Idle CDC 8/8 passed with real Kafka/Connect, canonical source helper/guard extraction, three purpose keys and no organization membership setup. For each purpose, the fixture publishes pulse1, takes the next locked cutoff, publishes only pulse2, then requires the actual fixed connector offset lsn AND lsn_commit and source slot confirmed_flush_lsn to cross that cutoff. It compares every bounded source frame to the actual Kafka envelope and decrypted bytes, independently computes the exact rolling source digest, archives pulse1 through the real PrivateHistoryProcessor with memory persistence, verifies its typed dataset/nonexecution, accepts typed source proof and deletes through that coverage. Pulse1 disappears; pulse2 remains. The additional real ClickHouse run below extends this initial memory-persistence rehearsal.

The successful idle fixture was session8213 with owned private-pg/private-kafka/private-connect-ae8a721c9ccc and network private-cdc-ae8a721c9ccc; its finally block removed all three containers and the network. Earlier follow-up attempts reproduced a stale statically imported Node decoder, an edit-script replacement escape error (corrected and XML/PG rechecked), and slow Connect startup. The final fixture uses a90-second readiness budget and last-error diagnostics; commit/LSN proof thresholds were never relaxed. Offset flush is1000ms only inside this isolated rehearsal. No production transport setting changed.

Generation cleanup follow-up: an actual PostgreSQL RED test demonstrated that empty new-generation coverage could delete an older-generation encrypted frame. Tenant and metadata cleanup predicates and row guards now require exact envelope generation equal to the accepted evidence generation. Final PostgreSQL 42/42 includes both tenant and metadata retention/direct-delete rejection. Old-generation payloads fail closed; clear or explicitly migrate their accepted ownership/archive state before advancing the producer generation. A generation bump alone never authorizes their deletion.

## Final real broker-to-ClickHouse acceptance

The optional real-store mode passed **11/11** actual PostgreSQL16/Kafka4/Debezium3.2/ClickHouse25.8 scenarios with the final source generation guards and production private worker classes. Native PowerShell command from the workspace root:

```powershell
$env:PRIVATE_CLICKHOUSE_TEST_BINDING_FILE='D:\work\heliorventures\.codex-tmp\private-ch-bindings.json'
node hrms-kafka/test/private-cdc.integration.mjs
```

The held ClickHouse binding was validated as coordinator-owned, synthetic and loopback. Fixed private_audit_worker/private_delivery_worker/private_operator_audit_worker users were used. Only the fresh generated scopes were inserted. For every purpose, all three actual Kafka frames were processed by the production PrivateHistoryProcessor and PrivateClickHouse; exact source bytes and encrypted/decrypted chunk restoration, persisted source position, raw-record hash, actual Kafka offset/checkpoint and duplicate processing after a newly constructed worker/store were verified. The actual verifyPrivateCapture read the exact source batches and durable ClickHouse frames/records, restored two covered raw records per purpose into independent files and wrote accepted proof artifacts. Source SQL accepted those proofs and cleanup removed the covered pulse while retaining its newer tail. All delivery test records were historical or nonexecutable markers; no receiver outcome was inferred.

Artifacts: `.codex-tmp/private-cdc-restore-25b3b528af7d/{audit,delivery,operator_audit}` contains six exact raw files plus three proof JSON files. Observed marker/connector boundaries:

| Purpose | Scope UUID | Through position | Marker LSN | Connector LSN and commit LSN |
|---|---|---:|---|---|
| audit | 62d33cc8-1375-47ea-9489-da0dce3662d6 | 4 | 0/2730260 | 0/2730D38 |
| delivery | 62d33cc8-1375-47ea-9489-da0dce3662d6 | 6 | 0/2732698 | 0/27331A0 |
| operator_audit | 2d00a6ac-e092-49bb-9ac8-dbb1aa9ad426 | 3 | 0/27362B8 | 0/2737240 |

Each purpose proof contains exactly two source frames and matching archive/restore SHA256. All three archived records/checkpoints per purpose were read back from ClickHouse, including the retained tail pulse. The coordinator also independently reproduced and corrected UInt64 JSON rounding above JavaScript's safe integer limit; the final end-to-end process loaded the decimal-string setting.

Successful real-store session13191 owned private-pg/private-kafka/private-connect-25b3b528af7d and network private-cdc-25b3b528af7d. They were removed by finally and a post-run Docker inventory showed only the held source container and coordinator-owned ClickHouse container. The shared62831 source was not modified. The held ClickHouse remains coordinator-owned for review/cleanup. An attempted fixture-only plugin-path optimization was rejected by Connect and removed; the final pass uses the image's supported default discovery with explicit PostgreSQL-plugin readiness. Production TLS/ACL deployment remains unproven by this isolated plaintext run.

The independently reviewed forward0125 legacy-export disabling block and removal of the duplicate0126 definition were included in the final PostgreSQL 42/42 rerun. The final-review agent separately passed eight actual PostgreSQL scenarios for new/pending/complete legacy-job denial, stored chunk preservation and canonical company OUTBOX behavior. No applied0121 changeset was edited.

## Post-retirement SQL catalog cleanup

Final PostgreSQL **42/42** and source contracts **4/4** passed after extending0126/0127. A RED catalog test first demonstrated private_fence_legacy remained callable after its source tables were removed. Both destructive entrypoints now exact-drop migration-only functions after the locked retirement assertion and before the table drops, with callers removed before callees and no CASCADE. Tenant removes10 helpers; metadata removes9.

Removed on both sources: private_assert_retirement(), private_legacy_export_accept(uuid,uuid,jsonb), private_legacy_export_publish(uuid,uuid,jsonb), private_legacy_export_published_frames(uuid,uuid,uuid), private_legacy_export_batch(uuid,uuid,uuid,integer,integer), private_legacy_export_start(uuid,text,uuid,bigint), private_dependency_digest(text), private_source_digest(text), private_fence_legacy(uuid,bigint). Tenant additionally removes private_assert_pending_migration(uuid,bigint). Names private_legacy_table_digest/private_pending_reconciled do not exist in these migrations. The obsolete trigger functions and old organization legacy start/mapper are also removed as previously specified.

Retained: private_legacy_export accepted manifests and pending destination/ownership provenance tables, compact survey/domain/delivery state and guards, source authority, private capture evidence/markers/pulse state/compaction, and capture tick/status/batch/accept/pulse/prune/cleanup APIs. They serve current private history, broker ownership, ongoing capture and guarded GC after legacy retirement. Canonical organization_history_export_next remains OUTBOX-only; historical stored chunks and application parsers remain. No retired raw-table helper is needed for history reads: accepted identities/hashes are read from durable manifests.

Actual post-retirement catalog tests verify all19 migration-only names absent, accepted manifests still readable, tenant private cleanup deletes the covered frame, and fresh capture/status/batch/pulse specification operate after tenant and operator retirement. The operator zero-row cleanup path also works. Proof tables and runtime private outboxes remain present.
