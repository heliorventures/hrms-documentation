# Organization service execution ledger

Plan: `2026-10-18-organization-service.md`; implementation spans 2026-10-18/19 local time. Existing feature branches/current dirty work retained. User explicitly approved this phase and a focused independent security review; focused validation authorization persists. No commits, deployments, production migrations, Dart or Flutter commands.

## Rulings

- Ruling: first ownership uses an operator-run metadata bootstrap plus live source `role:manage` ALL proof, without a public bootstrap resolver. This avoids tenant HR self-claiming arbitrary organization ownership. Cost if wrong: onboarding needs a revised operator provisioning flow.
- Ruling: global principal login links are account-owned. Only the verified source account may revoke its own global link; organization administrators revoke organization bindings. Cost if wrong: platform identity recovery/reassignment needs a separately authorized protocol.
- Ruling: metadata-only roles may activate centrally; any role containing tenant business capabilities remains pending until future target installation. Cost if wrong: mixed metadata/business roles cannot yet administer the organization; use distinct roles.
- Ruling: configuration writes serialize on the organization row and require expected organization/resource versions. Editing one's own assigned role, self-granting, revoking one's own binding and suspending one's login company are denied to prevent accidental lockout/escalation. Cost if wrong: these changes need another authorized administrator or the later recovery process.
- Ruling: company suspension revokes that membership's grant scopes and never resumes them automatically. Reactivation/detachment require the later fenced lifecycle protocol. Cost if wrong: no self-service resume/detach is delivered in this phase.
- Ruling: configuration reads use bounded keyset pages of version-1 JSON documents, with typed GraphQL operation inputs/results. No UI/codegen contract is changed yet. Cost if wrong: future UI needs a compatible typed adapter or explicit document-version migration.

## Execution evidence so far

- Task 1 RED: organization endpoint configuration, live identity response and capability catalog tests initially failed (3 expected failures). Source account eligibility test also failed before guards.
- Task 1 GREEN: 3 organization unit tests and focused Auth eligibility test passed. Source identity endpoint verifies the real browser JWT, company binding, current tenant/account/password state and fresh RBAC; organization consumers hold a private verified identity and no company database credentials.
- Task 2 RED: disposable PostgreSQL baseline failed on absent `organization_outbox`; after migration it failed on unimplemented registration. Both fixtures cleaned up their containers.
- Task 2 GREEN: full disposable metadata-store scenario passed: verified tuple registration without name/email merging, bootstrap and occupied-company denial, unauthorized access, company acceptance, pending business grants, explicit delegation checks, stale versions, concurrent serialization, history count/rollback and suspended-company denial.
- Task 3 RED/GREEN: anonymous GraphQL business query initially returned an empty success; after resolver guards it was denied while introspection still succeeded.
- Task 3 RED/GREEN: gateway opt-in/header tests failed before implementation and all 7 focused tests passed afterward. Gateway TypeScript compilation passed. Windows sandbox denied Node child-process execution; approved elevated focused runs succeeded.
- Several Rust runs waited on concurrent Cargo work in the shared target directory. No user-owned process was stopped.
- The final evidence and review disposition below supersede the earlier pending-check snapshot.

## Review package boundaries

Read the phase plan, this ledger and only these relevant source areas: new `hrms-svc/crates/kabipay-organization`, `kabipay-auth/src/organization_identity.rs` and main route; new database migration 0113 and existing foundation 0111; gateway changed source/header/subgraph files. Previous company-binding and RSA crates are existing uncommitted prerequisite work, not new organization endpoints. Existing loan files are unrelated and must not be edited.

Infrastructure, browser JWT verification-only migration, account merging, tenant business grant acknowledgements/fences, approvals/hierarchy, UI, Kafka/CDC/ClickHouse and deployed/restore acceptance remain pending. Do not grade this phase as a deployed complete cross-company HR feature.

## Final review and fix pass

