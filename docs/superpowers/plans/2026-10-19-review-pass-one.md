# Independent security and correctness review — pass 1

Reviewer: lower-model independent source review. Scope was the current organization identity, delegation/service credentials, live policy, command receipts, source tenant boundary, membership lifecycle/install fences, manager relationships, and key source adapters. Review used the bounded implementation summary and current progress ledgers, then focused source reads. No source files were changed. No commands, tests, builds, live databases, or production systems were run.

## Findings

No confirmed security or correctness defect was established in the reviewed paths. This is a source review result, not a release acceptance or proof of runtime behavior.

## Reviewed trust boundaries

- `hrms-svc/crates/kabipay-auth/src/organization_identity.rs`: source account JWT validation, tenant binding, active company/account checks, linked-employment eligibility, and current RBAC scope response.
- `hrms-svc/crates/kabipay-common/src/client_jwt.rs` and `hrms-svc/crates/kabipay-organization-security/src/{service.rs,delegation.rs}`: company-bound client RSA verification, key/tenant restrictions, service credential route/body/audience checks, and exact command delegation claims.
- `hrms-svc/crates/kabipay-organization/src/{identity.rs,runtime.rs,execution.rs,policy_endpoint.rs,runtime_policy.rs}`: login-company selection, live source identity calls, signing/execution, policy revalidation, authority and version checks, intent binding, and source acknowledgements.
- `hrms-svc/crates/kabipay-organization-tenant/src/{routes.rs,transport.rs,membership_lifecycle.rs,installation.rs}`: fixed-company routing, command authentication, receipt replay checks, installation monotonicity, membership locks, and post-commit ACK handling.
- `hrms-svc/crates/kabipay-{employee,leave,attendance,performance,payroll}/src/organization.rs` plus leave/timesheet shared workflow actor helpers and payroll proof construction: resource scoping, business validation entry points, manager authority, and module entitlement gates.

## Not demonstrated / follow-up

- Source adapters call `employee()` before the source makes the authenticated live-policy request (`kabipay-organization-tenant/src/transport.rs`, `run`). Leave, timesheet, and performance adapters use this lookup to derive the employee scope. The current path does not return that lookup result directly; a later live-policy denial aborts before command execution. I did not establish a data disclosure or authorization bypass from this ordering, so this is not recorded as a finding. A focused runtime trace could establish whether errors, logs, or measurable responses expose resource existence after revocation.
- Focused all-target compilation, SQL fixtures, browser behavior, migrations against upgraded tenant schemas, and full HTTP-chain acceptance were outside this pass. The review does not establish those behaviors.
- The bounded ledger lists source checks rerun after canonical manager/directory hardening as pending. Verify their fresh outcomes before final acceptance.

## Disposition

No fixes requested by this pass. Preserve the above follow-up as NOT DEMONSTRATED; do not treat this review as evidence that the full feature is accepted.
