# Infrastructure ownership and deployment separation

Status: approved for local implementation, independent reviews and focused checks on 2026-10-19. No live deployment or existing-data relocation is authorized.

## Intent

Keep business services, PostgreSQL changes, ClickHouse schema management, Kafka operations and deployment orchestration independently owned and executable. Preserve separate company databases, current authorization/receipt guarantees, existing platform data, and non-HRMS Finance/RMS routes.

## Verified findings before this phase

1. Organization PostgreSQL migrations0111–0123 are in `hrms-database` and included in the proper ops/tenant masters. Operational PostgreSQL grants/CDC publication templates also exist in `hrms-svc/infrastructure/organization`; their ownership must move to `hrms-database`.
2. ClickHouse server configuration, company/control table/view/grant SQL and Kafka/Connect composition/templates are grouped under `hrms-svc/infrastructure/organization`. ClickHouse currently has standalone SQL scripts rather than an independently versioned migration project.
3. `hrms-documentation/deploy/docker-compose.prod.yml` currently combines Caddy/PostgreSQL/Mongo with HRMS applications. The deployment script defaults to `/opt/apps`, with images under `/opt/apps/images`; it does not yet wire organization service/consumer/archive deployment.
4. `hrms-svc/Dockerfile` builds workspace binaries but exports only `kabipay-*`; the `bootstrap_organization` tool is therefore not included. The main application composition does not start `kabipay-organization`.
5. The Caddy template has shared Finance/RMS routes and common HRMS routes. The deployment script also builds a separate inline Caddy variant, creating divergent routing definitions. The template forwards `/auth/*` without a private-route exclusion.
6. The event package still exports the old coupled `processRecord` path used by older tests, alongside the independent production consumers. The old offline cleanup planner remains alongside the accepted-policy executor. These are confirmed cleanup candidates; their tests/callers must be migrated before deletion.

## Ownership

| Project | Responsibility | Excludes |
| --- | --- | --- |
| `hrms-database` | All production PostgreSQL migrations, roles/grants, RLS/publication provisioning and source/metadata database operational SQL | Kafka broker installation and ClickHouse schema |
| `hrms-clickhouse` (new standalone project) | ClickHouse server configuration, versioned company/control/diagnostic schema and grants, independent migration/status/validation commands | Source PostgreSQL access and HRMS business decisions |
| `hrms-kafka` (new standalone project) | Kafka/Connect installation, topic/ACL/connector lifecycle and maintenance commands, fixed source binding templates | PostgreSQL provisioning SQL and HRMS consumer/domain logic |
| `hrms-svc` | Rust services; HRMS event contracts, consumers, source exporters, archive/retention application behaviour and application container image | Broker/server installation and production database schema ownership |
| `hrms-documentation` | Canonical platform/HRMS deployment orchestration, Caddy routing, image/archive workflow and release/runbooks | Duplicate copies of schema or Kafka administration logic |

New projects are sibling working folders. Remote repositories, publishing and commits are not part of this approval.

## Deployment boundaries

- The shared platform layer owns Caddy, PostgreSQL, Mongo and references the independently maintained Kafka/ClickHouse installation artifacts. Platform setup must be independently invoked from an application update.
- New HRMS-specific runtime configuration, images/archive and deployment assets belong under an HRMS application folder. Existing `/opt/apps/data` storage, names, network membership and image archives must not be moved or recreated automatically.
- An explicit compatibility/cutover procedure must cover the current monolithic root Compose project. Changing a Compose project name or working directory must not silently create a second database volume or conflict with existing containers.
- Keep existing shared network names/routing compatible with Finance/RMS. Use private broker/database/archive networks; Kafka, Connect, ClickHouse and internal organization/source endpoints are not public Caddy routes.
- Public HRMS GraphQL stays behind its gateway. Review the actual company-bound Auth/gateway/source routing, organization service endpoint and feature flags before generating deployment configuration; compilation alone does not prove those production connections.
- Infrastructure install, PostgreSQL migration, ClickHouse migration, Kafka provisioning, application rollout and optional verified retention/cutover are separate explicit operations. No automatic age-only deletion or automatic legacy worker removal.

## DRY/SOLID and retirement requirements

Share transport/security/configuration helpers where semantics match. Keep business-event and control-event privacy/schema rules separate. Remove obsolete paths after their actual callers/tests use the supported path. Avoid forwarding files, copied SQL in multiple repositories and script-generated routing that differs from the canonical Caddy configuration.

Retain business data, source receipts/jobs, source-owned transactional outboxes and active notification/Finance delivery until their actual replacement and cutover are proven. This refactor cannot declare production retirement or delete old audit data merely because canonical event infrastructure exists.

## Completion evidence

Require current references/imports and independent project commands to resolve after extraction; migration version/checksum/status behaviour; Compose/rendered script/Caddy validation; scoped DRY/SOLID and caller review; actual synthetic separate-database/broker regression coverage; and an updated phase/cleanup matrix distinguishing implemented, synthetic proof and production acceptance.

Earlier feature acceptance remains valid for its recorded scope. Infrastructure ownership and deployment integration are additional unfinished work; production backfill, controlled rollout and legacy retirement were not completed by the earlier synthetic feature tests.
