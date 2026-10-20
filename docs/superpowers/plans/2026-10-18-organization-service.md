# Organization metadata service implementation plan

> Execute with the executing-plans skill, inline in the existing feature branches. The user approved this phase and a focused independent security review. Preserve unrelated work; no commits, deployments or existing-database migrations.

**Goal:** Provide a separately deployed organization GraphQL control plane with verified source identities, configurable company membership and roles, immediate central revocation and durable configuration-event handoff.

**Architecture:** The organization service opens only its explicitly configured metadata database. For each authenticated request it calls a configured, trusted source Auth identity endpoint; it receives current account/tenant eligibility and permissions, never company database credentials. Central administration uses live verified principal links and explicit organization capabilities. Tenant business grants remain pending for the later installation protocol.

**Stack:** Existing Rust/Axum/async-graphql/SeaORM/reqwest, PostgreSQL and the existing TypeScript stitching gateway. Reuse locked dependencies.

**Spec:** `docs/architecture/2026-10-18-organization-cross-company-management.html`.

## Decisions and release boundaries

- Source account tuples are linked only after live source verification. First registration creates one principal per verified account. Account merging, employment verification/backfill and identity-reassignment are separate security protocols; matching email never merges people.
- Global login revocation is self-service by the verified source account; organization administrators may revoke their organization's bindings, not another person's global identity in unrelated organizations.
- Initial organization/company ownership is established by an operator-run bootstrap command using a currently verified source account with `role:manage` at `ALL` scope. The command requires a dedicated metadata DB identity and is not an HTTP self-enrollment endpoint.
- Organization administrators have explicit central `organization:manage` and `organization:delegate` capabilities. These permit metadata administration/delegation, not payroll/employee operations. Ordinary company HR permissions never confer organization administration.
- Companies join through PENDING invitation and acceptance by a current source-company account with local `role:manage` at `ALL` scope. A central administrator cannot activate an arbitrary company's membership without its consent. Suspension is immediate centrally; detachment remains a later fenced drain protocol.
- Roles are configurable subsets of a supported capability catalog. Central metadata capabilities apply centrally. Roles containing tenant business capabilities create PENDING company grant scopes; no invented target acknowledgement activates them. Role changes/revocation increment versions and revoke/invalidate affected scope records atomically.
- Configuration changes write a small transactional organization outbox. No generic database history/retry archive or premature cleanup is introduced. Kafka/CDC consumers are a later phase.
- Public schemas remain introspectable; every business resolver requires source-verified identity and current policy. The gateway exposes the new subgraph only when explicitly enabled; current fleets remain unchanged.
- The existing browser HMAC trust distribution is still a production prerequisite. No claim of service-compromise isolation or production deployment acceptance follows from this phase.

## Review focus

1. Forged company/actor headers, substituted identities, redirects and expired/disabled source accounts must never produce verified organization authority.
2. Ordinary HR, foreign organizations, suspended source membership and revoked principal links must fail closed even with previously valid browser tokens.
3. Concurrent invitations, acceptance and administrative edits must serialize; stale versions fail without partial changes/outbox writes.
4. Metadata administration must not activate unacknowledged payroll/leave grants or silently broaden company scope.
5. Every successful mutation must commit its configuration event atomically; failed validation/authorization must leave state unchanged.

## Task 1 - Source identity boundary

Files: `kabipay-auth/src/organization_identity.rs`, Auth main wiring; new `kabipay-organization/{Cargo.toml,src/lib.rs,src/identity.rs,tests/identity.rs}`; workspace membership.

- [x] Write RED tests for endpoint configuration, successful verified identity and account eligibility; expand nonce/company/issuer/user substitution, denial, redirect, oversize, no-cache and early wrong-company coverage.
- [x] Add POST `/auth/client/organization-identity` with real JWT/binding/current account and RBAC checks, limited response and no-store headers.
- [x] Implement private verified source identity and allowlisted HTTPS client with loopback test exception, bounded transport and no caching.
- [x] Run focused Rust tests/checks.

## Task 2 - Transactional organization metadata

Files: `kabipay-organization/src/{store.rs,policy.rs,models.rs,bootstrap.rs}`, focused service integration fixture/tests; additive migration `0113_organization_control_outbox` and ops master include.

- [x] Execute disposable PostgreSQL RED/GREEN and expanded regression scenarios.
- [x] Add current identity/organization/member guards, serialized optimistic administration and atomic bootstrap (ORG-SEC-01 regression fixed).
- [x] Implement registration, paginated configuration reads, consent/suspension, configurable capabilities, scoped binding/delegation/revocation and self-owned verified-link revocation.
- [x] Keep tenant business grants pending; invalidate versions on role/scope changes without reviving revoked scopes.
- [x] Commit configuration facts atomically and verify injected outbox failures roll back all associated state.

## Task 3 - Service and gateway

Files: `kabipay-organization/src/{graphql.rs,main.rs,bin/bootstrap_organization.rs}`, gateway subgraph/header configuration and focused tests; runbook/progress.

- [x] Add protected GraphQL and test discovery/anonymous denial plus actual synthetic organization HTTP boundary.
- [x] Add explicit-only metadata startup and operator bootstrap CLI; no shared dotenv/tenant credentials fallback.
- [x] Add opt-in gateway integration; 15 gateway tests and TypeScript check pass.
- [x] Finish focused validation/runbook and independent Astra review after GPT 6.1 sol summarisation; fix the Important finding with RED/GREEN evidence. No commits.

## Completion boundary

This phase supplies the organization control plane. Target-company grant installation/fences, hierarchy/approval adapters, account merging, UI, Kafka/CDC/ClickHouse transport, full tenant-detachment and deployed security acceptance remain subsequent milestones.
