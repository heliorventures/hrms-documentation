# Claims, company locations, working calendars, and application guidance

Date: 2026-10-06
Status: Approved by the user on 2026-10-06. Implementation planning is in progress; product implementation has not started.

## Intended outcome

Every new expense claim and travel request has a supporting file. Authorized HR/admin users can report on claims and travel with useful filters. Companies can maintain locations, assign employees to them, and configure weekly offs by location. Employees and administrators can find pages and features and follow detailed instructions with real application screenshots.

The user authorized a deeper review of all four areas after the token-expense warning. This document records verified source behavior separately from proposed behavior. It does not authorize live migrations, deployment, or historical financial changes. Existing unrelated changes remain preserved; no automatic commits.

## Verified current behavior

| Area | Current source evidence | Implication |
| --- | --- | --- |
| Expense submission | `hrms-ui/src/modules/expenses/components/SubmitExpenseModal.tsx:140` and `hrms-svc/crates/kabipay-expense/src/services/expense_service.rs:175` require a receipt only when effective policy requires it. The GraphQL input accepts an optional receipt ID. | A UI-only required field would leave an API bypass. The service and effective submission hints must enforce the same rule. |
| Travel submission | `SubmitTravelModal.tsx`, `kabipay-expense/src/resolvers/types.rs:128`, `travel_request_service.rs:66`, and entity `d0033_travel_request.rs` have no supporting attachment. | Travel needs form, GraphQL, service, storage association, and migration changes. |
| File validation | `expense_service.rs:571` checks the attachment tenant and submitting uploader. | Reuse this ownership contract for both submission types and verify storage validity through the existing upload infrastructure. |
| Reporting | `reportCatalog.ts` and analytics `hr_report_types.rs` include pending requests, but no dedicated claim/travel report kinds. | Extend the existing reporting workspace and server reporting contracts. |
| Locations | `d0006_org_hierarchy.rs:54` defines tenant locations with address and retirement fields; employees have `location_id`. Assets can list active locations. The reviewed employee module has no location CRUD or assignment API, and new employees get a null location. | The location master exists, but usable maintenance and assignment flows are missing. |
| Employee page | `employee-profile/lib/mapBundleToModel.ts:251` sets `locationName` to a placeholder. | Show actual location data and offer authorized assignment management. |
| Weekly offs | `attendance_report_service.rs:190` treats an unscheduled Saturday/Sunday as weekly off. `leave_service.rs:2034` and `unpaid_leave_allocation.rs:17` also embed Saturday/Sunday rules. | All date consumers need a shared location-aware working-calendar contract. |
| Holidays | Attendance filters global/location holidays; `leave_service.rs:1978` and payroll `unpaid_leave_policy.rs:114` combine all tenant holiday calendars. | Leave and payroll currently cannot consistently respect location holidays. |
| Financial history | Payroll `unpaid_leave_policy.rs:76` reuses frozen date allocations and rejects changes to consumed requests. | Preserve frozen allocations and finalized payslips when introducing new calendar rules. |
| Guidance | `tourRegistry.ts` registers tenant page tours; `tourCoverage.test.ts` checks routes and declared anchors. Tour context supports permission/tab conditions. `PageInformation` renders arbitrary reference content in a drawer. | Extend the established system and add tab/task coverage; route coverage alone does not prove every feature is explained. |
| Search | `CommandPalette.tsx:49` searches authorized destinations; `navigationSelectors.ts` matches page labels, paths, section labels, and keywords. | Page search already exists. Feature discovery and direct tab/task destinations need fuller coverage. |

These are source findings, not browser, database, build, or deployment results.

## Recommended approach and alternatives

Extend the existing domain services, report workspace, tenant location master, tours, Page Information drawer, and command palette. Introduce one shared working-calendar module with dated location assignments and dated weekly-off policies. Keep reusable UI and domain units small and follow the repository's strict lint rules.

An isolated UI change would be cheaper, but would leave submission bypasses and inconsistent leave/payroll calculations. A separate reporting/help subsystem would duplicate authorization and navigation infrastructure. The integrated extension addresses the underlying gaps while retaining current application conventions.

