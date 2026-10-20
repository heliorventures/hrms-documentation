# Infrastructure ownership execution ledger

Approval: user explicitly approved the split, reviews and focused checks. Local implementation only; no live deployment/migration/retirement, automatic commits or data relocation. Preserve the existing feature branch and unrelated loan work. Native commands; no RTK/Dart/Flutter.

## Ownership and interfaces

| Workstream | Owned paths | Interface |
| --- | --- | --- |
| ClickHouse | `hrms-clickhouse/**`; original ClickHouse resources only | `deploy/compose.yaml`, `config/`, `migrations/`, `grants/`; independent `node scripts/migrate.mjs` status/apply/validate |
| Kafka/PostgreSQL | `hrms-kafka/**`; `hrms-database/provisioning/organization/**`; original Kafka/PG resources only | `hrms-kafka/deploy/compose.yaml`, connector templates and independent administration; canonical PG provisioning under database project |
| Application events | `hrms-svc/integrations/organization-events/**`; obsolete application cleanup planner | independent production consumers remain in svc; canonical schema/connector references point to new owners |
| Root integration | documentation deployment/scripts/runbooks/HTML; svc Dockerfile and remaining infra manifests; gateway routing | root platform and HRMS application rollout separated; fail-closed company routing, private internals; preserve current root data/project/network |

Agents must not edit another owner's paths without coordination. Consumers reference canonical external resources; no permanent duplicate SQL or forwarding copies. Record touched files, focused command outcomes and limitations in per-workstream ledgers. Root integrates reference changes in remaining fixture scripts.

## Extraction manifest

- `hrms-svc/infrastructure/organization/{clickhouse-config.xml,clickhouse.sql,company-history-grants.sql,control-history.sql,control-history-grants.sql}` -> ClickHouse project.
- `hrms-svc/infrastructure/organization/{connector.template.json,control-connector.template.json}` and broker/Connect installation -> Kafka project.
- `hrms-svc/infrastructure/organization/{cdc-source.template.sql,control-cdc-grants.template.sql,grants.sql}` -> database provisioning project.
- Application consumer/archive/retention/diagnostic behavior remains in svc. Existing transactional outboxes, receipts/jobs and active Finance/notification delivery remain until verified release cutover.
- Mixed installation Compose manifests will be replaced by independently owned infrastructure manifests plus HRMS application composition. Synthetic acceptance may compose those resources explicitly, with private production defaults kept intact.

## Progress

- [x] Explicit scope/cost approval recorded; current dirty feature checkout retained.
- [x] Ownership/interfaces and extraction manifest recorded before edits.
- [x] Independent projects and canonical references; standalone local Git branches initialized, no remotes/commits.
- [x] Platform/application deployment and public/private routing implemented; actual final container topology is an unperformed runtime gate.
- [x] DRY/SOLID and obsolete caller removal; active delivery/audit paths retained with explicit retirement prerequisites.
- [x] Approved focused checks and independent review fixes; exact proof boundaries below.
- [x] Design-phase/retirement matrix and architecture HTML v8 plus two location-adjusted mirrors.
- [x] Four actual application images + current two-company Kafka/Connect/proxy/TLS/ACL transport + six updated source-schema/capture lifecycle fixtures, with exact proof boundaries recorded.
- [ ] Production/browser/backfill/reconciliation/restore/failover/legacy retirement acceptance (separate release scope).

## Rulings

- User approval overrides skill suggestions to commit or request repeated routine approvals. Work stays uncommitted in the existing checkout, which contains required feature work.
- Synthetic checks cannot demonstrate browser behavior, production identity backfill, failover/restore acceptance, live rollout or retirement.

## Root integration and review outcome

