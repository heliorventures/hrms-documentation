# ClickHouse ownership workstream

Scope: approved infrastructure ownership design, 2026-10-19. Owned `hrms-clickhouse/**` and five original ClickHouse resources. No commits, live migration, secrets inspection or existing-data moves.

## Implemented

- Canonical resources moved, with no forwarding/duplicate SQL: `clickhouse.sql` -> `migrations/0001-company-history.sql`; `control-history.sql` -> `migrations/0002-control-history.sql`; company/control grants -> `grants/0003-company-history.sql`, `0004-control-history.sql`; TLS configuration -> `config/clickhouse-config.xml`.
- Independent Node 22 CLI: `node scripts/migrate.mjs status|apply|validate`; `--include-grants` explicitly includes grant execution; `validate --offline` checks local assets only. HTTPS environment transport; credential headers; redirects reject; server error bodies omitted.
- Server-owned Atomic CREATE TABLE lock excludes other runners across hosts. Intent journal precedes SQL and completion follows synchronous server responses. SHA256 drift, unknown versions and unresolved intents reject execution. Failure/crash retains lock; no automatic expiration or destructive replay.
- Operator-only maintenance recovery documented: stop/fence runners, inspect requests/mutations and all statement effects, complete reconciliation, record verified applied state, then drop retained lock. No automatic recovery command guesses whether ambiguous SQL executed.
- Standalone private Compose installation requires explicit existing host storage/TLS paths and external network. Missing host storage paths fail; no automatic data relocation/new named volume/public ports. Existing monolithic service must stop before reviewed cutover.

## Decisions

- Ruling: retain existing feature checkout and no commits per approval; no skill-created worktree or commit commands.
- Ruling: conservative server lock remains after every execution ambiguity; DBA maintenance recovery avoids unsafe lease expiry/takeover. Cost: recovery needs exclusive operator maintenance.
- Ruling: OTel diagnostics retain the existing separate exporter/backend; do not invent a duplicate diagnostics store or business payload route.
- Ruling: initial baseline executes reviewed existing idempotent SQL once on an existing schema; production adoption still requires rehearsal and approval.

## Evidence

- `node hrms-clickhouse/test/migrate.test.mjs`: 7/7 pass. Covers lexical statement splitting, checksum/unknown-version rejection, unresolved intent, lock preservation after failure, release on success, concurrent lock rejection, grant opt-in, completed intent, transport restrictions and canonical asset versions/checksums.
- Initial red: direct test invocation failed missing core module before implementation. `node --test` itself failed child spawn EPERM in sandbox; direct invocation uses Node built-in test runner without spawning.
- `node hrms-clickhouse/scripts/migrate.mjs validate --offline`: passes all four canonical assets.
- `docker ps`: sandbox pipe Access denied. Root notified to coordinate disposable ClickHouse access. Actual synthetic database/Compose validation pending; no production proof claimed.

## Review

Security/DRY/SOLID self-review: SQL single owner, credentials excluded from assets, private network/TLS defaults, grants opt-in and existing privacy predicates preserved. CLI transport, SQL parsing/journal engine and version loading separated; no external package or source DB dependency. Migration DDL is nontransactional, so unresolved state is deliberately fail-closed. Production backup/failover, managed principal provisioning, baseline adoption and cutover remain operational acceptance gates.

## Final synthetic evidence

- Root started the existing disposable acceptance project; HTTP synthetic endpoint only. `apply` recorded 0001/0002 once; `status` and connected `validate` pass with lock false. Grant versions remain pending on the shared synthetic server because managed principals are absent; no synthetic users were silently provisioned there.
- `CLICKHOUSE_SYNTHETIC_TEST=1 node hrms-clickhouse/test/synthetic.mjs`: PASS against actual ClickHouse 25.8. Separate random test databases prove server lock exclusion, repeat apply no-op, drift rejection, failed intent and lock retention. Canonical company/control schema and all grants successfully execute with disposable managed roles; 11 schema objects verified. Only randomly named test resources cleaned.
- Actual server test exposed invalid original multi-table GRANT syntax. Fixed 0003 to grant each existing object separately, preserving exactly the same privilege scope. Regression went from real HTTP 400 to pass. This is the only semantic SQL correction during extraction.
- Node built-in unit tests re-run: 7/7 pass. Compose configuration rendered successfully with explicit synthetic placeholder variables using `docker compose ... config --quiet`; no server installation was run.
- Production deployment, existing-data baseline adoption, power-loss/failover recovery and managed principal provisioning remain NOT DEMONSTRATED.

## Review fixes and gateway/runtime follow-up

