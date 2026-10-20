# Organization event application ownership cleanup

Scope: approved 2026-10-19 infrastructure ownership design; application event package and obsolete offline planner only. No commits, live deployment, production data relocation or retirement. Native Node/PowerShell commands; no RTK/Dart/Flutter.

## Changes and caller evidence

- Removed `src/events.mjs::processRecord` after tracing its only callers to `events.test.mjs`, `isolated-acceptance.mjs`, `isolated-cdc.mjs`, and `historical-retention-acceptance.mjs`. Production `worker.mjs` continues to call `processConsumerRecord` with independent inbox/history/reporting roles.
- Migrated those tests/fixtures to the supported independent role transactions, role identity fences and checkpoints. Inbox progress remains independent of ClickHouse. Historical accepted delivery acknowledges READY per role without creating a current projection. Unknown/PENDING pairs quarantine separately per role.
- Removed `ProjectionStore.markPartial`, whose sole caller was the obsolete coupled path. Kept `watermark`, `identity`, `checkpoint` and all active lifecycle/retention methods after caller trace.
- Removed obsolete `infrastructure/organization/cleanup-outbox.mjs`; workspace trace found only its README paragraph, handed to root integration to replace. Accepted-policy `src/cleanup-cli.mjs` and retention authorization stay canonical.
- Removed unused `replayExportChunk` export after workspace-wide trace found no callers. Retained strict `verifyExportChunk`, used by reconciliation fixtures. Moved test-only `progress` query helper from `src/reports.mjs` to `test/report-fixture.mjs`; its three actual callers are fixtures/tests. No production GraphQL/report behavior changed.
- Shared direct-socket ClickHouse HTTP transport in `src/clickhouse-http.mjs`; no proxy discovery/redirect following. Preserved separate URL policies, sanitized error contracts, company 32 MiB vs control 64 KiB response limits, and separate event validation/schema/privacy. Total deadline now bounds slowly trickling responses. Shared UTC millisecond conversion matches both declared DateTime64(3) schemas; exact source/archive nanosecond logic remains separate.
- Application fixtures now read canonical `hrms-clickhouse/migrations/0001-company-history.sql`, `0002-control-history.sql`, and `hrms-kafka/connectors/control-connector.template.json`. Remaining mixed Compose/root script reference changes belong to root integration.

## Rulings

- Ruling: isolate old acceptance/CDC fixtures with unique databases, topics, company/event IDs, connector/slot names and restricted CDC roles. Repeated checks otherwise collide with retained synthetic histories/global source roles. Wrong isolation would affect only fixture reproducibility; production authorization is unchanged.
- Ruling: fixture convenience may invoke three roles sequentially, but each uses the production independent transaction/checkpoint implementation. Actual subprocess failure-domain proof remains in gap-lifecycle, which ran successfully.
- Ruling: the historical restricted-role fixture receives policies on only its own freshly created synthetic metadata database so it can exercise all three roles; no production RLS/grants were broadened.

## Verification

- All 17 `test/*.test.mjs` files passed by direct native `node <file>` execution. Standard `node --test` failed at sandbox child spawn (`EPERM`), so direct test-file execution was used rather than claiming that runner worked.
- `ORGANIZATION_SYNTHETIC_ACCEPTANCE=true node test/historical-retention-acceptance.mjs`: PASS, exit 0; separate source/metadata DBs, actual restricted classifier, suspended/detached retained facts, no current projection/fence, three READY historical role checkpoints, six role-specific unknown/PENDING quarantines, four source receipts retained.
- `... node test/isolated-acceptance.mjs`: PASS, exit 0; six broker records, three logical versions, correction/tombstone semantics, metadata-only quarantine, independent PARTIAL checkpoints while inbox projection watermark stays READY.
- `... node test/isolated-cdc.mjs`: PASS, exit 0; actual Debezium snapshot + transactional correction; rolled-back outbox absent; restricted source role business-table read denied. Initial teardown exposed asynchronous connector/replication-slot detachment; teardown now waits and drops only its exact fixture slot before dropping its own DB/role. Exact initial failed-run resources were cleaned.
- `... node test/gap-lifecycle-acceptance.mjs`: PASS, exit 0 against root-verified `org-pipeline-accept-20261019` stack. Approved sandbox escalation was needed for production child worker spawning. Proves independent groups, ClickHouse outage/replay, six barriers, current membership epochs, real Debezium/persisted Connect offsets, archive restore, accepted-policy synthetic deletion, atomic cleanup receipt and retained source receipts/legacy audit.
- Initial fixed-ID shared acceptance attempt exposed synthetic ClickHouse collisions; unique event/company/database identities corrected fixture isolation and the rerun passed.

