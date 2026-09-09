# HRMS navigation review — 9 September 2026

Status: approved structure implemented in `hrms-ui`; final verification is recorded in the implementation section below. The original review and mapping are retained as a before/after reference. Scope: tenant sidebar and command-palette destinations, route registrations, navigation permissions, and relevant page contents. Operator-console navigation and public pre-joining routes remain separate audiences.

## Findings verified before implementation

1. There are 46 registered navigation destinations: 7 primary links, 36 grouped links, and 3 destinations without sidebar placement. Workplace contains 12 links, Organization 4, Payroll 4, HR 6, and Admin 10. These are configured totals, not what every employee sees; permissions filter them.
2. Leave is split between `/leave`, `/hr/leaves`, `/admin/leave-settings`, and shared workflow setup. Attendance and Timesheets have the same fragmentation. Company Holidays and Team Calendar are searchable but lack sidebar placement.
3. `/hr/people` and `/admin/employees` both load `AdminEmployeesPage` and both require `employee:manage` at ALL scope. They can share one visible Manage Employees entry. The employee directory is a different page with a different permission and should remain distinct.
4. `AdminSettingsPage` is an employee-directory snapshot plus descriptions of unavailable controls, not a working general-settings area. Remove it from normal navigation; preserve compatibility until its route is deliberately retired. Do not create an empty replacement Settings landing page.
5. Workplace Compensation contains salary bands and review cycles; Payroll Compensation contains components, structures, and employee CTC assignments. They are different functions with different permissions. Put both under Pay & Benefits and give them distinct names.
6. The shared workflow editor supports Leave, Expenses, Travel, and Timesheets. It does not currently take a route/query domain filter. Contextual Approval Rules entries need real domain filtering and selection, not several links that all open the same unfiltered page.
7. Active section selection uses URL prefixes. Regrouping destinations without changing that selection will retain HR/Admin/Workplace ownership. `SidebarSection` also hard-codes HR/Admin-specific subgroup headings using path regexes.
8. Desktop sections currently open flyouts; mobile sections expand inline. The section button style reflects open state, not persistent active destination ownership. `SidebarDestination` uses prefix matching without `end`, so `/leave` can also appear active on `/leave/holidays`. The redesigned navigation must resolve the exact selected destination and its functional parent.
9. Search keywords for `/payroll/payslips` describe payroll processing, while `/payroll/pay` contains tax declaration keywords. Correct these alongside labels so search takes users to the intended function.

Primary evidence, relative to `D:\work\heliorventures\hrms-ui`:

- `src/navigation/navigationModel.ts`, `workplaceDestinations.ts`, `navigationSelectors.ts`
- `src/components/layout/Sidebar.tsx`, `SidebarSection.tsx`, `SidebarDestination.tsx`, `CommandPalette.tsx`
- `src/routes/appRouteConfig.tsx`; `src/auth/navAccess.ts`, `permissionService.ts`
- `src/modules/admin/AdminSettingsPage.tsx`, `AdminWorkflowsPage.tsx`, `workflowSetup.ts`, `AdminLeaveSettingsPage.tsx`
- `src/modules/workplace/CompensationPage.tsx`, `OnboardingPage.tsx`, `SurveysPage.tsx`
- `src/modules/payroll/PayrollCompensationPage.tsx`; `src/modules/expenses/ExpensesPage.tsx`
- `src/modules/hr/HrHomePage.tsx`; `src/modules/reports/reportCatalog.ts`, `src/modules/admin/AdminReportsPage.tsx`

## Recommended structure

Group by business function. Keep permissions on individual destinations and actions; never require access to a parent overview to expose an allowed child. Show a parent only when at least one of its children is accessible. Within a function, order personal work first, team actions next, and configuration last. Keep settings details as page tabs instead of adding every policy field to the sidebar.

