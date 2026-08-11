# Auth Performance Runbook

## Deployment Defaults

Production Compose keeps the shared subgraph container conservative:

- `KABIPAY_DB_POOL_MAX=1`
- `KABIPAY_TENANT_DB_POOL_MAX=1`

The auth container overrides those values only for `kabipay-auth`:

- `KABIPAY_AUTH_DB_POOL_MAX=2`
- `KABIPAY_AUTH_TENANT_DB_POOL_MAX=4`
- `KABIPAY_AUTH_DB_IDLE_TIMEOUT_SECS=300`
- `KABIPAY_AUTH_DB_ACQUIRE_TIMEOUT_SECS=15`

Do not copy the auth values to `kabipay-subgraphs`; that container starts many
Rust services in one process group and would multiply database connections.

## Network Baseline

Inside production Docker, services should use `postgres:5432` on the Compose
network. Local tunnel timings are expected to look slower because each new
Postgres connection crosses the SSH/VPS path and may include TLS/session setup.

A SQLx slow-acquire warning means a connection was eventually acquired after
the warning threshold. It is not the same as an acquire timeout. A timeout is
controlled by `KABIPAY_DB_ACQUIRE_TIMEOUT_SECS` and should surface as a
retryable auth error when it happens on a tenant pool.

## Connection Budget

Keep PostgreSQL `max_connections=100`.

For the initial target of one organization and 5-10 active users on an
8-vCPU / 28-GB VPS:

- Auth ops pool: up to 2 connections.
- Auth tenant pool: up to 4 per active tenant in that auth process.
- Subgraphs: global 1 ops connection and 1 tenant connection per active tenant
  pool per service process.

Alert if sustained active connections approach 70. Use this as a practical
headroom threshold, not a hard database limit.

```sql
select state, count(*)
from pg_stat_activity
where datname = current_database()
group by state
order by state;
```

## Targets

Use request and phase logs from `kabipay-auth`:

- Login p95 should stay below 2 seconds on the VPS.
- Refresh p95 should stay below 1 second.
- Repeated `tenant_pool`, `password_verify`, `authorization`, or
  `session_persist` slow phases identify the bottleneck more precisely than a
  generic HTTP latency line.

## Smoke Flow

After deploy:

1. Resolve `heliorprd` and confirm the tenant id is
   `e6d4fc13-feb8-52a0-93bd-f66c795969b1`.
2. Clear browser storage or verify a legacy `kabipay.client.refresh` key is
   removed without a refresh call.
3. Log in with a valid user.
4. Create/read leave data.
5. Read/update the user's profile.
6. Inspect auth logs for route latency and slow phase entries.
7. Check `pg_stat_activity` for repeated active-connection pressure.

## Rollback

Rollback is configuration-only for pool sizing:

- Set `KABIPAY_AUTH_DB_POOL_MAX=1`.
- Set `KABIPAY_AUTH_TENANT_DB_POOL_MAX=1`.
- Restart only `kabipay-auth`.

Keep the tenant-session binding and strict tenant DB resolution changes; they
fix correctness and prevent stale tenant routing.

## Service Consolidation

Do not consolidate services for the initial rollout. With 5-10 concurrent
active users and one organization, the safer first move is right-sized auth
pools, blocking-password isolation, and phase visibility. Revisit service
topology only if production metrics show sustained CPU, memory, or connection
pressure after the above changes are deployed.
