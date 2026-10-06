# Locations and Working Calendars Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. The user selects the method before execution.

**Goal:** Configure company locations and weekly offs, including selected Saturdays, with consistent attendance/leave/payroll treatment and protected history.

**Architecture:** Reuse the location master and add dated assignments and calendar policy versions. A shared calendar snapshot resolves each employee/date; domain consumers retain their status, sandwich, half-day, and financial-history semantics. New leave saves its dated allocation so later configuration changes cannot alter approval/payroll.

**Tech Stack:** Rust, SeaORM/PostgreSQL, Liquibase, tenant business clock, React 18/TypeScript/GraphQL.

**Spec:** [Approved design, Workstream 3](../specs/2026-10-06-claims-locations-and-guidance-design.md).

## Global Constraints

- Confirmed first release: fixed weekly weekdays plus selected Saturdays, such as every Sunday and the second/fourth Saturday.
- Reject duplicate selections and simultaneous every-Saturday/selected-Saturdays settings.
- Future-dated assignment changes are rejected in this release.
- Dates before activation retain existing behavior; the initial tenant default explicitly represents the current Saturday/Sunday fallback.
- An explicit roster work assignment takes precedence over a recurring weekly off for that date; do not fabricate shift hours on other dates without a configured shift/roster.
- Legacy requests without saved date units follow the pre-activation rule, with existing approved-day reconciliation.
- Calendar changes do not recalculate finalized payroll or consumed allocations.
- `rtk` commands; no automatic commits/live migrations/deployments; user-owned validation. See [shared constraints](2026-10-06-claims-locations-and-guidance.md).

## Review Focus

1. A five-Saturday month: selected second/fourth Saturdays do not accidentally include the fifth; Task 2 uses October 2026.
2. Same-day location correction or competing administrators: exactly one assignment remains effective and stale revision loses; Task 1 checks both.
3. A location override ends: historical dates retain it while subsequent dates inherit the default; Task 2 tests dated inheritance.
4. Approval/payroll occurs after calendar edits: original leave date units are consumed; Task 4 checks request snapshot and frozen payroll precedence.
5. An unassigned employee or a location holiday elsewhere: use the tenant default and exclude other locations' holidays; Tasks 2/3 verify this.

## Task 1: Tenant location maintenance and dated employee assignment

**Files:** Create `hrms-database/changelog/migrations/0097_location_working_calendar/location_working_calendar.xml`; modify tenant master; generate `hrms-svc/crates/kabipay-db-entities/src/tenant/d0097_location_working_calendar.rs`; create employee `services/company_location_service.rs`, `services/company_location_tests.rs`, `resolvers/company_location_types.rs`; modify employee `services/mod.rs`, `resolvers/{mod.rs,query.rs,mutation.rs,types.rs}` and common `client_data_scope.rs` only for reusable exact-scope checks.

**Interfaces and storage:**
- Reuse `location`. Normalize names by trimming/collapsing whitespace; enforce case-insensitive active-name uniqueness per tenant under a transaction lock. Pre-existing duplicate names must not be renamed automatically; report a migration/configuration conflict for review before adding a unique constraint.
- Add `employee_location_assignment(id, tenant_id, employee_id, location_id nullable, effective_from DATE, revision BIGINT, changed_by, created_at, updated_at)`. Unique `(tenant_id, employee_id, effective_from)`; tenant/employee/date index; references must be tenant-consistent. Effective periods end at the next assignment start; no inferred pre-activation history.
- Produce `save_location(db, tenant_id, actor_user_id, command: SaveLocationCommand) -> KabiPayResult<location::Model>` and `retire_location(db, tenant_id, actor_user_id, location_id, expected_updated_at) -> KabiPayResult<location::Model>`.
- Produce `assign_employee_location<C: ConnectionTrait + Sync>(txn: &C, tenant_id, employee_id, actor_user_id, location_id: Option<Uuid>, effective_date: NaiveDate, expected_revision: i64, clock: TenantBusinessClock) -> KabiPayResult<LocationAssignment>`; only `effective_date == clock.now_date()` is accepted. A null location explicitly returns to the tenant default.
- `SaveLocationCommand` contains optional ID/expected update timestamp, name and optional address/city/state/country; create requires no existing ID and update requires the timestamp. `LocationAssignment` returns employee/location IDs, location name, effective date and revision. GraphQL `companyLocations(page: PageInput, search: String, activeOnly: Boolean = true)` returns paginated IDs/names/address fields; `companyLocationOptions(search: String, limit: Int = 50)` returns IDs/names only; mutations `saveCompanyLocation`, `retireCompanyLocation`, `assignEmployeeLocation` use the commands above. Management requires exact `employee:manage` ALL or `employee:write` ALL. Minimal options accept that authority, `employee:read` ALL, `leave:manage` ALL, `attendance:punch_policy` ALL, `expense:read` ALL, or `travel:read` ALL, after corresponding module/subscription checks; options do not grant management.

