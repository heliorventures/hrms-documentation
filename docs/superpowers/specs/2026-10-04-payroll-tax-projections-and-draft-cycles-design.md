# Payroll tax projections, configurable contributions and draft cycles

Status: approved by the user on 4 October 2026. Implementation planning is in progress. This document does not authorize live migrations, imports, payroll generation, deployment or commits.

Approval clarification: every related UI change must update the existing `hrms-ui/designs/ui-review.pen` and the affected in-application tour guidance. These are acceptance requirements, not optional follow-up documentation. Preserve unrelated design frames and keep tours explanatory without triggering business mutations.

## Outcome

HR can recalculate draft payroll, review employee deductions and finalize an immutable salary statement. Employees can understand projected annual tax and recorded payroll deductions without any claim that the application has paid tax to the government. Calculators and configuration are reusable across tenants; Solvian source conventions belong in its conversion profile and imported configuration.

This extends the [tenant import design](2026-10-02-solvian-reusable-tenant-import.md). The importer is already implemented; this scope addresses the additional leave conventions, automatic future calculations, tax projections and draft payroll lifecycle. Existing checkout changes must be preserved.

## Confirmed decisions

| Area | Decision |
| --- | --- |
| September 2026 | Reproduce the reviewed Excel earnings and deductions; retain source provenance. |
| October 2026 onward | Use effective-dated rules and current monthly inputs. October is Solvian's initial activation date, not a hardcoded engine condition. |
| Flat withholding | HR can assign a configurable percentage with a mandatory reason. Initially use earned gross after LWP, excluding the separately recorded incentive, as the source formulas do. |
| Tax settings | Support old regime, new regime and a percentage withholding override. Preserve the distinction between annual tax regime and withholding method. |
| Earlier earnings/TDS | Not presently available. Show clearly labelled projections until HR supplies actual history. Never manufacture historical deductions. |
| Tax year | April to March. A May 2026 joiner has current-employer earnings projected from joining through March 2027; an employee who joined in 2025 has April 2026 to March 2027 projected. |
| Provisional withholding | HR may review and accept a projected monthly TDS amount while earlier history is incomplete. The acceptance needs an acknowledgement and is retained with the finalized calculation. |
| Tax payment claims | No UI wording such as 'tax paid', 'paid to government' or 'tax remitted'. A projection is informational. A finalized payroll amount is labelled 'TDS deducted in payroll'. |
| ESIC | Both companies are covered. Employee eligibility and contribution bases remain explicit, effective-dated inputs. |
| Payroll lifecycle | Draft calculations can be repeated. Finalized/locked cycles cannot be recalculated or edited. |
| Payslip display | Company-level component visibility remains in force; employer contribution details can remain hidden. |
| Advances | Settlement of salary already paid; excluded from recurring salary and employee deduction totals. |

## Current code findings

- `kabipay-tax/src/services/tax_service.rs` stores tax configurations, slabs and computation amounts; it does not calculate the requested annual projection and remaining withholding.
- The employee declaration mutation accepts calculated TDS fields. Declaration writes can clear or replace amounts consumed by ordinary payroll. Separate declaration inputs from authorized calculation results.
- Ordinary payroll reads the latest stored monthly TDS for the financial year and uses simplified statutory calculations. The imported payroll path uses explicit reviewed period deductions.
- `run_payroll_for_cycle` currently requires DRAFT, writes payslips and changes the cycle to PROCESSED. A second calculation is not currently supported.
- Monthly imported inputs are locked once generated/processed. Keep that protection at finalization; introduce a separate draft calculation boundary.
- Solvian leave conversion currently rejects missing fields, signed usage and certain zero-balance unpaid usage conventions. The user has now confirmed their meaning.

## Reusable rules and ownership

Use the existing tenant/company authorization boundary and component catalog. Extend shared domain services rather than adding client-specific payroll branches or duplicating calculators in the importer and UI.

Company rules hold calculation basis, included component codes, rate, optional ceiling, rounding policy, effective period, source and required explanatory note for custom/imported overrides. Employee settings select the annual tax regime, withholding method, optional percentage and effective period. Employee-specific deviations require HR permission and a reason. Store actor and change history.

