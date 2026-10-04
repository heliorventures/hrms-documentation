# Solvian updated muster: source and system audit

Audit date: 2 October 2026. Scope approved: read-only workbook and source-code investigation.

This is an evidence report and proposed direction, not an approved implementation specification. No tenant database was queried or changed. No import, payroll run, migration, deployment, account reset, or commit was performed. Employee names, salaries, and full personal identifiers are excluded from this report.

## Source files and verified scope

Only the two explicitly requested files were audited; similarly named copies are excluded.

| Item | Consultancy (SCL) | Buildcon (SBL) |
| --- | --- | --- |
| File under `ClientDocumenation` | `Salary Muster FY 2026-27 SCL.xlsx` | `Salary Muster FY 2026-27 SBL.xlsx` |
| Company label inside workbook | Solvian Consultancy LLP | Solvian Buildcon LLP |
| Working-sheet period | September 2026 | September 2026 |
| Worksheet / header row | Sheet1 / 7 | Sheet1 / 6 |
| Employee data rows | 8-26 | 7-24 |
| Employee rows | 19 | 18 |
| Total row, excluded from employee count | 27 | 25 |
| Numeric employee-row formulas checked | 55 | 70 |
| Formula cache differences greater than 0.02 in those checks | 0 | 0 |
| Date system | Excel 1900 | Excel 1900 |

Source fingerprints, SHA-256:

- SCL: `6793a2ac89736e97355015eaaa9a5cd493092afdd8724b0e6976a321744a6cef`
- SBL: `01ed8b6d5c51f9a2b17b3af1a98295a6c134b2abb9983a5b9fb4be55cefee20d`

The formula check evaluates the arithmetic and SUM expressions found in numeric employee cells against their stored referenced values. It is not an Excel recalculation, visual review, or payroll acceptance test. Formula results agreeing with cached values does not establish that the business rule is correct.

## Source mapping evidence

Columns are shown as SCL / SBL. Proposed destination names describe logical template fields, not newly implemented API fields.

| Data | Source columns SCL / SBL | Interpretation or decision needed |
| --- | --- | --- |
| Employee identifier and name | D,F / D,F | Match within an explicitly selected tenant; missing identifiers need reviewed mappings |
| UAN | E / G | SBL E is a second UAN-labelled column and is entirely blank; SBL G contains 7 values; SCL E contains 5 |
| Designation and department | G,H / H,I | Resolve tenant-owned master records |
| DOB and joining date | I,J / J,K | Dates mix Excel serials and DD.MM.YYYY text |
| Confirmation date | K / L | Some missing; do not substitute joining date |
| Exit and last working date | L,M / M,N | Empty throughout these employee rows; employee status still needs an explicit import policy |
| Leave date text | N / O | SCL has 5 populated cells, some with ordinal dates, omitted years, or ranges; SBL has none |
| Opening leave, allotted, taken, balance | O:P:Q:R / P:Q:R:S | Year, signed-value semantics and opening-balance meaning are unresolved |
| Days for month and present days | S,T / T,U | Every month-day value is 30 |
| LWD in Days | U / V | LWP amount formulas reference this field; the header's meaning needs confirmation |
| Basic + DA, HRA, conveyance, other | V:W:X:Y / W:X:Y:Z | Some formula amounts use earned monthly gross rather than contractual fixed gross |
| Monthly Fix gross | Z / AA | Numeric and positive for all 37 employee rows; contractual meaning still needs confirmation |
| Allowance / OT | AA / AB | Period-specific amount; not automatically a recurring structure component |
| Paid-day field used by gross formulas | AB / AC | SCL label is Present Days; SBL label is No. Of Days |
| Explicit Leave (LWP) days | AC / no equivalent labelled field | Do not interpret SBL AC as LWP days |
| LWP amount | AD / AD | Formula uses fixed gross / 31 times U or V in relevant rows |
| Earned Monthly Gross | AE / AE | Payroll period result, separate from permanent salary configuration |
| Earned component split | AF:AG:AH:AI / AF:AG:AH:AI | Separate from agreed recurring monthly components |
| PF wage, ceiling, employee and employer amounts | AJ:AK:AL:AM / same | Import account identifiers separately from contribution rules and historical amounts |
| ESI wage, employee and employer amounts | AN:AO:AP / same | Eligibility and wage-base rules need confirmation |
| PT, dues, advance, TDS, other deduction | AQ:AR:AS:AT:AU / same | Historical amounts do not automatically become recurring deductions |
| Total deduction, other payable, net | AV:AW:AX / same | Reconciliation references; not salary structure inputs |
| PAN and Aadhaar | BE,BF / BB,BC | Existing Aadhaar model stores last four digits only |
| Second DOB column | BG / BD | Conflicts with primary DOB on specified rows below |
| Bank account holder, number, type, bank, branch, IFSC | BH:BI:BJ:BK:BL:BM / BE:BF:BG:BH:BI:BJ | Preserve account numbers as identifiers; source account-holder and branch fields need a supported destination decision |
| Gender | BA / no labelled equivalent | Do not derive gender from employee names |

