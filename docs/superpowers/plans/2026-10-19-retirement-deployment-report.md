# Retirement deployment evidence — 2026-10-19

Scope: approved local source/documentation changes and focused synthetic checks. No commit, live VPS connection, production migration, application rollout or historical data deletion.

## Changes

- The deployment environment contract now documents the organization-only manifest, bound maintenance service, private audit/delivery/operator workers, purpose-separated history servers, exact secret/config mounts, JSON file formats, Kafka principal/group boundaries and ClickHouse roles.
- Source adapter endpoints are fixed HTTPS: mTLS delivery/ownership on8450 and Finance Payroll/Employee on8451/8452. Source and history client/server certificate trust and proof keys are documented separately from encryption/webhook credentials.
- Deployment/runbook text replaces obsolete legacy-mode/source-outbox-worker instructions with reviewed source ownership/export/restore/reader handoff gates, retained rollback artifacts and the separately authorized organization bootstrap CLI.
- The renderer removes duplicate ops Auth/subgraph initialization and unreachable organization-only branches. Existing service identities, mount/network boundaries, public/private route artifacts and the compatibility-named operator Caddy fragment are retained.
- Finance reconciliation fixtures use HTTPS positive origins (including IPv6), preserve literal/secret/redaction negatives, and reject HTTP for either Finance origin without modifying the source file.

## Focused verification

Native PowerShell mock-SSH orchestration passed: render-only does not contact a remote; deployment uploads only the artifact inventory; stale env files are excluded; app release is separate from Caddy/SQL; deprecated combined switches and injected SSH selectors are rejected.

Focused native Node command:

```powershell
$env:CADDY_BINARY='D:/work/heliorventures/.codex-tmp/caddy-2.10.2/bin/caddy.exe'
node --test scripts/tests/deploy-env.test.cjs scripts/deploy/render.test.mjs scripts/deploy/private-events.test.mjs scripts/deploy/compose.test.mjs scripts/deploy/caddy.test.mjs
& scripts/deploy/deploy.test.ps1
```

The Node suite completed 34/35 passing, with one Git Bash subprocess `ETIMEDOUT` in the existing unquoted-whitespace fixture. Its isolated rerun passed 1/1 in 23.2 seconds using `node --test --test-name-pattern='unquoted leading whitespace' scripts/tests/deploy-env.test.cjs`; there was no configuration assertion failure or timeout-related code change. All other reconciliation/literal/secret/redaction cases, both HTTPS-to-HTTP negatives, renderer/private topology cases, actual Caddy loopback denials/generated parser adaptations and Compose CLI parsing passed. Initial sandbox execution could not spawn child processes (`EPERM`); the authorized rerun used temporary fixtures and local Caddy only. No remote deployment was exercised.

`git diff --check` on the owned deployment/docs/tests returned no whitespace errors. The earlier document-links check identified the canonical HTML's old link to removed `kabipay-outbox-worker/src/main.rs`; its owner corrected the canonical document, and the final focused routing/link suite passed below.

## Opt-in real private HTTPS/mTLS acceptance

Added `hrms-svc/integrations/organization-events/test/private-https.integration.mjs`. It imports the production `SourceDeliveryClient`, `DeliveryCoordinator`, ownership proof routines, `PrivateHistoryQuery` and `privateHistoryHandler`. A freshly generated synthetic server CA, separate client CA, unrelated CA and client/server certificates are used by ephemeral HTTPS servers bound only to 127.0.0.1. Docker runs cached `postgres:16` solely for OpenSSL through `--entrypoint sh`, `--network none`, `--pull=never`, a read-only container root and the fresh temporary PKI bind; no PostgreSQL server is started. The originally suggested Rust base tag was not cached; no image was pulled. All fixture servers, sockets, the unique temporary container and the checked direct temporary-directory child are cleaned up.

```powershell
cd D:/work/heliorventures/hrms-svc/integrations/organization-events
node test/private-https.integration.mjs --docker-fixture
```

