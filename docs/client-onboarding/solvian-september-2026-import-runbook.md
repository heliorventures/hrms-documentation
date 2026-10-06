# Solvian September 2026 import

The reusable utility is implemented in the native HRMS services. The database project's sole [README](../../../hrms-database/README.md) contains the converter, native build and wrapper commands. Client-specific conversion stays in `scripts/tenant_specific/solvian/imports`; reusable reading/normalization/wrappers stay in `scripts/reusable/imports`; tests are grouped by client and unit/integration/migration purpose. The retired roster/onboarding workflow is no longer needed.

## Reviewed rules

- Salary assignment starts on the employee's source joining date (`JOINING_DATE`). A later change must respect generated payroll history and use an appropriate effective date.
- Opening leave is provisionally as of 31 August 2026. Opening is the 2025 carry-forward; Allotted is the 2026 grant. Reconciled EL balance remains nonnegative; excess historical usage is retained as historical LWP, without invented dated requests or September deductions.
- September uses source gross/split formulas and the reviewed gross / 31 LWP rule. The explicitly enabled September blank-as-zero policy logs each numeric formula input substitution and retains the raw source state. NA/errors and future eligibility stay unresolved.
- Fixed gross times 12 is annual gross. Annual employer PF is separate; CTC remains pending where the source does not establish the employer PF rule. Other Payable is a monthly incentive.
- Advance is salary already paid. The slip shows net earned, advance already paid and remaining payable. Advance never changes fixed components or employee deduction totals. Imported transfer exports use remaining payable.
- Deductions are PF, ESI, PT and TDS, plus an optional HR-entered deduction with its actual reason. Missing reasons keep that period draft.
- Company HR/Admin selects visible salary components. Employer costs start hidden. Browser, print and PDF honor that selection while totals remain accurate.
- Approved future dated LWP requests must be reviewed against the monthly aggregate. Their date/unit fingerprint is bound to the reviewed period and checked at generation; included units are not deducted twice. LWP has no annual quota or consecutive-day cap and retains the existing approval workflow.

## Local source acceptance

| Source | Rows | Core identities ready | Salary ready | Leave opening ready | September financials ready |
| --- | ---: | ---: | ---: | ---: | ---: |
| SCL | 19 | 16 | 19 | 19 | 19 |
| SBL | 18 | 16 | 18 | 18 | 17 |

These are offline checks of the original workbooks, not live tenant import results. Review-only local packages deliberately use `SOURCE_REVIEW_ONLY`; do not apply them to a tenant. Financial readiness and core identity readiness are separate.

Five source codes require a client-reviewed map: SCL worksheet rows 24, 25, 26 and SBL rows 23, 24. One SBL additional deduction at AU11 needs its business reason. All 37 leave snapshots now reconcile using the confirmed blank/dash-as-zero and historical-unpaid conventions. Original signed values remain in the report. Pending/planned leave stays unknown. DOB conflicts, identifier omissions, bank-name omissions and employer-rule uncertainty remain in the reports; resolving one section does not discard other valid sections.

## Actual tenant execution

1. Deploy the revised employee/payroll/leave/tax services, composed GraphQL schema and UI, and apply migrations 0090-0095 through the existing migration workflow. Verify actual tenant changelog, schema columns and runtime API support. Migration 0095 protects used component financial definitions. Setting `runtime_contract_version` in options is an operator assertion, not an automated deployment check.
2. Supply each actual tenant code, UUID, schema, database mapping, import actor, reviewed code/login maps and exact preserved account usernames. Confirm active employee/payroll/leave ALL permissions, tax:manage ALL for tax sections or replacement, and the company's module subscriptions. Treat absent preservation names as explicit reviewed absence; do not invent management accounts.
3. Convert each exact original path using the reviewed options and September policy flag. Keep packages, reports and credentials outside tracked source with protected access. Run native Validate, then Preview. Review all source issues and section actions.
4. Partial normal imports may defer incomplete rows/sections. Replacement requires every employee core identity to be resolved, an exhaustive delete/retain table manifest, preservation of the actor/admin identities and an application write pause. Review the replacement plan before supplying its exact digest to Apply.
5. Apply rechecks target state and authorization under locks. It holds the control-plane database mapping stable while the tenant transaction runs. The mapping-table SHARE lock allows reads and temporarily prevents mapping updates. Replacement takes a snapshot backup and verifies its archive before deleting anything. The disposable fixture also proved restoration into a separate database; actual backup restoration remains operator acceptance.
6. Inspect the committed report and actual row counts. Independent sections use savepoints; malformed banking does not undo valid salary data. A committed replay makes no further domain/audit writes. To retry deferred data after review, correct the package or use a new `review_reference` and obtain a fresh Preview. Reconcile an uncertain commit using the staged run ID before retrying or distributing credentials.
7. Resolve missing identities and monthly draft inputs through HR flows. In Payroll → Monthly Inputs, preserve September's reviewed source amounts. Review company component visibility. Create the September draft cycle, select **Calculate draft**, and compare every employee's source amounts, statutory totals, LWP, incentives, net earned, advances and remaining payable. Calculating creates no payslip. Repeat calculation as often as required while DRAFT.
8. Select **Finalize & Lock** only after reviewing the current calculation. A changed input invalidates the review and requires recalculation. Finalization writes the reviewed statements and locks the cycle in one transaction; failure rolls back the entire cycle. Locked cycles cannot be recalculated or have their period inputs edited. No payment is initiated.

## October and later payroll

