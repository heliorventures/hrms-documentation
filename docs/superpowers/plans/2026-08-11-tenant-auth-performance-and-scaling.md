# Tenant Authentication Performance and Scaling Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Bind browser authentication to the slug-resolved tenant, fail closed when its database mapping is unavailable, and make auth/database behavior responsive for 5-10 concurrent users across up to four organizations.

**Architecture:** Tenant resolution moves above authentication so refresh restoration cannot run until the expected tenant UUID is known. The auth service uses strict tenant database resolution, blocking-task wrappers for Argon2, a shared authorization loader, auth-only pool overrides, and structured phase timing while the existing GraphQL service topology remains intact.

**Tech Stack:** Rust 2021, Tokio, Axum, SeaORM, SQLx/PostgreSQL, React 18, TypeScript, Vite, Docker Compose, Caddy.

## Global Constraints

- Production target: one 8-vCPU/28-GB VPS, initially one organization and 5-10 active users, growing to 3-4 organizations.
- Keep the 18 GraphQL processes unchanged in this project.
- Keep subgraph pool limits at one ops connection and one connection per active tenant pool.
- Auth-only production limits: ops maximum 2, tenant maximum 4 per active tenant, idle timeout 300 seconds, acquire timeout 15 seconds.
- Keep PostgreSQL `max_connections=100`; do not add PgBouncer or change Argon2 parameters.
- Never log usernames, passwords, password hashes, access tokens, refresh tokens, or database DSNs.
- Preserve unrelated dirty files, especially `hrms-ui/public/config.json`, generated GraphQL files, `hrms-ui/.env`, and `hrms-database/changelog/migrations/0047_user_username_login/user_username_login.xml`.
- Codex must not run unit tests or any Cargo, Dart, or Flutter command. Test commands below are for the user to run and report.
- Codex may run static inspection, configuration parsing, and `git diff --check` only.
- Do not create commits. Each task ends with a review checkpoint and a suggested commit message for the user.

---

### Task 1: Strict tenant database resolution and stable 503 errors

**Files:**
- Modify: `hrms-svc/crates/kabipay-common/src/error.rs`
- Modify: `hrms-svc/crates/kabipay-common/src/db.rs`
- Modify: `hrms-svc/crates/kabipay-auth/src/handlers.rs`
- Modify: `hrms-ui/src/utils/graphqlUserMessage.ts`

**Interfaces:**
- Produces: `KabiPayError::TenantDatabaseUnavailable(Uuid)` with code `TENANT_DATABASE_UNAVAILABLE` and HTTP 503.
- Produces: `KabiPayError::from_tenant_db(tenant_id, DbErr)` so tenant pool timeouts are sanitized as the same retryable 503 while other database errors retain their existing classification.
- Produces: `resolve_required_tenant_db(tenant_id, ops_db, cache, fallback_cfg) -> KabiPayResult<DatabaseConnection>`.
- Preserves: `resolve_tenant_db(...)` and `resolve_tenant_handle(...)` fallback behavior for existing subgraphs and development scaffolding.

- [ ] **Step 1: Add error-contract tests before changing the enum**

Add to `error.rs`:

```rust
#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn tenant_database_unavailable_is_retryable_without_internal_details() {
        let tenant_id = Uuid::parse_str("e6d4fc13-feb8-52a0-93bd-f66c795969b1").unwrap();
        let err = KabiPayError::TenantDatabaseUnavailable(tenant_id);
        assert_eq!(err.code(), "TENANT_DATABASE_UNAVAILABLE");
        assert_eq!(err.http_status(), axum::http::StatusCode::SERVICE_UNAVAILABLE);
        assert_eq!(
            err.to_string(),
            "organization workspace is temporarily unavailable: e6d4fc13-feb8-52a0-93bd-f66c795969b1"
        );

        let timeout = KabiPayError::from_tenant_db(
            tenant_id,
            sea_orm::DbErr::ConnectionAcquire(sea_orm::ConnAcquireErr::Timeout),
        );
        assert_eq!(timeout.code(), "TENANT_DATABASE_UNAVAILABLE");
        assert_eq!(timeout.http_status(), axum::http::StatusCode::SERVICE_UNAVAILABLE);
    }
}
```