Result: **6/6 passed** (parent plus five subtests), no failures/skips, 17.4 seconds on the final rerun (initial run also passed in 5.6 seconds). Missing/untrusted client certificates, wrong server CA and wrong server hostname were rejected before the fixture HTTP handler. Real HTTPS exercised source signing/reference/status negatives and fixed-path 404s; acknowledgement loss preserved the same lease and did not repeat the simulated receiver send; uncertainty went to DLQ and safe retry advanced its lease. Ownership kept exact decimal offsets `9223372036854775800`/`9223372036854775801` and retained the first authenticated receipt on duplicate publication. Actual HTTPS history requests verified response proof/hash/raw bytes, tenant/purpose/generation/replay negatives, coverage-unavailable 503 and private-route 404. Default invocation without `--docker-fixture` skips the test and does not run Docker or start servers.

This is **real native TLS transport with synthetic source/receiver state and history coverage storage**. It is not actual Rust adapter/receiver execution, PostgreSQL persistence or Kafka/ClickHouse lifecycle acceptance. Those separate acceptance fixtures and production certificate/ACL/restore gates remain distinct. No production implementation file was modified for this test.

## Final retired-worker orphan guard

Root audit identified that the old guard recognized only the global worker service label/name. Earlier company-bound releases used `outbox-<slug>` service labels; `compose up` leaves these running as orphans. A Docker-mock regression first reproduced the gap: an owned company container with absolute `kabipay-outbox-worker` command reached application startup and failed the expected-rejection fixture (exit 57).

`release.sh` now inventories all running containers in the owned `apps` Compose project and inspects both effective `Config.Entrypoint` and `Config.Cmd`, including absolute paths and shell command strings. A retired executable match blocks rollout. The old global service label and exact old global name outside the project are also checked; Docker listing/inspection failures block rollout. Inspected arguments and Docker failure details are never printed, and the guard never stops/removes a container.

Focused native command: `node --test --test-name-pattern='release blocks|inventories every running owned command' scripts/tests/deploy-env.test.cjs`. The final run passed **3/3**, covering old service label/name, renamed bound absolute command, shell launch, entrypoint, inventory/inspect failure, maintenance allowed, unrelated project excluded, no startup on rejection, no automatic stop/remove/kill and synthetic argument-secret redaction. The stronger mock returns command/entrypoint values only when the corresponding Docker template field is actually requested. This is local executable shell/mock evidence, not a production worker inventory or handoff.

## Final global operator route cleanup

A focused renderer regression reproduced obsolete company Employee/Notification upstreams on the global ops entry point, even though that subgraph container now runs only ops. `publicRoutes` now requires an explicit validated `ops` or `company` plane and shares the same private-deny/Auth/GraphQL/health/UI grammar. Ops adds explicit prejoining/employee-document/announcement-video 404s and contains no 4013/4028 upstream; company route generation retains its existing handlers. The compatibility-named `legacy-routes.caddy` artifact now contains only the operator routes and company-path denials.

With `$env:CADDY_BINARY` set to `D:/work/heliorventures/.codex-tmp/caddy-2.10.2/bin/caddy.exe` in PowerShell, final command: `node --test scripts/deploy/render.test.mjs scripts/deploy/private-events.test.mjs scripts/deploy/caddy.test.mjs scripts/deploy/document-links.test.mjs`. Result: **13/13 passed**, no failures/skips. Actual native Caddy returned 404 for ops company paths without incrementing a synthetic upstream hit counter; company paths and allowed Auth/GraphQL/health/UI returned 200. All generated private/root Caddy files adapted with the real parser; plane negatives, fixed private topology and canonical document links passed. No Rust or production operation was performed.

## Acceptance limits

Compose parsing does not start application services. The real Caddy loopback fixture verifies private-path denial against a synthetic upstream; parser adaptation validates generated private Caddy syntax. These checks do not demonstrate production certificates/ACLs, real source delivery, existing-data migration, complete application startup, browser behavior, production retirement or restore acceptance. Windows Git Bash/NTFS does not prove Unix 0600 modes; tests retain source assertions for explicit `umask`/`chmod` and execute mode checks on POSIX.