## Independent review findings handed to owners

- Kafka owner: short Compose bind mounts could auto-create missing data/secrets paths; recommended long binds with `create_host_path:false`.
- Kafka owner: independent ACL command omitted capture coordinator group/output/idempotent-write requirements and control group; requested explicit separate principal/group grants instead of broadening read workers.
- ClickHouse owner: migration admin transport lacked total timeout/response cap, and fresh `status` queried nonexistent schema; owner notified.
- Root renderer: actual JWT mode is `rs256`, not `rsa`; policy URL is origin-only because Rust appends full routes; tenant services and organization-internal policy proxy lacked a shared network; public wildcard Auth routing exposed private organization-identity route. Exact source locations were sent to root for fixes.

## Limits

Synthetic evidence does not demonstrate production TLS/ACL deployment, existing tenant cutover/backfill, failover/restore acceptance, browser behavior or production retirement. Existing live data, transactional outboxes, jobs/receipts and legacy audit were not retired. No source credentials were read or printed.

## Follow-up image and capture integration

- Image script now builds/saves/uploads `kabipay-organization-events` as the fourth HRMS image, defaults to `/opt/apps/hrms/images`, archives only the four explicit HRMS image families, and forwards Manifest/AppDir/ImageDir to application release. Deprecated CaddySiteAddress fails before native work. Uses shared validated native Remote.ps1 transport; supports absolute local output directories.
- Image evidence: PowerShell parse and git diff --check passed; mocked full orchestration verified four builds/four saves/four uploaded tars, exact archive families, deployment forwarding and early Caddy rejection. No actual image build/upload/deployment. Initial mock caught missing fourth save; corrected rerun passed.
- Capture worker uses operator-owned per-binding `connect_rest_url`. Production accepts only `https://capture-connect-<binding.tenant_id>:8443/`; no event/caller URL, global endpoint fallback, credentials/query/path/fragment or production HTTP. Explicit isolated tests alone allow HTTP loopback.
- Capture focused checks: endpoint rejection cases and two real local company HTTP endpoints pass; each endpoint receives its own exact connector-offset request. Event-supplied endpoint field is rejected. Changed production worker full lifecycle rerun is pending completion at this entry.
- Additional bounded reviews sent: root deploy upload must constrain artifact list instead of recursive arbitrary OutputDir; gateway supplied partial tenant endpoint map should fail closed; Kafka UUID version mismatch fixed by owner with v7/v8 regression. Earlier renderer rs256/origin-policy/network/private-identity fixes verified present and renderer tests4/4 pass.

Post-capture-change final check: all 18 event test files pass; syntax checks pass. Full lifecycle rerun remains pending because the Docker daemon became unresponsive: elevated targeted docker ps returned daemon API 500; fresh PG read-only status also waits. Earlier complete lifecycle PASS predates this capture URL selection change. No stack restart or resource mutation attempted. Running lifecycle session: 88859; read-only PG status session: 35268.

## Independent backup installation follow-up

