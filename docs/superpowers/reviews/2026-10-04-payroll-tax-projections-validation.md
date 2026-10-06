# Payroll tax projections and draft-cycle validation

Implementation is in the current database, service and UI checkouts. No files were staged or committed. Client schemas, client payroll and deployment were not changed.

The subsequent production audit found seven additional defects. The correction status below supersedes the earlier acceptance evidence; production acceptance requires the final database fixture and operator checks.

## Production-audit corrections

- BASIC overrides resolve before dependent salary percentages, including override-only BASIC. Self-referential BASIC is rejected.
- Used component codes, types and tax treatment are protected through the service and migration 0095. References include structures, employee overrides, payslips, recorded source months and opening history. Future financial changes use a new component; company display preferences remain editable.
- Configured contribution wages include incentives, overtime and arrears. Variable remuneration does not become recurring salary; zero variable amounts do not require wage classification.
- Drafts include pending arrears without consuming them. HR can expand each included amount and reason. Finalization verifies and applies the reviewed accruals once in the same transaction as the payslip. Source months reconcile explicit ARREAR earnings.
- Preparation validates every earning against the active company catalog, including incentive. Import setup includes OVERTIME and ARREAR. Missing definitions require review before finalization.
- Dated settings select the latest effective start and its latest revision. Scheduled starts survive corrections to earlier starts; expiry leaves an explicit configuration gap.
- Annual and quarterly preparation exports reconcile finalized payslips, source months and current-employer opening history in a consistent read snapshot. Projections are excluded, unknown deductions stay blank, evidence counts are included, and history spanning quarters requires a period breakdown.
- The expanded database run also exposed approval-time ordering of tax proofs. Deduction provenance now follows submission time; approving an older proof cannot supersede a newer submission, and identical latest submission times require review. The fixture establishes submission chronology explicitly and retains the expected deduction amount.

The calculation fingerprint and statement engine version are now v2. Existing draft snapshots must be recalculated. No legacy-data conversion or tenant-specific calculation exception is introduced.

Fresh independent review found a missing source-only reference guard; it was corrected and the reviewer confirmed closure at source level. The tax-proof ordering correction also passed a focused source review. The final disposable database run `hrms-native-import-aCyxEZ` passed migrations (including repeat execution), import/replay/replacement, all financial regressions, finalization, and backup restore; its PostgreSQL server shut down cleanly. The 121-test Rust suite passed, followed by a passing 102-test tax/payroll rerun after the proof-ordering correction. The final native build of tax, payroll and importer passed after all corrections. UI production build, 11 focused tests and all nine changed-file lint checks passed. The three affected Pencil frames had no layout problems, screenshots were inspected, and the final arrear disclosure is saved on disk. Browser retry failed before opening a page with `failed to write kernel assets` / `os error 3`; browser and live deployment acceptance remain separate.

## Delivered behavior

- Solvian conversion profile 3 normalizes the confirmed leave conventions and records the source values. The reusable importer accepts optional company rules, employee tax settings and opening history, with independent section outcomes.
- September source amounts remain unchanged. Automatic payroll uses effective company rules and employee eligibility; October activation belongs to configuration.
- HR can configure old/new annual tax projections or a reasoned percentage withholding override. Earlier unknown deductions remain unknown. Estimated earnings never become recorded deductions.
- Draft calculation can repeat without publishing payslips. Finalization requires the reviewed revision, unchanged inputs and each required provisional-tax acknowledgement, then atomically creates immutable statements and locks the cycle.
- Advances reduce the remaining settlement only. Company payslip visibility does not change financial totals. Statements retain the contribution policy and calculation evidence.
- HR settings, monthly input controls, draft review, employee projections, relevant tours and nine Pencil frames are updated. The user confirmed the final design save.

## Verification evidence