Percentage bases are selected from supported earnings/component groups. Tenant configuration may change the percentage withholding basis; this does not automatically change the statutory taxability of those earnings in annual projections. For example, excluding an incentive from a flat-percentage basis does not make that incentive tax-exempt.

Prefer structured formulas such as a sum of selected components multiplied by a rate, with explicit caps and rounding. Any expression support must use a bounded validated expression model, with no executable Python, JavaScript, SQL or arbitrary Excel evaluation. Store and display the resolved basis and intermediate amounts.

Unknown statutory eligibility cannot silently fall back to the old global stub. Use a reviewed company rule or an explicit, reasoned period override. Preserve the existing source-based PF/PT amounts for September; future rules use the same configurable domain boundary.

## Salary and tax projections

Build the financial-year timeline using salary assignments effective during each month and the employee's joining/exit dates. Do not apply a later salary revision to earlier actual months. Use the applicable proration rule for partial months and LWP.

Each month and component identifies its evidence as:

- Imported actual: verified source earnings or deductions for that period.
- Finalized payroll: the immutable payroll calculation for that period.
- Historical estimate: past earnings inferred from the known salary structure because actual history is missing.
- Future projection: expected earnings for an unprocessed future period.
- Not provided: missing historical TDS or other information that cannot be inferred.

CTC and annual gross may both be displayed. Project taxable income from component tax treatment, not directly from total CTC. Employer costs must not automatically become employee taxable earnings; apply any relevant taxable-benefit rules explicitly. Include known taxable incentives and arrears, while identifying future unknown variable amounts as excluded from the estimate.

Annual calculations use versioned tax-year rules: slabs, standard deduction, permitted exemptions/deductions, rebates, surcharge, marginal relief where applicable, cess and prescribed rounding. Regime selection alone is insufficient to calculate old-regime claims: declarations and evidence retain their own review status. Missing information is shown as a limitation of the projection.

A permitted tax-setting change recomputes the current financial year's estimate for subsequent withholding. It does not assign a separate annual tax regime to each past month or rewrite past slips.

### Incomplete historical information

Show projected annual income, projected annual tax and projected monthly TDS. Earlier TDS remains 'Not provided'; do not substitute zero or estimated deductions into an actual-history field.

Proposed provisional allocation: divide projected annual tax by the number of employment payroll months in the current tax year, after calculating income with partial-month proration. For example, May through March has eleven payroll months. This is an estimated monthly amount, not a calculation of the actual remaining liability. Handle zero eligible months without division.

Known imported/finalized deductions remain visible separately. While historical coverage is incomplete, do not display a numeric 'remaining tax' as though all earlier deductions were known. HR may accept the provisional current-month amount or supply a reasoned override. Finalization records the accepted payroll deduction only; it does not create tax-remittance records.

Once complete actual earnings and TDS arrive, replace historical estimates in the projection with the supplied actuals. Recalculate annual tax, subtract verified prior deductions once, and spread the remaining withholding over unfinalized eligible periods. Flag excess withholding for HR review rather than inventing a refund or a negative bank payment. Past slips remain intact.

Opening history must identify employee, tax year, covered period, current/previous employer source, earnings and deductions, with provenance and review state. Reject overlapping/double-counted coverage, including overlap with September's imported actuals. Repeated imports must not add the same history twice.

### Employee wording

Use labels such as 'Projected annual taxable income', 'Projected annual tax', 'Projected monthly TDS', 'TDS deducted in payroll' and 'Historical TDS not provided'. Use 'Estimated remaining TDS' only when verified historical coverage supports the figure, and retain the estimated nature of future income.

Display this explanatory note beside projections:

> Estimated tax based on your current salary structure, joining date and available payroll information. Missing historical earnings are estimated. Actual deductions may change when HR updates your records. Contact HR for confirmation.

Projected amounts never populate recorded deduction history. Finalizing a payroll statement records its TDS amount as a payroll deduction; it does not establish government deposit or payment. The application does not execute salary or tax payments in this scope.