- Independent event workstream review identified unbounded ClickHouse response/deadline and fresh status behavior. Fixed configurable 120s deadline (100ms..1h), 4MiB streamed cap, and read-only fresh status reporting all pending. Unit regression suite now 8/8.
- Root delegated gateway fixed endpoint configuration: `KABIPAY_ORGANIZATION_SUBGRAPH_URL`, `KABIPAY_OPS_SUBGRAPH_URL` select full /graphql destinations by subgraph plane. Startup validates HTTP(S), no credentials/query/fragment and exact /graphql path before introspection; numeric port callers retain compatibility. Company subgraphs retain fixed deployment base. No request URL/tenant header selects these endpoints.
- Gateway `npm --prefix hrms-gateway run build`: pass. `npm test` could not spawn under sandbox; all compiled Node test files invoked directly: 17/17 pass across subgraph configuration, forwarded headers and schema contracts.
- Service Dockerfile exports `bootstrap_organization` explicitly and exposes 4031. Cached lock manifests show no proven Rust >1.89 requirement (67 uncached mostly target-specific packages); actual Linux image build running under existing 1.89 rather than speculative compiler change.
- Explicit shared outbound TLS helper `kabipay_common::organization_http` loads optional `KABIPAY_ORGANIZATION_HTTP_CA_FILE`, bounds regular-file read to 1MiB and 32 PEM roots, retains public roots, hostname verification, no redirects/proxies and original identity/execution/policy deadlines. Wired to identity, execution and tenant policy clients. Cached reqwest manifest proves `rustls-tls` selects webpki roots, not native SSL_CERT_FILE trust.

## Additional current evidence

- Tenant endpoint map `KABIPAY_SUBGRAPH_ENDPOINTS` added for known tenant service names only, with the same fixed full-URL validation. Gateway build and subgraph tests 7/7 pass (18 total gateway tests across the four compiled files including prior unchanged suites).
- Shared organization HTTP CA tests pass 2/2 via `cargo test -p kabipay-common --lib organization_http --locked`. The separate organization/tenant `cargo check` is queued behind an IDE workspace check, identified by read-only process inspection; no unrelated processes stopped.
- Docker uses `cargo build --locked`; compiler remains 1.89 because no incompatibility has been demonstrated. Actual Docker build is in progress, using the earlier source snapshot before shared CA helper changes; do not equate that image with final CA source validation.

- Final checksum portability review: SQL SHA256 normalizes CRLF to LF and `.gitattributes` pins source line endings, preventing false Windows/Linux Git checkout drift while still rejecting SQL changes. Baseline files already LF, so existing synthetic journal hashes remain valid. Unit suite 9/9; connected validate remains passing.

## Resource-bounded final checks

- Correction: the most recent connected ClickHouse validate after newline normalization timed out at its120s deadline during build contention; it did not establish a new pass. Earlier real synthetic proof remains recorded; latest revalidation pending.
- Root directed cancellation of only our original Docker exec build after several minutes without output and WSL ~4GiB working set. Ctrl-C ended that own build session; no daemon/other process stopped. No image completion claimed.
- Dockerfile now defaults `CARGO_BUILD_JOBS=1`, uses `--locked`, and caches registry/target with BuildKit locking in the same build-and-export RUN so retried builds preserve compilation work while only binaries enter output. Retrying final source snapshot including shared CA helper with one job. Separate Rust check still waits on IDE target lock.

- Final jobs1 image retry failed before build at Docker Engine `_ping` with HTTP500. No daemon restart/container stop performed. Final service image completion remains NOT DEMONSTRATED. Scoped Rust source check acquired IDE-released target lock and is now compiling final common/organization code.

- Final scoped `cargo check -p kabipay-organization -p kabipay-organization-tenant --locked`: PASS. Total18m includes waiting for IDE target lock; final common/organization/tenant sources compile. Existing proc-macro-error2 future-compat warning remains unrelated.
- Independent gateway review found partial fixed tenant maps could fall back to a shared legacy base. Now any supplied `KABIPAY_SUBGRAPH_ENDPOINTS` must contain every known tenant service; absent map preserves old deployment compatibility. Empty/incomplete maps reject at startup. Root full generated maps remain compatible.

## Final handoff

- Final-source `cargo test -p kabipay-common --lib organization_http --locked`: PASS2/2 after absolute CA-path validation. Final organization/tenant source check PASS. Gateway final endpoint build/test PASS7/7; unchanged other compiled suites11/11, total18.
- ClickHouse final local suite9/9 and offline validation pass. Real CH schema/grant/concurrency/replay/failure checks passed before Docker resource failure; later connected revalidate timed out, so no final live-server refresh claim.
- No active tool build/check sessions remain. Original own Docker build canceled at root instruction; jobs1 final retry failed Engine_ping500. Service final image build and private CA TLS handshake remain NOT DEMONSTRATED. No daemon restart, live deployment, remote repo creation, commit or existing business-data deletion.

