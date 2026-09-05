# Tenant Authentication Performance and Scaling Design

## Problem

The application currently has two related runtime problems:

1. Tenant identity is resolved correctly from the slug, but client-session restoration
   uses one origin-wide refresh-token key. A refresh token from another tenant can
   therefore be submitted before the resolved tenant is known. The auth service derives
   the tenant directly from the refresh-token prefix, which caused the stale demo tenant
   UUID to be routed to a derived fallback schema and return a database error.
2. Database latency is amplified by cold connection pools, one-connection pool limits,
   synchronous Argon2 work inside async handlers, and several sequential authentication
   and RBAC queries.

The production target is an 8-vCPU, 28-GB VPS running PostgreSQL and the application on
the same Docker network. The initial load is one organization and approximately 5-10
simultaneously active users, growing to 3-4 organizations. Normal activity includes
login, leave operations, and employee self-service updates.

## Considered Approaches

1. **Harden and optimize the existing deployment (selected).**
   Bind client sessions to the resolved tenant, give auth service-specific pool limits,
   keep auth pools warm longer, move Argon2 work off async executor threads, reduce
   sequential authorization queries, fail closed on missing tenant database mappings,
   and add phase-specific latency telemetry. This addresses the demonstrated causes
   without destabilizing the domain services.
2. **Change pool sizes only.**
   This would reduce some queuing but would leave cross-tenant session restoration,
   blocking password verification, query fan-out, fallback-schema errors, and weak
   diagnostics in place.
3. **Consolidate all GraphQL services now.**
   A modular monolith or a smaller set of domain services would reduce duplicated pools
   and operational overhead, but it is a larger schema, gateway, deployment, and failure-
   isolation change than the current workload requires.

## Tenant and Session Contract

Tenant resolution becomes independent of authenticated user state. `TenantProvider`
will no longer use `AuthContext` to manufacture a tenant fallback from a restored user.
This allows the provider order to become:

```text
TenantProvider
  -> AuthProvider
      -> application routes
```

The browser must resolve an organization before restoring a client session. Operator
session restoration remains independent because it is not tenant scoped.

Client refresh tokens will be stored under a tenant-specific key. The auth state will:

- read only the refresh token belonging to the resolved tenant;
- remove the legacy origin-wide client refresh key;
- verify the UUID prefix before sending a refresh request;
- reject a token response whose `tenantId` differs from the resolved tenant;
- clear client authentication when the resolved tenant changes; and
- expose an authenticated tenant ID that route guards compare with the resolved tenant.

Protected tenant routes require both authentication and exact tenant equality. This
prevents an access token for one organization from being paired with the UI/header
context of another organization.

## Auth Database Resolution

Slug resolution continues to read the non-deleted tenant row by normalized subdomain
and return its real UUID.

Authentication, refresh, logout, and password-change operations must use an active
`kabipay_ops.tenant_database` row. They will not use the derived-schema development
fallback. A missing or inactive mapping returns a stable service-unavailable error and
does not attempt a query against `tenant_<uuid-prefix>`.

The public error contract will use code `TENANT_DATABASE_UNAVAILABLE` with HTTP status
503. Its user-facing message will state that the organization workspace is temporarily
unavailable; database host, schema, and driver details remain server-side only.

The derived fallback remains available only to explicitly permitted development or
scaffolding paths so existing local subgraph workflows are not changed unintentionally.

## Pool Configuration and Connection Budget

Production keeps the existing subgraphs at one ops connection and one connection per
active tenant pool. The auth container receives explicit overrides:

- ops pool maximum: 2;
- tenant pool maximum: 4 per concurrently active tenant;
- idle timeout: 300 seconds;
- acquire timeout: 15 seconds, returning an error promptly instead of hanging for a
  full minute under abnormal pressure.

These settings apply only to `kabipay-auth`; they must not be copied globally to all 18
subgraph processes. Pools keep `min_connections = 0`, so maximums are capacity limits,
not startup reservations. PostgreSQL `max_connections` remains 100 initially. The
deployment runbook will document the connection budget and require investigation before
raising either application pools or PostgreSQL capacity.

