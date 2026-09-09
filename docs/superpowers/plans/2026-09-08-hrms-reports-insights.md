# HRMS reports and insights implementation plan

> For agentic workers: use superpowers:subagent-driven-development task by task. No commits.

**Goal:** Complete HR/Admin CSV exports and useful period-filtered operational charts with underlying rows.

**Spec:** ../specs/2026-09-08-hrms-enhancements.md, Phase 4.

**Architecture:** Analytics service owns typed read models over tenant domain tables. Report-specific exact ALL permissions protect each report. Full CSV queries never inherit operational screen limits. Insights reuse report filters/classification and expose unavailable or unauthorized metrics explicitly rather than fake zeroes.

**Stack:** Existing Rust/SeaORM/GraphQL services and React/TypeScript; inline SVG or semantic HTML charts with keyboard-accessible drilldowns. No new chart library is necessary.

## Constraints

- Reports are HR/Admin only; enforce exact domain ALL permission on the server before DB access, not a role label or client-only gate. Never let analytics:read alone expose payroll amounts.
- Use selected inclusive workdate/date period and tenant scoping. Reject inverted ranges. Period bounds do not silently truncate exports.
- Payments are outside HRMS. Use the label Net salary generated, not salary paid.
- No arbitrary SQL report builder or execution of stored filters_json. Typed catalogue only.
- Preserve dirty WIP. No migrations, deployment, tenant writes, commits, Dart/Flutter or subagents from implementers. Scoped tests/builds are already authorized; coordinate Cargo to avoid duplicate target-lock waits.
- Prejoining report depends on the pending prejoining workflow and will be added with that workflow; do not fabricate candidate data from employee checklists.

## Task 1: Analytics report and metric read models

**Owner/files:** backend implementer owns only `hrms-svc/crates/kabipay-analytics/**` and its verification report. Create focused `services/hr_reports.rs`, `services/hr_insights.rs`, `resolvers/hr_report_types.rs` and wire existing modules/query. No DB migration required for existing sources.

**Contract:**

```graphql
enum HrReportKind {
  ATTENDANCE_PUNCTUALITY
  LEAVE_REQUESTS
  LEAVE_BALANCES
  PAYROLL_REGISTER
  UNPAID_LEAVE
  EMPLOYEE_MOVEMENTS
  TIMESHEET_HOURS
  COMP_OFF_CREDITS
  PENDING_REQUESTS
}
query HrReport($kind: HrReportKind!, $fromDate: NaiveDate!, $toDate: NaiveDate!, $employeeId: UUID, $offset: Int! = 0) {
  hrReportRows(kind: $kind, fromDate: $fromDate, toDate: $toDate, employeeId: $employeeId, offset: $offset, limit: 50) {
    columns rows totalRows
  }
}
query HrReportCsv($kind: HrReportKind!, $fromDate: NaiveDate!, $toDate: NaiveDate!, $employeeId: UUID) {
  hrReportCsv(kind: $kind, fromDate: $fromDate, toDate: $toDate, employeeId: $employeeId) { fileName csv rowCount }
}
query HrInsights($fromDate: NaiveDate!, $toDate: NaiveDate!) {
  hrInsights(fromDate: $fromDate, toDate: $toDate) {
    onTimeDays lateDays unknownPunctualityDays incompleteDays
    joiners exits activeHeadcount netSalaryGenerated generatedPayslips pendingRequests
    monthlyPayroll { month netSalaryGenerated payslips }
  }
}
```

Rows are non-null string matrices, column-aligned. Preview is bounded; CSV contains every authorized filtered row, with deterministic ordering and spreadsheet formula neutralization for free text. Return nullable metrics for unauthorized domains; zero is valid only after a successful authorized query. A common `ReportFilter { from_date: NaiveDate, to_date: NaiveDate, employee_id: Option<Uuid> }` carries matching report/insight predicates.

Catalogue semantics/permissions:

