# Legacy retirement tools and source ownership

## Implemented source boundaries

`hrms-svc/integrations/organization-events/src/private/legacy-{export,reconcile,cli}.mjs` implements the source operator export and protected restore. Its sole PostgreSQL connection comes from fixed source deployment configuration. Neither the private shared consumer nor an RPC accepts a source DSN. No organization membership is required. Global operator rows retain their nullable original tenant while their authenticated scope is the fixed metadata installation UUID.

The four tenant tables and metadata `operator_audit_log` use the forward source-owned `private_legacy_export_start/batch/publish/published_frames/accept` functions. Rows retain the exact PostgreSQL `to_jsonb(row)::text` UTF8 bytes. Numeric values are never parsed and reserialized for hashing, framing, persistence, restore or digest acceptance. Original IDs, database/schema/table and real microsecond timestamp hints are bound to the archive. All frames have `legacy_<table>` source kinds; none is executable delivery.

Exports use bounded UUID keyset batches and existing AES256-GCM framing, with a 16MiB source-row ceiling and 256KiB frames. An excessive row fails and leaves retirement blocked. Immutable fsynced ciphertext files and bounded batch indexes are installed without overwriting existing identities. Restarts reuse the exact event IDs/nonces/ciphertext, including recovery from the source's already published frames after local artifact loss. Incomplete indexes, conflicting source counts/hashes, changed generations and missing frames fail closed.

Protected restore separately retrieves ClickHouse records and encrypted chunks using the fixed source identity, authenticates every frame, compares exact original bytes, and writes independent fsynced `.raw` artifacts. Its rolling digest matches PostgreSQL: initial SHA256 of database, schema and table separated by byte31; then SHA256(previous digest || UUID text || SHA256(raw UTF8 bytes)) in UUID order. Source acceptance rechecks source generation, raw count/digest and dependency inventory under the source authority/table locks. Empty sources use the explicit verified-empty path.

Record lookup includes scope/database/schema/table/original UUID; chunk lookup includes scope/source kind/resource type/source generation/original UUID/frame index. Equal UUIDs in different legacy tables remain distinct. An immutable accepted record may retain its first transport generation when identical bytes are captured again in a later generation. Initial archive coverage is durable `INITIAL_ARCHIVE` with no expiry; the short lived source retirement acceptance and `LIVE_CAPTURE` cleanup evidence retain their separate expiry requirements.

`capture-cli.mjs` uses a separately committed source marker. The marker's table lock waits for earlier outbox writers, so its source LSN dominates the commits of all selected cutoff rows. Capture requires the fixed slot's confirmed flush LSN and the fixed connector's actual `lsn` and `lsn_commit` to pass that marker. It checks every retained source frame through the cutoff against protected authenticated chunks, their exact source positions and complete reconstructed records, writes independent raw restore artifacts, and compares the source's rolling frame digest/count before calling the typed source acceptance helper. A high checkpoint or maximum Kafka offset cannot establish this proof. Partition0 is the only supported partition; missing/changing partitions fail the typed gate.

Verification first publishes a source-owned encrypted capture pulse after the cutoff through the existing private outbox. Its source kind `capture_marker` is nonexecutable. This advances an idle detached connector without publishing the private marker table or inventing organization membership. Pulse metadata comes from typed source functions; ciphertext/event IDs survive retries and source JSONB key reordering. A compact source receipt prevents republishing a pulse after its outbox frame has been safely collected. Connector confirmation allows 90 seconds for the default 60-second offset flush; source slot status is refreshed after confirmation within that same readiness budget, with the original marker cutoff, generation and source digest held immutable. A lagging slot fails on timeout.

## Pending delivery and broker ownership

The source-owned maintenance binary adds operator modes before starting any business schedules:

```powershell
kabipay-tenant-maintenance.exe --migrate-delivery C:\protected\reviewed-plan.json
kabipay-tenant-maintenance.exe --migrate-delivery C:\protected\reviewed-plan.json --execute
kabipay-tenant-maintenance.exe --verify-delivery-ownership
```

