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
| SCL | 19 | 16 | 19 | 11 | 19 |
| SBL | 18 | 16 | 18 | 11 | 17 |

These are offline checks of the original workbooks, not live tenant import results. Review-only local packages deliberately use `SOURCE_REVIEW_ONLY`; do not apply them to a tenant. Financial readiness and core identity readiness are separate.

Five source codes require a client-reviewed map: SCL worksheet rows 24, 25, 26 and SBL rows 23, 24. One SBL additional deduction at AU11 needs its business reason. Fifteen leave openings require reconciliation of missing/signed source values. DOB conflicts, identifier omissions, bank-name omissions and employer-rule uncertainty remain in the reports; resolving one section does not discard other valid sections.

## Actual tenant execution

1. Deploy the revised employee/payroll/leave services, composed GraphQL schema and UI, and apply migrations 0090-0092 through the existing migration workflow. Verify actual tenant changelog, schema columns and runtime API support. Setting `runtime_contract_version` in options is an operator assertion, not an automated deployment check.
2. Supply each actual tenant code, UUID, schema, database mapping, import actor, reviewed code/login maps and exact preserved account usernames. Confirm active employee/payroll/leave ALL permissions and the existing company's module subscriptions. Treat absent preservation names as explicit reviewed absence; do not invent management accounts.
3. Convert each exact original path using the reviewed options and September policy flag. Keep packages, reports and credentials outside tracked source with protected access. Run native Validate, then Preview. Review all source issues and section actions.
4. Partial normal imports may defer incomplete rows/sections. Replacement requires every employee core identity to be resolved, an exhaustive delete/retain table manifest, preservation of the actor/admin identities and an application write pause. Review the replacement plan before supplying its exact digest to Apply.
5. Apply rechecks target state and authorization under locks. It holds the control-plane database mapping stable while the tenant transaction runs. The mapping-table SHARE lock allows reads and temporarily prevents mapping updates. Replacement takes a snapshot backup and verifies its archive before deleting anything. The disposable fixture also proved restoration into a separate database; actual backup restoration remains operator acceptance.
6. Inspect the committed report and actual row counts. Independent sections use savepoints; malformed banking does not undo valid salary data. A committed replay makes no further domain/audit writes. To retry deferred data after review, correct the package or use a new `review_reference` and obtain a fresh Preview. Reconcile an uncertain commit using the staged run ID before retrying or distributing credentials.
7. Resolve opening leave and monthly draft inputs through existing HR flows. Review company visibility and statements, then explicitly generate September via the normal payroll UI. Generation is separate from import. Compare source amounts, statutory totals, LWP, incentives, net earned, advances and remaining payable. No payment is initiated by this utility.

No live client import, reset, migration, deployment, payroll generation or automatic commit was performed during implementation. Keep the recovery snapshots until manual review is complete.
