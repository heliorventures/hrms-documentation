# Organization management foundation implementation plan

> **For agentic workers:** Use `superpowers:executing-plans` inline. The user approved architecture v5 and explicitly requested implementation on a new branch. Do not commit, push, deploy, or run Dart/Flutter commands.

**Goal:** Establish tested organization identity, explicit company grants, primary-reporting graph rules, and additive database foundations without enabling an incomplete authorization path.

**Architecture:** Company databases remain independent. Shared metadata owns principals and scoped organization grants; employee companies own management assignments and final decisions. Canonical business events use an atomic temporary outbox, CDC/Kafka delivery, and external retained history. Infrastructure and user-facing flows follow in subsequent milestones.

**Tech stack:** Rust 2021, existing workspace serde/chrono/uuid/thiserror versions, PostgreSQL, Liquibase. No new runtime dependencies for this slice.

**Spec:** [Approved architecture v5](../../architecture/2026-10-18-organization-cross-company-management.html).

## Global constraints

- Branch `feat/organization-cross-company-management` starts at each repository's existing `feat/employee-loan-management` HEAD; preserve unrelated working changes.
- Separate company databases, company-owned decisions, no cross-database SQL foreign keys or arbitrary organization-service tenant credentials.
- No tenant-name conditions, implicit organization access, automatic account linking, automatic payroll authority, or default broad company scope.
- Keep a bounded transactional outbox and compact duplicate-execution state; retire obsolete logging/polling only after migration gates.
- Explicit user approval covers focused tests and Rust compilation checks. Do not run production migrations, install infrastructure, start user-owned services, commit or push.
- Use native commands; no RTK, Dart or Flutter.

## Branch baseline

| Repository | Source HEAD | Pre-existing working changes |
| --- | --- | --- |
| hrms-svc | d7659aa018013220d5d0251d75393bf2921bf331 | None |
| hrms-database | fabf0cd0fa2dc9ef80b8a7e5239f21fa38886155 | README, tenant master, package scripts, RBAC tests, migration 0110 and loan-scope fixtures |
| hrms-gateway | e70f6017eade8487176c4b95bd6f890d05434ad9 | None |
| hrms-ui | 86a48019b3ad1cf5bb55161bf0d050ac3a94db67 | None |
| hrms-documentation | 1235403f8f897302c2dbacfb6823686fc5f42e06 | docs/runbooks/employee-loans.md |

## Review focus

1. Nil IDs, unsupported or malformed capabilities, invalid periods and zero/overflowing source versions must fail at parsing boundaries.
2. Same company membership does not imply employee access; missing/expired grants, wrong principals/companies, and stale accepted versions deny authority.
3. Company directions can alternate along a hierarchy; primary cycles and overlapping primary managers remain invalid, including self-reporting across two employments.
4. Source-company identity, actor attribution and immutable event identity must survive serialization without creating an authorization credential.
5. SQL constraints must reject cross-organization role scopes and overlapping primary periods, while additive migrations preserve existing local HR, loans and workflows.

## Task 1: Pure organization domain contracts

**Files:** Create `hrms-svc/crates/kabipay-organization-domain/{Cargo.toml,src/lib.rs,src/identity.rs,src/access.rs,src/hierarchy.rs,src/event.rs,tests/foundation.rs}`; modify workspace `Cargo.toml` and generated `Cargo.lock`.

**Interfaces:** Validated ID newtypes; `Capability::parse`; `EffectivePeriod::new`; explicit `CompanyGrant::authorize` using current trusted security state; `validate_primary_reporting_graph` for a consistent effective graph snapshot; validated `BusinessEventHeader` and serializable typed `BusinessEvent<P>`.

- [x] Write focused tests first for the five review classes and observe failures.
- [x] Implement fail-closed parsing, exact company/capability matching, version fences and graph validation in small focused modules.
- [x] Run focused crate tests/checks using `--target-dir target/organization-foundation`; 11 tests, check and warning-free Clippy passed.
- [x] Verify malformed serialized inputs cannot bypass constructors. The crate accepts trusted policy snapshots, not browser-provided assertions of authority.

## Task 2: Shared organization metadata migration

**Files:** Create `hrms-database/changelog/migrations/0111_organization_foundation/organization_foundation.xml`; modify ops `changelog/db.changelog-master.xml`.

**Interfaces:** `kabipay_ops.organization`, `principal`, `principal_login_link`, `organization_company`, `employment_ref`, organization role/capability/binding/company-scope tables. All remote employee/account references remain logical; local composite FKs enforce organization boundaries.

- [x] Add only new tables, checks and indexes. Seed no organizations, linked accounts or broad HR grants.
- [x] Enforce verified-login state, positive versions, valid effective periods, one occupied organization membership per company and matching organization on role/company bindings.
- [x] Test constraints using a disposable synthetic PostgreSQL fixture; no deployment `.env` or existing company database was used.

## Task 3: Employee-company relationship migration

**Files:** Create `hrms-database/changelog/migrations/0112_company_management_foundation/company_management_foundation.xml`; append to tenant master after existing uncommitted migration 0110; add dedicated organization integration fixture/test under `tests/integration/organization/`.

**Interfaces:** Company-local `actor_ref`, `management_assignment`, `assignment_capability`; local employee/actor FKs; logical global membership/principal references; tenant ownership checks and serialized overlap protection for primary assignments.

- [x] Preserve `employee.reporting_manager_id`, existing authority readers and all legacy decisions until a later controlled reader/writer migration.
- [x] Reject self-reporting and invalid periods; use PostgreSQL exclusion constraints to reject concurrent overlapping active primary intervals.
- [x] Confirm no new generic log archive or permanent retry-history table is introduced.
- [x] Verify two synthetic company schemas remain independent and preserve their existing employee rows.

## Subsequent implementation milestones

These remain required for the full feature. Each gets its own concrete plan against current callers before coding; the foundation alone does not enable cross-company operations.

1. Tenant-bound execution and delegated actor context: `kabipay-common/src/{db,middleware,context,jwt,subgraph}.rs`, authenticated service routing and dedicated database identities. Preserve existing same-company contracts.
2. Organization service and metadata APIs: verified identity linking, company onboarding, roles/scopes, accepted grant versions, lifecycle/revocation and organization bootstrap. Add protected organization gateway routing without exposing operator JWTs to tenant users.
3. Company-owned relationship APIs, consistent versioned hierarchy coordination, local reporting backfill, workflow/leave/review authority adapters, command receipts and immediate source-company command APIs.
4. Canonical outbox adapter, Kafka/CDC infrastructure, secure consumer identities, shared inbox projection and lifecycle/reassignment handling. Preserve external webhook and finance delivery contracts during cutover.
5. Existing-app Organization Management, My Approvals/My Team and company-labelled details, with generated GraphQL callers and centralized permissions; shared HR and payroll require independent capabilities.
6. ClickHouse history/reporting, OpenTelemetry diagnostics, source snapshots, corrections/tombstones, coverage, protected history search and source-confirmed outcomes.
7. Infrastructure pilot/failover/restore and safe bounded cleanup; retire old polling deployments, duplicate database history and obsolete code only after source/destination reconciliation.

## Completion evidence

Record implemented files, commands and results in the companion progress ledger. Mark live migration, browser, broker, deployment, isolation and restore checks as unverified unless actually executed. Keep unfinished milestones explicit; no claim that the full feature is complete from schema or domain tests alone.