Neither workbook has dedicated fields for pending approval totals, planned-leave status, manager, contact details, or a salary effective date. Blank, NA, zero and not-applicable must remain distinguishable. The older SCL employee workbook is outside this audit's data scope; enrichment from it requires an explicit source-precedence decision.

## Data issues to take to the client

All row references below are worksheet row numbers, not employee serial numbers.

| Finding | SCL rows | SBL rows | Proposed treatment |
| --- | --- | --- | --- |
| Employee code missing | 24,25,26 | 23,24 | Require reviewed existing-employee mapping or new codes before creating/updating that employee |
| Contractual split missing or nonnumeric | 9,10,11,15,19 | 7,8,19,22,23,24 | Keep valid employee information; defer salary configuration unless the client confirms a calculation rule |
| Numeric split differs from Monthly Fix gross | 16,18,23,26 | 11,17 | Determine whether this is an earned-pay split, proration, or a source correction; do not copy into permanent salary |
| Negative Leave Balance | 16,18,22,23 | 11,17,18,21,22 | Preserve source evidence; confirm debt/LWP/adjustment semantics |
| Negative Leave taken till date | 22,23 | 11,17,21,22,23 | Do not invert signs or interpret as used days without confirmation |
| Complete numeric leave components do not satisfy opening + allotted - taken = balance | 20,23 | 17 | Client reconciliation required; checks use fully numeric components |
| DOB columns disagree after date parsing | 11 | 9,24 | Skip disputed optional DOB field and log both cell references for review |
| Primary DOB is on/after joining date | 11 | None | Client correction required; employee import may continue without this optional DOB |
| Aadhaar missing | 9,18 | None | Field-level warning; retain any existing value |
| Bank account number missing | None | 7,8,12 | Keep employee and salary import independent; report bank section as incomplete |
| IFSC missing | None | 7,8,9,10,12 | Do not create an incomplete bank record or invent IFSC |
| Same bank account value on two employees | None | 10 and 13 | Request bank confirmation; do not merge employees |
| Positive source LWP amount | 16,18,23 | 11,17,22,23 | Determine historical/already-paid status before any deduction is eligible for payroll |

Every populated PAN, Aadhaar, UAN and IFSC examined passed a basic string-format check. This is not identity, bank or statutory verification. No matching nonblank PAN, full Aadhaar, name or employee-code value was found across the two workbooks; tenant-scoped identity resolution is still mandatory.

Additional source-rule observations:

- Both leave-allotment headers explicitly say `yr 2025`, despite September 2026 working-sheet titles and FY 2026-27 filenames.
- Several formulas calculate 50% Basic + DA, 25% HRA, 12.5% conveyance and 12.5% other allowance from AE, the earned monthly gross. This does not prove a universal contractual split.
- LWP formulas use fixed gross / 31, while other gross formulas use the 30-day month field and paid-day count. The intended rule cannot be selected from the filename or month alone.
- SCL total-deduction formulas at AV8 and AV11 reference AU twice. The cached result currently agrees with its formula; duplicate inclusion still needs client review if that deduction becomes nonzero.
- Textual leave dates do not establish whether leave was EL, unpaid, approved, pending, used or planned. No dated leave requests should be fabricated from these totals.