- [ ] **Step 2: User confirms the focused test initially fails**

User runs:

```powershell
cargo test -p kabipay-common error::tests::tenant_database_unavailable_is_retryable_without_internal_details
```

Expected before implementation: compilation fails because the variant does not exist.

- [ ] **Step 3: Implement the stable error contract**

Add:

```rust
#[error("organization workspace is temporarily unavailable: {0}")]
TenantDatabaseUnavailable(Uuid),
```

Map it to code `TENANT_DATABASE_UNAVAILABLE` and
`StatusCode::SERVICE_UNAVAILABLE` in the existing match expressions.

Add:

```rust
pub fn from_tenant_db(tenant_id: Uuid, error: sea_orm::DbErr) -> Self {
    match error {
        sea_orm::DbErr::ConnectionAcquire(sea_orm::ConnAcquireErr::Timeout) => {
            Self::TenantDatabaseUnavailable(tenant_id)
        }
        other => Self::Database(other),
    }
}
```

- [ ] **Step 4: Add strict and fallback resolver modes**

Introduce in `db.rs`:

```rust
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
enum MissingTenantDbPolicy {
    DerivedFallback,
    FailClosed,
}

async fn resolve_tenant_handle_with_policy(
    tenant_id: Uuid,
    ops_db: &DatabaseConnection,
    cache: &TenantDbCache,
    fallback_cfg: &TenantDbConfig,
    policy: MissingTenantDbPolicy,
) -> KabiPayResult<TenantDbHandle>;
```

Existing public resolvers delegate with `DerivedFallback`. Add:

```rust
pub async fn resolve_required_tenant_db(
    tenant_id: Uuid,
    ops_db: &DatabaseConnection,
    cache: &TenantDbCache,
    fallback_cfg: &TenantDbConfig,
) -> KabiPayResult<DatabaseConnection> {
    resolve_tenant_handle_with_policy(
        tenant_id,
        ops_db,
        cache,
        fallback_cfg,
        MissingTenantDbPolicy::FailClosed,
    )
    .await
    .map(|handle| handle.conn)
}
```

When no active mapping exists, `FailClosed` returns
`TenantDatabaseUnavailable(tenant_id)` before deriving a schema or opening a pool.
When strict-mode pool construction fails, log the underlying connection error with tenant
UUID server-side and return `TenantDatabaseUnavailable(tenant_id)` to the caller.

- [ ] **Step 5: Route tenant-auth operations through strict resolution**

Use `resolve_required_tenant_db` in `client_login`, `client_refresh`,
`client_logout`, and `client_change_password`. Logout remains best-effort 204 but must
not create a fallback pool.

For tenant-schema SeaORM operations in `handlers.rs` and `rbac.rs`, replace implicit
`DbErr -> KabiPayError::Database` conversion with:

```rust
.map_err(|error| KabiPayError::from_tenant_db(tenant_id, error))?
```

This applies to user/session/employee/RBAC/scope reads and writes so acquisition timeout
is consistently 503. Query and constraint failures keep their existing database-error
classification.

- [ ] **Step 6: Add frontend-safe mapping**

Add to `graphqlUserMessage.ts`:

```typescript
case 'TENANT_DATABASE_UNAVAILABLE':
  return 'This organization workspace is temporarily unavailable. Please try again shortly.';
```

- [ ] **Step 7: User verifies focused backend tests**

```powershell
cargo test -p kabipay-common error::tests::tenant_database_unavailable_is_retryable_without_internal_details
cargo test -p kabipay-common db::tests
```

Expected: all selected tests pass.

- [ ] **Step 8: Review checkpoint**

Codex reviews all auth database resolver call sites and runs
`git -C hrms-svc diff --check` plus `git -C hrms-ui diff --check`. No commit.

Suggested user commit: `fix(auth): fail closed on missing tenant database mapping`

