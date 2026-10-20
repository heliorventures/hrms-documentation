# Organization feature completion plan

User authorization: implement remaining features autonomously while the user is unavailable for eight hours; run focused validation and two lower-model review passes, fixing confirmed issues. Continue current branches; no commits, deployments, production migrations, Dart/Flutter commands, or unrelated worktree cleanup. Start 2026-10-18 18:56 UTC (2026-10-19 00:26 IST); availability window ends about 2026-10-19 02:56 UTC (08:26 IST). Do not invent deployment evidence if infrastructure is unavailable.

Spec: `docs/architecture/2026-10-18-organization-cross-company-management.html`. Earlier foundation/runtime/service plans and their ledgers are prerequisites, not work to repeat.

## Execution and ownership

- Root: organization service orchestration, live policy, global hierarchy, directory, target invocation, service/browser trust, gateway and integration. Own shared Cargo workspace/lock, organization/security/protocol crates and Auth/common JWT changes; organization metadata migration 0114.
- Tenant implementer (GPT 6.1 sol): new tenant-runtime library; source-owned leave, feedback/review, timesheet and payroll adapters; employee/leave/performance/attendance/payroll service route wiring; tenant/entity migration 0115. Do not edit organization service, UI, shared Cargo manifest/lock or security/protocol contracts without coordination.
- Integration implementer (GPT 6.1 sol): Kafka/CDC/ClickHouse/OTel deployment artifacts, broker projection/history worker and organization projection migration 0116. Purpose-limited events only; no tenant DB access in shared consumers. Do not edit source business/organization/UI files.
- UI implementer (GPT 6.1 sol): existing application Organization workspace, administration, My Team/Approvals, source-confirmed commands, owner reports and scoped payroll. Own UI only; coordinate exact schema from the root. Use existing components, navigation, feedback and generated GraphQL conventions.
- Two independent lower-model review passes after integration; use a dedicated GPT 6.1 sol summariser for bounded evidence/review context. Fix all confirmed Critical/Important findings; no production operations.

## Security and transport contracts

Separate company databases remain. Shared services never open arbitrary company databases. Runtime endpoints are deployment-controlled allowlists, not HR-editable URLs. Each source runtime is fixed to a company and uses its own restricted credentials.

New `kabipay-organization-protocol` crate is the sole shared wire contract (serde deny_unknown_fields). `OrganizationOperation` enumerates supported operations; there is no arbitrary SQL/GraphQL proxy. `OrganizationCommand` contains `command_id`, `resource_id`, `expected_version` (>0), `operation`, typed-at-adapter `payload`. The organization service serializes exact bytes once, hashes them, issues the existing RS256 delegation and sends those same bytes.

Operation -> source service -> capability:

| Operation | Service | Capability |
| --- | --- | --- |
| InstallGrant, Directory, InstallRelationship | kabipay-employee | organization:manage |
| LeaveDetail, LeaveDecision | kabipay-leave | leave:approve |
| FeedbackCreate | kabipay-performance | feedback:write |
| ReviewDetail, ReviewSubmit | kabipay-performance | performance:evaluate |
| TimesheetDetail, TimesheetDecision | kabipay-attendance | timesheet:approve |
| PayrollList, PayrollDraft, PayrollFinalize | kabipay-payroll | payroll:manage |
| ReadReceipt | original service | original operation's capability, resolved from stored intent |

`OrganizationCommandOutcome`: command/resource IDs, status (`COMMITTED`, `SUBMITTED`, `AWAITING_CONFIRMATION`, `REJECTED`), resource_version and purpose-limited result JSON. Never claim business approval from broker/HTTP acceptance alone. Mutations are transactionally idempotent with a target-owned receipt containing actor/resource/operation/hash/version and minimal result. Conflicting command-ID reuse fails; replay authorization remains current.

Delegation claims gain identity/link/membership epoch fields, checked against live policy. Company runtimes verify exact issuer/type/key/audience/company/capability/resource/version/command/body. A separate RS256 service credential proves the requesting runtime/company to private organization policy endpoints; possession of a company service key never permits another company's identity. Organization service credentials may query configured source Auth eligibility endpoints without storing browser tokens.

Source policy handshake: `POST /internal/organization/policy` receives original delegation token, exact command bytes (base64) and source-resolved employee ID. Its service credential binds exact body, target tenant, audience and route. Organization verifies delegation again, current source account eligibility via trusted Auth, principal/link/membership epochs, current authority/capability/scope and resource ownership. No cached positive policy overrides revocation.