- [ ] Add `locations_are_tenant_scoped`, `active_names_are_normalized_unique`, `assignment_requires_current_business_date`, `assignment_is_atomic_and_revision_checked`, `same_day_correction_keeps_one_version`, and `retirement_rejects_active_dependencies`. Assert rejected writes leave both employee current location and history unchanged; retirement is rejected for an assigned employee or active/scheduled location policy.
- [ ] Obtain failing output for `rtk cargo test -p kabipay-employee company_location` and disposable DB transaction cases.
- [ ] Create the dated tables plus calendar tables from Task 2 in the same coherent forward migration. Use row locks and expected revision/timestamp checks for writes. Location validation, assignment history, `employee.location_id`, and audit event commit together; follow the existing audit representation. Never expose another tenant's row via a UUID or search.
- [ ] Extend the employee DTO/queries with `locationId`, `locationName`, and `locationAssignmentEffectiveFrom`; resolve names rather than retaining the profile placeholder. Populate only tenant-safe public organization fields and keep private-profile protections intact.
- [ ] Generate only the new domain with `rtk proxy py -3 scripts/generate_db_entities.py --only 0097_location_working_calendar`. Obtain passing regression and disposable migration/rerun/read-back evidence before declaring this task validated.

## Task 2: Shared recurrence and dated working-calendar resolution

**Files:** Create common `src/working_calendar/{mod.rs,types.rs,rules.rs,repository.rs,tests.rs}` and export it in `src/lib.rs`; create attendance `services/weekly_off_policy_service.rs`, `resolvers/weekly_off_types.rs`; register them in existing module files and query/mutation roots; update the Task 1 migration.

**Interfaces and storage:**
- Add `working_calendar_profile(tenant_id PRIMARY KEY, activation_date DATE, revision BIGINT, activated_by, created_at, updated_at)` and `weekly_off_policy_version(id, tenant_id, location_id nullable, effective_from DATE, inherits_default BOOLEAN, fixed_weekdays JSONB, saturday_ordinals JSONB, created_by, created_at, superseded_at nullable)`. Use separate partial uniqueness constraints for tenant-default/location effective dates among rows with `superseded_at IS NULL`. Store weekdays as ISO Monday=1 through Sunday=7 and ordinals 1..5; sorted canonical arrays contain no duplicates. Empty recurrence means no recurring weekly off; a default version cannot inherit itself.
- Produce `WeeklyOffRule { fixed_weekdays: Vec<u8>, saturday_ordinals: Vec<u8> }`, `validate_rule(&WeeklyOffRule) -> KabiPayResult<()>`, and `is_weekly_off(date: NaiveDate, rule: &WeeklyOffRule) -> bool`. Ordinal algorithm: `1 + (date.day() - 1) / 7`, applied only on ISO Saturday=6. Selected ordinals cannot coexist with fixed weekday 6.
- Produce `load_calendar<C: ConnectionTrait + Sync>(db: &C, tenant_id: Uuid, employee_ids: &[Uuid], from_date: NaiveDate, to_date: NaiveDate) -> KabiPayResult<WorkingCalendarSnapshot>` and `WorkingCalendarSnapshot::day(employee_id: Uuid, date: NaiveDate) -> KabiPayResult<CalendarDay>`. `CalendarDay` contains `activated`, `location_id`, `weekly_off`, `holiday`, `has_roster_work`, and effective `policy_version_id`; load records in batches, not per date/employee queries.
- Produce GraphQL `workingCalendarPolicy(locationId: ID): WorkingCalendarPolicy`, `activateWorkingCalendar(activationDate: NaiveDate!): WorkingCalendarPolicy`, `scheduleWeeklyOffPolicy(input: ScheduleWeeklyOffPolicyInput!): WorkingCalendarPolicy`, and `previewWeeklyOffMonth(rule: WeeklyOffRuleInput!, month: Int!, year: Int!): [NaiveDate!]!`. The schedule input contains location, effective date, rule/inherit flag, and expected tenant profile revision; protect all with `attendance:punch_policy` ALL. Activation accepts today's tenant business date only, safely inserts/locks the profile, and transactionally seeds the explicit `[6,7]` default and existing non-null employee locations from activation; employees with null locations retain default inheritance. Repeated activation returns existing state only when the original date matches, otherwise fails; it never overwrites policy/history. `WorkingCalendarPolicy` returns activation date, revision, selected location, current version, and scheduled versions with their rule/inherit flags.

