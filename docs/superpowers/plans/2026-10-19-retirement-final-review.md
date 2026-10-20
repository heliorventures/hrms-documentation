# Independent final retirement security and design review

19 October 2026. Static scoped review of local uncommitted source. The dedicated execution summary was read before relevant source; no full execution logs or repository dump were used. The initial pass changed only this report and ran no builds/tests. A coordinator-authorized follow-up below found and corrected an obsolete export producer and ran focused local Node/PostgreSQL checks. No production service, commit or deployment was involved.

## Assessment

The initial inspected slices had no new confirmed P0/P1/P2 defect, and the two earlier P1 findings were corrected. A subsequent targeted cleanup audit found RSEC-3, an obsolete export producer still callable before destructive retirement; it is now corrected with focused execution below. This does not establish composed runtime acceptance or authorize destructive retirement.

The original deployment environment P2 is corrected in the inspected source: Finance origins use HTTPS, the release mode is organization-only, and the private process/key/env contracts are documented. A small follow-up wrong grant filename reference was sent to the coordinator; its status is recorded below.

## Earlier findings re-reviewed

### RSEC-1 — corrected in source

`hrms-database/changelog/migrations/0125_private_event_source/private_event_source.xml:250` now permits exactly the initial complete broker ownership tuple on an already DELIVERED receipt. The exception excludes every receiver acknowledgement, accepted time, status, identity and lease field; it requires the receipt's current source generation under a source authority lock. An existing broker tuple remains immutable. `hrms-svc/crates/kabipay-employee/src/services/private_ownership.rs:149` locks the receipt and returns its existing same-owner proof on duplicate acknowledgement instead of rewriting terminal fields. This resolves the execute-before-own and migrated-acknowledged-receipt failure described by RSEC-1 without discarding durable handoff evidence.

This is fresh static inspection. The coordinator reports actual PostgreSQL regression execution, including terminal ownership, but this reviewer did not rerun it or observe collector offset advancement through a composed worker chain.

### RSEC-2 — corrected in source

`hrms-svc/integrations/organization-events/src/private/query.mjs:27` passes database/schema from its fixed server binding to the store. `hrms-svc/integrations/organization-events/src/private/clickhouse.mjs:33` validates those identities and includes parameterized source_database/source_schema restrictions in the common predicate used by both records and count queries. The signed caller filter cannot select or override these identities. The delivery history provider independently applies the same trusted physical source restrictions to coverage, candidate, record, webhook intent and metadata queries at `src/private/delivery_history.mjs:12` and `:18`.

This is fresh static inspection. The parent/provider reports actual ClickHouse source-scope execution; that test is not an execution by this reviewer.

## Newly inspected boundaries