- Added application-only manifest renderer, scoped source/Auth/gateway/organization/consumer/archive fleet, fixed private endpoint maps and per-role environment contract. Global entry point is ops-only in organization mode; company Auth is client-only RSA. The organization process has metadata credentials only.
- Canonical shared platform retains existing root PostgreSQL/Mongo paths, external network and existing Caddy volumes. No app release installs those services or executes schema provisioning. Root Caddy is explicitly staged/reviewed; common public routes have ordered private denials. Each company delivery fleet has a separate outbound bridge; no host ports are published by application services.
- Four-image build/upload/archive flow and independent backup Compose/installer updated. Application release uploads only its generated allowlist, checks canonical existing distinct company file paths and required Finance settings before startup; post-validation checks actual Employee/Payroll container IDs. Removed unused TenantId/WithWorker switches.
- Current native Caddy parser + actual HTTP routing tests2/2 pass; private routes return404 without touching upstream, public paths work. Root renderer5/5, mocked PowerShell deployment, native release negative tests3/3, document-link/baseline test1/1, Compose CLI both application modes/platform and PowerShell parse checks pass. Config/CLI parsing does not prove a running deployment.
- Final Auth plane tests2/2, actual native Rust private-CA handshake3/3, gateway build/config8 + unchanged suites11, scoped organization/tenant/Auth Rust checks pass (see ClickHouse ledger).
- Current canonical PostgreSQL CDC source/control guard rehearsal passes on isolated native PostgreSQL17.6:46 SQL operations/assertions including setup. Proves source schema/role boundaries and strict privileges/publication negatives; unique slot configuration is covered by Kafka unit tests; not pinned16, production TLS/HBA or live deployment proof. Earlier public/shared-role fixture proof is superseded.
- Kafka/admin/proxy and application test counts/latest schema fixture changes are in their owner ledgers. Earlier real Kafka/CH/CDC lifecycle passed; full current topology/schema/capture rerun is still blocked by local Docker Engine HTTP500.

### Independent review closures

| Finding | Permanent source fix / evidence |
| --- | --- |
| Private route or wrong JWT/policy URL/network wiring | Ordered Caddy route, rs256 mode, origin-only policy URL and reachable private policy proxy; actual Caddy HTTP tests + Auth/Rust/gateway focused checks |
| Legacy global client/HMAC/unbound route bypass | Ops-only global fleet, client-only per-company Auth, bound source services; Auth route2 + gateway configuration tests |
| Legacy worker cutover guard missed generated container names | Exact Compose project/service label query plus old explicit name; both native mocked release negatives pass; no automatic worker stop |
| Existing business delivery had no outbound network | Company-specific egress bridge on Auth/business/outbox; central process excluded; static renderer assertions, final runtime proof pending |
| Duplicate/overlapping/aliased private-file mounts | POSIX normalization, allowed roots, non-overlap, release realpath-e guard; renderer negatives and independent closure review |
| Platform network ownership/state-volume/environment drift | Explicit external networks, exact existing PG/Mongo/Caddy identities and volumes, fixed env-file, PG/Mongo env allowlist; source re-review and Compose parse |
| Hardcoded public schema/shared CDC role/cluster slot | Canonical schema + company UUID-derived role/slot, strict effective privilege/cross-DB/publication guards; current offline/native PG17.6 proof |
| Publication filters/column lists and column-only grants escaped guards | Explicit prqual/prattrs/effective-column checks; source re-review and native negative cases |

Review reports: `2026-10-19-infra-deployment-review-one.md` and `...-two.md`; dedicated GPT6.1 evidence summary uses bounded ledgers. All reported actionable source findings closed. No unrelated loan business logic changed; its deployment Finance safety preflight was preserved.

## Tooling and pending runtime gates

The scoped release Docker build stalled under local memory pressure and was canceled only by its own session. A jobs1/locked/cache retry failed at Docker Engine_ping HTTP500. Subsequent read-only version/ps calls also returned500. Native/source/config checks continued. Local Docker restart was requested asynchronously because unrelated containers may be affected; it has not been authorized or performed. No VPS process/data was touched.

Own synthetic Kafka acceptance/TLS containers and scratch evidence remain retained; no Docker cleanup success is claimed while the daemon is unavailable. Agent-owned stale session Ctrl+C attempts returned Unknown process id; no unknown OS process was killed. Native PostgreSQL17.6 fixture server was stopped by its exact own data directory.

### Approved Docker recovery and serialized final checks

User explicitly approved restarting local Docker Desktop. `docker desktop restart --timeout 45` reported a startup timeout, followed by `docker desktop status` reporting running and `docker version --format '{{.Server.Version}}'` returning28.3.2. WSL listed only docker-desktop. The six containers belonging to the two recorded synthetic projects were verified exited; no VPS action occurred. This supersedes the pending-approval/unavailable-engine statements above.

The final Rust image is building with one job and locked dependency/target caches. Worker, gateway and UI image checks follow serially; Kafka multi-company TLS/CDC and current application lifecycle fixtures wait for the resource slot. No final image or changed runtime pass is claimed until the commands finish. Two additional review corrections are being verified: deterministic current-target image export despite persistent caches, and bounded cleanup of owned acceptance process trees.

