# Claim and Travel Reports Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. The user selects the method before execution.

**Goal:** Add expense-claim and travel-request reports with server filters, accurate pagination, and matching CSV export.

**Architecture:** Add two report kinds to the existing reports workspace. A focused claim/travel report service applies a shared validated filter to count, page, and export queries; legacy report behavior stays compatible.

**Tech Stack:** React 18, TypeScript, GraphQL, Rust, SeaORM/PostgreSQL, existing CSV serialization.

**Spec:** [Approved design, Workstream 2](../specs/2026-10-06-claims-locations-and-guidance-design.md).

## Global Constraints

- Expense reports require `expense:read` with ALL scope; travel reports require `travel:read` with ALL scope.
- Apply all filters on the server using bound parameters and validated enums/tenant-owned IDs.
- Use the same filter contract for paginated results, counts, and CSV export.
- Amounts remain decimal values. Do not aggregate different currencies into one amount.
- Report department/location describe the employee's current organization assignment unless a dated snapshot is available.
- No automatic commits; `rtk` commands; user-owned validation. Plan 1's travel file association is a prerequisite. See [shared constraints](2026-10-06-claims-locations-and-guidance.md).

## Review Focus

1. More than one page of matches: total count and CSV include all filtered records; Task 1 tests 125 matching rows with a 50-row page.
2. Trips spanning a filter boundary: overlap is inclusive; Task 1 tests a trip starting before and ending after the selected period.
3. Pending or partially approved claims: absent approval amounts remain blank and claimed/approved amounts differ; Task 1 pins both columns.
4. Rapid filter or tenant changes: obsolete responses cannot restore old rows/export; Task 2 tests late response suppression.
5. Formula-like titles and oversized exports: CSV escapes content and returns an explicit limit error; Task 1 tests both.

## Task 1: Report contracts and server queries

**Files:** Create `hrms-svc/crates/kabipay-analytics/src/services/claim_travel_reports.rs`, `claim_travel_report_tests.rs`, and `tests/claim_travel_fixture.rs`; modify `services/{mod.rs,hr_reports.rs}`, `resolvers/{query.rs,hr_report_types.rs}` and existing `tests/hr_reports.rs`; modify `hrms-ui/src/api/schema-extensions/hr-reports.graphql`.

**Interfaces:**
- Add `HrReportKind::{ExpenseClaims,TravelRequests}` (wire values `EXPENSE_CLAIMS`, `TRAVEL_REQUESTS`).
- Add optional GraphQL `claimTravelFilter: ClaimTravelReportFilterInput` to existing `hrReportRows` and `hrReportCsv`; legacy callers can omit it. Fields: `departmentId`, `locationId`, `expenseCategoryId`, `approvalStatus`, `paymentStatus`, `routeSearch`. Existing period and employee inputs remain unchanged. Reject expense-only filters on travel, travel-only filters on expense, and claim/travel filters on other report kinds.
- Produce `ClaimTravelFilter { base: ReportFilter, department_id: Option<Uuid>, location_id: Option<Uuid>, expense_category_id: Option<Uuid>, approval_status: Option<String>, payment_status: Option<String>, route_search: Option<String> }`, with kind-specific validation against existing status constants. `load_page(db: &DatabaseConnection, tenant_id: Uuid, claims: &ClientClaims, kind: HrReportKind, filter: &ClaimTravelFilter, offset: i32, limit: i32, clock: TenantBusinessClock) -> KabiPayResult<HrReportRows>` and `load_csv(db: &DatabaseConnection, tenant_id: Uuid, claims: &ClientClaims, kind: HrReportKind, filter: &ClaimTravelFilter, clock: TenantBusinessClock) -> KabiPayResult<HrReportCsv>` consume the same normalized filter.
- Produce shared `render_csv(columns: &[String], rows: &[Vec<String>]) -> String` extracted from the existing serializer. Export cap is 10,000 data rows; 10,001 returns `Report has more than 10,000 rows. Narrow the filters and try again.` without returning a partial CSV.

