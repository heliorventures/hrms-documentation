# Organization implementation progress

Plans: `2026-10-18-organization-foundation.md` and `2026-10-18-organization-runtime-security.md`.

- 2026-10-18: User approved architecture v5 and requested implementation from current branches.
- Created `feat/organization-cross-company-management` in all five repositories at the recorded source HEADs; existing database/documentation loan changes retained.
- User authorized focused migration tests and Rust compilation checks.
- Ruling: implement inline in the explicitly requested current checkouts/new branches; no additional worktrees, automatic commits, agents or production operations.
- Ruling: foundation is additive and grants no authority until trusted service/API adapters and lifecycle fencing are implemented.
- Pre-flight: domain identities/periods/capability names must match the additive SQL fields; no service currently consumes the new crate.
- Docker's local engine socket initially denied access. Approved elevated execution permitted only the synthetic disposable fixture; no live database fallback was used.
- Existing workspace build-directory lock was occupied. Stopped only this session's waiting Cargo process and used `target/organization-foundation`; no user-owned process was stopped.
- Source-approved architecture v5 is copied byte-for-byte into versioned `docs/architecture/2026-10-18-organization-cross-company-management.html` (SHA256 `BC1DB477E7C5930A9998EDFE9D6950AADFD9FDDC011970BA1575B982C91DD744`).
- Concurrent work: database HEAD advanced from the initial `fabf0cd` to `80fb0c7` (loan-role-scope commit) while this session was executing. This session ran no commit command and preserved the additional loan edits. Other recorded repository HEADs remain unchanged.
- Ruling: btree_gist is an explicit database prerequisite for concurrency-safe interval exclusion. Install/check through the tenant migration owner; keep the database-scoped extension on rollback because other schemas may depend on it.
- Ruling: event schema v1 encodes attribution in a tagged `actor` object supporting person/system actors. The earlier architecture actor-field example was conceptual; the versioned Rust header and runbook define the implementation contract.

## Task status

- Task 1: complete — validated domain contracts, explicit grant checks, iterative graph validation, canonical event headers. Eleven Rust tests, focused cargo check and Clippy passed.
- Task 2: complete — additive shared metadata SQL, no seed grants; tested against synthetic PostgreSQL 16.
- Task 3: complete — additive local actor/assignment SQL and tenant-bound FKs/exclusion constraint; eleven database scenarios passed, including concurrent conflicting writes.
- Full feature milestones: pending.

## Verification evidence

- RED: initial domain suite had eight expected assertion failures; existing serialization-shape test passed. Implemented guards then passed all nine initial tests; two additional source-binding/long-chain tests bring the final count to eleven.
- RED: disposable database `--baseline` intentionally failed because the pre-feature schema lacked `kabipay_ops.organization`.
- GREEN: `cargo test -p kabipay-organization-domain --offline --target-dir target/organization-foundation` — 11 passed.
- GREEN: `cargo check -p kabipay-organization-domain --offline --target-dir target/organization-foundation` — passed.
- GREEN: `cargo clippy -p kabipay-organization-domain --all-targets --offline --target-dir target/organization-foundation -- -D warnings` — passed.
- GREEN: `node tests/integration/organization/foundation.integration.cjs` — 11 PostgreSQL scenarios passed; test container removed by its own cleanup.
- GREEN: `node tests/unit/migrations/liquibase-sql-blocks.test.cjs` — 6 existing regression tests passed.
- Both new Liquibase XML files parsed successfully. SQL was executed directly from their forward blocks in the isolated fixture; a full Liquibase release/migration on an existing database was not run.
- At the end of the foundation slice, still pending: service identity linking/bootstrap, delegated authentication and tenant runtime isolation, real cross-company workflows, UI/gateway changes, Kafka/CDC/ClickHouse deployment, existing-data backfill, full migration rollback/restore and browser behavior. The runtime-security update below supersedes the primitive-level status only.
- No commits, pushes, deployment operations, production migrations, Dart/Flutter commands, infrastructure subscriptions or source-file deletions were performed by this session.

## Runtime-security phase - 2026-10-18

Continued on the existing feature branches after the user's next-phase request. Existing focused-test authorization remains in force. Implementation was inline; no agents, new branches, commits or production operations. Existing loan changes remain separate and intact.

### Implemented