1. In Payroll → Contribution Rules, review the effective **1 October 2026** company rule. Imported formulas remain explicitly client supplied. PF uses the source component weights and rates; custom ESI uses its source wage basis. HR may choose the separately implemented statutory wage-classification mode. A blank source ESI amount does not establish eligibility. Professional tax remains unconfigured until HR supplies it.
2. In Tax Settings → Employee Tax & History, select each employee's annual regime and residency. For the employees whose source formula proves 10% withholding, choose the configurable percentage override, its earned-component basis and an HR reason. The override is separate from the annual old/new-regime projection. Unresolved imported regime or eligibility is deferred, never guessed.
3. Create October monthly inputs in automatic mode. Confirm PF/ESI applicability, any applicable ESI continuation/daily-wage facts, monthly unpaid days, overtime, incentive, advance already paid and reasoned extra deductions. Review approved dated LWP against the aggregate; historical unpaid usage from August is never charged again.
4. Calculate the October draft and review results. Missing previous earnings/TDS history makes the annual calculation provisional. HR must explicitly acknowledge affected employees before finalization, including when a reasoned monthly withholding override is used. Unknown past deductions are not zero or remittance credits. If recorded TDS exceeds projected annual tax, HR must review and enter a reasoned monthly override before payroll can proceed; the system does not create a refund.
5. Future changes create effective settings revisions. They affect subsequent draft calculations; existing finalized statements keep their original figures and evidence. Enter later opening history by covered period and source reference; no period may overlap existing imported/finalized payroll. Corrections append a reviewed revision.
6. Pending arrears enter the next automatic draft as ARREAR earnings. Configure their tax and contribution treatment, expand each reviewed amount/reason, and finalize only after reconciliation. Drafts never consume arrears; finalization applies them once. Source months require their ARREAR component to equal the pending accruals.
7. Annual preparation exports include finalized payroll, imported source months and current-employer opening history exactly once. Evidence columns distinguish these records. Unknown deductions remain blank; amounts are not proof of remittance. Obtain a period breakdown before quarterly export when an opening-history total spans quarters.

Configure component codes, types and tax treatment before assigning/importing financial records. Used definitions are protected; create a new component for prospective changes. Visibility remains a company-level presentation setting. Effective rules select the latest start date and then its latest revision; an expired rule requires a new effective rule. Recalculate saved drafts after deploying the v2 payroll engine.

The employee tax view follows April–March: a May 2026 join projects May 2026 through March 2027. It distinguishes imported actuals, finalized payroll, historical estimates and future projections. Missing history hides unsupported remaining liability. Complete recorded history is deducted once when allocating remaining annual withholding. The view does not state that deductions have been remitted to the government. Only supported salary-tax cases are calculated automatically; unsupported cases require HR review.

### Illustrative payslip settlement

For a fictional monthly salary of ₹31,000, one unpaid day on the configured 31-day divisor, ₹1,000 incentive, ₹3,000 reviewed TDS, ₹200 PT and no employee PF/ESI:

| Item | Amount |
| --- | ---: |
| Earned recurring salary after ₹1,000 LWP reduction | ₹30,000 |
| Monthly incentive | ₹1,000 |
| Total earnings | ₹31,000 |
| Employee deductions | ₹3,200 |
| Net earned | ₹27,800 |
| Salary advance already paid | ₹5,000 |
| Remaining payable | ₹22,800 |

The LWP statement explains the reduction already reflected in earnings; it is not deducted twice. Employer contributions are retained in calculation evidence but hidden from payslip detail by default. Company component visibility changes presentation, not these totals. This example is illustrative, not a Solvian employee record.

## Reviewed location imports

The SCL/SBL salary layouts do not identify an office-location column. Supply a reviewed mapping with the converter's `--location-map` argument; never substitute department, bank branch, or an inferred company address. The mapping must match the exact workbook SHA-256 and tenant code:

```json
{
  "source_hash": "<exact workbook SHA-256>",
  "tenant_code": "<reviewed tenant code>",
  "locations": {
    "Sheet1:8": { "name": "Pune Office", "effective_from": "2026-10-07" }
  }
}
```

Sheet/row references identify source employees (the first employee row is 8 for SCL and 7 for SBL). Dates are explicit and illustrative above. Blank or omitted mappings preserve current locations and produce `LOCATION_NOT_SUPPLIED`; unmatched mappings block the package. The standard package accepts an optional `location` section on each employee with these same `name` and `effective_from` fields. Existing packages remain supported.

Apply migration 0097 before using location input. The importer matches normalized active location names only within the target tenant, creates a location when absent, and writes both the employee link and dated assignment in one section transaction. Retired locations and conflicting existing locations/history require review. A rerun of the same assignment does not increment revisions. Initial historical assignment dates are accepted only before calendar activation; with an active calendar, new assignments must use the company's current business date. No assignment can precede joining or be future-dated. Location input cannot clear or replace an existing different location.

For existing SCL/SBL data, first obtain the reviewed employee-to-location mapping, regenerate the package, and inspect its read-only preview. Use the ordinary import flow, not tenant replacement. Review every `location` result in the persisted report, then read back `employee.location_id`, the tenant's `location` rows, and `employee_location_assignment`. A successful schema migration alone does not demonstrate that employee locations were imported. Location correction does not rewrite saved leave snapshots or finalized payroll.

No live client import, reset, migration, deployment, payroll generation or automatic commit was performed during implementation. Keep the recovery snapshots until manual review is complete.
