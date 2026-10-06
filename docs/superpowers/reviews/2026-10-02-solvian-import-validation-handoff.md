# Native tenant import validation handoff

Implementation is in the current checkouts. Existing staged changes and unrelated guided-tour work are preserved. No automatic commit or live client operation was performed. The [operator runbook](../../client-onboarding/solvian-september-2026-import-runbook.md) links to the database project's single README and commands.

## Evidence observed locally on 4 October 2026

| Check | Observed result |
| --- | --- |
| Solvian converter | 28 tests passed; shared formula, cached ratio noise and September policy regressions included |
| Original source packages | 19 SCL + 18 SBL rows; both conform to current import schema's draft-compatible validation subset |
| Native offline financial validation | All 37 salaries, 22 leave openings and 36 September periods reconciled; 32 core identities ready |
| Payroll calculations and imported month applicability | 10 tests passed; historical LWP exclusion, advance settlement, optional employer costs and midmonth salary start included |
| Leave opening rules | 3 tests passed |
| Native package/reset/API contracts | 10 contract + 3 reset + 3 actual-service GraphQL document tests passed |
| Storage migrations | 5 checks passed on a disposable PostgreSQL cluster |
| Payroll UI | 35 tests passed, including fail-closed presentation/PDF regressions and existing permission checks |
| Private profile owner switching | 1 rendered stale-response test passed |
| Scoped lint | 27 feature-owned UI files passed; full repository lint is not claimed |
| Wrapper | Offline Validate passed using fictional package/options and a new private output directory |
| Full native fixture after final review fix | Passed full/repeated migrations, all-section import, replay, partial failure, stale-plan rejection, preserved-admin replacement, normal September/October payroll, dated LWP review, real midmonth-rule guarding and separate backup restoration |
| Final UI build | Passed after presentation/privacy fixes; ordinary existing Browserslist/chunk-size warnings |
| Final service check | Passed for native importer, employee, leave and payroll libraries/binaries |
| Final native executable build | Passed from the review-corrected source; existing dependency future-compatibility warning only |

Final disposable fixture evidence is at `C:/Users/ANIKET~1/AppData/Local/Temp/hrms-native-import-bSxtIN`; it contains fictional fixture data. The prior successful fixture and the intermediate test-setup failure remain distinct evidence in the ledger. Source review packages and offline validation reports are owner-restricted under the execution workspace and deliberately carry a review-only tenant code.

## Independent review

The dedicated GPT-6.1 Sol summarizer compressed execution evidence before Astra reviewed AST-selected converter functions and bounded native/payroll/leave/presentation source. The review found two Important issues and no Critical issues in the inspected paths:

1. Raw component fallbacks were visible while company presentation loaded or failed. The rendering boundary now requires a resolved company presentation; browser sheet and PDF generation have no raw component/statutory fallback. Export remains unavailable before details are ready. The new rendering test failed before the fix; the 35-test payroll UI suite passed afterward.
2. Imported applicability checked only month start, allowing midmonth joiners with missing inputs to fall into ordinary payroll. The guard now checks month end. A midmonth date regression failed before the fix and passed afterward. The disposable fixture also checks the real database query inside a rolled-back transaction. Its initial setup failure omitted a required audit actor and was corrected; that failure is not claimed as product-regression evidence.

The reviewer did not execute a browser, source conversion, migration or database test. Findings were fixed within the approved scope, with no second broad audit or unrelated refactoring.

## Remaining source and operator work

Five employee-code mappings, fifteen leave openings and the SBL AU11 deduction reason remain unresolved client data. Optional DOB/identifier/bank omissions and unknown employer cost are reported independently. Partial imports can retain valid sections; replacement requires every employee identity resolved.

Actual tenant mapping, active import actor/permissions, exact preserved usernames, login manifest, deployment/runtime support, applied tenant migrations, company settings, live counts and September statement acceptance remain operator checks. Building a local importer does not establish that an old running application honors the new fields. Actual client-schema reset/import/payroll/deployment was not run.

Known local toolchain warnings concern future compatibility of an existing Rust dependency, old Browserslist data and existing large UI chunks. New dependency upgrades and a whole-application performance refactor were not included.