---

### Task 2: Run Argon2 work outside Tokio async workers

**Files:**
- Create: `hrms-svc/crates/kabipay-auth/src/password_tasks.rs`
- Modify: `hrms-svc/crates/kabipay-auth/src/main.rs`
- Modify: `hrms-svc/crates/kabipay-auth/src/handlers.rs`

**Interfaces:**
- Produces: `password_tasks::verify(plaintext: String, stored_hash: String) -> KabiPayResult<bool>`.
- Produces: `password_tasks::hash(plaintext: String) -> KabiPayResult<String>`.
- Consumes: synchronous `kabipay_common::password::{verify, hash}`.

- [ ] **Step 1: Create the async wrapper test first**

```rust
#[cfg(test)]
mod tests {
    use super::*;

    #[tokio::test]
    async fn hash_and_verify_run_through_async_boundary() {
        let encoded = hash("correct horse battery staple".to_string()).await.unwrap();
        assert!(verify("correct horse battery staple".to_string(), encoded.clone())
            .await
            .unwrap());
        assert!(!verify("wrong".to_string(), encoded).await.unwrap());
    }
}
```

- [ ] **Step 2: User confirms the focused test initially fails**

```powershell
cargo test -p kabipay-auth password_tasks::tests::hash_and_verify_run_through_async_boundary
```

Expected: missing module/functions.

- [ ] **Step 3: Implement the blocking-task boundary**

```rust
use kabipay_common::{password, KabiPayError, KabiPayResult};

pub async fn verify(plaintext: String, stored_hash: String) -> KabiPayResult<bool> {
    tokio::task::spawn_blocking(move || password::verify(&plaintext, &stored_hash))
        .await
        .map_err(|error| KabiPayError::Internal(format!("password verification task failed: {error}")))?
}

pub async fn hash(plaintext: String) -> KabiPayResult<String> {
    tokio::task::spawn_blocking(move || password::hash(&plaintext))
        .await
        .map_err(|error| KabiPayError::Internal(format!("password hashing task failed: {error}")))?
}
```

Register `mod password_tasks;` in `main.rs`.

- [ ] **Step 4: Convert every handler call site**

Operator login, client login, and password change await `password_tasks::verify` with
owned password/hash strings. Password change awaits `password_tasks::hash`. Remove the
direct password import from `handlers.rs`. Do not trace passwords or hashes.

- [ ] **Step 5: User verifies the wrapper test**

```powershell
cargo test -p kabipay-auth password_tasks::tests::hash_and_verify_run_through_async_boundary
```

Expected: pass with existing hashes compatible.

- [ ] **Step 6: Review checkpoint**

Codex verifies handlers have no direct `password::verify` or `password::hash` call and
runs `git -C hrms-svc diff --check`.

Suggested user commit: `perf(auth): move password processing off async workers`

---

### Task 3: Reduce authorization query stages and duplicate role reads

**Files:**
- Modify: `hrms-svc/crates/kabipay-auth/src/rbac.rs`
- Modify: `hrms-svc/crates/kabipay-auth/src/handlers.rs`

**Interfaces:**
- Produces: `ClientAuthorization { roles, permissions, resource_scopes }`.
- Produces: `load_client_authorization(db, tenant_id, user_id) -> KabiPayResult<ClientAuthorization>`.
- Replaces: separate RBAC and scope calls in token issuance.

- [ ] **Step 1: Extract and test deterministic scope merging**

```rust
fn merge_resource_scope(
    best: &mut HashMap<String, ScopeType>,
    resource: String,
    candidate: ScopeType,
) {
    best.entry(resource)
        .and_modify(|current| {
            if candidate.rank() > current.rank() {
                *current = candidate;
            }
        })
        .or_insert(candidate);
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn resource_scope_keeps_widest_value() {
        let mut scopes = HashMap::new();
        merge_resource_scope(&mut scopes, "employee".into(), ScopeType::Self_);
        merge_resource_scope(&mut scopes, "employee".into(), ScopeType::All);
        merge_resource_scope(&mut scopes, "employee".into(), ScopeType::Team);
        assert_eq!(scopes.get("employee"), Some(&ScopeType::All));
    }
}
```