- ATTENDANCE_PUNCTUALITY: `attendance:read ALL`; first recorded punch per employee workdate, completed duration/incomplete flag, recorded late minutes and classification On time/Late/Unknown. Null recorded lateness is Unknown, never zero. Reuse existing persisted workdate/time semantics; no new grace calculation or schedule assumptions. Existing cursor-complete attendance daily export remains available for expected/absent days. Punctuality counts employee-days, not distinct employees or individual segments.
- LEAVE_REQUESTS: `leave:read ALL`; requests overlapping period with employee labels, type, dates, units and status, include unpaid/comp-off marker. Full source query, no 200-row cap.
- LEAVE_BALANCES: `leave:read ALL`; current stored balances for leave years intersecting period, labelled current balances, not historical as-of snapshots; exclude dedicated comp-off annual balance and direct users to separate comp-off credits.
- PAYROLL_REGISTER and UNPAID_LEAVE: `payroll:read ALL` or existing exact `payroll:manage ALL` when authorized by current payroll rules; use actual payslips joined to cycles whose month intersects period, employee labels, gross/deductions/net and stored unpaid calculation snapshots. No bank/account/identity documents in report.
- EMPLOYEE_MOVEMENTS: `employee:read ALL`; joining dates and completed/effective separations in range, named department/designation where stored; do not count pending separation requests as exits. Current active headcount is labelled current; do not imply historical reconstruction from snapshots with no producer.
- TIMESHEET_HOURS: `timesheet:read ALL` (verify canonical current permission in source); date-filtered employee/project/task hours and approval status using actual timesheet rows, no operational page cap.
- COMP_OFF_CREDITS: `leave:read ALL`; approval business date in period, credited/reserved/used/remaining/expired units and immutable expiry per employee credit. Explain balances are current ledger state for selected earning dates.
- PENDING_REQUESTS: require exact ALL read permissions for all included domains or return domain rows only for explicitly permitted domains. Company pending workload across leave, comp-off claims, timesheet batches and expenses/travel, with submitted/created date in range. This is company workload, not an assertion that the viewer is the eligible approver; do not expose approval actions or override workflow routing.

- [x] Write failing tests for exact scope rejection before database access, CSV escaping/formula prefixes, inverted ranges, null lateness classification, one employee-day classification and no export pagination cap.
- [x] Implement typed source queries with tenant-qualified joins and parameters; keep historical payroll source values immutable and avoid current salary as an export basis.
- [x] Implement independent full CSV and preview pagination using the same source filters. A preview limit must not limit the CSV query.
- [x] Implement metric aggregations with matching classification/filter semantics; payroll monthly trend sums stored net and labels generated values.
- [x] Run analytics test/check; export real SDL offline without DB, write `../reviews/2026-09-08-phase4-backend.md` with final type names/tests/source limitations.

## Task 2: Report catalogue and interactive insights UI

**Owner/files:** root owns `hrms-ui/src/modules/admin/AdminReportsPage.tsx`, `modules/insights/AnalyticsPage.tsx`, new typed documents and shared report renderer/CSV download helper; permission/navigation routes and tests.

- [x] Keep cursor-complete daily attendance export. Add domain-permitted catalogue options with concise meaning and inclusive period filter; replace limited leave/payroll exports.
- [x] Display 50-row paginated previews and Download CSV action fetching the full export. Bind data and async actions to tenant/account/client/filter, show errors/retry and meaningful empty state.
- [x] Insights compact period toolbar, metric strip, punctuality comparison, monthly salary-generated trend and employee-movement comparison. Accessible buttons in charts open matching report rows with the same filters; include text/table equivalent.
- [x] Relax the all-four-permissions reports route to an OR of authorized report domains while keeping each backend query exact scoped. Analytics remains analytics:read ALL plus per-domain metric permissions.
- [x] Preserve existing succession content as a secondary tab if its existing permissions remain applicable; no unsupported controls or fabricated metrics.
- [x] Test export completeness contract, chart drilldown filters, unauthorized report visibility, failed metric recovery and stale ownership. Run scoped lint/typecheck/build and actual SDL validation.

## Task 3: Final review

- [x] Independent source review of report filters, tenant scope, nullable metrics, CSV injection protection and full export behavior; fix material findings.
- [x] Record browser/live data limits separately.
- [ ] Add prejoining report when its workflow exists.

## Preflight ledger

- Task1 produces the exact typed operations consumed by Task2; backend and UI ownership do not overlap.
- Existing attendance exports already exhaust cursor pages and remain intact. Existing leave/payroll exports are capped and are replaced.
- Workforce snapshots have no verified producer; current employee/separation facts are used and labelled honestly.
- User asked for company pending counts; read-authorized workload counts do not grant approval permission. Drilldowns show report rows, without approval actions.

## Final source/static status

Implemented and source-reviewed; scoped tests, actual SDL validation, TypeScript, production UI build and scoped lint passed. See phase-specific review files. Checked items describe source/static work only. Browser, live tenant/provider, migration and deployment acceptance remain outstanding. No commits or live writes.