- `hrms-svc/crates/kabipay-common/src/private_events/delivery_history_client.rs:77`: original raw strings are hash-checked before Rust decoding, retaining large integer bytes; tenant, record and resource identity are validated. The pending overlay uses an explicit repeatable-read source snapshot, authenticated complete frames, current generation and bounded aggregate read budgets. Archive identity selection remains tied to accepted, unrevoked source manifests and current source authority. Shared mTLS/proof helpers preserve fixed paths, distinct request/response domains, request-body hashes and no redirects/proxies.
- `hrms-svc/integrations/organization-events/src/private/delivery_history.mjs:42`: the server selects only a configured tenant proof key, validates exact signed request/filter/coverage shapes, fences replay and current transport generation, and requires all three original delivery archive identities. Original event candidates are grouped before limits; data pages remain bound to their candidates. Webhook attempts require a corresponding webhook intent, excluding Finance attempts.
- `hrms-svc/crates/kabipay-analytics/src/services/analytics_service.rs:217` and `:334`: event merges reject immutable identity/content conflicts; compact receipts supply current destination outcomes. Replay keeps directory/module authorization in the resolver, locks source authority and receipts, rejects active/uncertain cases transactionally, and resolves failed destinations only to authenticated original intents. `delivery_history_client.rs:481` preserves intent hash, destination version, resource and absolute lease; source restoration, actor audit, fresh bounded broker command and receipt reset remain in the caller's transaction. No arbitrary destination, payload replacement or credential is accepted from the UI/broker.
- `hrms-database/provisioning/private-events/runtime-bootstrap.sql:20`: source initialization requires a dedicated non-owning unprivileged runtime role, checks effective outside-source and protected column/function privileges, retains existing source business grants, and creates only PREPARED authority with false cutover flags. Company registration is checked through a separate operator metadata connection. Empty/existing classification does not manufacture archive or retirement acceptance. Authority UPDATE(updated_at) supplies PostgreSQL row-lock permission without granting generation/state/evidence mutation.
- `hrms-documentation/scripts/deploy/render.mjs:143`: company/purpose private workers have separate secret directories and do not join source/metadata database networks; the history readers have separate secret directories and fixed-purpose processes. Source delivery uses a private fixed-path mTLS proxy on port8450; public routes reject internal paths. Source-only maintenance replaces the retired global worker. `scripts/deploy/release.sh:14` refuses a running legacy global worker without stopping it automatically.
- `hrms-database/changelog/migrations/0125_private_event_source/private_event_source.xml:590`: source authority locks serialize retirement against current producers; exact legacy table locks bind digest/dependency checks to a cutoff. Retirement requires accepted current archive/restore/dependency evidence, cutover/business/reader/ownership flags and complete current private capture evidence. The 0126/0127 entrypoints drop exact objects transactionally without CASCADE and retain compact source/business state.

The changes use shared proof, TLS and encryption helpers instead of introducing another transport security implementation. Fixed-purpose Node reader processes and source-owned replay/egress preserve separate responsibilities. No DRY/SOLID concern in these slices rises to an actionable P0/P1/P2 finding.

## Original P2 documentation correction — closed in source

`hrms-documentation/deploy/hrms/environment.md:32` prescribed HTTP Finance origins, while the final release preflight requires HTTPS; `:56` described a legacy mode rejected by the renderer. The document also omitted the newly required private worker/history/key configuration. This was sent to the coordinator immediately; the coordinator confirmed that the deployment owner is updating this exact contract and its checks. A later source inspection confirms the HTTPS origins, organization-only release boundary and private worker/history/key configuration now agree with the renderer. The substantive original P2 is closed in source; see the final addendum for the independent HTTPS fixture limits and a remaining grant filename reference.

## Evidence and limits

**Initial static pass performed by this reviewer:** bounded document review, targeted native source searches and static inspection of the named functions/configuration. Follow-up implementation and focused execution are recorded separately below; no Cargo build, browser or production execution was performed.

**Reported by owners/coordinator, not rerun here:** latest PostgreSQL39 retirement scenarios; bootstrap49 PostgreSQL checks; common19 and analytics4 fresh native tests; actual protected ClickHouse provider/source identity acceptance. The execution summary contains older checkpoints, so its older totals must not replace the later owner results. These counts describe separate boundaries and are not one composed acceptance suite.

**Declined to judge / explicit remaining gates:** production TLS/ACL and actual installed role grants require deployment-specific inspection; complete source-to-Kafka-to-source-egress-to-ClickHouse restore/replay, restart/ack loss, authentic capture completeness, authoritative Finance receiver effects and receiver idempotency require composed runtime evidence; browser DTO/permission behavior requires GraphQL/browser execution. These are established acceptance gates, not newly discovered source defects. Static review and isolated successful suites do not demonstrate them. Destructive acceptance must remain closed wherever their required evidence is missing.

## Follow-up RSEC-3 — P1 — obsolete lossy audit projection producer remained callable before retirement

**Found:** `hrms-svc/integrations/organization-events/src/source-export-cli.mjs:5` accepted LEGACY_AUDIT and selected `organization_legacy_export_start`. Historical migration0121's start/next functions read audit rows and create sanitized lossy company-history projections. Preparation0125 fenced legacy table writes only, so those reads and new export/chunk creation remained possible in PREPARED/FENCED. Disabling the path only in destructive0126 was too late. This is an obsolete producer/privacy-boundary violation; no full raw payload leak is asserted, since the historical mapper sanitized its projection.