- [ ] **Step 2: User confirms the focused test initially fails**

```powershell
cargo test -p kabipay-auth rbac::tests::resource_scope_keeps_widest_value
```

Expected: helper not found.

- [ ] **Step 3: Implement one authorization entry point**

```rust
pub struct ClientAuthorization {
    pub roles: Vec<String>,
    pub permissions: Vec<String>,
    pub resource_scopes: HashMap<String, String>,
}

pub async fn load_client_authorization(
    db: &DatabaseConnection,
    tenant_id: Uuid,
    user_id: Uuid,
) -> KabiPayResult<ClientAuthorization>;
```

Query `user_role` once. Use the resulting role IDs with `tokio::try_join!` to load role,
role-permission, and permission-scope rows. Then load permission rows when IDs exist.
Use `BTreeSet` for stable de-duplication and `merge_resource_scope` for widest scopes.
Remove old public loaders after their caller migrates.

- [ ] **Step 4: Parallelize independent claim reads**

In `issue_client_tokens`, run employee lookup and authorization loading through
`tokio::try_join!`. Pass the returned roles, permissions, and resource scopes into JWT
issuance without changing claims.

- [ ] **Step 5: Overlap best-effort last-login update**

After password verification, use `tokio::join!` so `touch_user_last_login` overlaps token
construction. Session persistence remains required; the last-login update stays
best-effort and non-fatal.

- [ ] **Step 6: User verifies authorization tests**

```powershell
cargo test -p kabipay-auth rbac::tests
```

Expected: deterministic scope test passes.

- [ ] **Step 7: Review checkpoint**

Codex verifies one `user_role` read per authorization load, reviews tenant filters, and
runs `git -C hrms-svc diff --check`.

Suggested user commit: `perf(auth): reduce authorization database stages`

---

### Task 4: Bind browser sessions to the resolved tenant

**Files:**
- Modify: `hrms-ui/package.json`
- Update mechanically: `hrms-ui/package-lock.json`
- Create: `hrms-ui/src/auth/tenantSession.ts`
- Create: `hrms-ui/src/auth/tenantSession.test.ts`
- Modify: `hrms-ui/src/auth/tokenStore.ts`
- Create: `hrms-ui/src/auth/tokenStore.test.ts`
- Modify: `hrms-ui/src/contexts/TenantContext.tsx`
- Modify: `hrms-ui/src/contexts/AuthContext.tsx`
- Modify: `hrms-ui/src/routes/RouteGuards.tsx`
- Modify: `hrms-ui/src/routes/AppRoutes.tsx`
- Modify: `hrms-ui/src/App.tsx`

**Interfaces:**
- Produces: `refreshTokenTenantId(token: string) -> string | null`.
- Produces: `sessionMatchesTenant(authenticatedTenantId, resolvedTenantId) -> boolean`.
- Changes: client refresh storage functions require a tenant UUID.
- Preserves: operator token storage and restoration.

- [ ] **Step 1: Add a frontend test runner without runtime dependencies**

Add script `"test": "vitest run"` and dev dependency `"vitest": "^1.6.0"` to
`package.json`. Update the lockfile with `npm install --package-lock-only`; Codex must ask
the user to run this command if package installation requires permission and must not
hand-edit lockfile dependency graphs.

- [ ] **Step 2: Write tenant-session tests first**