- Moved only three source files from `deploy/backup-runner` to `deploy/hrms/backup-runner`; Git blob comparisons prove Dockerfile, backup-entrypoint.sh and backup-now.sh are byte-identical. No backup data or credentials moved.
- Added `deploy/hrms/backup.compose.yaml`, containing only backup-runner on the external existing `apps_app-network` (override HRMS_APP_NETWORK), dedicated `env/backup.env`, own images/backups binds, no PostgreSQL installation or depends_on. Host directories must exist; bind auto-creation is disabled.
- Reworked `scripts/install-backup-runner.ps1` to default `/opt/apps/hrms`, use shared validated Remote.ps1 SSH/SCP transport, upload exactly the three runtime sources, and make SyncCompose upload only own `backup.compose.yaml`. Creates only own backup-runner/backups/images/env directories; no root Compose overwrite or startup/schedule/cutover action.
- Updated active `docs/operations/vps-backups.md` with own manifest/env/image paths, explicit existing PostgreSQL settings and network, independent commands, retained credential variable contracts and existing-schedule/restore cutover cautions.
- Verification: PowerShell parser PASS; mock native SSH/SCP orchestration PASS for both SyncCompose states; invalid shared-root/injected selectors rejected before remote work. Static manifest checks prove only one service, external network, dedicated env and no DB dependency. Git diff --check PASS. Docker checks intentionally not attempted while daemon reports API500; runtime database backup/S3/cron/restore behavior remains unverified by these source/mocks.

## Final stalled-session handoff

- Root requested Ctrl+C only for owned lifecycle exec session 88859 and read-only PG status session 35268, preserving synthetic resources and daemon evidence.
- Both tool calls returned `write_stdin failed: Unknown process id` for their respective session IDs. The tool no longer exposes either session, so Ctrl+C could not be delivered and process exit/cleanup is not demonstrated. No exact operating-system Node PID was captured; no process was guessed or killed.
- No Docker daemon restart, container deletion, source-data deletion, shared service termination or Rust Analyzer termination occurred. Root owns any resource/process reconciliation when Docker becomes healthy.
- Final capture evidence remains: 18 unit test files pass, including separate real loopback HTTP endpoints and negative URL selection checks. Full lifecycle PASS belongs to the earlier implementation; the lifecycle rerun after per-company capture URLs is NOT DEMONSTRATED because Docker returned daemon API500 and its exec session subsequently became unavailable.

## Final canonical company connector/schema contract update

- Canonical Kafka connector interface now requires a nonpublic companySchema and derives company-specific CDC role/slot. Added test/kafka-fixture.mjs, importing the actual hrms-kafka/scripts/admin.mjs connectors(binding) renderer with a complete validated binding. No fixture substitutes template placeholders or recreates company SMT configuration.
- Updated test/isolated-cdc.mjs and test/gap-lifecycle-acceptance.mjs to use rendered company name/topic/prefix/role/slot/publication/table filters/SMT. Only explicit isolated transport password/TLS settings are replaced. Both source fixtures now create/use company_fixture schema; gap source migrations, scoped grants/publication, export CLI, marker binding and accepted retention scope consistently target it. Role/slot names derive from tenant UUID rather than unrelated fixture tags.
- Updated test/control-cdc-acceptance.mjs to begin with canonical rendered control connector before its existing explicit synthetic source/role/slot/topic isolation overrides. Metadata privacy/schema semantics are unchanged.
- Added two focused contract tests verifying nonpublic filters, raw-marker/outbox predicate separation, absence of unresolved placeholders, distinct v4/v7 tenant CDC roles/slots, metadata source resolution and transport-only local overrides.
- Final offline checks: all 19 event test files PASS (previous 18 plus new canonical fixture-contract file); node --check PASS for isolated-cdc, gap-lifecycle, control-cdc and helper. Canonical source reference trace found no remaining direct template reads, unresolved-placeholder substitution or duplicated connector.class configuration in the three changed acceptance fixtures.
- Full company/control fixtures after this schema/connector change are NOT DEMONSTRATED. Docker daemon remains unhealthy; no Docker retry/restart, database migration, source write, live deployment or data retirement was performed for this follow-up. Earlier full synthetic PASS results do not prove these latest changed fixture sources.

