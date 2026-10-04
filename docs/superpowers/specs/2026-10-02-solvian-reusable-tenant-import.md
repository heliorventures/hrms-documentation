# Reusable tenant import and Solvian September 2026 setup

Status: approved design; native implementation is in progress. Live execution has not started.

3 October clarification: local validation is now agent-run. Advances remain salary already paid and are excluded from the salary split and deduction totals. Payslip component visibility is configured at company level by HR/Admin, with employer costs hidden by default. Visibility affects presentation only; calculations, snapshots and gross/deduction/net totals retain the complete amounts.

## Outcome and confirmed rules

Provide two distinct utilities: convert a client's raw data into a standard import package, then import that package into a selected tenant. The first Solvian load recreates client data while retaining the reviewed administrative accounts. It configures recurring salary and produces September 2026 payslips for externally paid salary.

The client adapter is specific to the two reviewed muster layouts. Tenant import, reporting, replay protection and reset controls are reusable. No automatic commit, live execution, deployment, or Dart/Flutter command is part of implementation. User-run validation remains the default unless explicitly delegated.

Confirmed by the user:

- Opening leave is 2025 carry-forward; Allotted is the 2026 grant despite the header saying 2025.
- Source leave balance represents balance to date. Unpaid leave has no paid-leave entitlement cap and requires the existing approval workflow.
- Confirmed excess paid-leave usage becomes historical LWP usage; operational EL balances must not be negative.
- Use the Excel payroll formulas. LWP divisor is 31 and remains editable.
- AF-AI supplies the split even where the earlier component columns are blank/NA.
- Annual compensation includes recurring gross multiplied by 12 plus annual employer PF. Other Payable is a period incentive excluded from recurring salary.
- Advance is salary already paid. Employee PF, ESI, PT and TDS are the statutory deduction categories. Additional deductions are configurable and require an HR-entered reason.
- Scripts will be run by the user against actual client schemas. A fresh load may clear tenant client data while retaining Aniket, Ritesh, Solvian HR and Solvian Admin accounts.

## Current source evidence

The reviewed originals contain 19 SCL employee rows and 18 SBL rows. All 37 AF-AI splits reconcile to AE and have proportions 50%, 25%, 12.5%, 12.5%. All Monthly Fix gross values are numeric and positive.

Use the verified source files and fingerprint evidence in `../../client-onboarding/2026-10-02-solvian-import-audit.md`. Do not discover inputs using a broad filename glob; similarly named copies are outside the reviewed import.

PF-wage formulas explicitly use earned Basic + DA, Conveyance and Other Allowance, with employer PF at 13% in the formula-bearing source rows. Basic + HRA happens to give the same numeric result in these sheets, but the configured rule must follow the actual Excel component set. Employee PF, ESI and tax applicability vary in the source and must not be inferred from UAN presence alone.

The current automated statutory calculation is a global simplified stub. The current LWP policy takes one earning component and a fixed divisor; it consumes dated approved requests. These limitations require domain changes for faithful, configurable payroll rather than direct insertion that bypasses normal payroll behavior.

## Two-step operator interface

### Step 1: client conversion

A read-only workbook converter selects an explicit client/layout profile and produces versioned JSON import packages. JSON is the initial machine-readable template container; conversion does not create or edit Excel workbooks.

The converter must:

- Read only the explicit workbook paths, identify employee rows and exclude totals/footer rows.
- Parse source identifiers as strings, money and day quantities as decimal strings, and supported dates as ISO dates.
- Preserve source filename, SHA-256, sheet, row and cell provenance on records and issues.
- Map source data into client-independent sections: Employees, Identity/Bank, Salary Rules/Assignments, Leave Opening Snapshots, Historical Leave Usage, Payroll Period Inputs, and Metadata.
- Separate blank, NA, zero, missing and an explicit clear-value instruction.
- Store only Aadhaar last four in the normalized application data; do not put full Aadhaar or unmasked identifiers into ordinary logs.
- Record conversion issues with issue code, severity, section, source reference and required action. Valid independent sections remain usable.
- Require operator inputs for tenant mapping, salary effective date and leave snapshot as-of date. These dates are not encoded reliably in the raw data and are not silently defaulted.