Grant installation returns authoritative configuration from live policy, writes target-local projection/fence transactionally, and acknowledges exact version/hash back to organization through a company-authenticated endpoint. Central grants activate only for acknowledged companies; business execution checks both local accepted state and fresh central policy.

Global primary reporting is reserved/validated centrally with serialized graph versions, including pending edges and effective-time boundaries, then installed in the employee company. Local assignment and fresh global versions/capabilities must agree. No tenant-specific names or fabricated local users/employment for foreign managers. Source-owned workflow writes retain original actor attribution.

## GraphQL workspace contract (root supplies SDL)

Use typed outer DTOs; versioned JSON configuration/directory/report documents may carry evolving field sets. All requests retain the source company's session; `x-login-company-id` always means login company, never selected target.

- `organizationWorkspaces`: organization ID/name/version and flags (`canManage`, `canDelegate`, `canApprove`, `canReview`, `canReport`, `canPayroll`) derived from current grants/assignments.
- Existing `myOrganizationIdentity`, configuration/catalog and configuration mutations remain.
- `organizationInvitations`, `organizationDirectory(organizationId,membershipId,after,first)`; `syncOrganizationDirectory`, `installOrganizationGrant`.
- `organizationRelationships(organizationId,after,first)`, `proposeOrganizationRelationship`, `endOrganizationRelationship`, `installOrganizationRelationship`.
- `organizationApprovals(organizationId,membershipId?,after,first)`, `organizationTeam(organizationId,membershipId?,after,first)`.
- `organizationResource(organizationId,membershipId,operation,resourceId,expectedVersion,payload?)` for protected source reads.
- `executeOrganizationCommand(organizationId,membershipId,command)` and `organizationCommandStatus(commandId)`. Inputs include stable command UUID and exact expected version; UI must show awaiting confirmation after uncertain transport, not optimistic success.
- `organizationProgress(organizationId,membershipIds?,from,to)` returns correction-aware logged/approved totals, per-company watermarks and explicit partial/stale status. No missing company is silently zero.
- `organizationHistory(organizationId,membershipIds?,from,to,after,first)` requires separate history/field permissions.

UI must keep selected target company separate from authentication, label every foreign-company record, reset caches on source-session change/revocation, and use shared feedback. Organization metadata capabilities are organization-wide configuration rights; tenant business permissions remain explicit per company. Ordinary local HR stays local.

## Events, projections and observability

- Source business writes use a small temporary canonical outbox in the same transaction. Versioned events expose only whitelisted inbox/directory/progress fields; private leave reasons, medical files, salary/bank details and private review bodies are excluded from general topics/history.
- CDC connectors are bound to their database/identity and a fixed trusted company topic. Consumers validate topic provenance against payload company, event schema/ID/version, then apply idempotently. Corrections/tombstones advance versions; replay must not double-count hours.
- Shared current inbox projections may live in the organization metadata DB. Complete retained business history and reporting facts go to ClickHouse; diagnostic OTel logs use a separate dataset and grants. Shared consumers never possess tenant DB URLs.
- Kafka, Kafka Connect/Debezium, ClickHouse and OTel deployment artifacts use explicit pinned OSS images/configuration, private networking, bounded storage/retention, WAL lag monitoring, retries/DLQ and backup/runbooks. No new public VPS ports beyond the existing reverse proxy are required.
- Cleanup tools default to dry-run and require capture/reconciliation evidence. Keep business receipts, source decisions and small transactional outbox. Do not drop old logs/history or retire delivery workers before history coverage/cutover checks pass. Infrastructure supplies transport retry; application retains authorization/version/idempotency/reconciliation rules.

## Validation and review gates

- TDD for policy, token confusion, stale/revoked membership, wrong-company/resource, command replay/races, primary cycles/future intervals, manager reassignment, corrections/tombstones, projection replay and uncertain outcomes.
- Synthetic PostgreSQL companies, deterministic source accounts and a real organization/source HTTP chain where feasible; isolated Kafka/ClickHouse tests if local images are available. Never load deployment `.env` or use existing company data.
- Focused Rust/TypeScript/UI tests, generated GraphQL contract checks, browser UI review where available, two independent review passes and regression fixes.
- Final report names exact implemented/verified/unverified areas and documents any infrastructure blocker. No claim that static mocks prove deployment, migration/restore, browser or broker acceptance.