## Workstream 1: Mandatory supporting files

- Require one receipt/supporting file for each new expense claim and one supporting file for each new travel request. A travel document may be an itinerary, quotation, invitation, or other trip evidence; the label must not imply a post-travel receipt is required before a trip.
- Validate required selection and existing file size/type limits before upload. Show upload progress; prevent duplicate submission and dismissal while upload/submission is running. Preserve the draft and successfully uploaded file ID on submission failure so retry does not unnecessarily upload again.
- Enforce presence, same-tenant ownership, and uploader ownership inside the submission transaction before creating the business record/workflow. A missing, foreign, or invalid file must create no claim, request, or workflow instance.
- Expense receipt hints always report the mandatory rule. Remove the editable optional-receipt switch from the expense policy editor and explain the company-wide requirement. Existing stored policy flags can remain for compatibility but cannot weaken enforcement.
- Add a supporting-file reference to travel requests with a forward migration and corresponding entity/GraphQL/client changes. Keep historical rows nullable because existing requests have no document; make the new submission contract mandatory. Never invent or backfill historical files.
- Expose file presence/name and an authorized view/download action in claim/travel details. Access to a file must follow access to its parent claim/request, with tenant and employee scope checked on the server. Do not expose raw storage URLs or internal IDs as report download links.
- Coordinate schema and UI rollout so the form supplies the required field before enforcement becomes active. Older clients receive a clear validation error.

Acceptance: both forms and direct GraphQL calls reject missing files; cross-tenant and other-uploader files are rejected; successful submissions retain the file; failure/retry preserves the draft; existing historical requests remain viewable and approvable.

## Workstream 2: Claim expense and travel reports

Add an **Expense & Travel Reports** domain to Reports and an entry from Expenses & Travel. Provide two report choices: **Expense claims** and **Travel requests**, covering pending, approved, partially approved where applicable, rejected, and paid where applicable.

| Report | Filters | Output |
| --- | --- | --- |
| Expense claims | Inclusive expense-date range, employee name/code, department, location, expense category, approval status, payment status | Employee code/name, department/location, expense date, submitted date, category, title, claimed amount, approved amount, currency, approval status, payment status, payment reference, linked travel, supporting-file presence |
| Travel requests | Trip overlapping the inclusive date range, employee name/code, department, location, approval status, origin/destination search | Employee code/name, department/location, origin, destination, start/end dates, purpose, estimated amount, currency, approval status, submitted date, supporting-file presence |

- Clearly label date semantics in the filters. Submitted date is an output column; a separate submitted-date filter is an optional future addition.
- Apply all filters on the server using bound parameters and validated enums/tenant-owned IDs. Use the same filter contract for paginated results, counts, and CSV export. Changing filters clears stale rows and pagination.
- Keep existing company-report access: expense reports require `expense:read` with ALL scope; travel reports require `travel:read` with ALL scope. Neither grants a new approval or payment capability. Unauthorized report kinds and filter values fail closed.
- Use stable ordering, server pagination/counting, and the existing CSV escaping and spreadsheet-formula protection. Bound export size and show the existing actionable overflow message; never silently truncate.
- Amounts remain decimal values. Do not aggregate different currencies into one amount. Show claim and approved amounts separately; a pending approved amount is empty rather than the claim amount.
- Report department/location describe the employee's current organization assignment unless a dated snapshot is available. Label this explicitly; do not imply historical organization accuracy from current joins.

Acceptance: every supported status appears correctly, date boundaries and overlapping trips work, each filter is tenant-safe, pagination counts match filtered rows, CSV matches the displayed filter, and unauthorized users cannot retrieve records through direct queries.

## Workstream 3: Company locations and weekly offs

### User flow

1. Add **Company Locations** under Settings, backed by the existing location master. Authorized HR/admin users create/edit name and address details, search locations, and retire unused locations. Validate uniqueness according to the agreed tenant naming convention and reject retirement while active assignments depend on the location.
2. Add a location picker in employee employment management; show the resolved location name and effective date. In this release, an assignment change takes effect on today's tenant business date and records dated history. Future-dated transfers and bulk assignment are separate enhancements. Do not assign existing employees to a guessed location.
3. Add a **Weekly offs** section to Attendance Policy. Configure the tenant default and a location override, with an effective date and a calendar preview. Employees without a location or override use the tenant default.
4. Replace free-text location IDs in holiday calendar administration with an authorized company-location picker. Preserve global calendars as available to every location.