## Auth/gateway plane boundary follow-up

- Root delegated fixed deployment plane enforcement. `KABIPAY_AUTH_PLANE=all|ops|client` parses before DB startup (absent defaults all). Auth group selection retains health always, ops-only excludes entire client group including introspection/identity and internal account/employment eligibility, client-only excludes all ops routes. Existing metrics/CORS/service-verifier layers remain after route selection.
- Ops-only Auth skips client signing configuration validation; no company private signer is required. Client-only Auth must not receive global ops HMAC secrets (root renderer notified); RS256 private keys remain company-local.
- `KABIPAY_GATEWAY_PLANE=all|ops` validates at startup, ops selects only ops subgraph and rejects organization enable. Gateway build/subgraph tests8/8 PASS. Pure Auth enum/router tests added without DB/secrets; test execution currently queues behind IDE workspace target lock. No Docker use.

- Ops gateway startup contract reviewed: production client-schema completeness is now applied only when tenant subgraphs are configured. Ops-only still validates ops subgraph availability and ownership rules; it no longer incorrectly requires employee/payroll/client fields.
- Added actual private-CA Rust client handshake fixture: Git OpenSSL generates unique ephemeral CA/server material; local Node HTTPS server proves matching supplied CA success, unrelated CA rejection and hostname mismatch rejection. Uses the production client helper path directly without mutating process env; cleanup guards stop server/remove only own temporary directory even on assertion failure. Execution pending Auth test/IDE Cargo lock.

- `cargo test -p kabipay-auth --lib plane::tests --locked`: PASS2/2. Pure enum validation and in-memory Router selection prove ops/client exclusions (including introspection/internal eligibility representative routes) and health preservation without DB. Total14m38 includes IDE workspace lock wait. Native CA3-test run now active.

## Final native TLS / plane test evidence

- `cargo test -p kabipay-common --lib organization_http --locked`: PASS3/3, including actual HTTPS handshake using native Git mingw64 OpenSSL3.2.4 and ephemeral Node server. Explicit fixture CA succeeds; unrelated CA and mismatched127.0.0.1 hostname reject. No process environment mutation, DB access, Docker or production secrets. Temporary native fixtures cleaned.
- Auth route-selection tests2/2 PASS and latest gateway build/configuration8/8 PASS. Final `cargo check -p kabipay-auth --locked` active for binary startup/route wiring.

- Final `cargo check -p kabipay-auth --locked`: PASS (46.81s), including binary startup/route grouping. Native fixture directory inventory returned0 remaining `organization-tls-*` directories. No active owned checks remain.
- Follow-up review: plane values are startup-only, never request-controlled; default all preserves legacy behavior. Group selection removes handlers rather than relying on proxy filtering. Ops-only excludes client/introspection/internal endpoints and client-only excludes ops; health/metrics/service-verifier layering preserved. Gateway ops mode cannot enable organization or require tenant schema. No automatic legacy worker retirement performed.

## Final image proof retry after authorized Docker recovery

- Root explicitly authorized local Docker restart and recovered Engine28.3.2. All six owned synthetic containers verified stopped by root; current Rust build tag `kabipay-svc:organization-review-20261019`, jobs1, --locked, actual release optimization unchanged. Raw logs ignored by *.log.
- Read-only health during quiet thin-LTO stage: rustc CPU49s/elapsed50s, RSS450MiB; WSL working set~1895MiB, VM7.6GiB/available6.3GiB, swap essentially unused. Active compilation, no demonstrated stall/resource failure.
- Ruling: do not delete all current cached binaries and force expensive relinks. Builder-only jq consumes checked Cargo JSON compiler-artifact bin executables, validates exact /app/target/release directory and allowed names, copies only current emitted artifacts, asserts bootstrap/organization/Auth. This rejects stale/retired target-cache binaries without discarding valid build work. Production Dockerfile updated; verification rebuild pending.
- Owned harmless stale executable fixture prepared under ignored `.codex-tmp/image-cache-review-20261019`; seed only after first success, then prove metadata-export final image excludes it. Root currently holds new Rust/heavy UI builds until capped TLS acceptance completes; existing current build continues, small inspection/preparation only.

## Fresh connected ClickHouse proof after recovery