## Runtime restart preparation (no container start yet)

- Root reports local Docker daemon recovered after user-approved restart; heavy Rust build currently owns runtime capacity. This workstream has not started containers, Docker builds or acceptance fixtures while waiting for the explicit runtime-slot-free message.
- Prepared test/run-acceptance.mjs with explicit synthetic opt-in and a six-fixture allowlist. Prints exact launcher PID/start timestamp and captured direct Node-child PIDs. Time limits: 180 seconds for ordinary isolated/CDC/retention fixtures, 240 seconds control CDC, 900 seconds gap lifecycle. On interruption/timeout/failure it stops only owned direct Node child handles and launcher, without Docker/SQL/resource deletion or unknown PID lookup. Syntax/invalid-selector checks pass.
- Intended sequential command, from event package: ORGANIZATION_SYNTHETIC_ACCEPTANCE=true node test/run-acceptance.mjs <fixture>. Planned order: isolated-acceptance, isolated-cdc, control-cdc-acceptance, historical-retention-acceptance, control-cleanup-acceptance, gap-lifecycle-acceptance. No concurrent TLS infrastructure fixture or image build.
- Offline readiness rechecked: changed isolated/gap/control fixture syntax plus canonical connector contract and two real local company endpoint checks pass. Latest full pipeline proof remains pending. Kafka reviewer withdrew the missing-request.end finding after confirming the helper already calls it; no helper fix was required.

## Owned process-tree termination correction

- Replaced immediate direct-child SIGTERM/launcher exit with test/owned-processes.mjs manager. Only exact still-live Node child handles returned by its own spawns are eligible. Windows executes taskkill.exe /PID <captured PID> /T /F with argv and shell:false, then awaits child exit. POSIX owned Node children start in dedicated process groups and cleanup kills only their owned group. No PID guessing, process searches, Docker actions or shared-service termination.
- run-acceptance.mjs now awaits owned tree cleanup on timeout/interruption/failure and after fixture completion before exiting. Cleanup failure is reported explicitly instead of claiming no orphan workers.
- Actual Windows focused regression PASS: synthetic Node child spawned its own Node grandchild; a timer invoked tree cleanup; both exact captured PIDs were verified absent. Opt-in regression PASS: launcher rejects before fixture import/resource access with no launcher/worker output. Test used approved escalation because sandbox blocks child spawning; no Docker/network/database operations occurred.
- Still waiting for root runtime-slot-free coordination. No acceptance container start/build or full fixture retry was performed in this correction.

## Current complete unit-file rerun

Root requested fresh serial direct-Node execution after adding owned-process regression. Approved escalation was used for native child-process proof; no Docker/database commands ran. Current result: 20 test files, 53 tests passed, zero failed files, every exit code 0.

Exact files and passed counts: archive.test.mjs 2; archive-http.test.mjs 1; backfill.test.mjs 1; capture.test.mjs 8; capture-bindings.test.mjs 2; cdc-json.test.mjs 1; connect-checkpoint.test.mjs 1; control.test.mjs 6; control-retention.test.mjs 1; diagnostics.test.mjs 1; events.test.mjs 10; history.test.mjs 3; independent.test.mjs 3; kafka-fixture.test.mjs 2; metrics.test.mjs 4; operations.test.mjs 1; owned-processes.test.mjs 2; retention.test.mjs 1; service-proof.test.mjs 1; time.test.mjs 2.

This supersedes earlier 17/18/19-file unit counts. Full latest-schema company/control/CDC/gap acceptance remains pending the root-assigned runtime slot.

## Role-specific Kafka reader identities

