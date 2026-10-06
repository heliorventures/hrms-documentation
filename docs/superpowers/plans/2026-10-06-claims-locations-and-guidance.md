# Claims, Locations, and Guidance Implementation Plans

Approved design: [claims-locations-and-guidance-design](../specs/2026-10-06-claims-locations-and-guidance-design.md).

Status: All four areas were approved and implemented in the current working branches. Focused regression tests were explicitly delegated. Independent review and its correction pass found no remaining Critical or Important source issues. Release acceptance remains pending migrations, generated GraphQL contracts, lint/typechecks/builds and browser/disposable-database verification. See [implementation and verification handoff](../reviews/2026-10-06-claims-locations-and-guidance.md). The unfinished additional request was withdrawn by the user.

| Order | Plan | Result |
| --- | --- | --- |
| 1 | [Mandatory supporting files](2026-10-06-mandatory-claim-travel-files.md) | Expense and travel submissions require evidence, preserve upload retries, and provide authorized attachment access. |
| 2 | [Expense and travel reports](2026-10-06-claim-travel-reports.md) | Filtered company reports, pagination, and matching CSV export. |
| 3 | [Locations and working calendars](2026-10-06-location-working-calendars.md) | Company locations, dated assignments, weekly offs including selected Saturdays, and consistent attendance/leave/payroll calculations. |
| 4 | [Guidance and feature search](2026-10-06-guidance-feature-search.md) | Tenant page/tab and feature guidance, detailed page help, labelled design illustrations, and authorized feature destinations. Live screenshots and role-based browser acceptance remain pending. |

Plan 2 uses Plan 1's travel supporting-file column. It reports current location using the existing employee field and does not require calendar activation. Plan 3 preserves that current field while adding history. Plan 4 captures screenshots only after the underlying screens exist. Do not run these as concurrent writers to shared schemas, route registries, or generated clients.

## Execution constraints

- Follow the approved design and each plan's interfaces. Read applicable current coding/lint and domain skills before writing product code.
- Use `rtk` for shell commands. No automatic commits, Dart/Flutter commands, live migrations, deployment, or live payroll changes.
- The user explicitly approved focused regression tests and instructed implementation to continue while local services are unavailable. Lint, typechecks, builds, live migrations and deployment remain user-owned. Never claim runtime acceptance without output.
- Preserve existing UI employee-directory changes, Pencil assets, review documents, and documentation/payroll work. Inspect current Git status/diffs at execution time. Use an isolated worktree if needed; resolve how uncommitted prerequisite UI changes enter it before implementation.
- Use focused source/AST-selected context. If the user chooses multi-agent execution, use a dedicated GPT 6.1 sol summariser for execution logs/history before presenting those records to Astra, as requested. Do not create extra workers in advance of that choice.

## Readiness and rollout

Current tenant master ends at `0095_payroll_catalog_integrity`. Planned migration names are `0096_travel_supporting_file`, `0097_location_working_calendar`, and `0098_leave_working_dates`. Recheck for concurrent additions before creating any migration; if a number is occupied, select the next available number and update the plan references together.

Targeted entity generation must select the migration that originally created a changed table: `--only 0033_travel_request` after adding the travel column; `--only 0097_location_working_calendar` / `--only 0098_leave_working_dates` for new tables. The generator follows subsequent included alterations; selecting an add-column-only migration produces no domain entity. Never hand-edit generated entities or rewrite all domains unnecessarily.

Database validation uses a disposable tenant schema. New attachment enforcement requires a coordinated UI/backend release: apply the additive migration, make upload-enabled clients available, then activate mandatory server validation during a reviewed release window. No intermediate release may be described as satisfying mandatory uploads until service enforcement is active.

Calendar activation is an explicit tenant configuration action after the schema and consumers are available. Existing requests and frozen payroll allocations keep their legacy treatment. Before final delivery, collect focused tests, UI lint/build, disposable DB migration/transaction results, browser role/scope checks, and screenshot verification. Missing evidence stays listed as outstanding work.

## Review handoff

Native implementation was approved and used. A dedicated GPT 6.1 sol summariser compressed execution evidence before a focused independent Astra review. The review and its follow-up corrections are recorded in the handoff. Commits and release acceptance remain with the user.