- Verified exact full container f3a9bd6a976fb3254f38604de60798c9792a9e02a5bfb16ee68c0d08da7ee2f2, projectorg-pipeline-accept-20261019/serviceclickhouse, initiallyExited/no memory cap. Root authorized window: capped only it768MiB/no extra swap and started only this container. Running/notOOM; no other acceptance containers started by this workstream.
- Fresh journal reported allpending. Canonical schema apply0001/0002 PASS; repeatapply returnedempty; connectedvalidate PASS with lockfalse and grants0003/0004pending until separately managed principals exist.
- Fresh actual server `test/synthetic.mjs` PASS: concurrent exclusion, repeatapply no-op, checksum drift, failure lock/intent, 11 canonical schema objects/all grants with isolated roles, actual100ms HTTP timeout retaining intent/lock/rejecting replay, and total streamed response cap4MiB.
- Root-cause fixture correction: a single repeat4194305 hit verified serverCode131 TOO_LARGE_STRING_SIZE (maxrepeats1,000,000), not client cap. Changed fixture to4097 rows of1KiB; actual cap check then PASS without increasing server limits.
- Cleanup queries show0 remaining owned-prefix test databases and0 test roles. CH remains running768MiB for Eventfixtures; root/Event notified exclusiveDDL window released. This refresh supersedes earlier timeout/unavailable historical state for this scoped synthetic proof only.

## Actual Node image artifacts

- Worker `kabipay-organization-events:organization-review-20261019` built/exported; inspectedIDsha256:f6cae358081753a3eef254c08d3a5dc687328e6d69c7fedd3a47d82aa6deac9f, runtimeusernode. Network-none container `node --check src/worker.mjs` PASS, no worker/app started.
- Gateway `kabipay-gateway:organization-review-20261019` built/exported; inspectedIDsha256:e537f9acdffb5a45eb491a711d6b13ee83b806f2ec9be8aec88f1004f85591f8. Compiled subgraph endpoint/plane suite insideimage/networknone PASS8/8.
- Windows PowerShell5 turns Docker normal progress stderr into NativeCommandError and wrapperexit1 despite successful image export; independent imageinspection/probes verified actual artifacts. Subsequent redirected builds explicitly exit Docker nativeLASTEXITCODE to preserve result. No app secrets or DB connections involved.
- UI actual image build now active serially after worker/gateway; root released Nodebuild resource window beside original Rustjobs1 compile. No second Rust build started.

- UI `kabipay-ui:organization-review-20261019` actualDocker build nativeexit0 (tsc+Vite PASS), imageIDsha256:6ccb2f20720e6d8ef813e49e476ba458549704850f91077b3128547776715ecf. Network-none probe confirms nonempty index.html, assetsdirectory and nginx1.27.5 executable; no server/browser flow started. All Node image builds idle, Rustfirstbuild remainsactive.

## Final actual Rust image / cache regression / ELF evidence

- First real Rust1.89 release workspace build completed/exported (including source libraries and maintenance targets); image inspectedsha256:c1f9cdf8109d29d0e4981e493532e05298eb3277d1728c5face7dc2d4d058d9d. Required bootstrap/organization/Auth executable probePASS. No speculative compiler upgrade/profile relaxation.
- Owned ignored cache fixture build succeeded against exact default BuildKit `/app/target` cache: asserted current bootstrap/organization existed, then wrote harmless executable `kabipay-retired-cache-fixture`. No existing business data/containers changed.
- Final warm-cache metadata export build nativeexit0. Builder-only jq filters current Cargo compiler-artifact bin targets by expected names, validates exact release paths, copies only emitted executables, and asserts required outputs. No deletion/forced relink of valid cached outputs.
- FINAL service image `kabipay-svc:organization-review-20261019` IDsha256:ecb431e3c2035b74df1ffc6d4046c56637d763e6e4b1095e3de852ff7de8612b. Network-none probesPASS: required bootstrap/org/Auth/ops/employee/payroll executable; seeded stale executable and intentionally excluded maintenance helper absent.25current allowed executables inventoried; existing current outbox worker remains intentionally packaged for supported legacy workflow, with no automatic retirement.
- Final runtime `ldd` bootstrap_organization/kabipay-organization/kabipay-auth PASS, all loader/libgcc/libm/libc resolved, no missing libraries. No app startup/fakeCLIhelp, DB connection, secrets mount, upload, VPS operation, commit or live deployment.
- All four actual image artifacts now built/inspected (Rust, Node events worker, gateway, UI). All owned build/probe sessions finished; root notified completion. Earlier image/Engine NOT DEMONSTRATED entries describe historical failed attempts and are superseded by this final artifact proof; production runtime/cutover acceptance remains separate.

- Final cleanup nativeexit0: same BuildKit target cache tiny fixture removed ONLY `/app/target/release/kabipay-retired-cache-fixture`, asserted absence and retained current bootstrap/organization executables. No cache prune, dependency/incremental deletion or other branch artifact removal. Final metadata build reused current compilation (`Finished release` in1.57s), confirming no forced relink. Final image metadata exposes4031 alongside existing service ports; no host port published by probes.
- Owned helper/build/probe processes are complete; no application/server started by artifact inspection. Synthetic runtime container lifecycle remains with root/Event acceptance owners; no daemon or unrelated process stopped.
