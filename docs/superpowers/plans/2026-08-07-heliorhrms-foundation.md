# HeliorHRMS Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace hardcoded tenant and UI foundations with HeliorHRMS branding, slug-based tenant resolution, centralized permissions, safe errors, reusable UI primitives, and an Expenses module split.

**Architecture:** Add a public auth tenant resolver, resolve tenant metadata before authenticated tenant routes, and ensure GraphQL/login use resolved tenant IDs only. Move cross-cutting UI concerns into services/constants/primitives, then refactor Expenses into hooks and focused components.

**Tech Stack:** React 18, TypeScript, Vite, Tailwind CSS, graphql-request, Rust Axum auth service, SeaORM.

## Global Constraints

- Do not run unit tests.
- Do not run Dart or Flutter commands.
- Do not commit changes.
- No business logic in JSX.
- Component/page files should be 400 lines or less, excluding generated files.
- Do not hardcode permissions in route/module files; use a permission service.
- Do not hardcode production tenant IDs in config; resolve tenant by slug.
- If slug is not provided, show a HeliorHRMS marketing/demo/about page.
- Do not surface raw database/internal errors to users.

---

### Task 1: Tenant Resolver Contract

**Files:**
- Modify: `../hrms-svc/crates/kabipay-auth/src/handlers.rs`
- Modify: `../hrms-svc/crates/kabipay-auth/src/main.rs`
- Modify: `src/auth/authClient.ts`

**Interfaces:**
- Produces: `GET /auth/client/tenants/:slug`
- Produces: `resolveTenantBySlug(slug: string): Promise<ResolvedTenant>`

- [ ] Add a safe tenant metadata DTO returning `id`, `name`, `status`, `subdomain`, `logoUrl`, `primaryColor`.
- [ ] Query `kabipay_ops.tenant` by lowercased `subdomain`, excluding deleted tenants.
- [ ] Return unauthorised/not-found without database details.
- [ ] Add frontend REST client wrapper for the resolver.

### Task 2: Frontend Tenant Bootstrap

**Files:**
- Modify: `src/config.ts`
- Modify: `public/config.json`
- Modify: `src/contexts/TenantContext.tsx`
- Modify: `src/api/client.ts`
- Modify: `src/contexts/AuthContext.tsx`
- Modify: `src/routes/AppRoutes.tsx`

**Interfaces:**
- Produces: `TenantProvider` with `resolutionStatus`, `resolvedTenant`, `tenantSlug`, `requiresTenant`
- Consumes: `resolveTenantBySlug`

- [ ] Make dev tenant optional and explicitly named as dev-only.
- [ ] Resolve tenant slug from hostname or `/t/:slug` path.
- [ ] Block tenant app routes until slug is resolved.
- [ ] Use resolved tenant ID for login and GraphQL headers.
- [ ] Remove GraphQL fallback to config tenant ID.

### Task 3: Branding and Public Page

**Files:**
- Create: `src/constants/brand.ts`
- Create: `src/modules/public/MarketingPage.tsx`
- Modify: `index.html`
- Modify visible KabiPay UI strings.

**Interfaces:**
- Produces: `APP_BRAND`
- Produces: public no-slug landing page.

- [ ] Centralize visible product name as `HeliorHRMS`.
- [ ] Replace visible app-shell and auth copy.
- [ ] Add no-slug marketing/demo/about route.

### Task 4: Permissions Foundation

**Files:**
- Create: `src/auth/permissions.ts`
- Create: `src/auth/permissionService.ts`
- Modify: `src/auth/navAccess.ts`
- Modify: `src/routes/AppRoutes.tsx`
- Modify: `src/components/layout/Sidebar.tsx`
- Modify: `src/components/layout/CommandPalette.tsx`

**Interfaces:**
- Produces: `PermissionCode`, `Capability`, `createPermissionService(session)`

- [ ] Centralize permission strings and capability rules.
- [ ] Replace route/sidebar/command-palette hardcoded checks.
- [ ] Keep module migrations incremental.

### Task 5: UI Foundation

**Files:**
- Create: `src/constants/queryLimits.ts`
- Create: `src/components/common/PageNotice.tsx`
- Modify: `src/utils/graphqlUserMessage.ts`
- Modify: `src/components/common/Button.tsx`
- Modify: `src/components/common/Input.tsx`
- Modify: `src/components/common/Select.tsx`
- Modify: `src/components/common/Modal.tsx`
- Modify: `src/components/common/Table.tsx`
- Modify: `.eslintrc.cjs`

**Interfaces:**
- Produces: deny-by-default user error mapping.
- Produces: accessible UI primitives with loading/error/empty table states.

- [ ] Prevent raw GraphQL/database messages from rendering.
- [ ] Add stricter lint rules while temporarily ignoring existing large generated/legacy files.
- [ ] Improve accessibility defaults in common primitives.

### Task 6: Expenses Module Split

**Files:**
- Modify: `src/modules/expenses/ExpensesPage.tsx`
- Modify/Create files under `src/modules/expenses/components`, `hooks`, `utils`

**Interfaces:**
- Consumes: permission service, query limits, safe error mapper, upgraded table.

- [ ] Move expense types/constants outside the page.
- [ ] Move board loading and mutations into hooks.
- [ ] Replace stale alert-only submit modal with working component.
- [ ] Keep route page under 400 lines.

### Static Verification

- [ ] Run `git diff --check`.
- [ ] Inspect line counts for touched hand-authored files.
- [ ] Report that unit tests/lint/build were not run unless user runs them.
