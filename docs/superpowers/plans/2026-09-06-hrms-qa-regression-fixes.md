# HRMS QA Regression Fixes

## Goal

Close the reproducible QA gaps with requirement-driven tests across the UI, services, and tenant schema while preserving working timezone, notification, login, attendance-cap, and scroll behavior.

## Verified current behavior

- Punch timestamps and attendance exports use the tenant timezone and canonical UTC instants.
- Daily attendance reporting aggregates every completed segment and exposes total logged minutes.
- Exactly 24 hours is rejected by the attendance daily cap.
- Direct-notification action URLs are displayed, authorized, and opened by View.
- Employee status changes preserve authentication unless the employee crosses the TERMINATED boundary; independently disabled login accounts remain disabled.
- The authenticated shell owns the single page scrollbar.
- Canonical Employee and Admin roles receive attendance:punch_self with SELF scope through migration 0067 and the supported seed/bootstrap scripts.

## Implementation

1. Add regression tests for decimal values persisted with four zero decimal places, then normalize expense approval display and comparisons without accepting more than two non-zero decimal places.
2. Add a forward tenant migration linking leave requests to private file_storage rows with a tenant-safe foreign key. Validate file tenant and uploader ownership in the leave submission transaction.
3. Replace the leave supporting-document reference field with a PDF/JPG/PNG file chooser, upload the file before submission, and send the typed file ID. Retain legacy reference output for historical rows.
4. Add server-backed leave pagination with total count and stable ordering, then add Previous/Next controls to Recent Leave Requests and leave-report details.
5. Render leave-request detail rows and payroll-cycle detail rows below report summaries. Use exact employee IDs for attendance filtering to remove ambiguous name matches.
6. Add or strengthen regression coverage for attendance aggregation, the 24-hour boundary, tenant-time display, notification navigation, single-scroll ownership, and termination-only login deactivation.
7. Add a read-only attendance authorization audit script for tenant operators. Existing tenants must run pending Liquibase changes and reauthenticate so refreshed JWT claims contain the canonical punch scope.
8. Regenerate GraphQL client artifacts after schema/document changes, run focused UI and Rust tests, run database contract tests, then run builds and diff checks.

## Deployment notes

- Do not write tenant data or deploy as part of this change.
- Apply tenant Liquibase migrations with scripts/update-tenant-liquibase.ps1 during deployment.
- Run scripts/update-indian-tenant-timezones.ps1 in preview mode before any explicit timezone update.
- Users must sign out and sign in after RBAC migration so access tokens contain refreshed permissions and scopes.