Confirmed first release: fixed weekly weekdays plus selected Saturdays, such as every Sunday and the second/fourth Saturday. Configure either every Saturday or selected first-through-fifth Saturday occurrences. The occurrence is the calendar-date ordinal within its month: `1 + floor((day_of_month - 1) / 7)`. A fifth-Saturday rule applies only when that month has a fifth Saturday. Reject duplicate selections and simultaneous every-Saturday/selected-Saturdays settings. Show the resulting off dates in a monthly preview before saving. Rotating employee-specific patterns are outside this release.

### Data and rule contract

- Maintain dated employee-location assignments and dated weekly-off policy versions. Each policy contains fixed weekdays plus optional Saturday ordinals; normalize and validate the recurrence before saving. Update the existing `employee.location_id` and dated assignment atomically when today's assignment changes. Historical calendar readers resolve assignments by date; current reports and the employee page use the current assignment. Future-dated assignment changes are rejected in this release, so the current value cannot become premature or require a scheduler. Reject overlapping assignment/policy periods and stale writes; a correction on the same effective date updates that version with an audit entry rather than adding an overlapping period.
- Establish an activation date. Dates before activation retain existing behavior; the initial tenant default explicitly represents the current Saturday/Sunday fallback. Existing location IDs may seed assignments from activation only, without inventing earlier history.
- Resolve location for the business date, then location policy, then tenant default. Holidays include tenant-global calendars and that date's employee location only. Do not union other locations' holidays.
- An explicit roster work assignment takes precedence over a recurring weekly off for that date; do not fabricate shift hours on other dates without a configured shift/roster. Preserve current shift and attendance-day timezone/boundary behavior.
- The shared calendar returns weekly-off and holiday facts plus policy provenance. Attendance status precedence, leave sandwich rules, and approved half-day behavior remain separate explicit domain rules.
- Use the shared rule in attendance daily reporting, leave preview/submission/dated allocation, relevant holiday views, and newly allocated unpaid leave in payroll. Review comp-off eligibility and scheduled-absence calculations for the same dependencies during implementation.
- Persist leave date units and the relevant calendar/location-policy provenance when the request is created. Approval and payroll consume those stored dates rather than recomputing an old request under a new policy. Existing payroll-frozen allocations remain authoritative.
- Legacy requests without saved date units follow the pre-activation rule, with existing approved-day reconciliation. A mismatch requires HR review; never silently prorate or rewrite approved days. Calendar changes do not recalculate finalized payroll or consumed allocations.
- Include new calendar/assignment inputs in the payroll draft fingerprint wherever calculations depend on them so a stale preview cannot be finalized.
- Reuse company-wide employee management authorization for location maintenance/assignment, and existing attendance policy management authorization for weekly-off configuration. Validate tenant ownership and scope in every query/mutation. Record actor and effective dates in audit history.

Acceptance: two locations with different weekly offs give consistent attendance and leave results; second/fourth Saturdays are off while first/third/fifth Saturdays remain working days unless configured otherwise; fifth-Saturday and month/year boundary cases resolve correctly; global/location holidays resolve correctly; no-location employees use the default; a mid-period location change resolves by date; policy edits cannot change old approved leave/frozen payroll; rostered work overrides recurring weekly off; retired or foreign locations cannot be assigned.

## Workstream 4: Tours, page instructions, screenshots, and search

### Coverage and detailed instructions