The first command executes the full bounded transaction and rolls it back. The explicit execute command commits. Plans are at most64KiB/100 entries and contain reviewed source UUIDs/hashes, current generation, manifest identity, classification, operator/reason and exact destination UUID/version sets. They contain no payload, URL or secret. A `TRANSFERRED` entry with an uncertain previous outcome additionally requires `authorize_retry_uncertain:true`. The original raw row, source fence/generation, archive manifest, source-owned destination reconstruction, immutable receipt hash and expected destination versions are checked inside the source transaction.

Plan shape (synthetic identities; real values come from the reviewed source export):

```json
{"version":1,"tenant_id":"11111111-1111-4111-8111-111111111111","source_generation":1,"accepted_by":"reviewed-source-operator","entries":[{"legacy_table":"outbox_event","legacy_id":"22222222-2222-4222-8222-222222222222","manifest_id":"33333333-3333-4333-8333-333333333333","source_row_sha256":"0000000000000000000000000000000000000000000000000000000000000000","classification":"TRANSFERRED","reason":"Reviewed exact destination set and prior delivery evidence","authorize_retry_uncertain":false,"expected_destinations":[{"destination_id":"44444444-4444-4444-8444-444444444444","destination_version":1}]}]}
```

Keep each accepted entry immutable when resuming or splitting a backlog into bounded plans. A changed resolution hash fails instead of replacing an accepted decision. `HISTORY_ONLY` is restricted to already processed outbox/acknowledged Finance rows. A webhook `ACKNOWLEDGED` resolution additionally requires source correlation and exact PostgreSQL JSONB payload equality. `RECONCILED_NONEXECUTABLE` is an explicit operator decision with a reason, never an automatic fallback for unknown evidence.

`PROCESSED` outbox rows and Finance rows with an actual nonnull `delivered_at` remain history only. Finance has neither a status column nor a created_at column; its source timestamp hint uses its actual available/delivered time. Pending Finance carries the original terminal operation UUID and fixed Payroll destination. Its authoritative current Employee terminal state and original operation reference must match before a fresh private reference intent is created. The existing execution adapter continues to create fresh signed Employee-to-Payroll requests and verify their authoritative receipts.

Webhook transfer uses the source fanout helper and preserves original v1 event IDs/payload. An acknowledged destination is recognized only from the exact stored v1 envelope, source tenant/outbox/aggregate/type/payload/time, subscription UUID, `is_success=true` and HTTP2xx. Its receipt is marked delivered in the same transaction as the other destination intents. A default delivered_at cannot prove success. Unknown/ambiguous evidence remains unresolved until an explicit operator nonexecutable or retry decision; it cannot silently become a new command.

Compact pending mappings are not sufficient on their own. The new signed source `POST /internal/private-events/ownership` endpoint records broker ownership only after the collector's Kafka work publication is acknowledged. The source validates the scoped proof before resolving its tenant DB, then locks current authority and the immutable destination receipt. It stores the first owner/receipt/time and preserves them on duplicate work offsets. This acknowledgement does not assert receiver success. The final ownership operator mode calls `private_assert_pending_migration` before marking the source ownership switch complete.

The ownership request uses the source delivery proof key and domains `kabipay-private-ownership-request-v1`/`kabipay-private-ownership-response-v1`, each followed by NUL. Ordered request fields are version,tenant_id,intent_id,destination_id,source_generation,destination_version,intent_hash,broker_owner_id,topic,partition_id,kafka_offset,request_id,issued_at. The response repeats these fields followed by receipt_sha256,accepted_at,already_owned. Kafka offset remains a decimal string. The first receipt SHA256 covers the compact ordered request excluding only request_id/issued_at; duplicate valid work offsets return the original signed receipt with already_owned=true. Source expected owner is `KABIPAY_PRIVATE_DELIVERY_BROKER_OWNER_ID`; worker owner is `PRIVATE_DELIVERY_BROKER_OWNER_ID`. Both identify the same stable logical worker across rolling restarts.

## Operator configuration and sequence