## Verified current-system capabilities and limitations

### Salary

The current payroll model supports salary components, structures, effective-dated employee assignments and employee overrides. Calculation bases are FIXED_MONTHLY, FIXED_ANNUAL, PERCENT_OF_CTC and PERCENT_OF_BASIC. FIXED_MONTHLY is annualized by multiplying by 12 and converted back to monthly breakup amounts by dividing annual amounts by 12.

The assignment field is named `ctc`. Annual gross and total employer cost cannot be silently treated as interchangeable. A confirmed definition is needed before populating it or selecting PERCENT_OF_CTC rules. Payroll resolves the assignment effective at the first day of the payroll month.

Two implementation details also need acceptance coverage: the breakup resolves annual basic before employee overrides, so percentage-of-basic components combined with a basic override need verification; the payroll run processes active employees and falls back to employment-history salary when no structure exists. A successful basic-data import with deferred salary is therefore not proof of payroll readiness. The cutover needs an explicit readiness check rather than relying on import success alone.

The existing Consultancy reset script is a destructive tenant replacement, uses the older workbook and creates monthly employment-history salary values rather than salary structures. Its workflow does not meet this reusable update-import requirement.

Sources:

- `hrms-svc/crates/kabipay-db-entities/src/tenant/d0012_payroll.rs`
- `hrms-svc/crates/kabipay-payroll/src/services/payroll_service.rs`, calculation basis validation, amount_from_rule, salary_breakup_for_structure and run_payroll_for_cycle
- `hrms-database/scripts/reset-solvian-consultancy-from-workbook.cjs` and its operator documentation

### Leave

The model separates annual policy from employee balances: entitled, carried forward, used, pending and balance. The current balance formula is entitled + carried forward - used - pending. Pending means reserved days for requests awaiting approval, rather than unused leave.

The current leave service refuses a computed negative available balance. Negative source balances need a confirmed business treatment and, if retained as operational balances, a consistent domain change covering imports, future reservations, approvals, adjustments and accrual. Direct database insertion would bypass that rule and leave later operations inconsistent.

The current year and monthly-accrual calculations use January-December. Annual entitlement takes precedence over monthly accrual when both are populated. If the client uses an April-March leave year or annual quota plus monthly vesting, that must be designed explicitly.

A historical used-days snapshot can preserve aggregate usage without inventing past requests. Pending/planned requests require dates and status, plus cutover rules to avoid reserving the same days twice. Missing pending/planned data must be reported as unknown rather than assumed to be zero.

Sources:

- `hrms-svc/crates/kabipay-db-entities/src/tenant/d0011_leave.rs`
- `hrms-svc/crates/kabipay-leave/src/services/leave_service.rs`, apply_balance_movement and balance_days_from_components
- `hrms-svc/crates/kabipay-leave/src/services/leave_admin.rs`, entitled_days_from_policy_as_of

### LWP and payslips

The current tenant policy supports an enabled flag, one earning-component code, a fixed numeric divisor and before/after-statutory treatment. Calculation uses that earning component / configured divisor times approved unpaid days. It consumes approved, dated, non-deleted unpaid leave requests and records immutable date allocations and payslip calculation snapshots. The manual salary-structure code UNPAID_LEAVE is explicitly forbidden to avoid duplicate deductions.

The current payslip document already displays unpaid days, the calculation and the treatment. It can show the result after the correct policy and supported source records exist.

The workbook's gross-based formulas cannot be reproduced simply by selecting BASIC in this policy. Monthly LWP totals without dates also cannot feed the existing request-driven calculation. Depending on confirmed scope, use verified dated requests or design an audited payroll-period input with source provenance and consumption tracking; neither invent dates nor charge already-paid amounts again.

Automated statutory payroll calls `statutory_india::compute`, which is explicitly a simplified stub. Its wage-base, employer-PF and tax handling differ from fields/formulas in these workbooks. Importing salary structures alone does not prove that the system will reproduce the client's net salary. Employee applicability, wage bases, caps, employer costs, tax handling and rounding need separate confirmed payroll acceptance cases.

