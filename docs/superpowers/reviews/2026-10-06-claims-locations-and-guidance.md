# Claims, locations and guidance implementation handoff

The approved source changes are in `hrms-ui`, `hrms-svc` and `hrms-database` on the existing working branches. No commits, live migrations, payroll recalculation or deployment were performed. Unrelated payroll resolver changes, Pencil design edits and existing review documents were preserved.

## Result and entry points

| Area | Result | UI entry point |
| --- | --- | --- |
| Evidence | Every new expense claim and travel request requires a private supporting PDF/JPG/PNG of at most 6 MiB. Retries reuse the successful upload; stale owner completions cannot submit. Downloads follow the parent request's read/approval authorization. Historical requests without evidence have an explanatory state. | Expenses → Expense Claims / Travel Requests |
| Reports | Own-domain company-wide access protects separate expense/travel reports. Named department/location/category filters, inclusive dates or trip overlap, approval/payment statuses and employee/route searches apply consistently to rows, counts, pagination and CSV. CSV fails explicitly above 10,000 matching rows. | Reports → Expenses & Travel |
| Locations | Active names are normalized and unique. Manage locations, assign an employee from today's company business date, retire only after dependencies are removed, and retain dated history. | People → Company Locations; employee profile → Employment (HR) |
| Weekly offs | Explicit activation, dated company defaults and location overrides/inheritance, fixed weekdays and first–fifth Saturday ordinals, preview, optimistic revisions and audit. Attendance and holiday scope use the dated location/calendar; submitted leave dates and existing payroll allocations remain frozen. | Attendance Policy → Location Working Calendars |
| Guidance | Shared feature metadata connects current tenant pages/tabs, tour steps, detailed Page Information instructions and page/feature search. Permissions and selected-profile server access filter destinations. Navigation protects forms and offers an explicit leave confirmation; it never invokes a business action. | Page Tools → tour / Page Information; header search |

Canonical raw GraphQL sources and schema extensions are registered for the new fields. Generated client files were preserved because the configured gateway at `http://127.0.0.1:4009/graphql` is unavailable. Regenerate against the updated services before release.

## Review rulings

A dedicated GPT 6.1 sol summariser compressed execution evidence before an independent Astra source review. The reviewer initially found two Important guidance defects: target-specific profile access and dirty forms remaining blocked after save. Both were corrected and the follow-up review found no remaining Critical or Important defect in the inspected source. This is conditional source readiness, not runtime or deployment acceptance.

Profile guidance consumes the selected employee's server-derived access, bound to employee/client/authorization identity. Private destinations remain hidden until that access resolves. Successful mounted attendance/leave-balance saves clear only their captured form version; later edits remain dirty. Other changed forms retain a conservative guard with explicit confirmation available. Read-only report filter forms do not count as unsaved business edits.

Comp-off earning has no weekly-off eligibility setting in the existing contract. Its policy/window/per-date units and HR approval behavior were retained. The proposed first-versus-second-Saturday earning restriction was explicitly marked inapplicable in the calendar plan; no new earning restriction was invented.

## Screenshot and coverage evidence

The six included WebPs are synthetic design illustrations captured read-only from `hrms-ui/designs/ui-review.pen`. Their captions, node IDs, source and SHA-256 hashes are in `hrms-ui/src/guidance/help/screenshotManifest.json`. Accessible enlargement returns focus to the opener. They are labelled design illustrations because controls can differ from the updated application.

The user supplied `https://heliorprd.heliorsoft.com/`, but the Browser tool failed during bootstrap before connecting. No production session or employee data was read. Actual screenshots of the new controls remain pending an updated runnable application and synthetic test account.

`hrms-ui/docs/guidance/coverage.json` inventories 52 tenant page routes, 80 static tab references, 224 anchors and 711 action references from 569 selected source files. Regression coverage links tenant routes and static tabs to shared feature/tour/help definitions. Action references and dynamic expressions are a source review inventory; their presence is not evidence that every conditional control rendered or worked under every role. Browser acceptance must exercise role-, record- and data-dependent states, delayed anchors, empty states and mobile layouts.

## Focused verification

Recorded passing backend runs: submission evidence 4; claim/travel reports 17 with one ignored PostgreSQL fixture; working calendar 6; private reader 2; company location normalization/date 2; attendance 89; leave 55 with one ignored database test; payroll unpaid leave 21; entity generator 3. These results overlap earlier narrower runs and should not be added into a single test total.

The final focused UI run passed all 218 tests across 45 files, with zero failed assertions, recorded in `hrms-ui/docs/guidance/final-regressions.json`. Earlier failing fixture runs are execution history, not release acceptance. The current UI suite includes uploads/retry ownership, attachments, exact expense/travel scopes, reports, calendar/leave preview, profile access and guidance/navigation/help regressions.

The final profile-target/search/coverage rerun passed 13 tests after extracting a shared target helper to follow coding conventions. Final UI/service/database whitespace checks passed. Obsolete generated failure reports were removed; their disposition remains in the execution ledger.

Formatting and whitespace review do not establish lint, typecheck or build success. Existing large functions in touched legacy screens are listed in `hrms-ui/docs/guidance/source-size-review.json`; new production components were kept within the configured function-size limit. Lint/typecheck/build remain user-owned.

## User-run release validation

Apply additive migrations `0096_travel_supporting_file`, `0097_location_working_calendar` and `0098_leave_working_dates` through the existing reviewed tenant migration process. First validate a disposable tenant. Migration 0097 deliberately halts when existing active location names normalize to duplicates; review those conflicts rather than automatically renaming data. UI and backend upload enforcement require a coordinated release.

From `hrms-ui`, after the updated local services are available:

```powershell
rtk npm run codegen
rtk npm run lint
rtk proxy npx tsc --noEmit
rtk npm run build
```

From `hrms-svc`, the supplied report acceptance fixture is ignored by default and only accepts a disposable localhost PostgreSQL URL. It creates its own schema and changes that disposable database:

```powershell
$env:HRMS_IMPORT_TEST_DATABASE_URL = 'postgres://postgres@127.0.0.1:5432/hrms_disposable_test'
rtk cargo test -p kabipay-analytics --test claim_travel_fixture -- --ignored
```

The fixture covers 125 records, paging/count/CSV consistency, decimal and nullable approval amounts, inclusive overlapping trips, literal searches, foreign filters and the actual export limit. It was not run during implementation. Database transaction/concurrent-writer acceptance for file rejection, location assignment/activation, policy revisions and leave snapshot atomicity also remains pending.

Before deployment, browser-check mandatory evidence and retry, scoped attachment downloads, both report filters/CSV, two locations with second/fourth Saturdays (including a five-Saturday month), current and historical attendance/holidays, same-day location correction, global versus location holidays, working-roster precedence, spanning/half-day/sandwich leave and unchanged frozen payroll allocations. Check denied profile/search/help destinations, unsaved forms, keyboard focus and screenshot enlargement. Capture replacement screenshots with synthetic data after these controls are available.