Use independent restricted directories per table/manifest. Source configuration is fixed by the operator deployment: `PRIVATE_SOURCE_DATABASE_URL`, `PRIVATE_SOURCE_DATABASE`, `PRIVATE_SOURCE_SCHEMA`, `PRIVATE_SOURCE_SCOPE_ID`, `PRIVATE_SOURCE_GENERATION`, `PRIVATE_SOURCE_CA_FILE`, `KABIPAY_PRIVATE_EVENT_KEYS_FILE`, `PRIVATE_SOURCE_TABLE`, `PRIVATE_EXPORT_ID`, `PRIVATE_EXPORT_DIRECTORY`. PostgreSQL CA verification is required. `PRIVATE_ISOLATED_FIXTURE=true` permits plaintext only on a loopback fixture.

The source DSN rejects all driver TLS/credential-path overrides (`ssl*` and `uselibpqcompat` query parameters), so the supplied CA and `rejectUnauthorized:true` cannot be replaced by connection-string parsing.

```powershell
node src/private/legacy-cli.mjs fence
node src/private/legacy-cli.mjs export
node src/private/legacy-cli.mjs restore
node src/private/legacy-cli.mjs accept
node src/private/capture-cli.mjs tick
node src/private/capture-cli.mjs verify
node src/private/capture-cli.mjs accept
```

Fence is a source operator cutover, and must only run after the reviewed deployment/old worker fence decision. Export resumes until it reports complete. Restore/accept additionally require purpose-specific `PRIVATE_HISTORY_URL/USER/PASSWORD`, an independent `PRIVATE_RESTORE_DIRECTORY` and `PRIVATE_ACCEPTED_BY`. Capture requires `PRIVATE_CAPTURE_PURPOSE`, the marker ID returned by tick as `PRIVATE_CAPTURE_MARKER_ID`, independent `PRIVATE_CAPTURE_RESTORE_DIRECTORY`, `PRIVATE_CONNECT_URL`, `PRIVATE_CONNECTOR_NAME`, `PRIVATE_CONNECTOR_TOPIC_PREFIX` and the fixed connector's CA/client certificate/key files. The source SQL acceptance propagates actual source switch flags; it accepts no caller supplied switch booleans. The retirement migrations remain a separate reviewed operation.

After the reviewed reader/business switches and source ownership verification finish, rerun `legacy-cli.mjs accept` for each table to refresh the short lived retirement acceptance and its actual source gate snapshot. This does not expire the immutable initial archive coverage.

## Evidence recorded in this task

RED: `node test/private-legacy.test.mjs` failed with missing implementation module; `node test/private-capture-proof.test.mjs` likewise failed before the capture module existed. The sandbox blocked child spawning for `node --test` (`spawn EPERM`); invoking the focused Node test files directly runs Node's test API without child workers.

GREEN: `node test/private-legacy.test.mjs` passed14 tests: original numeric/Unicode/unknown bytes and microseconds; exact restart IDs; all5 table raw multi-frame roundtrips through the real private processor; nullable global ops tenant; oversized/raced/incomplete/conflicting source rejection; source-published frame recovery; history-only versus unresolved classification; shared delivery-store UUID collisions across all3 tables and later-generation identical-byte restoration preserving first record lineage; explicit verified-empty proof; source DSN TLS override rejection. The TLS case first failed against the missing guard and then passed after the guard was added. `node test/private-capture-proof.test.mjs` passed6 tests: connector/complete-record requirements; rejection of missing chunks/stale generation despite a high checkpoint; mandatory independent restore and exact source frame count; encrypted idle pulse restart and collected-pulse protection; pulse checkpoint/slot-status timing; immutable marker and bounded slot timeout rejection. The timing and marker-mutation cases failed before the readiness correction and passed afterward. The pulse case first failed against the missing export before implementation. These use in-memory protected-store substitutes and do not establish deployed ClickHouse/Kafka behavior.

