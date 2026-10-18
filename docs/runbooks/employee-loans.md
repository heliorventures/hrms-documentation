# Employee loans: operation and release gates

This module records payments made outside HRMS. Approving a request does not transfer money or create a repayable principal balance. Record each confirmed disbursement before recovering its funded balance. Payroll, Loans and FNF share the Payroll service and its transaction; each module owns its storage. Employee owns employment, clearance and durable resignation approval operations.

## Company setup

One tenant represents one company. Configure its timezone and currency before creating policy versions. Loan amounts and rates use decimal strings; do not import binary floating-point values. Payroll currently supports loan recovery in its existing INR/two-decimal calculation contract. Other currencies remain available for separately tracked loans and are rejected for unsupported Payroll recovery.

Enable the independently entitled `LOANS` module deliberately. Assign exact permissions and scopes: employee `loan:read` and `loan:submit` SELF; HR permissions as required for approval, disbursement, repayment, management, policies, corrections, exit review and export. A role name alone grants no authority. HR resignation/FNF operations require `onboarding:manage` ALL. Workflow administration requires its existing workflow management authority.

Create an active LOAN_REQUEST workflow with nonempty configured `loan:approve` steps before publishing a policy. Policy decisions include eligibility, exposure, interest limits, allocation, payroll capacity protections, overrides, residual recovery and reviewed set-off/tax references. Publish immutable versions; retire overlapping active policy versions before activating a replacement. Existing account terms retain their approved policy reference.

Navigation: **Loans → My loans**, **Loan administration**, **Loan policies**. Policy setup links to **Workflows** with the Loans domain selected. Resignation and FNF review remain under **Hiring & Exit → Onboarding and exit**.

## Private service configuration

Both Employee and Payroll must receive the same independently generated `KABIPAY_FINANCE_SERVICE_SECRET`, at least 32 bytes. Store it in the deployment secret manager. It is separate from browser JWT signing and must never be printed in logs or committed.

- Payroll: `KABIPAY_FINANCE_EMPLOYEE_URL` is the internal Employee service origin.
- Employee: `KABIPAY_FINANCE_PAYROLL_URL` is the internal Payroll service origin.

Origins must use HTTP/HTTPS and contain no credentials, query, fragment or path. The transport adds `/internal/finance`. Use private networking or authenticated TLS and deny public ingress to that route. Requests and responses are signed and bound to tenant, caller, recipient, action, request ID and time. Service clocks must be synchronized. Transport timeouts do not cancel an approval or release a financial hold.

Release Employee and Payroll together with the transferred FNF schema ownership and matching gateway. Deploy matching secret configuration to both services. There is currently no dual-key rotation window; coordinate rotation and verify private calls before accepting financial work.

### VPS environment preparation

`scripts/deploy-on-vps.ps1 -Deploy` includes `-SyncEnvExample`. Reconciliation now adds missing template defaults while preserving all existing environment values. It deliberately updates the image tag, migrates legacy JWT aliases to the canonical key, and removes the legacy global `DATABASE_URL` override. Edit the VPS `.env` explicitly when changing an existing setting; changing `.env.example` no longer rotates credentials or replaces operator configuration.

The blank `KABIPAY_FINANCE_SERVICE_SECRET` template entry is never copied as a shared example secret. When the VPS value is missing or empty, reconciliation generates 32 random bytes as 64 hexadecimal characters on the VPS. Subsequent releases retain that value. The `.env` and timestamped backups have mode `0600`. Include them in the protected configuration backup; do not paste them into logs or commit them. Existing invalid or reused JWT/Finance secrets stop deployment before environment replacement.

