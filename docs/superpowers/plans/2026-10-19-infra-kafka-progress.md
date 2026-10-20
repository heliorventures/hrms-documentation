# Kafka / PostgreSQL ownership execution ledger

Plan: 2026-10-19-infrastructure-ownership-design.md; approved local implementation and focused checks. No commits/live deployment/data relocation.

## Canonical paths

- svc infrastructure/organization connector.template.json + control-connector.template.json -> hrms-kafka/connectors/ (originals removed).
- svc infrastructure/organization cdc-source.template.sql + control-cdc-grants.template.sql + grants.sql -> hrms-database/provisioning/organization/ (originals removed).
- New Kafka independent installation hrms-kafka/deploy/compose.yaml; operator binding example, Node admin script, tests and README.
- New PG independently runnable provision.ps1 and README; psql quoted database parameters and role/database preflight checks; original RLS untouched.

## Decisions

- Existing approval overrides skill worktree/commit suggestions: existing checkout is the approved source of required feature work; no commit created.
- Source credentials remain fixed file-provider values per company/metadata. Admin REST host is fixed private connect:8443 with mTLS; no arbitrary caller URL.
- Broker default deny, no auto topic creation, no public ports. Topic/ACL operations create literal resources only; no automatic ACL revocation or destructive connector/slot removal.
- Single broker factor 1 remains the existing baseline; no HA claim. One Connect deployment is fixed to one company ID; separate company stacks require an explicit independent network/DNS topology.
- PG roles are provisioned with certificate/password lifecycle out of band; canonical command validates roles are non-superuser/non-bypass and appropriate replication. Does not alter RLS or silently replace existing publications.

## Focused checks

- node hrms-kafka/test/admin.test.mjs: PASS 2/2 template/table binding and unsafe identifiers/principal rejection.
- node hrms-kafka/scripts/admin.mjs validate --config hrms-kafka/binding.example.json: PASS.
- docker compose -f hrms-kafka/deploy/compose.yaml config --quiet with isolated synthetic environment: PASS (no secrets read).
- Initial node --test failed spawn EPERM in sandbox; direct node test runner invocation passed. --test-isolation is unavailable in current Node version.
- Initial Compose parse caught unquoted flow-volume interpolation; corrected quoted mount. A relative synthetic data path failed as an undefined volume; absolute synthetic path validated as documented.

## Limitations / remaining acceptance

- Current environment lacks native psql. No production SQL or grants executed; synthetic PG provisioning execution pending coordination with root.
- No live broker/Connect mTLS, ACL enforcement, publication/slot delivery, failover/restore, production source binding or rollout demonstrated here.
- Existing acceptance containers managed by root remain untouched by this workstream.

## Additional synthetic evidence