GREEN: `node test/private-legacy-pg-acceptance.mjs` exercised the actual forward functions on the held isolated PostgreSQL16 logical fixture on19October2026. All5 populated tables exported/restored/accepted: audit4, outbox1, webhook1, Finance1, ops1 =8 raw rows. Actual atomic source outbox envelopes were consumed by the real private processor;9 frames were replayed with identical IDs (18 accepted publication observations). Source and independently restored full-byte digests matched. Wrong source generation and altered restore hash were rejected. The protected store in this rehearsal was an in-memory substitute, explicitly reported by the script.

GREEN: `node test/private-capture-pg-acceptance.mjs` called the actual canonical source pulse functions in its own temporary schema on the same isolated PostgreSQL16 fixture. Real AES frames roundtripped the exact source-generated metadata; source JSONB ordering, restart identity, conflicting frame/generation rejection and collected-pulse nonpublication passed. Removal was simulated only in this owned helper fixture; the separate database suite proves evidence-controlled cleanup. This test does not assert connector or Kafka/ClickHouse coverage.

GREEN: `cargo check -p kabipay-tenant-maintenance -p kabipay-employee --tests --offline`; focused `cargo test -p kabipay-employee -p kabipay-tenant-maintenance --lib --bin kabipay-tenant-maintenance --test due_offboarding_postgres --no-run --offline`; then native test executables. Eight owned Rust tests passed: ownership2 pure/frozen cross-language tests plus1 actual PostgreSQL service test; migration3 pure tests plus1 actual PostgreSQL migration test; and1 moved scheduler PostgreSQL integration test. Explicit fixture tests used `PRIVATE_LEGACY_TEST_DATABASE_URL` and `--ignored --test-threads=1`; they were actually run and passed, rather than counted as ignored successes.

The ownership PostgreSQL service test installs the canonical forward receipt trigger. It verifies two already delivered destinations (migrated acknowledgement and execute-before-ownership), the real source delivery service returning the existing acknowledgement before/after broker ownership without an available source payload or URL, first signed ownership acceptance, duplicate work at a different offset retaining the first proof, unchanged terminal intent/outcome/lease/acknowledgement fields, and rejected mutations/wrong identity/current generation. The migration PostgreSQL test checks dry-run rollback, unresolved uncertainty rejection, exact two-destination fanout and retained original acknowledgement, Finance operation reference/state, deterministic restart, conflicting resolution, incomplete/complete durable destination ownership and generation rollover. It calls the canonical `private_assert_pending_migration` predicate in an owned fixture schema. The scheduler fixture moved from the retired worker to `kabipay-tenant-maintenance/tests`; it proves employee/user/session behavior, compact original event/time pairing and decrypted private intent content.

Full Kafka→ClickHouse populated archive restoration and idle connector pulse acceptance remain the parent's coordinated transport rehearsal; this report does not replace that evidence with mocks. No live source migration, deployment, destructive retirement, credential disclosure or automatic commit was performed.



## Final acceptance-fixture routing conformance

Updated only test fixtures after the canonical private-stream router changed. Company fixtures now resolve the checked `routedByValue` placeholder to `company` rather than subscribing to the literal template. Both company fixtures execute the exact current0125 stream columns and scope constraints. The control CDC fixture uses EventRouter with checked `event_stream` and canonical0124 `routed_envelope` construction, updates its source-prefix predicate, and retains a per-run synthetic topic suffix so exact broker offset assertions remain isolated. Its replay/conflict case now changes the routed event payload and preserves JSON-string wire wrapping. The historical0113/0114 sequence, NULL-organization identity, sink recovery, replay, quarantine and reader-policy assertions remain in place. Production connector templates were not changed.

RED: `node test/acceptance-routing.test.mjs` failed3 cases before the helpers/fixture corrections. GREEN: the same3 cases now pass, `node test/private-streams.test.mjs` in hrms-kafka passes3, and native Node syntax checks pass for the helper and all3 changed acceptance executables. The initial sandbox suite run hit `spawn EPERM` in `owned-processes.test.mjs` and child-launch assertions in `source-export-retirement.test.mjs`. The official `npm.cmd test` was then run with approved sandbox escalation:118 passed,0 failed,0 skipped.