The default origins `http://127.0.0.1:4013` and `http://127.0.0.1:4016` apply to the current Compose layout, where Employee and Payroll run in the same `kabipay-subgraphs` container. Adjust both origins explicitly if ports or service topology change. Preflight accepts ASCII DNS names, canonical four-part IPv4 addresses, and pure hexadecimal IPv6 addresses (including compression). Other address forms fail closed. Finance settings and the canonical JWT signing key must be single-line literal dotenv values without variable interpolation or backslash escapes, so preflight can validate the effective values without evaluating configuration. The value or opening quote must start immediately after `=`; quote intentional leading spaces. Simple single- or double-quoted literals and trailing comments follow the [Compose dotenv syntax](https://docs.docker.com/compose/how-tos/environment-variables/variable-interpolation/). Existing values are preserved; unsupported syntax stops deployment before restart.

Every `-Up` validates required Finance settings before restarting containers, including when general post-deployment validation is skipped. Normal post-deployment validation also checks that the running subgraphs container received the exact configured Finance secret and origins, without printing their values. Configuration propagation does not prove a successful signed business operation: complete the resignation/FNF acceptance and worker reconciliation checks below before enabling financial work.

Local deployment regressions use disposable containers and dummy credentials only:

```powershell
node --test scripts/tests/deploy-env.test.cjs
```

Run from `hrms-documentation` with Node and Docker available. The tests use the cached `postgres:16` image with networking disabled; they do not contact the VPS.

The database repository also retains the actual full-master/full-tenant Liquibase rehearsal, including repeat-update history checks and the three exact prior loan checksums:

```powershell
powershell.exe -NoProfile -File tests/migrations/test-full-liquibase.ps1
```

Run from `hrms-database` with Node, installed npm dependencies, Java 17 and the cached `postgres:16-alpine` image. It creates its own database, uses only a random loopback port and removes its unique container and temporary files. It never loads repository connection settings. This remains a fresh-database regression; rehearse actual target history and data separately on a disposable restored tenant before production.

## Routine financial work

Record actual disbursements and receipts with the original external reference, method, value date and reviewed evidence reference. Do not record an intended transfer as a completed payment. Duplicate submissions use the original idempotency key; never change that key merely because the response was lost.

HR can configure a future monthly arrangement, a permitted one-period amount or a permitted skip/accrual pause. Forecast schedules are projections; ledger entries and issued evidence represent actual recovery. Payroll recalculation is required after loan inputs or the cycle payment date change. Finalization waits until the payment date in company time and rejects stale reviewed versions.

Cancel unused approval capacity explicitly when it is no longer needed. This operation does not waive existing principal or interest, create a repayment or erase historical evidence. Repaying a partially funded cancelled loan must preserve the cancellation and close only the actual debt.

For a payment on or after a pending resignation request, an HR/Admin exception requires an explicit reason and `onboarding:manage` ALL in addition to `loan:disburse` ALL. Employee supplies authoritative pending status through the signed private service boundary. Resignation submission and funding use the shared financial lock. Payment evidence retains the verified separation reference and reason; company-wide readers can review the reason in payment history. Employee readers continue to see their payment amounts and references. A durable successful retry returns its original result if HR status later changes.

For an incorrect historical external payment, HR reviews the recalculated reversal and confirms the current adjustment with a reason and reconciliation reference. For an omitted earlier payment, choose **Review earlier repayment** or **Review earlier disbursement** on the account. Both require the corresponding payment permission ALL and `loan:correct` ALL. Review current and corrected principal/interest, original payment date, current posting date and preserved issued allocations before confirming. The server repeats the calculation and rejects a changed fingerprint or account version. Original external payment dates remain evidence; the loan ledger records the current correction. Issued payslips/FNF evidence remain unchanged.

Historical replay uses recorded occurrence dates and existing ledger order within each day; a newly entered event follows existing events on the same date. Excess credit/refund cases fail closed. Late funding also requires unused approval capacity and is unavailable after unused funding cancellation or a confirmed exit arrangement. Do not substitute a false current payment date. Write-offs, credit refunds and waivers remain outside the approved first-release command set and must not be represented as ordinary repayments.

The account's **Financial check** is available to HR with `loan:manage` ALL. A bounded private worker also checks new/changed accounts and revisits unchanged accounts daily. Checks compare ledger/posting/allocation totals, recorded payments/credits and issued Payroll/FNF sources in both directions. Issued recovery verification also requires matching source revision, value date, approved terms and calculation fingerprint; equal amounts alone do not verify the source. Each run retains an immutable result. Exceptions hold further Payroll/FNF loan recovery for that employee until a subsequent successful check verifies the evidence; checking does not repair the ledger or alter issued records. Resolve the cited source through the authorized financial process, then run the check again. Private event acknowledgements occur only after every affected account has a current report and are deduplicated transactionally. Exit approval holds continue to require authoritative Employee operation reconciliation separately.

## Resignation and FNF

Before approving resignation, review current funded principal, posted interest, earned unposted interest, forecast payoff, unused commitment and unapplied credit. Specify final Payroll and FNF amounts separately. Any continuing balance requires an allowed arrangement, next due date, monthly amount, active named follow-up owner and agreement reference. Approval records the decision; it does not post recovery.

Payroll coverage shows the latest 12 issued salary references and all prepared draft cycles for this employee. Choose the final draft cycle from that list; references are revalidated before authorization. FNF can attach an issued payslip as a reference, with its immutable net amount. Such a reference is excluded from both new FNF earnings and loan set-off capacity. An issued payslip is not proof of a bank payment. Payslip loan links open the authorized account workspace with a shareable `?loan=` reference.

HR approval first registers a durable Employee operation, then obtains Finance authorization, then commits the HR transition and private confirmation event atomically. The background workers retry private confirmation/cancellation and reconcile authoritative HR outcomes. An expired or unreachable operation remains held; never release it by deleting guard rows or by assuming a timeout means cancellation.

After an uncertain response, reopen the financial approval screen. Resume the saved review as the initiating HR user, or explicitly acknowledge cancellation of a REGISTERED operation and reload authoritative status before preparing a new decision. A COMMITTED operation cannot be cancelled; refresh its recorded result. Cancellation may need worker reconciliation before Loan writes become available again.

FNF requires explicitly reviewed benefit amounts, amounts already paid, OTHER recoveries and source-specific loan eligibility. Enter explicit zero only after resolving that component. Issued final salary is a Payroll reference and must not be added again as FNF earnings. Calculate and save the review before finalizing; editing the date or any source requires a new saved calculation. Finalization requotes and atomically posts Loan recovery, source allocations and immutable FNF evidence.

Example: payoff 20,000; eligible available FNF 12,000; loan recovery 12,000; employee cash zero; continuing loan receivable 8,000. Show all outcomes separately. An issued settlement stops the old Payroll loan recovery; rehire does not restore the old plan automatically. Former employee access is not automatically reopened; HR can export an authorized statement.

## Migration and rollout

Back up each tenant database and review the full Liquibase upgrade in a disposable restored copy first. Release additive 0103 Loans, 0104 catalogue/permissions, 0105 immutable payslip evidence, 0106 exit coordination, 0107 immutable reconciliation results, 0108 reviewed late-payment validation and 0109 contractual repayment dates before the coordinated services/gateway and UI. Never run a destructive rollback against accounts or posted financial records.

Migration 0109 adds a nullable first repayment date without rewriting issued evidence or existing schedule rows. Existing arrangements use the earliest original schedule item as date evidence. If an old arrangement has no usable date, HR must save an explicit reviewed deduction arrangement; the system does not invent a date. Skips and short recoveries continue within the reviewed term even after the original forecast ends. Outstanding debt beyond that term blocks automatic Payroll recovery with `LOAN_REPAYMENT_REVIEW_REQUIRED`, requiring HR to review the balance and configure a new arrangement within company policy.

Deduction changes and period overrides have read-only financial previews using the same validation and calculations as saving. Select Skip explicitly; a blank or zero amount is not a skip instruction. Previews show contractual dates, applicable valuation dates, expected completion, projected interest and residual balance. Unfunded projections label the assumed funding date, which cannot precede the approved terms' effective date. The employee schedule follows saved arrangements, including future changes; it does not accept an arbitrary replacement repayment date.

Preflight existing FNF duplicates in each intended tenant schema (read-only; substitute the verified schema identifier):

```sql
SELECT tenant_id, separation_id, COUNT(*)
FROM "verified_tenant_schema".fnf_settlement
GROUP BY tenant_id, separation_id
HAVING COUNT(*) > 1;
```

Resolve duplicates through an approved evidence-preserving reconciliation before adding the unique constraint. Preserve existing processed FNF records and IDs. Classify old generic recovery explicitly as OTHER until reviewed; do not seed loan balances or reclassify all old recovery as a loan. Opening balances and imports require a separate approved migration.

After schema readiness: deploy coordinated services/private workers/gateway, deploy generated UI, configure policy/workflow/permissions, perform authenticated acceptance, then explicitly activate the tenant. Do not enable recovery merely because XML validation or compilation passed.

## Local evidence and release acceptance

Run native executables from the appropriate repository. On Windows with limited C: space, set TEMP and TMP to a writable D: directory before Cargo/Vite. Keep active Cargo build folders intact.

```powershell
# hrms-svc: separate invocations; do not overlap Cargo checks.
py -3 scripts/check_loan_boundaries.py
cargo test --offline -p kabipay-payroll --lib
powershell -NoProfile -File scripts/test-loans.ps1
powershell -NoProfile -File scripts/test-loans.ps1 -Payroll
powershell -NoProfile -File scripts/test-loans.ps1 -Exit

# hrms-database: XML/structure checks are not a full tenant upgrade.
py -3 tests/migrations/validate_loan_xml.py
py -3 -m unittest discover -s tests/migrations -p test_loan_exit_coordination.py
py -3 tests/migrations/test_loan_reconciliation.py

# hrms-ui, after exporting both actual service schemas and regenerating the client.
npx vitest run src/modules/loans src/hooks/useRetainedQuery.test.tsx
npx tsc --noEmit
npx eslint src/modules/loans src/routes/loanRouteConfig.tsx
npm.cmd run build

# hrms-gateway
npm.cmd test
npm.cmd run build
```

Production acceptance additionally requires actual full tenant Liquibase upgrade, current disposable database suites including concurrency/rollback, authenticated HR and employee browser flows, mobile/dark/keyboard review, browser print and PDF payslips, lost-response approval recovery, unsupported currency behavior, private network/secret checks and operational reconciliation. Static checks and earlier suite results do not prove newly changed financial paths.

The execution ledgers at `.loan-implementation/progress.md` and `.loan-implementation/review-fixes-progress.md` record local results and unresolved gates. No local check authorizes deployment, live tenant migration, grants or activation.

### 11 October review corrections

The eight code-review findings were corrected: recurring recovery after skips or short salary, intermediate workflow approval, calendar-period interest pauses, future arrangements, explicit skips, read-only proposed-change previews, returned decision reasons and withdrawal during review. Follow-up regressions cover overdue contractual dates for funded, unfunded and continuing arrangements; future permitted funding dates; and zero-balance completion status.

Migration 0109 must precede the updated services. New previews are owned by Payroll and the isolated UI client is generated from the actual exported service SDL. Independent scoped financial, workflow and UI/API reviews found no remaining concrete blockers in these corrections.

Confirmed local checks: 37 Loans PostgreSQL tests, 24 domain tests, 72 Payroll library tests, 2 Loan schema/authorization tests, 19 PostgreSQL Payroll/FNF tests, 4 PostgreSQL Employee exit tests, 81 UI tests and 13 gateway tests. UI and gateway builds, TypeScript, focused Loan lint/Clippy, GraphQL caller checks, private-storage boundaries, eight migration XML validations and the additive-anchor structural regression passed.

The updated Pencil approval, skip and summary states remain pending because no design document is open in the editor. Full restored-tenant Liquibase upgrade, authenticated browser acceptance and deployed-environment checks above remain release gates; this local evidence is not a zero-defect guarantee.