**Correction:** new/unapplied forward0125 now makes both `organization_legacy_export_start` and the legacy projection mapper fail closed, and installs the single canonical OUTBOX-only `organization_history_export_next` definition. It rejects legacy jobs before the COMPLETE shortcut and filters company rows by event_stream. The duplicate next-function definition was removed from new0126, which retains its exact helper drops and destructive gates. Applied historical0121 was not changed. The CLI accepts only OUTBOX and calls its fixed canonical start function. Stored manifests/chunks and historical JS parsers are preserved. The older broad gap-lifecycle fixture launcher now uses canonical OUTBOX; its pre0125 historical archive fixture remains explicit. The obsolete expense service comment referring to old outbox status was corrected.

**RED evidence:** focused actual PostgreSQL fixture reported a missing expected rejection for new legacy export creation; the CLI regression demonstrated LEGACY_AUDIT passed validation and requested a database credential. Initial sandbox process creation errors were environmental and were not counted as the behavioral RED. A five-second child startup timeout was increased before the actual CLI RED was observed.

**GREEN performed by this reviewer:**

- `node --test test/source-export-retirement.test.mjs test/backfill.test.mjs` in the organization-events project: 4 passed. This executes the actual CLI without a source credential, proves legacy rejection before credential/network setup, preserves canonical validation, and parses an existing legacy manifest.
- `node tests/integration/organization/legacy-export-retirement.integration.cjs --docker-fixture` in hrms-database: 8 actual PostgreSQL16 checks passed. The fixture installs exact historical0121 functions to create stored legacy data, then exact canonical0125 replacement functions. It proves denial for new/pending/complete legacy jobs and the mapper, unchanged stored manifest bytes/hash, canonical company-only OUTBOX export/idempotence and denial under fenced source state. It owns a fresh loopback-only container, verifies its exact name and removes it in finally. It does not use the held shared source fixture or source credentials.
- Native Node syntax checks for source-export-cli and the adapted gap-lifecycle fixture succeeded. Scoped git diff checks succeeded.

The full gap-lifecycle Kafka acceptance fixture was adapted but not executed in this follow-up; no composed Kafka publication claim is made. The new PostgreSQL regression applies the exact affected function definitions, not a full migrated tenant deployment. The infrastructure owner was asked to rerun the final whole retirement fixture after these canonical source changes. This follow-up includes implementation by the reviewer and should receive coordinator/independent inspection before integration.

A targeted Rust module/import/direct SQL search found only the approved source-owned legacy migration helper, embedded synthetic tests, private-history kind labels and preserved API names. No additional active obsolete entity import/runtime poller was identified in that search.

## Final bounded independent addendum — precision, actual protected restore and HTTPS fixtures

This addendum is static independent inspection of the coordinator/deployment owner's final changes. No product code was changed and no test was rerun for this addendum. No new executable P0/P1/P2 finding is asserted from these slices.

### Int64/UInt64 precision correction

`hrms-svc/integrations/organization-events/src/private/clickhouse.mjs:14` pins `output_format_json_quote_64bit_integers=1` on the fixed process URL. `src/clickhouse-http.mjs` clones that URL before adding query/parameter fields, retaining the output setting on every request. JSONEachRow parsing therefore receives decimal strings for 64-bit positions instead of rounded JavaScript numbers. Existing checkpoint comparisons use BigInt and source frame position comparisons convert from the preserved strings; bounded UInt16/UInt32 frame counts/sizes remain normal numbers.

`test/private-history-ch.integration.mjs:20` writes checkpoint offset 9007199254740993 as a string and checks the actual stored offset and UInt64 query result return exactly that decimal string. The coordinator reports actual ClickHouse RED rounded to 9007199254740992 before the setting and GREEN afterward, plus 34 focused unit tests. This reviewer inspected those assertions and transport code but did not rerun them.