### Step 2: reusable tenant import

A CLI reads the standard package with no client column knowledge. Default operation is preview. It resolves actual tenant/database/schema mappings and validates prerequisites without changing data.

The preview describes exact preserved accounts, employee/login creation, deletions in reset mode, master/configuration changes, effective salary assignments, leave opening data, period inputs, payroll readiness and unresolved issues. Execution binds to the reviewed input/configuration fingerprints and target identity.

Normal import supports create/update with explicit clears and repeat-safe domain identities. Reset is a separate explicit mode for the first Solvian load, rather than the generic importer's default behavior.

## Recurring salary and employer cost

For each employee, derive split proportions from AF-AI divided by earned gross AE; apply those verified proportions to contractual Monthly Fix gross. The normalized source amounts AF-AI are also retained independently as September reconciliation targets.

Do not copy reduced earned amounts into the recurring structure. Reconcile the recurring split to Monthly Fix gross using decimal arithmetic and a documented final-component rounding adjustment.

Store/show annual gross and annual employer cost separately:

`annual gross = recurring monthly gross * 12`

`annual CTC = annual gross + annual employer PF`

Recurring component calculations must use annual gross as their gross-based percentage denominator. Existing PERCENT_OF_CTC behavior must remain compatible for existing tenants; it cannot be repurposed silently after employer PF is added to CTC. Add an explicit gross basis where needed.

Keep employer PF as an employer-cost rule, not an employee earning or deduction. Calculate recurring employer cost from the recurring wage base, rather than annualizing a September amount reduced by LWP or joining proration. Per-employee source exceptions must appear in the preview rather than being overwritten by a universal inferred rule.

Use effective-dated assignments and immutable/versioned structure rules. A new client import must not mutate a structure that other employees or periods already depend on. Retained management employees need an explicit payroll participation decision in the preview.

## September period inputs and payroll reconciliation

The source September sheet is the reconciliation reference. Inputs retain employee/period identity, provenance, paid/proration days, September LWP days/value, monthly incentive, advances already paid, additional deductions and available source contribution/tax inputs.

Configure the gross-based LWP rule with divisor 31. Preserve differences between the source's fixed-divisor LWP formula and its month/paid-day gross formulas as explicit period calculation rules. Do not force these distinct source formulas into one inferred calculation or subtract the same reduction twice. September earned components, deductions and remaining payable must be reconciled individually against source results, including per-employee exceptions.

Support tenant/employee payroll configuration for the observed component bases, rates, applicability, ceilings and rounding. Source amounts that are hardcoded or do not determine a future rule must remain audited September overrides or review issues; a monthly zero is not proof of permanent exemption.

The normal salary-to-payslip calculation must consume the imported period inputs. Imported monthly LWP totals without dates require a supported period input; do not fabricate approved dated requests. Future dated approved LWP remains supported through the existing workflow. A request/period input may contribute only once, and cumulative imported historical LWP must not automatically contribute to September payroll.

Keep payslip calculation snapshots and clearly distinguish source/import origin from later HR edits. Closed/finalized records must not be silently recalculated on replay. Before September generation, report and resolve conflicting payroll inputs; do not use the existing statutory stub as an unnoticed fallback for this configuration.

## Advances, incentives and additional deductions

Other Payable is an employee/month incentive. It contributes to the period statement and remaining payable but not recurring gross or annual CTC. Its tax/contribution treatment must be explicit in the source-driven calculation; do not infer it from its label.

Advances are employee/month settlement entries:

`earned salary after period adjustments + incentive - statutory deductions - additional deductions = net earned salary`

`net earned salary - advance already paid = remaining payable`

Show advances separately from PF, ESI, PT and TDS. Source AV already includes advances in some rows; normalization must decompose it rather than import it as a deduction and then charge the advance again. Record source advances as externally paid, not as payments made by HRMS. If advance exceeds monthly net, record/report the outstanding credit and require an explicit settlement decision rather than silently creating a negative disbursement.