```typescript
import { describe, expect, it } from 'vitest';
import { refreshTokenTenantId, sessionMatchesTenant } from './tenantSession';

describe('tenant session binding', () => {
  it('extracts only a valid tenant UUID prefix', () => {
    expect(refreshTokenTenantId('e6d4fc13-feb8-52a0-93bd-f66c795969b1.opaque'))
      .toBe('e6d4fc13-feb8-52a0-93bd-f66c795969b1');
    expect(refreshTokenTenantId('demo.opaque')).toBeNull();
  });

  it('requires exact authenticated and resolved tenant equality', () => {
    expect(sessionMatchesTenant('e6d4fc13-feb8-52a0-93bd-f66c795969b1', 'e6d4fc13-feb8-52a0-93bd-f66c795969b1')).toBe(true);
    expect(sessionMatchesTenant('342205fc-98b1-5421-8a11-b30821c86aa0', 'e6d4fc13-feb8-52a0-93bd-f66c795969b1')).toBe(false);
    expect(sessionMatchesTenant(null, 'e6d4fc13-feb8-52a0-93bd-f66c795969b1')).toBe(false);
  });
});
```

- [ ] **Step 3: Write tenant-keyed storage tests first**

Use an in-memory `Storage` test double and assert:

```typescript
setClientRefreshToken(TENANT_A, 'tenant-a-token');
setClientRefreshToken(TENANT_B, 'tenant-b-token');
expect(getClientRefreshToken(TENANT_A)).toBe('tenant-a-token');
expect(getClientRefreshToken(TENANT_B)).toBe('tenant-b-token');

storage.setItem('kabipay.client.refresh', 'legacy-token');
clearLegacyClientRefreshToken();
expect(storage.getItem('kabipay.client.refresh')).toBeNull();
```

- [ ] **Step 4: User confirms frontend tests initially fail**

```powershell
npm test -- --run src/auth/tenantSession.test.ts src/auth/tokenStore.test.ts
```

Expected: new modules/exports are absent.

- [ ] **Step 5: Implement pure tenant-session helpers**

Create `tenantSession.ts` with a strict UUID expression and:

```typescript
export function refreshTokenTenantId(token: string): string | null;

export function sessionMatchesTenant(
  authenticatedTenantId: string | null | undefined,
  resolvedTenantId: string | null | undefined
): boolean;
```

Equality is case-insensitive after UUID validation; missing/invalid values return false.

- [ ] **Step 6: Scope client refresh storage by tenant**

```typescript
const LEGACY_CLIENT_REFRESH_KEY = 'kabipay.client.refresh';
const CLIENT_REFRESH_PREFIX = 'kabipay.client.refresh.';

export function setClientRefreshToken(tenantId: string, token: string | null): void;
export function getClientRefreshToken(tenantId: string): string | null;
export function clearClientSession(tenantId: string | null): void;
export function clearLegacyClientRefreshToken(): void;
```

Do not change operator token APIs. `clearAllTokens()` keeps its current no-argument
signature and removes every storage key beginning with `CLIENT_REFRESH_PREFIX`, plus the
legacy key and operator key. `clearClientSession(tenantId)` removes only the selected
tenant's client token and the in-memory client access token.

- [ ] **Step 7: Remove the provider cycle**

In `TenantContext.tsx`, remove `useAuth` and the `user?.tenantId` fallback. Set
`currentTenant` to `resolvedTenant ?? emptyTenant()`.

Reorder `App.tsx`:

```tsx
<TenantProvider>
  <AuthProvider>
    <CommandPaletteProvider>
      <AppRoutes />
    </CommandPaletteProvider>
  </AuthProvider>
</TenantProvider>
```

- [ ] **Step 8: Split operator and client restoration**

In `AuthContext`, operator restoration remains independent. Client restoration runs
only when the tenant status is `resolved`. It removes the legacy key, reads the resolved
tenant's key, validates the refresh prefix, removes mismatches without an API request,
and calls `refreshClientSession(expectedTenantId)` only on a match.

Change application to:

```typescript
const applyTokens = useCallback((pair: TokenPair, expectedTenantId: string) => {
  if (!sessionMatchesTenant(pair.tenantId, expectedTenantId)) {
    clearClientSession(expectedTenantId);
    throw new Error('tenant session mismatch');
  }
  setClientAccessToken(pair.access);
  setClientRefreshToken(expectedTenantId, pair.refresh);
  // retain existing parsed JWT and user state updates
}, []);
```

