# Synthetic organization HTTP execution fixture

Owned scope: `hrms-svc/scripts/test-organization-execution.cjs` and this ledger. No production source edits, live company database access, commits, deployment, Dart or Flutter commands.

## Harness authored

- Uses disposable `postgres:16-alpine` with `--pull=never`, a random container name and loopback port. Creates three physically separate fixture databases: organization metadata, company A, company B. The source fixture binary refuses any other database names or a non-loopback host.
- Loads checked-in complete source and ops entity fixture schemas, then executes actual organization 0111–0117 SQL in their respective databases. This is SQL application in a generated baseline, not a full Liquibase upgrade.
- Starts real organization service and real fixed-company Auth/Employee/Leave routes. Keys are generated afresh per company, service and purpose; no private key or bearer value is logged. Bootstrap runs through the actual operator CLI.
- Seeds current Auth accounts and `role:manage` ALL scopes, employees, active module entitlement, one unpaid leave request with saved working date and reporting-manager workflow.
- Exercises identity registration, invitation/acceptance, membership source installation, both directory syncs, foreign PRIMARY relationship proposal/install, team, a seeded current inbox purpose projection, leave detail/decision, exact receipt replay, and stale/forged/inactive/revoked denials.
- The inbox projection insert is a declared seam: separate Kafka/CDC worker acceptance exists, but this HTTP fixture does not run that pipeline.

## Current execution status

`node --check hrms-svc/scripts/test-organization-execution.cjs` passed. Root built current organization service, bootstrap CLI and SDL; SDL confirms `Int!`, `UUID!`, `DateTime!`, and `OrganizationCommandInput!` used by the harness.

The refreshed source fixture binary produced an **exit 0 full base chain**: all generated schemas and actual 0111–0117 SQL, both real RSA Auth routes, bootstrap, invitation/acceptance, membership installs, both directory syncs, foreign PRIMARY manager install/team, seeded purpose projection, real unpaid leave detail/approval, exact receipt replay with one workflow action, and stale version/forged company/inactive actor/central principal revocation denials. A second exit 0 run added B suspend with source fence and command denial, resume with restored team, then terminal detach with retired source assignment, retained receipt and command denial. Every run removed its disposable container and generated key files.

An additional recovery regression was added after these passes. The harness clears B's central installation ACK fields and marks the exact command intent uncertain after a real successful source install, while preserving the source receipt. It then calls real `organizationCommandStatus`. Against the earlier source binary, this was **red as expected**: status returned `COMMITTED`, but central `installed_version` remained null (`status read must restore central ACK`, `0 !== 2`). The source implementer has authored a `ReadReceipt` re-ACK change and is rebuilding the fixture binary. This database mutation is an explicit synthetic lost-ACK seam; it does not simulate a real network outage. Recovery has no green claim yet.


Root refreshed rerun after source receipt reACK fix and current organization binary: node scripts/test-organization-execution.cjs EXIT0. Actual status read restored simulated lost membership ACK; complete base/lifecycle/denial chain passed again. Later CancelCommand recovery and performance lock changes still require fresh binary/rerun.


## Final root-owned expanded regression

Final fresh run76186 EXIT0 includes all prior cases and source-fenced cancellation (never delivered, no undo after commit, other actor denied, retained tombstone blocks late original, fresh command once, one cancel audit), unknown-install graph reservation, atomic manager replacement/reverse reports/cycle denial, principal revocation while company active, suspended-manager END/install and full lifecycle. R2-004 authority-change regression reproduced RED15164 and passed GREEN8306/final76186 after exact authority filtering; no repeated workflow action. Actual notification SQL extracted from the source also passed legacy/local/foreign/ended recipient assertions. Every fixture removed its own random PostgreSQL container/processes/generated keys.