Sources:

- `hrms-svc/crates/kabipay-payroll/src/services/unpaid_leave_policy.rs`
- `hrms-svc/crates/kabipay-payroll/src/services/unpaid_leave_calculation.rs`
- `hrms-svc/crates/kabipay-payroll/src/services/unpaid_leave_allocation.rs`
- `hrms-svc/crates/kabipay-payroll/src/services/statutory_india.rs`
- `hrms-ui/src/modules/payroll/components/PayslipDocument.tsx`

### Employee and bank information

Existing employee records have optional user linkage, required employee code/name/joining date, and UAN/ESIC fields. PAN, Aadhaar last four, and bank records are separate. A bank record requires account number, IFSC and bank name. The reviewed employee-bank model has no account-holder-name or branch field. The employee profile has no direct confirmation-date field. These fields need an explicit supported destination and display requirement; storing them invisibly in custom fields should not be presented as an accessible feature.

Existing login credentials and roles should be preserved during updates. The workbooks do not provide login-provisioning instructions. Imported PAN/bank details must not be marked verified merely because they pass formatting checks.

Source: `hrms-svc/crates/kabipay-db-entities/src/tenant/d0007_employee_core.rs` and `kabipay-employee/src/services/employee_service.rs`.

## Recommended two-step direction, subject to decisions below

1. **Client conversion adapter:** Read the raw workbook with a layout-specific profile, distinguish fixed compensation from payroll-period results, normalize typed data, and produce a versioned standard import package plus conversion issues. Record source file hash, sheet, row and cell references. Require explicit tenant mapping and business-rule inputs. Keep original files unchanged.
2. **Reusable tenant importer:** Consume only the standard package. Validate tenant identity, schema compatibility, employee matches, domain rules and references; preview creates/updates/unchanged/deferred results; then apply an approved plan through shared domain logic. The core must not contain SCL/SBL column positions or Solvian-specific salary assumptions.

Logical template datasets would cover Employees, Bank/Identity Details, Salary Components/Rules, Salary Assignments, Leave Policies, Leave Opening Snapshots, optional dated Leave Requests, optional Payroll-Period Inputs, and Import Metadata. The concrete container format and operator interface remain to be selected.

| Approach | Trade-off |
| --- | --- |
| Client adapters + versioned template + shared domain-backed importer (recommended) | Reusable across tenants; keeps business rules consistent; requires deliberate import boundaries and replay tracking |
| Extend the old client scripts to write each table | Quicker initial scripting, but duplicates payroll/leave rules and couples import behavior to a client layout |
| Build a complete upload/mapping UI first | Useful for frequent HR-operated imports, but adds UI/workflow scope before business rules are confirmed |

Recommended validation behavior:

- Missing optional data: import valid sections, log warnings, and preserve existing values. Blank source data must not erase existing values by default; explicit clearing needs separate intent.
- Invalid/conflicting data: defer the affected field or section and continue independent records. For example, valid employee data can succeed while salary is deferred.
- Missing essential employee identity: defer that employee and dependent sections; other employees continue. Do not guess a match from a name or worksheet row.
- Tenant identity, incompatible schema or unreadable/template-invalid input: stop the affected tenant batch. Continuing would make the import destination or meaning uncertain.
- Each written section must be transactional. Report success only after commit. Handle an uncertain commit by reconciling stored run/section identity before retrying.
- Corrected-file reruns must not duplicate assignments, leave usage or requests. Use stable tenant/employee/domain keys and stored import-run provenance; file hash alone is insufficient.
- Preserve existing attendance, requests, payslips, roles, credentials and employees absent from the source. A proposed import is an update/create operation, not roster deletion.
- Version salary rules and effective assignments rather than changing a shared structure that other employees or periods depend on.
- Leave snapshot replacement must account for transactions occurring after its as-of date and for accrual already represented in the source.
- Logs should include run ID, tenant, source row/cell, section, issue code, severity, proposed action, final outcome and client-follow-up reason. Mask sensitive values and protect any export containing employee details. Summary statuses should distinguish imported, updated, unchanged, partial, deferred and failed, with per-section counts.