| Parent or direct link | Contents |
| --- | --- |
| Dashboard | Direct entry, first in navigation |
| People | Employee Directory; Manage Employees; Org Chart; Profile Reviews; Documents; Reports |
| Attendance | My Attendance; Attendance Management; Reports; Attendance Policy |
| Timesheets | My Timesheets; Approvals; Project Access; Reports; Settings; Approval Rules |
| Leave | My Leave; Approvals; Team Calendar; Company Holidays; Reports; Settings; Approval Rules |
| Expenses & Travel | Claims & Travel; Reports; Categories & Policies; Approval Rules |
| Pay & Benefits | Payslips & Tax; Payroll Processing; Salary Setup; Salary Bands & Reviews; Benefits; Tax Settings; Reports |
| Hiring & Exit | Recruitment; Pre-joining; Onboarding & Exit |
| Talent & Development | Performance; Learning; Succession Planning |
| Engagement | Surveys; Announcements |
| Assets | Direct entry to the existing Assets page |
| Grievance & Speak Up | Direct entry to the existing grievance page |
| Reports & Insights | Insights; All Reports — also retain contextual report access under the relevant functions |
| Settings | Roles & Permissions; Service Health |

Notifications stays accessible through the existing notification bell; Profile & Settings through the account menu. Both remain searchable. Reports & Insights and Settings can sit toward the bottom. Assets and Grievance need no one-item submenu. Do not replace Workplace with another miscellaneous parent.

This increases the fully privileged user's top-level choices from 12 to 14 while eliminating the 12-item Workplace and 10-item Admin buckets. Most users see fewer choices after permission filtering. The objective is understandable destinations, not an arbitrary total of ten. Compact spacing, short labels, and expansion of the active group are preferable to a third navigation level.

## Complete mapping of existing destinations

Every existing registry destination appears once below. Proposed contextual report/workflow views are additional entry points described separately; their implementation does not exist yet.

| Existing path | Proposed visible location / disposition |
| --- | --- |
| `/insights` | Reports & Insights → Insights |
| `/dashboard` | Dashboard |
| `/attendance` | Attendance → My Attendance |
| `/timesheet` | Timesheets → My Timesheets |
| `/leave` | Leave → My Leave |
| `/expenses` | Expenses & Travel → Claims & Travel |
| `/notifications` | Notification bell + search → Notifications |
| `/leave/holidays` | Leave → Company Holidays |
| `/leave/team-calendar` | Leave → Team Calendar |
| `/profile/settings` | Account menu + search → Profile & Settings |
| `/organization/employees` | People → Employee Directory |
| `/organization/org-chart` | People → Org Chart |
| `/organization/documents` | People → Documents |
| `/organization/profile-reviews` | People → Profile Reviews |
| `/workplace/benefits` | Pay & Benefits → Benefits |
| `/workplace/recruitment` | Hiring & Exit → Recruitment |
| `/workplace/prejoining` | Hiring & Exit → Pre-joining |
| `/workplace/onboarding` | Hiring & Exit → Onboarding & Exit |
| `/workplace/workflows` | Shared editor reused by Leave, Timesheets, and Expenses & Travel → Approval Rules; retain generic route for compatibility, remove generic menu entry |
| `/workplace/performance` | Talent & Development → Performance |
| `/workplace/surveys` | Engagement → Surveys |
| `/workplace/succession` | Talent & Development → Succession Planning |
| `/workplace/compensation` | Pay & Benefits → Salary Bands & Reviews |
| `/workplace/learning` | Talent & Development → Learning |
| `/workplace/assets` | Assets |
| `/workplace/grievance` | Grievance & Speak Up |
| `/payroll/payslips` | Pay & Benefits → Payslips & Tax |
| `/payroll/compensation` | Pay & Benefits → Salary Setup |
| `/payroll/pay` | Pay & Benefits → Payroll Processing |
| `/payroll/tax` | Pay & Benefits → Tax Settings |
| `/hr` | Remove redundant workbench from menu/search; retain old route and revise its legacy labels/links |
| `/hr/people` | Duplicate of Manage Employees; retain compatibility route without a second menu/search result |
| `/hr/leaves` | Leave → Approvals |
| `/hr/attendance` | Attendance → Attendance Management |
| `/hr/timesheets` | Timesheets → Approvals |
| `/hr/timesheet-assignments` | Timesheets → Project Access |
| `/admin/employees` | People → Manage Employees |
| `/admin/attendance-policy` | Attendance → Attendance Policy |
| `/admin/timesheet-settings` | Timesheets → Settings |
| `/admin/leave-settings` | Leave → Settings |
| `/admin/expense-categories` | Expenses & Travel → Categories & Policies |
| `/admin/notifications` | Engagement → Announcements |
| `/admin/reports` | Reports & Insights → All Reports; reuse report workspace for contextual domain views |
| `/admin/access` | Settings → Roles & Permissions |
| `/admin/module-health` | Settings → Service Health |
| `/admin/settings` | Remove misleading settings entry from menu/search; preserve old route pending deliberate retirement |