- Dedicated disposable database `infra_provisioning_20261019` in root-managed synthetic PostgreSQL only: schema-only metadata fixture plus canonical migration-extracted outbox/marker table DDL. All three canonical SQL files executed successfully.
- Exact publication table membership: company outbox + company marker, control metadata outbox only. Existing checkpoint/identity/barrier RLS flags all true. Source outbox SELECT true/INSERT false; projection worker tenant SELECT false; worker checkpoint query obeyed RLS.
- Negative wrong-database check exposed unsupported psql `\quit 3` exit semantics; root cause corrected using SQL error under ON_ERROR_STOP. Negative check now returns nonzero; valid worker grants reapply succeeds.
- Independent reviewer found missing capture/control ACLs; distinct principal bindings plus exact groups and producer IdempotentWrite now included. Offline suite PASS 3/3 including ACL scope regression.
- Actual isolated canonical TLS installation found Apache image required SSL file credential contract; corrected *_FILENAME/*_CREDENTIALS variables and `/etc/kafka/secrets` mount. Broker reached STARTED and mTLS admin topic listing succeeded; Connect internal topics created over TLS.
- Pinned Debezium image overwrites CONNECT_REST_ADVERTISED_* from ADVERTISED_HOST_NAME/ADVERTISED_PORT; corrected actual input variables. HTTPS REST probe pending its plugin scan completion.
- Review correction: all persistent/secret bind mounts now use bind.create_host_path:false to prevent missing-directory creation.

- Final canonical Compose renders successfully with synthetic env; broker+Connect actually start. Private Connect GET /connectors returns HTTP200 [] using client certificate, verified CA and DNS; the same probe without client certificate is rejected. No public ports added.
- PowerShell provisioning wrapper parser and Node admin syntax checks pass. SQL executed inside approved synthetic PG via docker exec psql because native psql is not installed; wrapper live libpq service/TLS configuration remains operator acceptance.

- Root requested explicit optional metadata Connect extraction: `deploy/control-connect.compose.yaml` now canonical; only control-connect, separate source network/secrets/state topics/principal. Compose config PASS. Company connector command no longer applies metadata connector; control-connectors uses fixed private control-connect:8443. Actual separate optional control worker startup not yet tested; shared image TLS contract was exercised by company Connect.

## Final topology changes and limits

- Broker-only install `deploy/compose.yaml`; independently repeatable company Connect/proxy `deploy/company-connect.compose.yaml` with unique derived UUID aliases; optional dedicated `deploy/control-connect.compose.yaml`. All three final manifests rendered with synthetic configuration.
- Capture proxy added: separate capture client CA and separate Connect REST administrator truststore. Exact company GET offsets/status allowlist, no mutation/list/cross-company requests, bounded timeout and response size. Broker worker certificates must never be trusted by the REST admin truststore. Offline allowlist test passed.
- Final admin ACL regression checks passed 4/4; proxy allowlist test passed 1/1. Metadata Connect/control principals receive no company topic/state privileges.
- Independent actual topics command created four exact event/marker/control/quarantine topics before Docker daemon control calls stalled. Actual final full ACL provisioning completion NOT DEMONSTRATED; no success claim. Root notified of pending exec sessions and own synthetic resources.
- Earlier actual mTLS installation proof predates final derived hostname/admin truststore/proxy split. Final topology live rerun and proxy container/HTTPS negative checks remain required after Docker daemon recovery. This is explicitly NOT DEMONSTRATED, not production acceptance.
- Synthetic database and own infra-kafka-tls-20261019 containers/networks remain available for root-coordinated inspection/cleanup. No existing acceptance resources were stopped/removed.
- Independent application review caught UUID version drift: Kafka/proxy now accept canonical versions 1..8, aligned with renderer/Rust/event binding. Version7/version8 regression added; final admin suite PASS5/5.

## Root integration review handoff

Bounded read-only review of render.mjs, deploy-on-vps.ps1, Remote.ps1, platform.sh, release.sh and platform Compose. Findings sent to root (root owns fixes):

1. Important: platform.sh manually creates private networks while platform Compose initially treated them as managed; align external/managed ownership to avoid label conflicts.
2. Important: storage guard checked PG/Mongo mounts but not existing Caddy named volume identities/existence; guard against empty state recreation.
3. Medium: platform Compose interpolation should explicitly bind platform-root env file rather than unrelated caller cwd .env.
4. Credential concern: entire historical platform .env injected into postgres/mongo may expose unrelated app/cloud secrets; scope DB env explicitly. Actual .env was never read.

No shell injection found in reviewed quoted shell arrays/native SSH argument paths; Remote.ps1 constrains interpolated fields. Organization-mode removal of global Auth/tenant/legacy worker routes is an acknowledged in-progress root change, not reviewed as final behavior yet.

Root reported Docker daemon HTTP500; no further heavy Docker checks started. Final topology/ACL/proxy runtime proof remains NOT DEMONSTRATED. Existing synthetic resources retained for root-coordinated recovery; no production mutation or commit occurred.

## Local actual proxy HTTPS proof (Docker-independent)

- Generated one-day synthetic-only OpenSSL key/certificate under temporary directory (no production keys/read/write). Native OpenSSL required approved sandbox escalation; Windows PowerShell treated OpenSSL progress stderr as an error although certificate files were generated successfully.
- `node hrms-kafka/test/proxy-https.mjs <temporary-test-certificate-directory>` PASS1/1 under approved local loopback permission.
- Actual HTTPS upstream+proxy verified CA/hostname/client certificate, allowed exact company offsets HTTP200, denied PUT403, denied other connector403 without upstream call, rejected no-client-certificate TLS handshake.
- Production construction still fixes company-derived upstream DNS/8443 and `/run/secrets` inputs; test construction injects local request transport and disposable key loader only. Final Compose DNS, admin-vs-capture CA separation deployment, complete ACL provisioning, source CDC delivery remain NOT DEMONSTRATED after Docker daemon500. No new Docker checks started during daemon outage.

## Source contract correction (current canonical ownership)

Root source audit identified that BoundTenantDatabase rejects public schema, shared organization_cdc credentials violate company isolation on a shared PG cluster, and slot names are cluster-wide. Canonical company schema is now required/validated exactly against runtime identifier+reserved schema rules. Connector table filters and topic predicates use escaped separators and the fixed source schema; raw marker topic includes schema.

Company role derives only from UUID: organization_cdc_<32hex>. Company slot derives only from UUID: organization_company_<32hex>. No passwords/roles are created here. Wrapper requires CompanyId/SourceSchema and SQL independently checks role/schema binding. Shared canonical CDC guard rejects memberships/ownership, unrelated effective table privileges, source mutation privileges, effective CONNECT to other databases, broad publications and any publication exposing unrelated tables. Expected publications are idempotent only for exact table membership/count/publish operations; mismatches fail without modification. Metadata uses its own fixed role/boundary checks. RLS is untouched; no grant/publication/PUBLIC revocation occurs.

Default PUBLIC CONNECT intentionally fails until a DBA separately reviews/preserves grants and hardens CDC access; HBA first-match own-db/cert/private-address allow plus other-db/address/physical-replication rejection is an additional prerequisite, not assumed proven by SQL.

Evidence: Kafka offline suite PASS7/7 (including two-company schema/role/topic/slot separation); native provision.test.ps1 wrapper mock +static SQL contracts PASS without DB. Earlier public-schema/shared-role PostgreSQL rehearsal is SUPERSEDED and does not prove current SQL. Actual current guard/publication/CDC delivery rehearsal remains NOT DEMONSTRATED pending Docker recovery. No Docker checks or production actions run for this correction.
- Follow-up independent security review fixed full-table publication equivalence: expected publication rejects row filters (prqual) and column lists (prattrs). Effective privilege checks include column-level SELECT/INSERT/UPDATE/REFERENCES grants on other relations and column mutation privileges on source tables; dedicated CDC role cannot have inbound/outbound memberships. Native wrapper/static SQL contract checks pass; actual PostgreSQL execution of these new guards remains NOT DEMONSTRATED.

## Current canonical native PostgreSQL proof

Native PostgreSQL17.6 installed tools were verified explicitly. `tests/native-cdc.test.ps1` initialized a unique cluster under workspace `.codex-tmp`, listened only on127.0.0.1 at an ephemeral port, exercised current canonical files, and stopped only its owned data directory in finally. Success fixture: `.codex-tmp/native-cdc-76978ab99a204610b364a2d9720f2b90`, port58610. No existing service/database was accessed.

PASS46 SQL operations/assertions (includes fixture setup): default PUBLIC CONNECT rejection; two fixed company schemas/roles/publications and exact reapply; cross-company CONNECT detection; PUBLIC table SELECT and explicit private-column SELECT rejection; source-column UPDATE rejection; membership rejection; publication row filter, column list and table count mismatch rejection; unrelated/all-table/schema publication rejection; reserved-schema/wrong-role rejection; existing RLS preserved; central metadata exact reapply and column-list rejection.

Harness corrections before the passing run: one excess parent traversal initially placed its unique fixture under D:/work/.codex-tmp; that owned server stopped and only the verified exact fixture removed. Workspace boundary assertion now precedes initialization. PowerShell error record line wrapping broke a negative-message assertion, fixed formatting. Native Windows -c marshalling stripped identifier quotes in fixture DDL, so all fixture SQL now uses UTF8 files with -f, preserving case. Canonical SQL already used -f. These were harness defects, not evidence of current canonical SQL passing before the final run.

Scope: current guard SQL proven on native PostgreSQL17.6, NOT the pinned PostgreSQL16 image, TLS/pg_hba deployment, logical replication slot delivery, final Compose/proxy topology, backfill/restore or production rollout. Earlier public/shared-role rehearsal remains superseded; current native proof replaces only the earlier pending SQL-guard proof. Docker-specific delivery acceptance remains pending.

## Final runtime preparation under serial resource hold

No Docker starts/builds while the root-owned Rust build holds the runtime slot. Added offline PKI and executable bounded rehearsal under test/tls-runtime, with distinct broker client, Connect admin client, capture client and PostgreSQL client CAs; fixed source client certificate paths now make the documented HBA identity enforceable. Source PostgreSQL certificate CN derives from the exact company role, private source address/database HBA and SCRAM password are tested separately.

Security review corrected shared reader group ownership: explicit inbox/history/reporting principals replace obsolete consumerPrincipal, all seven identities distinct, each reader receives only its literal own checkpoint group. controlGroupId collisions with all derived reader/capture/Connect groups fail. Heartbeats enabled by templates now have exact bounded topics/connector-only ACLs, preventing forbidden implicit topic creation. Offline admin suite PASS11/11. Runtime test will require actual reporting-to-inbox GROUP_AUTHORIZATION_FAILED.

Runtime fixture uses minimal synthetic transport envelopes only. It does not claim business event validation, metrics, projection correctness or production acceptance. Granular transcript/check labels and owned container logs distinguish TLS/DNS/auth/ACL/CDC/capture-helper proof. Existing Java dependency startup plan was replaced by the application's already-installed pure-JS KafkaJS for batched administration and probes, reducing memory and avoiding many JVM starts. Runtime slot is still held; no final runtime success is claimed.

## Pinned16 TLS runtime investigation (in progress)

Root released the capped runtime slot after measured WSL resource recovery. Current owned fixture `.codex-tmp/kafka-tls-1792395273962` starts the canonical broker plus two independently bound company Connect/proxy instances and PostgreSQL16.15. Actual pinned16 canonical company provisioning/exact reapply and default PUBLIC CONNECT rejection passed. Source verify-full TLS plus SCRAM accepted the fixed own certificate identity and rejected cross-database HBA access, wrong certificate CN and wrong password; source server log independently corroborated CN rejection.

Earlier attempts stopped before delivery proof. Harness defects were corrected independently: Docker static source IP requires a network with explicitly configured subnet; PostgreSQL deliberately reports a generic password error for certificate CN rejection, so the negative assertion also inspects the source server log. Repeated unchanged10s connector PUT timeout correlated with Connect distributed group NOT_COORDINATOR/rebalance startup and no source/JDBC validation yet. REST GET alone was an inadequate readiness predicate. Fixture now polls both exact worker groups Stable with one member before configuration, retaining original request timeout and TLS/ACL boundaries. Final CDC/proxy/helper success remains pending.
## Final pinned16 two-company TLS/CDC rehearsal PASS

Fresh run EXIT0 on2026-10-19 with fixture `.codex-tmp/kafka-tls-1792395273962`; granular evidence is `runtime-transcript.log`, `PASS.txt`, `lsn-one.txt`, `lsn-two.txt` and `logs/*.log`. Canonical broker/company manifests ran with fixture-only memory caps, isolated networks, no host ports, and source PostgreSQL16.15 (Debian16.15-1.pgdg13+2). Optional central control Connect was not started.

PASS: pinned16 default PUBLIC CONNECT rejection and exact company schema/derived role/two-table publication provisioning/reapply; fixed source certificate CN+verify-full+SCRAM authentication; cross-database HBA, wrong CN and wrong password rejected (wrong CN also corroborated in source server log). Both source connectors reached RUNNING and actual logical streaming with distinct cluster-wide slots.

Canonical plan provisioned19 exact topics and112 literal ACL entries. Targeted actual negatives proved other-company Connect topic access denied, read-worker business-topic Write denied, and reporting identity cannot join inbox checkpoint group. The latter captured the real GROUP_AUTHORIZATION_FAILED protocol code30: KafkaJS otherwise discards the underlying coordinator error and throws generic GroupCoordinatorNotFound, so generic failure alone is never accepted as proof.

Both company outbox IDs and raw marker IDs/source LSNs arrived through actual CDC. Both derived proxy endpoints accepted capture-client GET offsets and rejected PUT/list/other connector paths. Ambiguous `connect` DNS failed hostname verification. Broker and capture client CAs were rejected by direct Connect admin REST; Connect admin CA was rejected by the capture listener. The production application connectorConfirmation helper confirmed each actual marker LSN through its private company proxy.

Readiness root cause confirmed: early REST GET200 preceded distributed coordinator availability (NOT_COORDINATOR/rebalance; prior company-one group assignment07:49:35 only during cleanup). Exact two-group Stable/one-member polling, tolerating only coordinator bootstrap14/15/16, preceded unchanged10s PUTs successfully in the final run (company-one08:02:46.256Z; company-two08:03:01.688Z). No TLS, HBA, ACL or production timeout boundaries were relaxed.

Scope: synthetic minimal transport envelopes prove TLS/auth/topic/CDC/proxy/checkpoint transport only. They do not prove business-event validation, metrics, projections, restore/backfill, optional control connector delivery or production rollout. Native17.6 remains the broader46-operation negative SQL-guard matrix; pinned16 rehearsal proves the bounded subset listed above. Owned resources were preserved only for final log capture and are removed explicitly by exact fixture label; existing stacks remain untouched.
Cleanup confirmed: removed final owned container IDs8df62208ca7a/94a66f644b9d/3dba55e6a548/5a2f75888cd3/1d47639fba97/b81e571093ed; exact four fixture networks; source volume after verifying hrms.synthetic label. Final container/volume label queries and network name query all returned empty, exit0. A PowerShell scalar splat initially attempted characters as volume names (all rejected); explicit verified exact volume removal then succeeded. Runtime slot released to root; no additional tests/containers started.

## Cleanup scalar safety follow-up

The character expansion occurred in the one-off manual cleanup command; the runner used an array concatenation rather than scalar splatting. The permanent runner nevertheless now normalizes the complete discovery pipeline into an array, derives no deletion arguments by scalar splatting, and removes volumes one exact name per invocation through `Cleanup.ps1`. Every candidate name must have the fixed fixture prefix and every inspected hrms.synthetic label must match before any volume is removed. Fixture project must case-sensitively equal its validated unique directory name both before startup and again before cleanup. Container discovery also normalizes the complete pipeline.

Native mocked Docker regression `test/tls-runtime/cleanup.test.ps1` EXIT0: zero volumes issues no rm; one volume remains one complete argument; multiple volumes issue separate intact names; foreign label fails before any deletion; mismatched fixture project fails before any Docker operation. No Docker stack or actual cleanup was run for this regression; existing final runtime cleanup remains confirmed empty.