Scheduled/focus refreshes use the authenticated tenant ID and stop on resolved-tenant
mismatch.

- [ ] **Step 9: Enforce equality in routes**

`ProtectedLayout` and login redirects treat the client as tenant-authenticated only when:

```typescript
isAuthenticated && sessionMatchesTenant(authTenantId, currentTenant.id)
```

- [ ] **Step 10: User verifies frontend behavior**

```powershell
npm test -- --run src/auth/tenantSession.test.ts src/auth/tokenStore.test.ts
npm run build
```

Expected: pass. A legacy demo refresh is removed, `heliorprd` resolves, and no refresh
request uses the demo tenant UUID.

- [ ] **Step 11: Review checkpoint**

Codex confirms generated GraphQL and runtime config files remain untouched and runs
`git -C hrms-ui diff --check`.

Suggested user commit: `fix(auth): bind browser sessions to resolved tenants`

---

### Task 5: Add route-aware and phase-aware auth telemetry

**Files:**
- Create: `hrms-svc/crates/kabipay-auth/src/request_metrics.rs`
- Modify: `hrms-svc/crates/kabipay-auth/src/main.rs`
- Modify: `hrms-svc/crates/kabipay-auth/src/handlers.rs`

**Interfaces:**
- Produces: middleware `record_request(Request, Next) -> Response`.
- Produces: `record_phase(phase: &'static str, tenant_id: Option<Uuid>, started: Instant)`.

- [ ] **Step 1: Add a pure phase-threshold test**

```rust
const SLOW_PHASE: Duration = Duration::from_millis(250);

fn phase_is_slow(elapsed: Duration) -> bool {
    elapsed >= SLOW_PHASE
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn phase_threshold_is_250_milliseconds() {
        assert!(!phase_is_slow(Duration::from_millis(249)));
        assert!(phase_is_slow(Duration::from_millis(250)));
    }
}
```

- [ ] **Step 2: User confirms the focused test initially fails**

```powershell
cargo test -p kabipay-auth request_metrics::tests::phase_threshold_is_250_milliseconds
```

- [ ] **Step 3: Implement sanitized request logging**

The middleware records method, URI path without query string, status, and latency in
milliseconds. Log 5xx at error, 4xx at warn, success at debug. Do not record headers or
bodies. Register it using `axum::middleware::from_fn` and remove the duplicate generic
`TraceLayer` from auth only.

- [ ] **Step 4: Instrument auth phases**

After each awaited result and before propagating errors, record `tenant_lookup`,
`tenant_pool`, `user_lookup`/`session_lookup`, `password_verify`, `authorization`, and
`session_persist`. Fields are only phase, optional tenant UUID, and elapsed milliseconds.

- [ ] **Step 5: User verifies the telemetry test**

```powershell
cargo test -p kabipay-auth request_metrics::tests::phase_threshold_is_250_milliseconds
```

Expected: pass.

- [ ] **Step 6: Review checkpoint**

Codex inspects telemetry for secret-bearing fields and runs
`git -C hrms-svc diff --check`.

Suggested user commit: `feat(auth): add safe request phase latency telemetry`

---

### Task 6: Apply auth-only pool settings and document capacity

**Files:**
- Modify: `hrms-documentation/deploy/docker-compose.prod.yml`
- Modify: `hrms-documentation/deploy/.env.example`
- Create: `hrms-documentation/deploy/AUTH_PERFORMANCE.md`

**Interfaces:**
- Produces: deployment aliases mapped to existing service pool variables.
- Preserves: global subgraph limits 1/1.

- [ ] **Step 1: Add auth container overrides**

```yaml
environment:
  KABIPAY_DB_POOL_MAX: ${KABIPAY_AUTH_DB_POOL_MAX:-2}
  KABIPAY_TENANT_DB_POOL_MAX: ${KABIPAY_AUTH_TENANT_DB_POOL_MAX:-4}
  KABIPAY_DB_IDLE_TIMEOUT_SECS: ${KABIPAY_AUTH_DB_IDLE_TIMEOUT_SECS:-300}
  KABIPAY_DB_ACQUIRE_TIMEOUT_SECS: ${KABIPAY_AUTH_DB_ACQUIRE_TIMEOUT_SECS:-15}
```

