# Organization runtime and delegated-command security

> Execute inline under the approved architecture and continuation request. Preserve all existing work; no commits, pushes, production migrations or deployments. Existing approval covers focused tests/checks.

**Goal:** Enforce an explicit company database binding in deployed runtime paths and supply a separate verifier for narrowly scoped internal commands.

**Spec:** [Architecture v5](../../architecture/2026-10-18-organization-cross-company-management.html).

## Decisions and boundaries

- Existing deployments remain compatible when no binding configuration is supplied. Cross-company feature deployments must use fixed bindings and restricted database/secret identities.
- `KABIPAY_BOUND_TENANT_ID`, `KABIPAY_BOUND_DATABASE_URL`, and `KABIPAY_BOUND_SCHEMA` form one startup configuration. Partial/blank/malformed configuration fails. Bound resolution never substitutes an ops-registry URL or derived schema.
- Public bound tenant GraphQL requests are checked before any database/entitlement lookup. They accept only an authenticated client of the bound company; operator and development-header identities cannot enter this runtime path. Database-bearing startup paths validate registry coordinates; scaffold services without database work still carry the identity guard.
- Central authentication remains a separate deployment concern. Its tenant cache also honors binding configuration; the ops service rejects company-binding configuration rather than pretending to be a tenant runtime.
- Delegation uses a dedicated issuer, RS256 public-key verification, explicit key IDs, exact service/company/action/resource/body/version/command matching and at most five minutes of validity. Browser JWTs are not delegation tokens.
- The verifier returns authenticated command attribution, not a local user or employee. A future command handler must still load current identity/grant/assignment state, apply resource/field scope and commit idempotently. No new command endpoint or token-issuing HTTP endpoint is enabled in this phase.
- Runtime code does not establish infrastructure isolation by itself. Real database roles, secret-store permissions, network controls and control-plane read privileges require deployment acceptance. Current entitlement reads still use the control plane; no claim that all fleet credentials have been removed.
- Existing browser JWT HMAC signing secrets are a separate production isolation prerequisite. This phase preserves that contract and records the need for verification-only browser trust distribution before production cross-company rollout.

## Task 1: Fixed company database resolution

Files: `kabipay-common/src/db/bound.rs`, `db.rs`, focused bound tests, `subgraph.rs`, `subgraph_bound_tests.rs`, auth/worker startup constructors.

- [x] Write failure tests for partial configuration, credential redaction, wrong tenant (including foreign cached handles), mapping coordinates and unauthenticated/operator boundary access. Additional URL-coordinate test observed RED before implementation.
- [x] Add an immutable binding to `TenantDbCache`; deny mismatched IDs before registry/cache work and use only startup-parsed connection options and the configured schema.
- [x] Initialize binding once at each existing production cache constructor; restrict outbox, Employee Finance and Payroll reconciliation worker discovery to its configured company. Scope attendance maintenance and tenant import too.
- [x] Preserve unbound resolver behavior and the existing client/operator JWT contracts.
- [x] Check common/auth/worker callers and existing focused regression tests. All 88 common unit tests and seven affected packages' all-target compilation checks passed.

## Task 2: Separate delegated-command cryptography

Files: new `kabipay-organization-security` crate, workspace membership, existing workspace dependency references, synthetic test-key fixtures and security tests.

- [x] Write tests for valid attribution, wrong issuer/audience/company/key/algorithm, expiration, future issuance, excessive lifetime, malformed IDs and altered command bodies/resources/versions.
- [x] Implement issuer/verifier primitives with separate RSA keys and fixed token type. Runtime verifiers hold only configured public keys; minting keys belong only to the future trusted organization issuer.
- [x] Keep authenticated context private/read-only after verification. Bind the exact body digest without embedding login tokens or sensitive request bodies.
- [x] Run focused Rust tests and Clippy with compilation, without upgrading existing dependencies. Nine security tests and warning-free Clippy passed.

## Task 3: Evidence and handoff

- [x] Add isolated database proof; fixed routing, startup mapping failures and restricted-role cross-database denial passed in disposable PostgreSQL 16. This does not establish deployed privileges.
- [x] Document startup variables, key rotation, dedicated identities, stale-policy denial, retries and the required future live authorization/idempotency adapter in `docs/runbooks/organization-runtime-security.md`.
- [x] Update progress with results and remaining service/API/UI/broker/history work.

## Scope completion

The code-level goals of this scoped plan are implemented. No command transport/endpoint, fresh-policy adapter, idempotent business transaction, production browser-key migration or deployed credential isolation is complete. These remain release prerequisites and are not implied by the tests above.
