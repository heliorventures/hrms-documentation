# Organization management foundation

The feature branch begins at the existing employee-loan branch in each repository. This first slice is additive: it supplies domain contracts and database structures; organization APIs, identity verification, delegated service authentication, cross-company workflow readers and UI are subsequent milestones.

## Added contracts

`hrms-svc/crates/kabipay-organization-domain` has no storage or transport dependency. It validates organization/company/person IDs, capability syntax, half-open effective periods, exact company grants and current accepted versions. Its hierarchy validator checks a consistent effective graph snapshot. The eventual writer must coordinate graph versions and validate future effective boundaries before activating assignments.

Grant inputs must come from trusted current policy and accepted target state. They are deliberately not deserializable user claims. The returned employee scope must still be applied to the resource and field policy, together with target workflow rules. A canonical event records attribution; it is not an access token.

Version 1 events use the named fields in `BusinessEventHeaderInput`, with an explicitly tagged `actor` object (`person` or `system`). Person actors retain principal, login company, authority reference and version; system actors retain a bounded service identity. Payloads remain typed per feature. The existing architecture's flattened actor illustration is conceptual; implementations and future consumers use this versioned Rust contract.

## Database rollout

- Ops migration `0111_organization_foundation` creates organization, verified-login, company-membership, employment-directory and explicit scoped-role structures in `kabipay_ops`. It seeds no companies or grants.
- Tenant migration `0112_company_management_foundation` creates local actor references, management assignments and assignment capabilities. It preserves `employee.reporting_manager_id` and existing authorization readers for a later controlled migration.
- `btree_gist` must be available and installable in each participating PostgreSQL database. The tenant migration installs it in `public` if absent and uses an exclusion constraint to prevent concurrent overlapping active primary-manager periods. Check provider/role support before a real migration; do not replace this constraint with a race-prone application-only lookup.
- Other-database principal/employment IDs remain logical references. The future service must verify organization membership, person identity, employment, capability support and a versioned global hierarchy. These migrations alone do not activate cross-company access.
- No log history, payroll data, existing workflow actions, outbox data or legacy columns are deleted. No tenant database credentials are added to organization services.

Use the existing reviewed ops/tenant deployment process only after the full migration release is approved. This runbook intentionally does not target an existing company database or issue production migration commands.

## Focused checks

From `hrms-svc`:

```powershell
cargo test -p kabipay-organization-domain --offline --target-dir target/organization-foundation
cargo check -p kabipay-organization-domain --offline --target-dir target/organization-foundation
cargo clippy -p kabipay-organization-domain --all-targets --offline --target-dir target/organization-foundation -- -D warnings
```

The separate target directory avoids contending with another developer's workspace compilation. Existing lockfile versions are reused.

From `hrms-database`, with Docker running and the already available `postgres:16-alpine` image:

```powershell
node tests/integration/organization/foundation.integration.cjs
```

The harness creates a uniquely named disposable PostgreSQL container, binds only to loopback, uses synthetic credentials/data, loads no `.env`, and removes only its own container. It executes the new migration SQL blocks, not the entire Liquibase release. It checks local constraints, cross-organization FKs, verification state, company isolation, period adjacency and concurrent overlapping writes. It does not establish broker, service, UI or deployed-database acceptance.

The optional `--baseline` switch intentionally skips migrations and must fail its first foundation assertion. It demonstrates that the synthetic pre-feature schema does not satisfy the test.

## Remaining work

The next implemented slice is documented in [company runtime and delegated-command security](organization-runtime-security.md). It adds optional fixed company binding and separate cryptographic primitives; it does not yet enable organization APIs or cross-company decisions.

Follow [the implementation plan and milestones](../superpowers/plans/2026-10-18-organization-foundation.md) and its progress ledger. Do not retire the current outbox worker, audit readers or generic history until the Kafka/CDC/ClickHouse pipeline, access controls, source history coverage and cleanup gates are implemented and verified.