Existing redirects `/hr/leave-settings`, `/hr/access`, and `/payroll`, plus employee-detail routes, should remain valid. The generic workflow compatibility route needs a deterministic menu-owner fallback; do not infer an arbitrary functional owner from its old Workplace prefix.

## Page-level details and permissions

- Leave Settings already has Types, Policies, Balances, Holidays, and Comp-off tabs. Keep these within Leave Settings. Approval Rules remains a separate entry because `workflow:manage` and `leave:manage` are separate permissions. A company-holiday calendar and holiday configuration serve different purposes and must keep distinct access checks.
- Expenses & Travel already contains claims, travel requests, approval actions, and payment actions in one page. Keep that working page; do not invent separate approval/payment menu destinations without real routed views. Approval Rules should offer Expense and Travel workflow types within this function.
- Onboarding & Exit already has Joining Checklist and Exit & Separation tabs using local state. Retain one menu entry initially; separate sidebar entries would require real deep-linkable tab state.
- Surveys already contains participation, management, and aggregate reports. Keep them together with existing permission checks. Announcements is the existing publishing page; personal received notifications remain in the bell.
- Domain reports should reuse the existing report workspace with a validated domain filter and URL-backed selection. Current selection is local state. Examples: leave requests/balances/comp-off under Leave; attendance reports under Attendance; hours under Timesheets; payroll register/unpaid-leave calculations under Pay & Benefits; employee movements under People. Expenses & Travel can expose the existing pending-requests report restricted to its supported domains; do not imply a standalone claims report exists. If the backing query cannot restrict those domains safely, add that support before exposing the contextual entry. Pending Requests remains available centrally with its existing permission filtering.
- Preserve the current ALL requirement for configuration. Timesheet Settings currently requires BOTH `timesheet:manage` and `attendance:punch_policy` at ALL scope; regrouping must not silently change that rule. Preserve approval scopes, employee-directory scope, and distinct payroll/compensation permissions.
- Shared workflow navigation is presentation filtering, not new authorization. Preserve `workflow:manage` at ALL scope and existing backend checks. An approver must not gain workflow editing merely because Approval Rules sits beside Approvals. Backend authorization changes are outside this menu review.
- Module parent visibility is the union of accessible children. A leave approver without leave-read access must still reach the allowed approval queue. A parent must not route through an overview the user cannot access.

## Implementation guidance for a future authorized change

Use one navigation registry with explicit functional ownership, permission target, destination ID, and route matching. Sidebar, compact flyouts, mobile expansion, and command-palette group labels should consume the same metadata. Distinguish the navigation URL (which may contain a domain query) from the exact route/capability used for access checks: `canRoute` currently looks up exact strings, so passing a URL with a query to it would deny access.

Resolve active entries by the most specific route and supported query state, then derive the parent. Retain nested employee-detail matching while avoiding simultaneous My Leave and Company Holidays selection. Remove HR/Admin subgroup regexes. Keep contextual workflow/report views tied to their correct parent after reload/back/forward. Hidden legacy destinations must not reappear through search.

Existing URL paths can remain during this change. Human-facing labels, page headings, links, search terms, and menu ownership must use the new functional organization. Renaming URLs is a separate migration and is unnecessary for this result. Update stale HR workbench text and duplicated compensation headings in the same implementation.