### PostgreSQL-to-protected-ClickHouse restore adapter

`test/private-legacy-pg-acceptance.mjs` explicitly binds a loopback synthetic PostgreSQL fixture and, optionally, the named loopback ClickHouse fixture. For an existing accepted source manifest, the publisher hook skips the SQL publish mutation. It independently fetches each original stored SQL envelope, requires deep equality with the authenticated exporter frame, and feeds that actual envelope/source position into the real PrivateHistoryProcessor and optional real PrivateClickHouse store. The exporter retrieves/decrypts existing published frames; restoreExport subsequently reads stored records/chunks and recomputes original byte and dataset digests. Existing acceptance is not rewritten: the new restore digest must equal both original source and original accepted restore digests. Wrong generation/hash acceptance calls remain negative tests whose SQL validation runs before any acceptance UPDATE.

The coordinator reports all five legacy table kinds, eight raw rows/nine frames and eighteen direct replays GREEN against real PostgreSQL plus real protected ClickHouse. The source publisher hook bypasses Kafka, so it proves the protected persistence/independent restore boundary without demonstrating Kafka publication, routing, offset ownership, crash handling or a composed worker chain. Existing accepted rows remain untouched in the inspected branch. In-memory fallback runs must retain their distinct evidence label.

### Updated deployment documentation and actual HTTPS fixture

`hrms-documentation/deploy/hrms/environment.md` now names the renderer's HTTPS Finance origins on source ports8451/8452, the organization-only release boundary, source delivery mTLS port8450, per-process key/env/mount boundaries, current proof generations, private history URLs and separate private Kafka identities/groups. These correct the original tracked P2.

`hrms-svc/integrations/organization-events/test/private-https.integration.mjs` creates its own short-lived fixture PKI using a cached Docker image with no network, then uses production Node SourceDeliveryClient, DeliveryCoordinator, ownership proof helpers and the production audit history handler over real loopback HTTPS/mTLS. Its five nested scenarios plus enclosing test cover absent/foreign client certs, foreign CA, wrong hostname, signed reference/status failures, fixed paths, acknowledgement loss with same-lease probing, uncertain disposition, exact large ownership offsets, repeated ownership proof, history purpose/scope/replay/coverage checks and route rejection. The coordinator reports six tests GREEN. The source receipt/receiver and history coverage store are fixtures: this does not establish Rust/PostgreSQL lease behavior, Finance receiver effects, Caddy runtime enforcement, delivery-history server composition or Kafka behavior.

One actionable documentation reference was sent to the coordinator: the environment contract names `hrms-clickhouse/grants/0006-private-history.sql`, whereas the canonical file is `hrms-clickhouse/grants/0006-protected-private-history.sql`. This is a bounded P2 operator instruction correction, distinct from the now-resolved HTTPS/mode/private configuration issue. No product edit was made by this reviewer for it.

### RSEC-3 validation provenance

The infrastructure owner directly reports that the full actual PostgreSQL retirement suite passed 40 scenarios after the final0125/0126 export correction, including exact tenant/operator drops and capture/retirement/generation/GC negatives. This supplements this reviewer's eight focused actual PostgreSQL export regressions. The coordinator owns independent inspection of the RSEC-3 SQL authored by this reviewer; this addendum does not describe self-review as independent approval.

## Coordinator closure of follow-up review

The grant reference is corrected to `hrms-clickhouse/grants/0006-protected-private-history.sql`; the canonical file exists. The current HTML and mirrors pass local-reference/ID/frozen-hash verification. The coordinator independently inspected the RSEC-3 forward preparation and exact retirement drops: the source-kind rejection precedes COMPLETE, only company stream rows enter canonical export, stored historical readers remain, and the gate executes before migration helpers are dropped. Final infrastructure evidence is42 actual PostgreSQL scenarios, including post-retirement runtime capture/cleanup; complete default Liquibase metadata41/tenant267 fresh and repeat masters also passed with native process exit0. These results preserve the production acceptance limits stated above.