GREEN: `node test/acceptance-routing-pg-acceptance.mjs` with explicit synthetic opt-in and the held loopback PostgreSQL fixture DSN created its own `routing_fixture_<UUID>` database, applied the exact forward routing DDL, and executed the actual Rust store insert SQL. All3 company stream values and invalid stream/scope constraints were checked; the control trigger emitted a source-bound envelope with no transport-column leakage; native historical, routed-object and EventRouter JSON-string inputs produced identical consumer DTO hashes; a changed payload produced a conflicting hash. The script dropped only its own database. The held source schemas/data were not modified. This proves SQL/consumer conformance, not broker transport.

The six historical Kafka/ClickHouse acceptance scenarios were subsequently rerun on a new isolated stack. All six passed; the completed transport proof and cleanup record follow.

## Completed historical transport regression

Project `private-retirement-regression-14197c3e5766403cbcea3b5a0ada9d37` was freshly created from the synthetic acceptance Compose file with the `cdc` profile, cached images only, and a local CPU/memory override. All four container IDs and Compose project labels were verified before use. No earlier project or storage was reused.

| Scenario | Result | Actual checks |
|---|---|---|
| `isolated-acceptance` | PASS | Six broker records, three logical history events, corrections/deletion, metadata-only quarantine and independent checkpoints |
| `isolated-cdc` | PASS | Two real Debezium events, snapshot plus committed correction, rolled-back outbox absence, restricted CDC business reads denied |
| `control-cdc-acceptance` | PASS | Four real CDC events; NULL-org identity; sequence/configuration revisions; failed sink holds offset3; recovery/replay/conflict quarantine through offset7; restricted workers/readers |
| `historical-retention-acceptance` | PASS | Suspended/detached history retained, current projection/fence empty, unknown/pending memberships durably quarantined, source receipts preserved |
| `control-cleanup-acceptance` | PASS | Exact source hash and encrypted restore, stopped legacy offsets, default dry-run, missing-history rejection, accepted scoped deletion and atomic cleanup receipt |
| `gap-lifecycle-acceptance` | PASS | Separate source/metadata DBs, three independent groups and six barriers, real CDC plus persisted Connect offsets, missing-partition rejection, suspension/resume/detach, historical manifest and encrypted archive restore, gated cleanup preserving source receipts and historical audit |

The first actual `isolated-cdc` attempt exposed another synthetic DDL omission: EventRouter requires `source_position` for its source-position header, but that standalone fixture had never installed0121. Connect reported `source_position is not a valid field name`, and the scenario timed out. A source-contract regression reproduced the omission, the synthetic table gained canonical `source_position bigserial NOT NULL`, and the regression plus actual CDC rerun passed. The other historical fixture assertions remained intact. An earlier Windows preload invocation failed before entering the fixture because its absolute path needed a `file:///` URL; both initial logs are retained. No product configuration was changed for either correction.

Final `npm.cmd test`: **118 passed,0 failed,0 skipped** after the actual-run correction. The earlier three Kafka routing contract tests and syntax checks also passed.

Evidence is retained in [the owned regression directory](../../../deploy/acceptance/evidence/private-retirement-regression-14197c3e5766403cbcea3b5a0ada9d37/summary.json): six completed scenario logs, final unit log,71 exact raw Kafka records across18 topics, boundaries and15 consumer-group offset snapshots,11 ClickHouse table snapshots, encrypted archive/source-export files, and four container logs. [The SHA256 index](../../../deploy/acceptance/evidence/private-retirement-regression-14197c3e5766403cbcea3b5a0ada9d37/sha256-index.json) covers47 evidence files (1,327,539 bytes at capture). These fixtures and artifacts contain only synthetic data.

Cleanup revalidated the recorded IDs/labels and removed exactly the four owned containers and their one exact labelled network. [The cleanup receipt](../../../deploy/acceptance/evidence/private-retirement-regression-14197c3e5766403cbcea3b5a0ada9d37/cleanup.json) records zero remaining owned containers/networks. No volumes, unrelated containers, networks or data were removed; no `down -v`, orphan removal, deployment, production migration or commit occurred.