Do not apply these overrides to subgraphs or the worker.

- [ ] **Step 2: Document environment values**

Keep global 1/1 and add:

```dotenv
# Auth-only Docker Compose overrides. Do not apply globally to subgraphs.
KABIPAY_AUTH_DB_POOL_MAX=2
KABIPAY_AUTH_TENANT_DB_POOL_MAX=4
KABIPAY_AUTH_DB_IDLE_TIMEOUT_SECS=300
KABIPAY_AUTH_DB_ACQUIRE_TIMEOUT_SECS=15
```

- [ ] **Step 3: Write `AUTH_PERFORMANCE.md`**

Document `postgres:5432`, why tunnel timing differs, slow-acquire warning versus timeout,
safe `pg_stat_activity` counts, sustained 70-connection alert threshold, p95 targets,
smoke flow, rollback, and why service consolidation is deferred.

- [ ] **Step 4: User validates Compose**

```powershell
docker compose -f deploy/docker-compose.prod.yml --env-file deploy/.env.example config --quiet
```

Expected: auth renders 2/4/300/15; subgraphs render 1/1.

- [ ] **Step 5: Review checkpoint**

Codex statically reviews YAML, checks no secrets were introduced, and runs
`git -C hrms-documentation diff --check`.

Suggested user commit: `perf(deploy): size auth pools independently`

---

### Task 7: Coordinated verification and handoff

**Files:**
- Review only: all Task 1-6 changes.

**Interfaces:**
- Produces: evidence-backed handoff with unrun commands and deployment smoke results.

- [ ] **Step 1: Inspect repository state**

```powershell
git -C hrms-svc status --short
git -C hrms-ui status --short
git -C hrms-documentation status --short
```

Confirm unrelated changes remain untouched.

- [ ] **Step 2: Run allowed static verification**

```powershell
git -C hrms-svc diff --check
git -C hrms-ui diff --check
git -C hrms-documentation diff --check
```

Inspect all call sites of `resolve_required_tenant_db`, `resolve_tenant_db`,
`getClientRefreshToken`, `setClientRefreshToken`, `clearClientSession`, and
`sessionMatchesTenant`.

- [ ] **Step 3: Give the user the test list**

```powershell
cd D:\work\heliorventures\hrms-svc
cargo test -p kabipay-common error::tests::tenant_database_unavailable_is_retryable_without_internal_details
cargo test -p kabipay-common db::tests
cargo test -p kabipay-auth password_tasks::tests::hash_and_verify_run_through_async_boundary
cargo test -p kabipay-auth rbac::tests
cargo test -p kabipay-auth request_metrics::tests::phase_threshold_is_250_milliseconds

cd D:\work\heliorventures\hrms-ui
npm test -- --run src/auth/tenantSession.test.ts src/auth/tokenStore.test.ts
npm run build

cd D:\work\heliorventures\hrms-documentation
docker compose -f deploy/docker-compose.prod.yml --env-file deploy/.env.example config --quiet
```

- [ ] **Step 4: User performs local tenant smoke verification**

Confirm `heliorprd` resolves to `e6d4fc13-feb8-52a0-93bd-f66c795969b1`, a legacy demo
refresh is removed without an auth request, invalid credentials return 401 against the
correct mapping, a missing mapping returns 503 without derived-schema fallback, and logs
contain safe route/phase timings.

- [ ] **Step 5: User performs production smoke verification**

After coordinated deploy, verify login, leave create/read, and profile read/update for
two users. Inspect `pg_stat_activity` and confirm there are no repeated slow acquisitions,
pool timeouts, tenant mismatches, or 5xx errors.

- [ ] **Step 6: Final review checkpoint**

Codex reports changed files by repository, static checks, every runtime/test command it
did not run, user-provided results, deployment observations still pending, and confirms
that no commit was created.