| Check | Result |
| --- | --- |
| Solvian converter | 36 tests passed; all 37 salary structures and leave snapshots converted |
| Native leave normalization | 4 tests passed |
| Real packages, offline native validation | SCL: 19 rows, 16 core-ready, 19 salary/leave/period sections. SBL: 18 rows, 16 core-ready, 18 salary/leave and 17 period sections. No database writes |
| September financial preservation | Every period-input object unchanged against the prior approved conversion |
| Rust tax/payroll/importer suite | 121 tests passed; the final 102-test tax/payroll rerun passed after the proof-ordering correction. Common-crate tests also passed. One database fixture is deliberately ignored by the ordinary suite and run separately |
| Backend compile check and native build | Compile check passed; final tax/payroll/importer native build passed after all corrections |
| Disposable PostgreSQL migration/import/payroll fixture | Final rerun passed: full and repeat migrations through 0095; import, replay and partial-section handling; admin-preserving replacement; draft/finalization concurrency and rollback; automatic payroll; BASIC overrides; source-only catalog guards; incentive contributions; arrears and overtime persistence; opening-history exports; proof chronology; immutable statements; advance settlement; component visibility; backup restore |
| UI tests | Broad payroll/tour run: 61/62 passed; the old default-tab expectation was corrected and its six-test suite passed. Subsequent affected run: 9/9 passed |
| UI production build | Passed; final TypeScript check also passed after the last source changes |
| Changed UI source lint | New files clean; 24 findings remain in three existing large page/hooks, confirmed against the original checkout baseline. This is not a whole-project lint pass |
| Pencil inspection | Nine affected frames returned no structural problems; rendered states inspected and final file saved |
| Browser acceptance | Not performed: browser runtime bootstrap failed before execution with missing kernel assets |

Private evidence is under `.codex-tmp/payroll-tax-20261004/`. The final successful database fixture is `hrms-native-import-aCyxEZ`. The full-suite/check/build logs are `backend-final-tests.log`, `backend-final-check.log` and `backend-final-build.log`; final post-proof test/build command results are also recorded in the execution handoff. Do not publish client conversion packages or record-level reports.

## Independent review and corrections

A dedicated GPT-6.1 Sol agent compressed the execution evidence. One fresh reviewer then inspected the targeted tax, payroll, import, authorization, migration and UI paths without modifying files.

The review identified five important issues and no critical issues. All five corrections are implemented. Unit regressions and the final disposable database concurrency/loader cases passed:

1. Period editors reserve the database write lock before checking cycle status, so finalization cannot overtake an editor that already passed the draft check. A concurrent fixture holds that editor transaction open while attempting finalization.
2. Payroll eligibility uses joining/exit dates. Probation employees are included, future joiners and earlier exits are excluded, and inactive employees without an exit date require review instead of silently disappearing.
3. Previous-employer completeness survives loading independently of known partial TDS. Explicit incomplete coverage remains provisional, including when the known deduction is zero.
4. Excess recorded TDS produces an employee explanation and blocks automatic payroll until HR supplies a reasoned monthly withholding override. Payroll does not generate a refund.
5. Covered opening-history months no longer require reconstructed salary assignments. The selected payroll month is calculated independently of unrelated historical assignments. The historical-assignment regression was observed failing before the correction.

The expanded database fixture additionally found that valid values returned from `NUMERIC(15,4)` (for example, `0.0000`) failed the two-decimal money validator. Validation now ignores trailing zero padding while continuing to reject fractional paise, negative amounts and out-of-range values. A focused regression covers both valid padding and invalid precision. The synthetic package now explicitly supplies a known salary from joining for its missing-history estimate case; separate regressions cover missing historical assignments supported by opening history.

## Operator handoff and remaining acceptance

Use the [September and October runbook](../../client-onboarding/solvian-september-2026-import-runbook.md). Review the pending tenant migrations through 0095 with their matching service/UI changes before deployment. Live backup, migration, import, browser review and finalization remain separate operator actions.

The real source still needs five employee codes (SCL rows 24/25/26 and SBL rows 23/24) and the reason for SBL row 11's additional deduction. Future tax regimes/residency, PF/ESI eligibility, PT and missing tax history require HR review; blank September statutory cells do not establish future eligibility.

Input locking currently serializes writers briefly across the tenant schema and conservatively invalidates a draft when another relevant employee record changes. Lock acquisition has a bounded timeout. This protects legacy input writers but should be measured under the tenant's real workload.

Browser acceptance must cover desktop/mobile layouts, keyboard focus, restricted roles, tenant/employee switches, repeated drafts, stale-input recovery, provisional acknowledgements and locked-cycle behavior. Tours must remain explanatory and issue no business mutations. Unit, build and Pencil results do not replace these checks.
