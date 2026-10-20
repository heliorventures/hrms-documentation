# Organization production hardening

User request: reassess the review comments, fix confirmed engineering issues, and prepare the existing live shared fleet for a controlled release. The user confirmed one ops registry and one shared fleet/VPS. Continue the current dirty feature worktrees; no commits, production connections, deployments or tenant migrations.

Goal: prevent accidental tenant omission at cutover and bound the source preparation migration without changing company isolation or weakening durable evidence.

Architecture: retain company-bound RSA Auth and source runtimes. A separate database operator queries the live registry read-only using an existing libpq service, compares ACTIVE and SUSPENDED companies and their subdomains with a rendered release, and emits a short-lived inventory receipt bound to checksums of every release artifact. The application release verifies the receipt and all checksums before starting services. This is operator evidence against mistakes, not an authorization credential. Provisioning and tenant status/subdomain changes must remain frozen between the query and cutover.

Review decisions:
- The existing 0115 rollback guard is intentional data protection. Do not remove it or synthesize local actors for foreign principals.
- Dirty worktrees and missing Git remotes are release provenance tasks, not runtime defects; the user owns commits and publishing.
- Existing-database rehearsal, real identity mapping, production TLS/ACLs, browser workflows, failover and off-host restore need deployment evidence. Local fixes cannot attest those results.
- Necessary migration locks remain explicit; target a bounded maintenance operation, not a zero-downtime claim.

## Task 1: bounded source upgrade

- [x] Add an actual PostgreSQL regression for lock contention, atomic failure, survey snapshots, and audit scan count.
- [x] Observe failures with the current 0125 SQL.
- [x] Set transaction-local five-second lock waits and sixty-second statement limits.
- [x] Replace per-survey audit subqueries with one windowed audit scan, preserving transition filtering, earliest opening, latest timestamp/UUID tie-break, empty history and tenant scope.
- [x] Run the upgrade fixture and existing private retirement regression in fresh owned containers.

## Task 2: shared fleet cutover guard

- [x] Add failing renderer/operator/release regressions for missing/suspended companies, subdomain mismatch, changed artifacts, expired/future receipts and no startup on rejection.
- [x] Include company bindings and a strict SHA256 artifact index in each rendered release.
- [x] Add the read-only operator inventory CLI under hrms-database/provisioning/organization using psql service/passfile configuration and verified TLS.
- [x] Validate the exact registry set and issue a fifteen-minute receipt without source credentials.
- [x] Enforce receipt, tag, artifact hashes and validity in release.sh before image loading/startup; supply the receipt through the deployment wrapper.
- [x] Run focused Node, PowerShell and native Bash checks; exercise the actual registry query in owned PostgreSQL where available.

## Task 3: evidence and release handoff

- [x] Correct stale policy-decision wording in both HTML mirrors while preserving the frozen baseline.
- [x] Document inventory generation, provisioning freeze, migration time bounds, rollback boundaries and remaining real-data acceptance.
- [x] Record current verification, review the final diff, and retain unperformed production gates explicitly.

Validation uses native executables and narrowly scoped local tests. No Dart/Flutter or RTK. No whole service build or broad repeated suite without a new reason.

## Verification evidence, 19-20 October 2026

- Before the migration correction, the new PostgreSQL regression failed three cases: fallback statement timeout instead of the intended lock timeout, absent local limits, and repeated audit scans. After correction, `node tests/integration/organization/source-upgrade.integration.cjs --docker-fixture` passed all five cases. The fifth also executes the actual registry SQL through native psql with the operator output flags and verifies valid JSON. Owned PostgreSQL containers were removed by the fixtures.
- `node tests/integration/organization/private-retirement.integration.cjs --docker-fixture`: 42 passed. This separately executes the complete preparation/retirement SQL; it does not rehearse real tenant data or a Liquibase release.
- Database `npm.cmd test`: 6 and 5 passed; `node --test tests/integration/organization/private-retirement.contract.test.cjs`: 4 passed.
- The new deployment regressions first demonstrated startup without inventory and then startup with a receipt expiring during preparation. Both now reject before startup. A legacy mode argument also fails closed.
- PowerShell `scripts/deploy/deploy.test.ps1`: passed with SSH/SCP mocked, including mandatory evidence before remote connection.
- Final combined documentation/deployment run: `node --test scripts/deploy/inventory.test.mjs scripts/deploy/render.test.mjs scripts/deploy/private-events.test.mjs scripts/deploy/document-links.test.mjs scripts/tests/deploy-env.test.cjs`: 43 passed, zero failed/skipped. Earlier fixture-only failures were corrected before this final run; they were temporary test-directory/checksum-format compatibility issues.
- Native Bash tests run through Git Bash on Windows. No real VPS Docker/Compose or application health proof is claimed.
- `git diff --check` returned zero in both repositories for tracked changes. Git emitted line-ending conversion notices; untracked feature files are not covered by that command. New JavaScript/Bash paths were exercised by the focused tests.
- A dedicated GPT 6.1 sol summariser prepared bounded context for an independent final source reviewer. That reviewer reported no confirmed additional source defect; the review ran no commands beyond source reads.
- Migration timeouts apply per statement/lock acquisition, not to total transaction elapsed time. The migration still needs a maintenance window and representative data rehearsal.