Latest read-only build health supersedes the earlier4GiB resource assumption: WSL reports7.6GiB total/6.3GiB available, working set1.9GiB, and an active one-core rustc process at450MiB RSS. Root permits the bounded two-company Kafka TLS fixture beside the existing single-job compile; subsequent heavy image builds wait for the TLS fixture, and the application acceptance stack remains stopped. No process cancellation or daemon change is authorized by this scheduling adjustment.

Final security review found the former shared consumer principal could join all three role groups. Kafka bindings are being changed to distinct inbox/history/reporting identities with one literal group each, plus explicit control-group collision rejection. An active reporting-to-inbox authorization negative is required before closing this finding. This is an implementation gate, not production acceptance.

### Fresh runtime evidence after recovery

- Kafka final two-company rehearsal EXIT0: PostgreSQL16.15 source certificate/SCRAM/HBA boundaries, canonical schema/role/publication reapply,19 topics/112 literal ACL entries, actual distinct-slot outbox/marker transport and the production capture helper through separate private proxies. Reporting-to-inbox access was explicitly rejected with GROUP_AUTHORIZATION_FAILED/code30. Reader identity separation is now source- and runtime-closed. Heartbeat topics are explicitly provisioned. Optional metadata/control Connect was not started in this TLS rehearsal; it proves transport, not business projections.
- Exact final TLS fixture containers/networks/volume were removed and discovery was empty. A manual scalar-splat cleanup defect was corrected with prevalidated ownership and intact per-volume arguments. Root independently ran all five native mocked cleanup cases PASS; no actual resources were recreated.
- Fresh ClickHouse canonical0001/0002 apply/repeat/validate and disposable11-object/grant/concurrency/drift/failure/timeout/response-cap tests PASS. Root independently ran connected validate: lockfalse,0001/0002 applied, managed-principal grants0003/0004 intentionally pending. Disposable test databases/roles returnedzero; no production data touched.
- Worker image built with runtime user node; network-none syntax check PASS. Gateway image built; compiled endpoint/plane tests8/8 PASS inside the image. UI build and final Rust deterministic-artifact image remain pending.
- Current event fixtures now derive heartbeat/source topics from the canonical Kafka plan. The earlier stale-heartbeat test setup error was correlated in Connect logs and corrected; primary/cleanup failures are preserved together. Current-source isolated acceptance and actual company CDC fixtures PASS; control/history/retention/full-gap fixtures are still running. Do not substitute these partial results for the final six-fixture gate.

### Final event and deployment checks

All six current event acceptance fixtures completed with exit0: isolated acceptance, company CDC, control CDC, historical retention, control cleanup and full gap lifecycle. The gap fixture's public synthetic nonce marker is now explicitly qualified; production retention authorization is unchanged. Final direct-Node unit rerun passes20 files/55 tests. Exact captured launcher/worker PIDs were verified absent; only the four verified acceptance containers were stopped and all are Exited, with volumes/state retained.

All three Node application images now built and inspected: worker (non-root/syntax), gateway (compiled endpoint/plane8 tests in network-none image) and UI (actual TypeScript/Vite build plus static assets/nginx artifact). Final Rust image remains in progress; deterministic artifact/sentinel/ELF checks are not yet claimed.

Root fresh rechecks: renderer5/5, Compose parsing1/1 and actual Caddy HTTP/parser2/2 PASS; the first Caddy rerun used a path one directory above its binary and failed to spawn, then the corrected verified bin/caddy.exe invocation passed. Architecture/mirror links/anchors and frozen baseline hash1/1 PASS. Kafka admin11/11, ClickHouse9/9/offline four assets PASS. New-project source text whitespace checked explicitly (25 Kafka/14 ClickHouse files) because ordinary git diff does not check untracked files; only EOF blanks/default LF attributes changed, no immutable migration SQL changed.

### Final Rust image gate closed

First release image completed. An owned harmless retired executable was seeded into the same BuildKit target cache. Final warm build using authoritative Cargo JSON compiler-artifact output completed with native exit0 and exported25 current allowed executables; the retired sentinel and intentionally unexported maintenance helper are absent. No forced dependency/binary relinks were used for this correction.

Final svc image is sha256:ecb431e3c2035b74df1ffc6d4046c56637d763e6e4b1095e3de852ff7de8612b. Root independently inspected all four exact organization-review-20261019 image tags and ran network-none ldd for bootstrap_organization, kabipay-organization and kabipay-auth: all runtime libraries resolve, exit0. These are build/artifact proofs, not application startup, browser, deployment, restore or retirement acceptance. All source implementation/review and scoped local validation tasks in this ownership phase are complete; the separate release and active legacy replacement gates remain open.