- [ ] Add `claim_report_filters_count_and_page`, `travel_report_uses_inclusive_overlap`, `report_requires_exact_domain_all_scope`, `report_rejects_foreign_filter_ids`, `report_preserves_decimal_and_null_approval`, `csv_matches_filtered_report`, and `csv_rejects_over_limit`. Assert 125 rows give total 125 and first page 50; second/final pages have stable nonduplicate IDs. Retain current CSV formula/quote/newline protection tests.
- [ ] Obtain failing output from `rtk cargo test -p kabipay-analytics claim_travel`. Follow existing `tests/payroll_report_fixture.rs` for ignored disposable-DB tests using `HRMS_IMPORT_TEST_DATABASE_URL`, the localhost connection assertion and fixture schema; never print the connection string. Run the new fixture with `rtk cargo test -p kabipay-analytics --test claim_travel_fixture -- --ignored` only through user-owned validation against that disposable database.
- [ ] Implement tenant-constrained joins for expense/category/employee/department/location and travel/employee/department/location. Expense uses inclusive expense-date filtering; travel uses `from_date <= selected_to AND to_date >= selected_from`. Search matches literal employee names/codes and origin/destination; escape SQL wildcard characters for literal substring search. Preserve decimal text.
- [ ] Apply ALL authorization and subscription-filtered claims before any DB access; validate IDs belong to the tenant. Build count and ordered page/export predicates from the same normalized filter, with a consistent read snapshot for count/page. Use bound values; ordering ends in unique request ID. Fetch at most 10,001 export rows. Do not load the whole company dataset to implement page filtering.
- [ ] Expose exact columns from the approved design, including current organization labels, approval/payment separation, linked travel, and supporting-file presence. Add a tenant-safe options query `claimTravelReportOptions(kind: HrReportKind!, search: String, limit: Int = 50)` returning department/location/category option IDs/names, protected by that kind's report authority; no category options for travel. Obtain focused passing and persisted-fixture outputs.

## Task 2: Report filters and navigation

**Files:** Modify `hrms-ui/src/modules/reports/{reportCatalog.ts,reportDocuments.ts,ReportResult.tsx,ReportResult.test.tsx}`, admin `AdminReportsPage.tsx`; create report `ClaimTravelReportFilters.tsx`, `useClaimTravelReportFilters.ts`, `ClaimTravelReportFilters.test.tsx`; update `src/navigation/{navigationModel.ts,navigationAuthorization.ts}`, related catalog/navigation tests, and admin `guidance/AdminReportsPageTour.ts`.

**Interfaces:** Extend UI `HrReportKind` and `ReportFilter` with Task 1's wire names/input; add `REPORT_DOMAINS.expenses` containing both kinds. `useClaimTravelReportFilters(kind: HrReportKind)` produces `{ draft, applied, updateDraft, apply, clear }` with the same fields as the server input. `ClaimTravelReportFilters` consumes allowed kind and authorized option data; changing report kind clears incompatible filter values. List and CSV use one immutable applied-filter snapshot.

- [ ] Add `report_catalog_checks_each_domain_permission`, `claim_filters_apply_to_rows_and_csv`, `travel_hides_expense_only_filters`, `changing_kind_clears_incompatible_filters`, `stale_result_cannot_restore_rows`, and `export_limit_message_is_visible`. Assert expense-only access never reveals travel options or results; denied options do not produce raw ID entry fields.
- [ ] Obtain failing output from `rtk npm test -- src/modules/reports src/modules/admin/AdminReportsPage.test.tsx src/navigation/navigationSelectors.test.ts`.
- [ ] Add the two report definitions, Expenses & Travel report navigation, and current-organization/date semantics helper text. Render reusable filters and a clear/reset action; obtain options from Task 1. Use friendly named pickers rather than raw UUID text inputs. Retain existing generic report selection and daily-attendance behavior.
- [ ] Extend row and CSV documents with the optional input, reset pagination when applied filters change, and use existing report-owner protection for identity changes. Keep pending approved amount blank. Update guidance for filters, page results, and CSV download.
- [ ] Obtain passing focused outputs and browser proof for employee search, category, department/location, statuses, date boundaries, page changes, clear filters, denied kind, and CSV. Compare parsed CSV row counts/content to a persisted filtered fixture.

## Verification handoff

Provide focused commands above, `rtk cargo test -p kabipay-analytics`, UI `rtk npm run lint`, and `rtk npm run build`. DB validation must include cross-tenant IDs, multiple currencies, partial approvals, >50 rows, 10,001 exports, identical filter semantics, and denied direct queries. No tests or runtime results have been produced during planning.
