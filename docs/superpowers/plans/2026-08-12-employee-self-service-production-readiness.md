# Employee Self-Service Production Readiness Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Secure and operationalize employee profile reviews, evidence access, validation, audit notifications, and remaining section-local UX.

**Architecture:** Keep list contracts masked and add a separately authorized detail contract for sensitive review data. Encrypt new pending payloads with application-managed AES-256-GCM, perform decision side effects transactionally, and expose a dedicated HR review workspace while retaining local React reconciliation.

**Tech Stack:** PostgreSQL, Liquibase, Rust, SeaORM, async-graphql, AES-GCM, React, TypeScript, GraphQL Code Generator.

## Global Constraints

- Do not run unit tests or Dart/Flutter commands.
- Do not create commits.
- Preserve unrelated dirty files.
- Treat server authorization as authoritative and fail closed for encryption configuration.
- Never return sensitive requested values from list queries or notification/audit payloads.

---

### Task 1: Secure persistence and validation

**Files:**
- Create: `hrms-database/changelog/migrations/0051_employee_self_service_readiness/employee_self_service_readiness.xml`
- Modify: `hrms-database/changelog/tenant.changelog-master.xml`
- Modify: `hrms-svc/crates/kabipay-db-entities/src/tenant/d0050_employee_self_service.rs`
- Create: `hrms-svc/crates/kabipay-employee/src/services/profile_payload_crypto.rs`
- Modify: `hrms-svc/crates/kabipay-employee/src/services/profile_change_service.rs`
- Test: focused module tests beside validators and cipher envelope code

- [ ] Add unexecuted tests for future DOB, length bounds, IFSC/account formats, encryption round-trip/tamper rejection, and approval revalidation.
- [ ] Add encrypted payload storage and non-sensitive summary metadata.
- [ ] Centralize typed validation and call it from submission and approval.

### Task 2: HR detail, queue, audit, and notifications

**Files:**
- Modify: employee resolver types, queries, mutations, and profile-change service
- Modify: GraphQL schema extensions and client operations
- Test: resolver/service authorization and transaction-side-effect coverage

- [ ] Add masked review queue and HR-only decrypted detail query with data-scope checks.
- [ ] Write audit log, outbox event, and in-app notifications inside the request transaction.
- [ ] Notify scoped HR reviewers on submission and the requester on resolution.

### Task 3: Reliable evidence and signed preview

**Files:**
- Modify: employee document/profile-record services and resolvers
- Modify: profile Documents, Education, Work Experience, and review UI

- [ ] Add authorized signed preview/download actions.
- [ ] Add compensation for uploaded objects/documents when record linkage fails.
- [ ] Remove N+1 evidence lookups with batch loading.

### Task 4: Review workspace and section-local UX

**Files:**
- Create: HR review page and accessible review/edit dialogs
- Modify: routes/navigation/profile shell and profile tabs

- [ ] Add centralized queue, detail drawer, decision states, and requester-visible status.
- [ ] Replace `window.prompt` and `window.confirm` with controlled accessible dialogs.
- [ ] Remove remaining post-mutation profile-wide refetch callbacks.

### Task 5: Org-chart operations and handoff

**Files:**
- Modify: org-chart tree/page and tests

- [ ] Add search, expand/collapse, and actionable data-quality warnings.
- [ ] Add unexecuted regression tests for cycles, orphans, validation, authorization, and local reconciliation.
- [ ] Run only allowed static/build verification and provide exact user-run unit/integration commands.

