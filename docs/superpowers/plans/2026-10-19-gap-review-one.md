# Organization gap closure independent review 1

Read-only source review, 2026-10-19. Started with the bounded review input and central progress ledger. No builds, tests, migrations, deployments, or business commands were run. Findings below are source-derived reproducible paths; runtime reproduction is not claimed. The parent implementation was still changing while this review ran.

## G1 — P2: Employee update reverses the account administration lock order

Locations: `hrms-svc/crates/kabipay-organization-tenant/src/transport.rs:549` and `:679`; `hrms-svc/crates/kabipay-employee/src/services/employee_service.rs:1217` and `:1222`.

The source transport takes the `company-account-admin:{tenant}` advisory lock before the employee row for EmployeeEmployment, but excludes EmployeeUpdate from that early lock list. EmployeeUpdate first acquires its employee row FOR UPDATE, then calls `update_in_transaction`, which always takes the same account administration advisory lock.

Reproduction schedule: an EmployeeUpdate transaction obtains employee E's row lock. A concurrent EmployeeEmployment transaction obtains the company account advisory lock and waits for E. The update then waits for that advisory lock. PostgreSQL must abort one transaction as a deadlock victim. The ordinary profile update and employment administration paths therefore cannot reliably run concurrently.

Permanent correction: use the same account-advisory-before-domain-row order for every operation entering the shared update core, including EmployeeUpdate. Audit local callers against that same ordering, and cover the two actual concurrent transaction paths in a disposable database regression.

## G2 — P1: Payroll reviewed draft detail is rejected as a company collection

Locations: `hrms-svc/crates/kabipay-organization-protocol/src/lib.rs:193`; `hrms-svc/crates/kabipay-organization-tenant/src/transport.rs:638`; `hrms-svc/crates/kabipay-payroll/src/organization.rs:45`; `hrms-ui/src/modules/organization-workspace/OrganizationPayrollReview.tsx:36`.

`PayrollList` represents both a membership-scoped collection and a cycle-scoped detail read. The shared protocol marks every PayrollList request as a company collection. Before adapter dispatch, the transport consequently requires its resource ID to equal the membership ID and its expected version to equal the membership version.

The actual reviewed draft UI sends PayrollList with `resourceId=cycleId`, the cycle's source version, and `payload.cycle_id=cycleId`. With the normal distinct membership/cycle IDs, transport rejects that request before reaching the adapter's cycle detail branch. This prevents loading the reviewed payroll draft through the intended source flow and blocks the UI path that requires that review before finalization. Passing a membership ID instead cannot solve it: the adapter explicitly requires `cycle_id == resource_id`.

Permanent correction: provide a distinct typed PayrollDetail operation with payroll-cycle resource/version fencing, and retain membership resource/version fencing for PayrollList. Alternatively, derive request-sensitive collection classification only after strict typed payload validation in a common contract; ensure the detail path locks and validates the cycle/resource version rather than bypassing them. Exercise the real UI-shaped source request through the shared transport.

## Reviewed boundaries and limits

- Traced fixed source database use, closed service/operation dispatch, explicit ALL company administration authority, source account guards, request-only password handling in administration and hash-only central command intent, source receipt replay checks, and principal attribution.
- Traced payroll original-intent matching, cryptographically verified fresh authority, live policy lookup, local membership/grant/actor fences, durable claim recovery, business rollback, and terminal lease fencing in the same transaction. No additional confirmed authority bypass was found within those inspected paths.
- Traced central report/archive current authorization before and after external I/O, curated history output, and the archive sidecar's authenticated encryption and complete envelope hash reconciliation. Central itself checks hash shape rather than recomputing envelope hashes, but the sidecar independently verifies those hashes before returning; this is not reported as a demonstrated exploit.
- Inspected critical retention evidence/policy/candidate locking, expiry rechecks and source cleanup receipts. This limited review does not establish complete Node history/capture/retention acceptance, all source migration behavior, or production TLS/ACL/key custody.
- The compressed evidence lists final HTTP, heterogeneous CDC, generated client/browser, requirement matrix and production release checks as unfinished or in flight. This review does not convert any of those into executed evidence or assert all original requirements complete. The frozen baseline was not modified.

No automatic commits were made. The only file written by this reviewer is this requested report.

## Independent correction recheck — 2026-10-19

Both findings above describe the earlier reviewed source and are now **closed at source review**. This addendum preserves the original findings for traceability. Only the changed relevant contracts and their direct callers were read again; this reviewer ran no tests or builds.

### G1 closure

The current transport includes EmployeeUpdate beside EmployeeEmployment in the early company account advisory lock list (`transport.rs:559-567`), before the generic employee row FOR UPDATE (`transport.rs:683`). The subsequent shared core's acquisition of the same transaction advisory lock (`employee_service.rs:1222`) is reentrant. The two organization command paths therefore now share advisory-before-employee-row ordering, removing the reported wait cycle.

The local GraphQL `update_employee` resolver calls `update_for_actor` directly (`resolvers/mutation.rs:423`); that wrapper opens a new transaction and invokes the shared core before acquiring any employee row lock (`employee_service.rs:1210-1223`). The other direct shared-core caller is the organization adapter, now covered by the transport's early advisory lock. No remaining inversion was found among those direct callers.

Runtime evidence is attributed to the root implementer, not independently executed here: root reports HTTP driver session 27224 held the account advisory lock, observed the source update waiting, successfully acquired the employee row FOR UPDATE NOWAIT in the holding transaction, released the advisory lock and observed the update COMMITTED. That schedule directly targets the original inversion.

### G2 closure

The protocol now defines PayrollDetail separately, maps it to the Payroll service, `payroll:manage`, `payroll_run`, and read semantics, and excludes it from `is_company_collection` (`protocol/src/lib.rs:47,86-90,127-131,169-173,203-213,241-243`). Central authority includes PayrollDetail in the explicit ALL-only payroll operations (`runtime_policy.rs:223-231`). The unchanged generic source resource fence consequently handles detail as a payroll cycle and checks its resource version, while PayrollList retains the membership collection fence.

The source adapter requires PayrollDetail's nonempty cycle_id to equal resource_id; PayrollList rejects a cycle_id alias (`kabipay-payroll/src/organization.rs:45-73`). The actual reviewed draft UI now sends PayrollDetail with cycle ID and the cycle's latest source version (`OrganizationPayrollReview.tsx:25-39`). The original collection/detail mismatch is removed without bypassing the source cycle version fence.

Runtime evidence is attributed to root: root reports the real central-to-source PayrollDetail request returned draft/fingerprint, the PayrollList cycle alias was rejected, the UI component contract exercised cycle version 7 versus membership version 19, and generated clients/type/lint/build passed. Root also reports actual payroll finalization of 1000 with restart/revocation acceptance. This reviewer has not independently inspected raw execution output for those reported runs.

These closures do not declare the whole organization feature complete. Root reports full HR and protected archive/report HTTP acceptance and separate lifecycle corrections still in progress; the earlier integration and production release limitations remain applicable.