- Updated only owned test/kafka-fixture.mjs to provide explicit distinct inboxPrincipal, historyPrincipal and reportingPrincipal in addition to connect/capture/control/controlConnect identities. Obsolete consumerPrincipal is removed; all seven canonical identities are distinct. Transport-only fixture overrides remain unchanged.
- Canonical fixture contract tests2/2 PASS; helper and isolated/gap/control fixture syntax checks PASS; no consumerPrincipal references remain in the application fixture package. No Kafka-owned files changed and no Docker/runtime actions occurred while TLS runtime owns the slot.

## Runtime execution after approved Docker recovery

- Root released the runtime slot after exclusive TLS/ClickHouse checks. Verified acceptance project container IDs: PostgreSQL2ccad515e62f, Kafka44dc9d93a2c3, Connectf4b42060ee9d, ClickHousef3a9bd6a976f. Started only the first three; CH was already running. Read-only PG/Kafka/Connect/CH readiness passed. No migration journal access or DDL.
- Initial isolated acceptance PASS/exit0. Initial canonical isolated CDC failed exit1: cleanup reported SYNTHETIC_SLOT_STILL_ACTIVE and masked CDC timeout. Correlated source had two outbox rows but only one broker record/three checkpoints; exact connector/task reported RUNNING. Connect logs identified canonical heartbeat topic UNKNOWN_TOPIC_OR_PARTITION: fixture precreated legacy __debezium-heartbeat while current canonical config emitted organization.heartbeat.organization.company.<UUID>. Producer retries blocked streaming correction and graceful task stop.
- Corrected fixture topic provisioning to use same validated canonical binding with topics(binding)+connector config; updated company and control heartbeat resources. Added required-topic regression and primary+cleanup preservation regression; four canonical/helper tests PASS. Isolated fixture now aggregates original and cleanup failures; launcher prints bounded child causes. No timeout increase.
- Exact failed-run resources reconciled after connector404 and dedicated slot/database/role evidence. WalsenderPID82 and idle JDBCPID81 both belonged to unique source database isolated_cdc_a830e18fae9b4282b71aa9423ab2c202 and organization_cdc_bf490971e7f94288b032cf74326e5f79. Only those correlated fixture backends were terminated, then exact slot/database/role removed. No guessed OS PID or unrelated resource termination.
- Current-source serial rerun: isolated-acceptance PASS/exit0 (launcher38260); isolated-cdc PASS/exit0 (launcher32736), actual canonical nonpublic schema/UUID role+slot, snapshot plus streamed correction, rolled-back outbox absent and source business read denied. Control CDC is next/running at this entry; final six-fixture outcomes follow.

## Current-source runtime results through fixture five

All commands used ORGANIZATION_SYNTHETIC_ACCEPTANCE=true and test/run-acceptance.mjs serially, with no concurrent Kafka TLS fixture.

| Fixture | Launcher PID | Result / exit | Actual proof |
| --- | --- | --- | --- |
| isolated-acceptance | 38260 | PASS / 0 | Six broker records, three logical versions, correction/tombstone, private-field-free quarantine, three independent partial checkpoints |
| isolated-cdc | 32736 | PASS / 0 | Canonical nonpublic schema and UUID role/slot; two actual Debezium snapshot/stream events; rolled-back outbox absent; business-table read denied |
| control-cdc-acceptance | 32620 | PASS / 0 | Four real CDC events, actual0113/0114 sequence, NULL-org retained, rollback absent, failed sink held offset/replayed, conflict quarantine, restricted source/CH/reader privacy |
| historical-retention-acceptance | 30128 | PASS / 0 | Separate source/metadata DBs, suspended/detached handling, no current projection/fence, three READY checkpoints, six unknown/PENDING role quarantines, four source receipts retained |
| control-cleanup-acceptance | 22380 | PASS / 0 | Actual PG/Kafka/CH, exact source hash/encrypted restore, stopped legacy offsets, accepted-policy dryrun/fixed source, one synthetic outbox deletion with atomic receipt/source receipt retained |