- Immutable optional company binding in `kabipay-common`: three-variable complete configuration, safe URL/schema parsing, startup registry consistency, secret-redacted diagnostics, fixed connection options, wrong-company rejection before registry/cache/pool work and guarded cache reuse. Explicit connection coordinates prevent implicit host/user/database selection; URL query options are allowlisted before SQLx can log unknown parameters.
- Shared public GraphQL accepts only the bound company's authenticated clients. Operator/development-header/anonymous identities are denied there before entitlements or tenant DB reads. Existing active-account, entitlement and business authorization remain in place; unbound deployments retain their existing path.
- All production cache constructors use startup configuration. Outbox/Employee Finance/Payroll reconciliation enumerate only the bound company; attendance maintenance/import respect the same boundary. The ops service rejects a company binding. Removed an existing outbox-worker startup message that included the ops DSN.
- Separate `kabipay-organization-security` crate: RS256, configured public-key IDs, fixed issuer/type, exact service/company/capability/resource/version/command/body binding, bounded lifetime and a private verified context. Synthetic RSA test keys are explicitly documented as public test material. Existing dependency versions were reused; only two local package entries were added to the lockfile across both phases.
- Added `scripts/test-bound-runtime.ps1` and an opt-in ignored Rust fixture test, plus [runtime-security runbook](../../runbooks/organization-runtime-security.md) with diagrams, startup configuration, key rotation, retry/live-policy responsibilities and deployment prerequisites.

### Evidence

- RED: five initial common binding/identity assertions failed before guard implementation. The additional explicit URL-coordinate test also failed before stricter parsing. Initial security suite recorded six assertion failures before implementation.
- GREEN: `cargo test -p kabipay-common --lib --offline -- --test-threads=1` - 88 passed, including nine new binding/identity tests and existing account/scope/approval tests.
- GREEN: `cargo test -p kabipay-organization-security --offline --target-dir target/organization-foundation` - 9 passed.
- GREEN: `cargo clippy -p kabipay-organization-security --all-targets --offline --target-dir target/organization-foundation -- -D warnings` - passed.
- GREEN: `cargo check -p kabipay-auth -p kabipay-employee -p kabipay-notification -p kabipay-outbox-worker -p kabipay-tenant-import -p kabipay-payroll -p kabipay-attendance --all-targets --offline` - passed after final runtime changes. Existing leave dead-code/example warnings and the dependency future-compatibility notice remain.
- GREEN: `powershell -NoProfile -File scripts/test-bound-runtime.ps1 -Prepared` - final disposable PostgreSQL fixture passed. Fixed-pool marker, wrong-company denial, matching registry acceptance, mismatched/unsupported/inactive/duplicate registry denial and restricted-role cross-database CONNECT denial were exercised. The harness cleaned up its own container and restored its process variables; no existing company database or deployment `.env` was used.
- NOT CLEAN: `cargo clippy -p kabipay-common --lib --offline -- -D warnings` reports nine findings in unchanged `error.rs`, `middleware.rs`, `workflow_approval.rs` and `working_calendar/writes.rs`. No new phase file was identified by those diagnostics; no warning suppressions or unrelated rewrites were introduced.
- `git diff --check` passed for the service and documentation tracked changes. This is whitespace validation, not runtime/deployment proof.

### Remaining release requirements

The scoped code-level runtime/security primitives are complete. Organization service APIs/bootstrap, verified identity linking, fresh lifecycle/grant readers, private authenticated command routing, business authorization/idempotency receipts, cross-company workflows and UI remain pending. No new command endpoint or signing HTTP endpoint is exposed. Kafka/CDC/ClickHouse and migration/restore/browser/deployed-isolation acceptance remain pending.

Current browser JWTs still use a shared HMAC signing secret. Before claiming production service-compromise isolation, migrate browser trust so runtimes have verification-only keys, restrict control-plane/database/secret permissions, and validate network/TLS/routing controls. The synthetic restricted-role test establishes its fixture's privileges only. No outbox, tenant log/history records, existing delivery paths or database schemas were removed in this phase.

## Organization metadata service phase - 2026-10-18/19

The next scoped backend phase is implemented; see [its plan](2026-10-18-organization-service.md), [execution/review ledger](2026-10-18-organization-service-progress.md) and [runbook](../../runbooks/organization-service.md). It adds live source identity verification, operator bootstrap, organization/company configuration, explicit central roles/delegation, revocation, versioned transactional configuration facts and opt-in gateway routing. An independent security review found an atomic bootstrap composition issue; the regression reproduced it and the shared transaction fix passed disposable PostgreSQL checks.

This does not activate source-company approvals, target business grant acknowledgements/fences, UI, Kafka/CDC/ClickHouse or production deployment. Existing browser trust and deployment prerequisites still apply. No commits or production migrations were performed.