## Decisions still required

1. Exact tenant codes/identities and target environment; operator CLI utility or in-application upload flow; reviewed identity mapping for the five rows without employee codes.
2. Salary effective date and leave snapshot as-of date per tenant; whether September payroll has already been paid; whether September figures need historical import, reconciliation only, or a new payroll run.
3. Meaning of Monthly Fix gross; annual gross versus total CTC; approved contractual splits for regular and blank/NA-component rows; treatment of employer costs, variable pay and employee exceptions.
4. Leave year behind the 2025 label; EL annual quota, annual grant versus monthly accrual, joining/confirmation eligibility, carry-forward rules and applicability of NA.
5. Meaning and treatment of negative taken/balance values; whether the client term pending means remaining leave or pending approval; dates/status for any actual pending/planned requests.
6. LWP basis (basic/gross/component set), divisor (fixed or calendar days), before/after-statutory treatment, component allocation/rounding, dated versus month-total inputs, and prevention of double charging historical deductions.
7. Confirmed employee-level payroll applicability and calculation cases for PF, ESI, PT, TDS, advances/other deductions, and rounding before promising workbook-to-payslip parity.
8. Corrections for conflicting DOBs and the shared bank-account value; destination/access requirements for bank holder, branch and confirmation date; whether the older SCL workbook may fill missing fields.

## Verification limits and next stage

The counts, column mappings and source issues above were checked directly against the two workbooks. The system capabilities were checked in current local source. Database contents, deployed migrations, tenant mappings, existing employee matches, API behavior, payroll reconciliation and browser rendering remain unverified.

Implementation depends on the business-rule responses and an approved concrete design. No build, test suite, lint, typecheck or migration was run. The diagnostic was read-only with respect to workbooks and databases; its only output was structural/issue evidence. Existing unrelated changes in the database, UI and documentation repositories were preserved.

## Follow-up: client rules and revised direction

User clarification received on 2 October 2026:

- Configure actual recurring salary from the September data and generate September 2026 payslips. Payment is external to HRMS.
- Use a configurable divisor of 31 for LWP.
- Annual compensation should show recurring monthly gross multiplied by 12 plus annual employer PF. Monthly Other Payable is an incentive/period earning and is excluded from recurring salary.
- Advance is salary already paid, rather than an extra earning or an additional statutory deduction. User identifies the statutory deduction categories as employee PF, ESI, PT and TDS.
- Some leave allocations may originate in 2025 and carry into 2026; other allocations may originate in 2026. There is no confirmed uniform policy. Source balance is understood to be balance to date.
- Convert confirmed excess paid-leave usage to historical unpaid-leave usage rather than operating negative EL balances. LWP should require approval without a paid-leave quota restriction.
- User prefers a fresh tenant reset/import preserving Aniket, Ritesh, Solvian HR and Solvian Admin accounts. This supersedes the earlier update/create-only proposal for the initial Solvian load. Reusable import should still support normal update/create mode and a separately controlled reset mode.

These are design inputs, not records of an executed reset or import.

### Follow-up source verification

- `leave_service.rs` reserves paid-leave balance only when `lt.is_paid && !uses_comp_off`; unpaid requests already use the required approval workflow without that reservation. Preserve date/overlap and approval controls while configuring LWP as unpaid.
- PF-wage formulas AJ8 (SCL) and AJ7 (SBL) explicitly use AF + AH + AI: earned Basic + DA, conveyance and other allowance. Employer-PF formulas use AJ multiplied by 13% in the formula-bearing rows reviewed. Every employee-row PF wage numerically equals both Basic + HRA and Basic + Conveyance + Other in this source because HRA equals those two other allowances combined. Numeric agreement does not decide the future wage-base rule.
- SBL has a nonzero Other Deduction at AU11. This needs classification because the user identifies only four statutory deduction categories.
- Advance is populated on SCL row 9 and SBL rows 9,10,14,16. Other Payable is populated on SCL row 22 and SBL rows 9,16. Treat these as employee/period inputs, not shared recurring structure amounts.
- The existing reset allowlist contains only `aniket.dobhada` and `ritesh.jain`. The management-account utility defines `solvian.hr` and `solvian.admin`. The current reset cannot be reused unchanged to satisfy the expanded account-preservation requirement.