- Inventory accessible tenant routes, tabs, and user actions from their registries and focused source parsing. Maintain a coverage matrix linked to owning features so newly added routes/tabs/actions require guidance. Keep existing permission and module-subscription checks.
- Update every accessible tenant page tour against current UI, including the new reports, locations, assignments, weekly offs, and required files. Audit existing tabs and conditionally available functionality instead of relying only on the presence of a route-level tour.
- Keep explanatory tours free of business mutations. Tab navigation can select a visible tab with normal UI navigation; it must not submit forms, upload files, approve requests, or save configuration. Dirty forms must not be discarded by guidance navigation.
- Add reusable **How to** content to Page Information: prerequisites, numbered steps, required fields, validation constraints, what happens after submit/save, where to check status, and relevant error recovery. Render only instructions the user can access.
- Provide employee walkthroughs for requesting leave, uploading evidence, claiming an expense, requesting travel, viewing request/approval/payment status, and other applicable page actions. Provide HR/admin walkthroughs for every available configuration tab, including expense categories/policies, leave types/policies/balances, holidays, workflows, locations, and weekly offs. Extend to the remaining modules through the coverage matrix.
- Keep concise action-critical instructions beside the form; the drawer contains the longer reference material. Avoid moving required-field errors into the drawer.

### Screenshots

- Capture real current application screens with synthetic demonstration data after the relevant UI exists. Prefer focused screenshots of the referenced control or tab, with captions, alt text, and readable enlargement in the drawer.
- Use static, versioned help assets with recorded route/tab/task provenance. Do not use tenant documents, actual employee financial details, browser sessions, tokens, or storage URLs in screenshots. No generated or fabricated screenshot is presented as a verified application view.
- Verify every image against the implemented UI. If the local app/demo session cannot be opened, mark that walkthrough's screenshot as outstanding in the delivery checklist; do not claim screenshot coverage is complete.

### Feature search

- Extend the existing authorized command palette with task/feature metadata associated with real routes and tab IDs. Match page titles, tab names, feature terms, and common synonyms such as “claim expense,” “request leave,” “travel report,” “expense type,” “holiday,” “location,” and “weekly off.”
- Results clearly distinguish page and feature destinations. Feature results navigate to the correct visible tab and optionally focus a stable action anchor; they do not execute the action.
- Filter results by the exact feature's capability and module access, not only the parent route. Search cannot reveal hidden admin tabs or dead destinations. Retain current keyboard navigation, focus restoration, and Ctrl/Cmd+K behavior.

Acceptance: every accessible route/tab has guidance, required actions have corresponding how-to material, screenshots show the actual current controls, unauthorized features do not appear, and feature search reaches the intended page/tab without triggering a business action.

## Implementation boundaries and sequence

Treat these as four separately reviewable implementation plans under this shared design. Deliver uploads and reports first; then location maintenance and shared calendar integration; complete detailed help/screenshots against the resulting screens. Feature-search metadata and coverage infrastructure can be developed with the corresponding pages.

Primary owners: `kabipay-expense` and expense UI; `kabipay-analytics` and reports UI; `kabipay-employee`, `kabipay-common`, attendance, leave, payroll and tenant migrations; `src/guidance`, `PageInformation`, and navigation/command palette. GraphQL schema/client generation and database entities must stay synchronized with their owning contracts. Confirm migration ordering in the active checkout at implementation time.

## Validation and review

Implementation must provide focused regression tests for server attachment enforcement, tenant/scope isolation, filtered reports/export, dated calendar resolution, leave/payroll history protection, and authorized feature navigation. Follow the repository's existing test infrastructure; do not introduce a new environment-dependent framework unnecessarily.

The user owns tests, lint, typechecks, and builds unless explicitly delegated. Supply exact `rtk` commands with the implementation handoff. Planned checks include UI `rtk npm test`, `rtk npm run lint`, `rtk npm run build`, and focused Cargo tests for expense, analytics, calendar rules, leave, payroll, and employee location behavior. Also require disposable PostgreSQL migration/transaction validation and browser walkthrough checks with employee, HR/admin, and restricted accounts.

Static inspection or `rtk git diff --check` cannot establish runtime acceptance. Do not commit, deploy, apply tenant migrations, or alter live financial data automatically.

## Decisions for user review

1. Weekly-off scope is confirmed: fixed weekdays plus selected Saturdays. Review the recurrence UI and monthly preview behavior described above.
2. Review the proposed reports, filter/date semantics, and the location/calendar precedence and history protections.
3. Approve this written design before writing the four detailed implementation plans. Plan review and execution selection follow under the architectural workflow.