Additional deductions require amount, reason, employee, period, actor and audit history. Preserve SBL AU11 as a source amount with a missing-reason issue until HR supplies the actual reason. Employee/basic-data import can proceed; that payslip remains unresolved/draft for finalization until its required deduction reason is supplied. Do not invent a business reason.

## Leave opening and history

Maintain per-employee 2026 EL balances with carry-forward from Opening and current-year grant from Allotted. Preserve verified paid usage and the as-of date; future accrual must not re-grant entitlement already represented by the snapshot.

No uniform recurring annual grant is inferred. An employee with no confirmed paid entitlement may use the unpaid type through approval, with zero paid availability rather than an invented entitlement.

When components and source signs reconcile unambiguously, allocate usage to paid entitlement first and excess to historical LWP. For example, entitlement plus carry-forward of 10 with 12 total taken becomes EL used 10, EL balance zero and historical LWP used 2.

Some raw Taken values are signed negatives or source totals disagree. Apply the confirmed column meaning but preserve such discrepancies as explicit per-employee reconciliation issues; do not silently invert signs, treat NA as zero, or manufacture grants. Source absence is recorded as unknown. Aggregate historical usage is not an approved dated request and does not trigger another balance deduction.

LWP is configured as unpaid and has no paid-entitlement restriction. Keep the existing approval, overlap and date validation controls. Show historical LWP usage and dated future approved usage distinctly, with period attribution for payroll.

## Actual-schema reset controls

Generating this utility does not execute it. The user/operator performs preview and execution against actual tenant schemas.

- Resolve the exact tenant mappings; do not reuse hardcoded Consultancy identities for Buildcon.
- Candidate preserved usernames are `aniket.dobhada`, `ritesh.jain`, `solvian.hr` and `solvian.admin`; resolve and display actual matches per tenant before execution. Missing matches are issues, never an excuse to generate or delete another privileged account.
- Retain existing passwords, MFA values, roles/grants and valid employee linkage for preserved users. Preserve tenant identity/subscriptions and migration/permission foundations.
- Define deletion scope through reviewed schema metadata and an explicit allowlist/retention manifest. Never perform an unrestricted cross-schema deletion.
- Require an operator-controlled write pause, verified backup and target/configuration fingerprints before reset execution.
- Normalize and preview before destructive changes. Reset/recreation is transactional within each tenant; import-run provenance must survive recreation or be restored within the same transaction.
- Handle uncertain commit outcomes through persisted run identity and read-only reconciliation before retry.
- Create staff logins only under a reviewed account-creation manifest; use random first-login credentials, protected output and forced password change. Ordinary issue logs contain no credentials.

## Validation and outcomes

Report committed outcomes by employee and section: created, updated, unchanged, partial, deferred and failed. Include missing-field/client-follow-up logs and aggregate counts. Warnings cannot imply salary/payroll readiness when a financial section is unresolved.

Core identity/destination/schema ambiguity blocks the affected employee or tenant batch; optional data omissions defer only the affected field/section. Preserve existing values on normal update unless an explicit clear is provided.

Replay protection uses stable tenant/employee/domain keys and persisted run/section provenance, not file hash alone. Salary assignments, opening snapshots, historical usage, advances, period deductions and payslips must not duplicate on rerun.

Validation covers normalization against the reviewed source, exact September reconciliation, gross/CTC denominator separation, optional-data behavior, account preservation, tenant isolation, no duplicate LWP/advance charging, and atomic reset rollback. User runs approved tests/builds/migrations unless execution is explicitly delegated. Local/static evidence is separate from actual-schema and browser acceptance.

## Delivery boundary

Implementation includes the conversion utility, reusable importer, required payroll/leave domain and schema support, and operator instructions. UI changes are limited to the required payroll input/reason fields and statement details using existing authorization.

Pending operator inputs are explicit CLI/configuration requirements: actual tenant/database identity, effective salary date, leave as-of date, preserved-account matches, new login manifest and write-pause/backup paths. Client corrections or deduction reasons are tracked as issues rather than replaced with guesses.

No live reset, import, September payroll generation, payment, deployment, automatic commit or test/build execution is authorized merely by approval of this written design.