- [ ] Add `second_fourth_saturday_october_2026`: with fixed `[7]`, ordinals `[2,4]`, assert October 10/24 and October 11 are off; October 3/17/31 are not. Add `fifth_saturday_only_when_present`, invalid 0/6 ordinals and 0/8 weekdays, duplicate/contradictory selections, leap-year/month/year boundary tests, and `empty_rule_has_no_weekly_off`.

  Core assertions for `second_fourth_saturday_october_2026`:

  ```rust
  let rule = WeeklyOffRule { fixed_weekdays: vec![7], saturday_ordinals: vec![2, 4] };
  for value in ["2026-10-10", "2026-10-24", "2026-10-11"] {
      assert!(is_weekly_off(value.parse().unwrap(), &rule));
  }
  for value in ["2026-10-03", "2026-10-17", "2026-10-31"] {
      assert!(!is_weekly_off(value.parse().unwrap(), &rule));
  }
  ```
- [ ] Add snapshot tests for date before activation, location/date transfer, default inheritance, other-location holiday exclusion, global holidays, roster precedence, and current/default/location policy versions. Obtain failing output from `rtk cargo test -p kabipay-common working_calendar` and focused attendance weekly-off policy tests.
- [ ] Implement pure recurrence and batched tenant-only resolution: greatest effective date <= work date for assignment/policy, location override before default, global/location holiday union, and explicit roster-work suppression of recurring off. Retain the activation marker so each legacy consumer can preserve its original pre-activation semantics.
- [ ] Implement policy commands under the tenant profile row lock with optimistic revision. Permit today/future policy dates and prohibit past effective dates. For a correction at an existing today/future effective date, supersede the existing row and insert a new version ID in the same transaction; retain the old record for saved leave provenance. Otherwise insert the new effective date, with the next date delimiting its period. Represent stopping a location override as a dated `inherits_default=true` version. Do not rewrite rules in an earlier dated version. Include activated profile/date and policy revision in UI state so scheduling cannot proceed against an unactivated calendar. Add `same_day_policy_change_preserves_prior_leave_snapshot` to prove a custom rule can follow today's activation without changing previously saved units.
- [ ] Obtain passing rule/resolver tests, DB concurrency/activation rerun proof, and a monthly preview matching the same pure recurrence function used by backend consumers.

## Task 3: Attendance, holiday scope, and location/calendar administration UI

**Files:** Modify attendance `services/attendance_report_service.rs`; create UI `modules/admin/{AdminCompanyLocationsPage.tsx,companyLocationDocuments.ts,companyLocationTypes.ts,WeeklyOffSettings.tsx}`, hooks `useCompanyLocations.ts` and `useWeeklyOffSettings.ts`, and focused tests; modify admin `AdminAttendancePolicyPage.tsx`, `components/LeaveHolidaysSection.tsx`, `hooks/useAdminLeaveHolidays.ts`; employee profile `tabs/EmploymentManagementTab.tsx`, `hooks/useEmployeeProfileData.ts`, `lib/mapBundleToModel.ts`, `types.ts`; modify `src/routes/appRouteConfig.tsx`, relevant auth route rules, navigation, schema extension registration, and employee GraphQL documents. Create `CompanyLocationsPageTour.ts` and register it.

**Interfaces:** Consume Tasks 1/2; add route `/admin/company-locations` protected by location-management authority and navigation label `Company Locations`. `WeeklyOffSettings` owns location/default selection, effective date, weekday/ordinal selection, inheritance mode, preview, and revision-controlled save. Employee assignment picker shows current location/effective date and requests today's business-date change with expected revision.

- [ ] Add `attendance_uses_location_off_days`, `rostered_work_overrides_recurring_off`, `holiday_scope_excludes_other_locations`, and `unactivated_attendance_retains_legacy_behavior`. Preserve absence/incomplete-punch/status ordering from the current report; assert scheduled Saturdays are working days and unknown schedule hours remain unknown.
- [ ] Add UI tests for authorized CRUD, stale-save reload guidance, denied locations, retirement conflicts, monthly second/fourth Saturday preview, every/selected Saturday conflict, missing location default, and friendly picker errors. Obtain focused failing outputs before implementing.
- [ ] Replace only the activated branch of attendance weekly-off/holiday selection with Task 2's snapshot; keep existing expected-minutes/clock logic. Add a locations screen and reusable named location picker. Wire the employment location action without overwriting unrelated employee-directory edits. Replace raw holiday-calendar location UUID entry with the options query.
- [ ] Add the weekly-off settings section, explicit today's-date activation action, visible effective-date policy/provenance, preview and inheritance controls. Explain the initial Saturday/Sunday default and require a separate explicit policy save for changing it. Add corresponding tour/help anchors and authorized search destinations; existing policy/geofence controls keep their independent save behavior.
- [ ] Obtain `rtk npm test -- src/modules/admin src/modules/organization/employee-profile src/navigation` focused outputs and attendance service tests. Browser-check two locations, changing an employee today, current versus historical reporting, policy activation/default, selected Saturdays, and denied navigation.