## ESIC wage calculation

Official ESIC guidance confirms the Code on Social Security wage definition applies from 21 November 2025. It includes basic pay, DA and retaining allowance, specified exclusions, and an add-back when relevant excluded remuneration exceeds 50%. The March 2026 Ministry FAQ retains the Rs.21,000 ESI wage ceiling. A gross-salary ceiling check or universal gross/2 formula is insufficient.

The reusable calculator therefore needs component classifications, the applicable exclusion/add-back calculation, effective eligibility, contribution-period continuation rules, employee/employer rates, employee-share exemptions and rounding. Version the legal rules separately from a tenant's imported override. Verify applicable notifications when implementing the rules, including changes after the sources below.

Solvian's workbook formula `earned gross * 0.5` is preserved as source configuration with an explanatory imported note. It is not certified as the standard rule for every employee. A generic 'Other allowance' label does not establish a statutory exclusion; its classification must be explicit. Show the selected basis and reason to HR and permit reviewed changes for future periods.

September's eight blank employee-ESI cells retain the approved source-period zero treatment and provenance. Their existence does not permanently disable ESI. Do not infer future eligibility from gross salary, a blank cell or ESIC identifier presence alone.

Employer contribution visibility on slips remains a company presentation setting. Hiding a component does not remove it from calculations or contribution reporting.

## Confirmed Solvian leave normalization

Keep these raw-file conventions in the Solvian converter; reusable import receives explicit normalized values:

- Blank Opening and Allotted mean zero.
- Where all four leave fields are blank, normalize opening, allotted, used and remaining to zero, with a source-convention log.
- Negative Taken is the absolute count of historical usage, as confirmed by the client. Negative balances represent excess usage, not a negative operational paid-leave balance.
- Paid used is limited to entitlement; paid remaining is nonnegative; usage beyond entitlement becomes historical unpaid leave.
- SCL row 23: 7.5 historical unpaid days and zero paid balance.
- SCL row 20: 6 historical unpaid days and zero paid balance, retaining the source's zero balance.
- Derive a blank balance from known entitlement and usage. Preserve source values and explain normalization rather than overwriting provenance.
- If a nonblank source value still contradicts the confirmed conventions, log a section-level exception. Do not silently reinterpret unrelated contradictions.

Pending/planned request statuses remain unknown unless actually supplied; zero historical usage does not prove that no requests are pending. Approved future leave is unpaid when no paid entitlement exists, unless HR later allocates paid leave. Historical usage does not create dated requests or another payroll deduction. Preserve the approved 31 August 2026 snapshot date.

## Draft calculation and finalization

Keep one cycle per tenant and period. Add a draft calculation result/version within that cycle, rather than creating duplicate cycles or published payslips for previews.

1. HR maintains monthly inputs and applicable settings.
2. Calculate creates/replaces the current draft result with earnings, contributions, tax projection, overrides, warnings, LWP and settlement.
3. Recalculate can run repeatedly. It does not book deduction history, consume leave allocations, apply arrears or publish payslips.
4. Any relevant input, history or rule change invalidates the reviewed draft. Show which inputs changed.
5. Finalize verifies the reviewed calculation/version against current inputs under a transaction and the existing period locks. It then writes immutable payslips/statements, records authoritative payroll deductions, applies period allocations once and locks the cycle atomically.
6. Duplicate finalization must not create duplicate slips, tax history, LWP allocations or arrear application. Return the established result or a stable already-finalized response.

Existing PROCESSED cycles map to finalized/locked behavior; do not reopen historical records during migration. Locked cycles reject calculation and edits in the API as well as the UI. Corrections use a separately authorized adjustment or revision workflow; this scope must not add a casual unlock button.

Store the exact salary/rule versions, inputs, sources, tax assumption status, HR acknowledgements, component amounts and settlement used for each finalized statement. Company display preferences must not change the underlying financial snapshot.

## Authorization and validation