Alternative considered: merely rename HR/Admin and retain their children. Rejected because Leave and other functions remain fragmented. A larger alternative is separate routed views for every page tab; that creates substantially more UI work and should only be done where a distinct destination helps users. Recommended: functional grouping with targeted contextual workflow/report views, reusing existing pages.

## Validation and handoff

The initial review was based on source inspection, not signed-in browser or production validation. At that stage no application code was changed, and the Markdown inventory was checked against both navigation registry files: 46 destinations, no missing or duplicate mapping rows. Implementation after the user's approval is recorded below.

Before claiming a future implementation complete, verify permission-specific navigation for self-service users, approvers, managers, configuration-only users, and fully privileged users; hidden parents; denied direct links; legacy URLs; domain filters; active parent/item state; search labels and duplicates; keyboard/mobile/desktop flyouts; and back/forward/reload behavior. Run focused navigation, route, authorization, workflow/report integration tests, TypeScript, and changed-file lint. Obtain signed-in browser evidence separately.

Unrelated dirty work observed before review: `src/components/common/Modal.tsx`, `Modal.test.tsx`, `src/modules/prejoining/admin/ConfirmJoinedModal.tsx`, and `PrejoiningAdminPage.test.tsx`. Preserve it during implementation.

The closing status check also showed concurrent changes to `src/modules/workplace/AssetsPage.tsx`, `assets/AssetInventorySection.tsx`, `assets/AssetSectionToolbar.tsx`, plus new `AssetsPage.test.tsx` and `assets/AssetOptionPicker.test.tsx`. These were not made by this review. Reinspect the live worktree before implementation.

## Implemented outcome

The user approved implementation and then explicitly approved combining it with the concurrent My Work/Performance task. Final visible order, subject to permissions:

1. Dashboard
2. My Work: My Tasks, Notifications, Completed / Archive
3. People
4. Attendance
5. Timesheets
6. Leave
7. Expenses & Travel
8. Pay & Benefits
9. Hiring & Exit
10. Performance (direct link)
11. Talent & Development: Learning, Succession Planning
12. Engagement: Surveys, Announcements
13. Assets (direct link)
14. Grievance & Speak Up (direct link)
15. Reports & Insights
16. Settings: Roles & Permissions, Service Health

The My Work notification entry supplements the existing bell. Profile & Settings remains in account controls and global search. HR, Admin and Workplace are no longer menu parents. Leave has its personal page, approval queue, calendars, settings, domain reports and approval-rule editor together. Other functions similarly contain their existing management/configuration routes.

Existing URLs and guards remain valid; the registry stores exact permission paths separately from contextual URLs. Report links additionally require a permitted report within the selected domain. Shared access filtering drives both sidebar and command palette. Active selection derives from destination metadata and domain, including legacy aliases and nested employee details. Only one calendar/report entry is marked current. Filtering expands matching sidebar groups. Search shows functional names instead of raw HR/Admin route URLs.

The duplicate employee-management link and obsolete workbench/settings menu entries are removed. The legacy workbench now offers permission-filtered Quick Links from the same registry. Salary Setup, Salary Bands & Reviews and Tax Settings have distinct headings.

Workflow domains validate before mounting the editor, filter creation choices and returned records, guard mutation targets, and reset drafts on domain/authorization changes. Reports validate domain and report selection before querying, preserve selection in the URL, and reset owned state when domain or authorization changes. Crafted cross-domain selections make no report query.

### Deliberate scope limits

- Expenses & Travel has no separate Reports entry: the existing pending-request API cannot restrict rows to that function. Pending Requests remains under All Reports. This avoids advertising a scoped report the backend cannot provide; adding server-side domain filtering is a separate report feature.
- Workflow lists retain their existing global bounds of up to 30 definitions and 50 requests before domain filtering. The page discloses this and says no matching records in the loaded set, rather than implying none exist anywhere. This is not exhaustive tenant workflow reporting.
- No connected browser was available (`agent.browsers.list()` returned an empty list). Signed-in desktop/mobile visual acceptance and production data behavior remain unverified. No deploy, commit, migration, or live write was performed.
- Concurrent My Work/Performance, Assets, Page Information, Modal, pre-joining and other worktree edits were preserved. The feature build checks the combined live checkout; this task does not claim ownership of those other changes.