- Dedicated GPT 6.1 sol summariser compressed only the phase plan/ledger for an independent GPT 6 Astra reviewer. The reviewer inspected the named source package and relevant callers/schema in read-only mode; no broad repository/history context was supplied.
- Review identified one Important finding, **ORG-SEC-01**: bootstrap committed registration before its own occupancy/final-write transaction. No Critical findings or Minor findings were reported. The original review verdict was not ready to merge until this was resolved.
- Final: fixed ORG-SEC-01 - fresh eligible account in an occupied company reproduced RED: principal/link/event counts rose despite a failed bootstrap. Registration and bootstrap now share one transaction, with tenant -> account advisory lock -> principal/link ordering. Expanded disposable suite passed GREEN, including an injected failure at the final bootstrap outbox insert; principal/link/org/history counts remain unchanged on both failures. No second review was dispatched, per executing-plans workflow; regression evidence verifies the fix.
- New-crate strict Clippy initially identified an eight-argument event helper. Replaced separate aggregate coordinates with `EventSubject`; final `--no-deps -- -D warnings` passes without warning suppressions.
- Final: Ruling: central metadata capabilities are intentionally organization-wide; company scopes anchor eligible memberships, while tenant business authority retains target scopes. This is now explicit in the runbook and tested by scoped B metadata administration reading both companies. Cost if wrong: a narrower administration capability/target-scope policy is needed before granting those sensitive capabilities.
- Final: Ruling: invitations return IDs/versions to the inviter; delivery/discovery for pending-company accounts remains outside this backend phase. Cost if wrong: accepting administrators need details through the reviewed onboarding process until an invitation inbox exists.
- Final: Ruling: target payroll/leave authorization and grant installation/acknowledgement/fencing remain disabled/pending, rather than inferred from central rows. Cost if wrong: the feature cannot yet execute cross-company business actions.
- Final: Ruling: account merging, recovery and identity reassignment remain separate proof protocols. Cost if wrong: multiple company accounts remain separate principals and revoked links need an authorized recovery process.
- Final: Ruling: current outbox payloads are version-1 internal configuration facts, not a completed Kafka/CDC consumer contract or ClickHouse archive. Cost if wrong: external event/history parity and cleanup cannot be claimed.
- Final: Ruling: existing HMAC browser trust and deployed credentials/network controls remain explicit prerequisites. Cost if wrong: no service-compromise isolation claim is justified.
- Final: Ruling: migration/isolation/backup/restore/deployment acceptance is not established by disposable forward-SQL checks. Cost if wrong: release approval remains outstanding.
- Final: Ruling: browser/UI/actual gateway stitching was not exercised; the organization HTTP boundary was exercised with synthetic source Auth and PostgreSQL. Cost if wrong: end-user flow and live integration acceptance remain outstanding.
- Final: Ruling: the reviewer did not run tests; validation below was executed and inspected by the implementer. Cost if wrong: test coverage is not independent execution proof.
- Deferred minors: none reported by the independent reviewer. No automatic commit/merge/branch cleanup is authorized, so source and plan records remain for manual review.

## Final verification evidence

- Organization crate tests: 4 unit tests and 1 GraphQL boundary test pass. Disposable PostgreSQL test is deliberately ignored by ordinary Cargo runs and was run explicitly through its harness.
- Auth source identity tests: current eligibility and early wrong-company rejection pass, including real synthetic JWT verification before a disconnected database can be reached.
- `cargo check -p kabipay-auth -p kabipay-organization --all-targets --offline` passed after final runtime changes.
- `cargo clippy -p kabipay-organization --all-targets --no-deps --offline -- -D warnings` passed. This scopes linting to the new package; prior common-library findings were not rewritten or suppressed.
- Final `node scripts/test-organization-control.cjs --prepared` passed: registration/identity separation, occupied and late-failure bootstrap rollback, source consent, pending business grants, scope/delegation, role version/fence invalidation, stale/concurrent writes, configuration pagination, organization HTTP authorized reads/forged-header/substituted-source rejection, atomic history rollback, suspension and revoked-link denial. It uses synthetic source Auth, not a real deployed source Auth database chain.
- Gateway: all 15 tests across header, subgraph, client schema and loan schema ownership regression files passed; TypeScript `tsc --noEmit` passed.
- Database: 6 existing Liquibase SQL-block regression tests passed; new migration 0113 XML parsed. Only disposable forward SQL was executed.
- Tracked `git diff --check` passed across service, gateway, database and documentation. No dependency versions were upgraded; Cargo.lock adds only local organization packages across these phases.
- Final fresh combined `cargo test -p kabipay-organization -p kabipay-auth --offline`: 19 ordinary Rust tests passed (14 Auth and 5 organization), with the disposable test ignored there and passed separately through its harness. Final new-crate strict Clippy passed again.
- Final branch audit: all five repositories remain on `feat/organization-cross-company-management` at the recorded HEADs (service d7659aa, database 80fb0c7, gateway e70f601, documentation 1235403, UI 86a4801). UI is unchanged; existing unrelated loan changes remain. Read-only Docker check returned no `hrms-org-control-` containers. No existing database or production service was accessed.

## Delivered scope

The scoped organization metadata backend is implemented, with an [operator/developer runbook and diagrams](../../runbooks/organization-service.md). Existing tenant business flows, outbox/history readers and unrelated loan work are preserved. Full cross-company employee management and deployment remain incomplete until the remaining milestones above are implemented and accepted.