Exact completed launcher PIDs30684,37948,38260,32736,32620,30128,22380 and control-worker PIDs35984/36440 were checked via Get-Process -Id and all were absent. No guessed process termination occurred. Launcher also awaits owned tree cleanup before successful completion; completion JSON now explicitly includes remaining owned_child_pids for future invocations.

Final gap lifecycle launcher33592 and its captured child handles remain running at this entry. Final unit counts/container-stop verification follow after it completes.

## Gap lifecycle schema-proof correction and rerun

- First current-schema gap run (launcher33592) reached final accepted-policy execution, then failed exit1 with SQLSTATE42P01: public.organization_synthetic_fixture absent. The source Pool now intentionally uses company_fixture search_path; its unqualified test-only nonce table had moved into that schema. Production retention safety guard intentionally queries public.organization_synthetic_fixture, as the control fixture already does.
- Corrected only the gap fixture nonce CREATE/INSERT to explicit public.organization_synthetic_fixture, with a comment separating fixed synthetic execution proof from nonpublic company business/outbox data. No production guard, grant, policy or source-schema authorization was changed. Syntax check passed.
- Exact failed gap launcher33592 and all captured child PIDs32356,1044,15028,12232,36172,38240,16952,16124,38232 were checked absent after launcher failure/cleanup. No guessed termination occurred.
- Rerun gap launcher26420 started at2026-10-19T08:29:37.997Z with900000ms limit. Earlier five final-source fixtures remain PASS/exit0; this correction only affects the final gap fixture's synthetic nonce setup. Final outcome follows.

## Final current-source acceptance and resource handoff

Final gap-lifecycle rerun (launcher26420, started2026-10-19T08:29:37.997Z) PASS, exit0. Actual proof: separate source/metadata databases; three independent groups; ClickHouse failure leaves inbox advancing; sink restart/replay; six partition barriers; missing partition denied; source attendance3600seconds; legacy private fields absent; source manifest hash verified; encrypted archive restore; real Debezium plus persisted Connect LSN offsets; current membership epochs; stopped synthetic legacy group; default cleanup dryrun; nonce rejection; one accepted-policy synthetic outbox deletion; source receipts/legacy audit retained; cleanup receipt atomic. Completion explicitly reported owned_child_pids:[]. This supersedes the prior pending/failed gap outcome; failures and root-cause corrections remain above for audit.

All six final current-source fixtures are PASS/exit0: isolated-acceptance38260; isolated-cdc32736; control-cdc32620; historical-retention30128; control-cleanup22380; gap-lifecycle26420. The first five sources were unaffected by the final gap-only nonce qualification correction. No production identity/backfill/rollout/retirement is inferred from synthetic acceptance.

Fresh final serial direct-Node unit execution after runtime:20files,55tests passed,0failed files, every exit0. Counts match the earlier exact file list except kafka-fixture.test.mjs now4tests (added canonical heartbeat provisioning and primary/cleanup preservation); all other counts unchanged. Actual owned-process tree timeout/opt-in regression2/2 passed within that rerun.

Exact current execution launcher/worker PIDs30684,37948,38260,32736,32620,30128,22380,35984,36440,33592,32356,1044,15028,12232,36172,38240,16952,16124,38232,26420,2992,24672,21492,33300,9560,11976,38200,36088,1640 were checked via Get-Process -Id after completion; all absent. No active owned runtime launcher/worker handles remain. No guessed/shared process termination occurred.

After all checks, exact container IDs/names/project labels were reverified and only the four authorized org-pipeline-accept-20261019 containers were stopped (not removed). Final labeled Docker state: Connectf4b42060ee9d Exited143; Kafka44dc9d93a2c3 Exited143; ClickHousef3a9bd6a976f Exited0; PostgreSQL2ccad515e62f Exited0. Volumes/state retained. No other containers, Docker daemon restart, ClickHouse migration journal operations, VPS/live deployment, commit or production data retirement occurred in this runtime sequence.