The production auth container must connect to `postgres:5432` over the Docker network.
Local development through the loopback VPS tunnel will remain slower and is not a valid
production latency benchmark.

## Password Processing

Argon2 hashing and verification are CPU- and memory-intensive synchronous operations.
Every auth call site will execute them through Tokio's blocking task pool rather than on
an async runtime worker. Join failures become internal errors without exposing password
or hash material.

The existing Argon2 parameters and stored PHC hash format remain unchanged. The change
affects scheduling only, so existing passwords remain compatible.

## Authentication Query Flow

The client-login result remains atomic with respect to required session creation:
credentials must validate, authorization claims must load, and the refresh session must
be persisted before tokens are returned.

The implementation will reduce latency without weakening that contract:

- load the user's role IDs once instead of once for RBAC and again for resource scopes;
- reuse those role IDs for role, permission, and scope loading;
- execute independent employee and authorization reads concurrently after password
  verification when pool capacity permits;
- preserve deterministic permission de-duplication; and
- keep last-login updates best-effort without delaying a successful token response when
  the update itself fails.

No authorization information is cached across users or tenants in this change.

## Observability

HTTP failure logs will include the request method and matched route without logging
credentials, tokens, usernames, or database DSNs. Auth telemetry will separately measure:

- ops tenant lookup;
- tenant-pool acquisition;
- user lookup;
- password verification;
- authorization loading; and
- refresh-session persistence.

Slow-phase warnings use explicit phase and tenant UUID fields. This makes pool queuing,
database work, and Argon2 CPU time distinguishable from total HTTP latency.

Operational thresholds for the initial deployment are:

- warm tenant resolution p95 below 100 ms;
- normal leave/profile operations p95 below 500 ms;
- login p95 below 1 second during ordinary load; and
- sustained PostgreSQL usage below approximately 70 of 100 connections.

These are monitoring targets, not reasons to hide warnings by increasing SQLx's slow-
acquire threshold.

## Service Topology

The 18 GraphQL processes remain unchanged for the initial release. The VPS has adequate
CPU and memory for 5-10 active users, and requests are naturally divided among domain
services.

Service consolidation becomes a separate project when measurements show sustained
connection pressure, materially higher tenant counts, or unacceptable deployment and
operational complexity. It will not be mixed into this auth and pool correction.

## Error Handling

- A stale or mismatched browser refresh token is removed locally and is never sent.
- An absent tenant database mapping fails closed as `TENANT_DATABASE_UNAVAILABLE` with
  HTTP 503.
- Pool acquisition timeout returns a sanitized HTTP 503 response suitable for retry;
  other unexpected database failures remain internal errors.
- Invalid credentials remain a generic unauthenticated response.
- Internal logs never include passwords, refresh tokens, access tokens, or DSNs.

## Verification

Focused tests will cover tenant-keyed token storage, mismatched-session rejection, route-
guard tenant equality, strict tenant database resolution, and the refactored auth/RBAC
result. Deployment configuration will be checked for auth-only overrides and unchanged
subgraph limits.

Per repository instructions, Codex will not run unit tests or any Cargo, Dart, or Flutter
commands. Static verification will include targeted source inspection, configuration
parsing, repository diff review, and `git diff --check`. The user will run the documented
backend and frontend test commands and share their output.

## Rollout

1. Deploy the UI, auth service, and production configuration changes as one coordinated
   release so session binding and strict tenant resolution cannot drift.
2. Clear the legacy browser refresh key during the first load after deployment.
3. Confirm the auth container resolves PostgreSQL through the Docker service name.
4. Observe login latency, pool acquisition, error rate, and `pg_stat_activity` during a
   small login and leave/profile smoke test before wider use.

Rollback restores the previous application images and pool environment values. Database
schema changes are not required for this design.

## Scope

This work does not consolidate services, alter Argon2 parameters, change JWT claim
semantics, raise PostgreSQL `max_connections`, modify tenant data, or change leave/profile
business behavior. No automatic commit will be created.