## Task 4: Save leave dated allocations and protect payroll history

**Files:** Create migration `0098_leave_working_dates/leave_working_dates.xml` and generated domain; create leave `services/leave_working_dates.rs` and tests; modify leave `services/{mod.rs,leave_service.rs,comp_off.rs}`, holiday queries in `resolvers/query.rs`, payroll `services/{unpaid_leave_policy.rs,unpaid_leave_allocation.rs,payroll_fingerprint.rs}`, and relevant tests. Update employee holiday UI queries only if their existing parameters cannot express the current employee scope.

**Interfaces:** Add `leave_working_date_snapshot(leave_request_id PRIMARY KEY, tenant_id, employee_id, from_date, to_date, requested_days DECIMAL, date_units JSONB, calendar_provenance JSONB, created_at)`. JSON units contain `{date, units}` with decimal strings; provenance records calendar activation and location/policy IDs by date. Produce `build_leave_date_units(snapshot: &WorkingCalendarSnapshot, employee_id: Uuid, from: NaiveDate, to: NaiveDate, half_day: bool, sandwich: bool) -> KabiPayResult<Vec<(NaiveDate, Decimal)>>`, `save_leave_date_snapshot<C: ConnectionTrait + Sync>(...)`, and `load_leave_date_snapshot<C: ConnectionTrait + Sync>(db: &C, tenant_id, request_id) -> KabiPayResult<Option<LeaveDateSnapshot>>`. Preserve currently approved half-day and sandwich behavior; legacy nonactivated requests retain original holiday/weekend semantics.

- [ ] Add `leave_snapshot_survives_policy_and_location_change`, `leave_preview_matches_persisted_date_units`, `legacy_approved_allocation_preserves_pre_activation_rules`, `payroll_prefers_frozen_allocation_then_request_snapshot`, `mismatch_requires_hr_review`, and `calendar_change_invalidates_unfinalized_draft_fingerprint`. Include a request spanning September/October, mixed-location holidays, half-day Sunday, and sandwich dates. Assert finalized payslip amounts and frozen allocations never change.
- [ ] Obtain failing outputs for `rtk cargo test -p kabipay-leave leave_working_dates` and focused payroll allocation/fingerprint tests, including the existing overlap/count reconciliation cases.
- [ ] Add the snapshot migration/generation. Compute preview/submission chargeable dates through one date-unit builder after activation; save the request and snapshot in the same transaction. Approval uses the saved units; edits requiring changed dates must generate a newly reviewed snapshot through the normal request lifecycle. Leave/holiday views use global plus resolved employee-location calendars after activation.
- [ ] Payroll first uses its existing frozen allocation. If none exists, use a request snapshot and verify IDs/date range/approved days; otherwise use the existing legacy allocator, regardless of current activation. Never backfill guessed historical dates. Include calendar profile/versions/assignment/snapshot changes in draft fingerprints, tenant-constrained, while preserving finalized statements.
- [x] Audit comp-off worked-date eligibility and scheduled-absence helpers against the shared calendar. Source review found no recurring-weekend assumption or weekly-off eligibility policy flag in `kabipay-leave/src/services/comp_off.rs`: earning is decided through the existing policy/window/per-date-unit and HR approval rules. Preserve those rules and credited history. The proposed first/second-Saturday earning assertion is inapplicable to the current contract; introducing that restriction requires a separate business rule and is outside this implementation.
- [ ] Obtain passing leave/payroll/comp-off tests and disposable DB evidence for request-plus-snapshot atomicity, foreign snapshots, stale draft detection, and unchanged persisted finalized payroll. Supply user-run validation commands; no live recalculation or payroll import is part of this plan.

## Verification handoff

Provide common/employee/attendance/leave/payroll focused commands above, UI focused tests, `rtk npm run lint`, and `rtk npm run build`. Integration acceptance requires a disposable tenant with two location policies, global/location holidays, a location change, spanning leave, pre-activation records and a frozen payroll allocation. Schema validation, browser previews, and persisted financial-history comparisons are separate acceptance evidence.