### Proposed salary-advance representation

Keep the employee's full salary entitlement intact. Store advance paid as an employee/period settlement entry and show it separately from statutory deductions:

`earned salary after LWP + monthly incentive - (PF + ESI + PT + TDS) = net earned salary`

`net earned salary - salary advance already paid = remaining payable`

The statement should show both net earned salary and remaining payable. Do not increase gross/CTC by the advance, charge it as a recurring structure deduction, or subtract it twice through both source Total Deduction and a separate settlement line. An advance exceeding that month's net needs a confirmed treatment for the remaining credit; it should not silently become a negative payment.

### Leave conversion boundary

For a confirmed example of 10 paid days available and 12 taken, import 10 EL used, zero EL remaining and 2 historical LWP used. Keep that historical counter separate from September payroll LWP. A negative balance can be cumulative across several months; its absolute value is not automatically September's unpaid days.

The row-level distinction between 2025 carry-forward and 2026 allocation remains unconfirmed. Ask whether Opening maps to carry-forward and Allotted maps to the 2026 grant despite the 2025 header. Avoid automatic recurring grants until allocation/eligibility is confirmed.

For source totals without exact dates, a supported historical usage/period-input record is required rather than invented approved leave requests. Record the source September days and amounts once and reconcile the generated September statement against them.

### Revised reset boundary

Preparation must resolve the two actual tenant identities and target environment, preview the deletion scope and exact preserved users, take and verify a backup, and preserve authentication values, roles, tenant mappings/subscriptions and schema foundations. Retained users need valid linked employee records and usable approval permissions after recreation. Application writes must be paused for the reset/import window. No reset should leave a tenant committed with its imported financial sections silently missing; complete normalization and dry-run validation before destructive execution, then keep reset/recreation transactional.

Optional missing data should remain row/section issues, not block an otherwise valid dataset. Salary/leave sections with unresolved rules must be clearly deferred in the reviewed plan rather than reported as ready or fabricated during reset.

### Remaining decisions after this clarification

1. Opening versus allotted leave column mapping, leave snapshot date and employee exceptions; historical LWP versus September-specific unpaid usage.
2. Authoritative PF wage basis, employer rate/ceiling and applicability, including whether to follow the explicit Excel formulas or the user's Basic + HRA description for future changes.
3. Classification of SBL AU11 and whether blank/NA contractual splits use a standard split, a consolidated salary component or another employment category.
4. Exact tenant identities/environment and confirmed preserved-account matches; recurring salary effective date and proration for September joiners.
5. Advance period attribution and treatment when advance exceeds monthly net. The proposed settlement representation above awaits review.

The reusable utility, monthly settlement inputs, payroll changes and reset execution are not implemented or performed by this follow-up.

## Confirmed answers and AF-AI verification

The user subsequently confirmed Opening as 2025 carry-forward, Allotted as the 2026 grant, and the explicit Excel formulas as the authoritative calculation rules. Blank/NA earlier component cells are to be resolved using AF onward. Additional deductions are configurable with an HR-supplied reason. The operator will run generated scripts against actual client schemas.

A focused check of all 37 employee rows confirmed AF-AI reconcile to AE and provide the same 50% Basic + DA, 25% HRA, 12.5% Conveyance and 12.5% Other Allowance proportions. There are no unusable AF-AI splits in the reviewed files. Apply these proportions to contractual Monthly Fix gross for recurring configuration; retain AF-AI as earned September amounts for period reconciliation.

The written design is `../superpowers/specs/2026-10-02-solvian-reusable-tenant-import.md`. It supersedes unresolved formula/split/mapping questions above with these confirmed decisions. Salary effective date, leave snapshot date, actual tenant mappings, preserved-account matches and missing employee-code mappings remain explicit operator inputs. The real reason for SBL AU11 remains an HR follow-up rather than a fabricated value.