### Implementation files

Paths below are relative to `D:/work/heliorventures/hrms-ui`:

- Navigation: `src/navigation/navigationModel.ts`, `workplaceDestinations.ts`, `navigationSelectors.ts`, `useAccessibleNavigation.ts` and focused regression tests.
- Menu rendering: `src/components/layout/Sidebar.tsx`, `SidebarHeader.tsx`, `SidebarNavigation.tsx`, `SidebarSection.tsx`, `SidebarDestination.tsx`, `CommandPalette.tsx` and layout tests.
- Legacy shortcuts/labels: `src/modules/hr/HrHomePage.tsx` and its test; one-heading edits in `src/modules/workplace/CompensationPage.tsx`, `src/modules/payroll/PayrollCompensationPage.tsx`, `PayrollTaxPage.tsx`.
- Workflows: `src/modules/admin/AdminWorkflowsPage.tsx`, `workflowSetup.ts`, `useWorkflowData.ts`, `useWorkflowEditor.ts`, `WorkflowForms.tsx`, `WorkflowRecords.tsx`, `AdminWorkflowsPage.test.tsx`, `workflowDomain.test.ts`.
- Reports: `src/modules/admin/AdminReportsPage.tsx` and its existing test; `src/modules/reports/reportCatalog.ts`, `reportCatalog.test.ts`, `AdminReportsPage.test.tsx`.
- Execution plan: `docs/superpowers/plans/2026-09-09-functional-navigation.md`.

### Verification evidence

- `npm run build`: passed, including TypeScript and Vite production compilation. Vite reported the existing-style large-chunk advisory and an outdated Browserslist dataset; dependencies were not changed.
- Scoped ESLint: navigation/layout/legacy shortcut implementation and tests passed; workflow/report implementation and tests passed with `--max-warnings=0`. Cosmetic one-heading edits were covered by TypeScript/build and diff checks without refactoring their unrelated existing page logic.
- Scoped `git diff --check`: passed. Windows line-ending conversion notices are not whitespace errors.
- Independent code review resolved both actionable findings: honest bounded workflow empty states, and clamping command-palette keyboard selection if permissions shrink the open results list. The latter has a regression test that first reproduced the undefined-destination exception.
- Final integration: 20 files / 165 tests exercised. The combined run passed 164 tests; the remaining legacy-shortcut test had an incorrect expectation excluding Documents (available to every signed-in user). Corrected only that expectation; its focused rerun passed 1/1 and scoped lint passed. All 165 cases are now verified; no production code changed after the successful build.

Combined integration command, run from `hrms-ui`:

```powershell
node node_modules/vitest/vitest.mjs run src/navigation src/components/layout/Sidebar.test.tsx src/components/layout/SidebarSection.test.tsx src/components/layout/SidebarDestination.test.tsx src/components/layout/CommandPalette.test.tsx src/modules/hr/HrHomePage.test.tsx src/auth/permissionService.test.ts src/routes/routeRegistry.test.ts src/routes/RouteGuards.test.tsx src/modules/reports src/modules/admin/AdminReportsPage.test.tsx src/modules/admin/AdminWorkflowsPage.test.tsx src/modules/admin/workflowDomain.test.ts src/modules/admin/workflowSetup.test.ts --maxWorkers=2 --minWorkers=1 --testTimeout=30000
```

Focused correction verification:

```powershell
node node_modules/vitest/vitest.mjs run src/modules/hr/HrHomePage.test.tsx --maxWorkers=1 --minWorkers=1 --testTimeout=30000
npx eslint src/modules/hr/HrHomePage.test.tsx --max-warnings=0
```

The 30-second per-test limit was selected for the concurrently active Windows checkout. React Router future-flag advisories were emitted; no runtime acceptance is inferred from these test results.