Reuse existing tenant-scoped payroll and tax permissions. HR/Admin manages employee calculation settings and overrides; employees submit their own declarations and view authorized statements. Employee declaration mutations must not set, clear or replace calculated withholding. Server-side calculations are authoritative.

Missing optional data must not block independent employee, bank, salary or leave imports. Report missing information per section. Payroll finalization requires a valid reviewed calculation, including an explicit provisional-tax acknowledgement where applicable. Such acknowledgement does not waive unrelated missing salary or statutory inputs.

Use decimal amounts, bounded rates/dates, explicit rounding and reconciliation. Test isolation between tenants, authorization, effective dates and concurrent calculation/finalization. Keep sensitive identities and financial source content out of general logs.

## Acceptance examples

| Scenario | Required result |
| --- | --- |
| Confirmed 15 leave exceptions | Normalize using the approved convention; reconcile each original row and retain source logs. |
| Entire leave section blank | Zero entitlement/usage/balance, with future approved leave eligible for LWP. |
| September source import | Earnings, TDS, PF, ESI, PT, LWP and settlement reconcile to Excel. |
| Employee joins May 2026 | Project joining date through March 2027; no April 2027 in that tax year. |
| Employee joined in 2025 | Project April 2026 through March 2027, replacing estimates with available actuals. |
| Earlier TDS missing | Show 'Not provided'; no fictitious paid-tax or historical deduction entry. |
| Provisional October tax accepted | Record acknowledgement and finalized October deduction; do not claim government payment. |
| Later opening history supplied | Recompute future withholding without duplicating September or changing locked slips. |
| Percentage changed from a future month | Apply new rate/basis/note prospectively; preserve previous financial snapshots. |
| User-supplied annual example | Reproduce the displayed projection with its explicit rounding: tax Rs.621,363; verified Apr-Aug TDS Rs.252,400; seven remaining deductions of Rs.52,709. Validate statutory rounding separately. |
| Draft recalculated repeatedly | Replace draft result; no duplicate slips, deduction history or consumed allocations. |
| Input changed after review | Reject stale finalization and require refreshed calculation. |
| Cycle locked | Reject recalculation/edit through both API and UI. |
| Self-service declaration saved | Preserve HR-owned calculated withholding and finalized history. |
| Custom ESI formula | Require source/reason/effective date; distinguish it from the standard rule. |
| Advance on slip | Net earned and remaining payable differ by advance; taxable earnings are not reduced again. |

## Delivery boundaries and review

Implement in cohesive stages: leave conversion; rule/settings and tax-history contracts; projection calculators; draft/finalization domain services; HR/employee UI and statements; focused integration acceptance. Produce the implementation plan after written-design approval. Verification should use synthetic/disposable data before any separately authorized live action.

This is documentation only. No test/build, live database action, deployment or commit was performed for this design. Existing validation evidence for the prior importer does not prove the new behavior.

## Primary sources checked on 4 October 2026

- [ESIC headquarters: new wage definition, 11 December 2025](https://esic.gov.in/attachments/circularfile/New_wage_definition_u_s_2_88_of_The_Code_on_Social_Security_2020_1765902209.pdf).
- [ESIC explanation of wage definition and contribution examples, 13 December 2025](https://esic.gov.in/attachments/circularfile/Change_in_ESI_compliance_subsequent_to_change_in_definition_of_term_ldquo_Wages_rdquo_after_implementation_of_the_Code_on_Social_Security_rsquo_2020_1765632604.pdf).
- [Ministry of Labour additional FAQs, 16 March 2026](https://www.labour.gov.in/static/uploads/2026/03/a4ccf4c6d97c4f1f36a6d83f8c64213d.pdf).
- [Income Tax Department: tax-year explanation](https://www.incometax.gov.in/iec/foportal/help/all-topics/e-filing-services/objective-and-scope-new-act-faq).
- [Income-tax Act 2025, section 392: salary withholding and adjustment](https://www.incometaxindia.gov.in/w/section-392-5).
- [Section 202: new regime](https://www.incometaxindia.gov.in/w/section-202-78) and [section 19: salary deductions](https://www.incometaxindia.gov.in/w/section-19-199).
