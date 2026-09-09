# Approved HRMS enhancement design

Approved in conversation on 2026-09-08. Implementation proceeds in four phases; no automatic commits, deployment, tenant migration execution, or live-data writes. Preserve unrelated work. Do not run Dart or Flutter commands.

## Phase 1: attendance accuracy and compact working screens

- Monthly average = completed segment duration / distinct workdates with positive completed duration. An open segment adds neither duration nor a denominator day; a completed segment on that same date still counts.
- Aggregate the entire selected period on the backend independently of cursor pagination. Bind self-service summaries to the authenticated employee, using the same attendance read authorization as myAttendance.
- Attribute overnight work to the stored workdate, including shifts ending in the following month. Prefer canonical instants; use the existing tenant-timezone fallback for historical time-only rows.
- Display average, completed workdays, total completed hours, and incomplete-punch count in a compact summary. Do not present unavailable data as zero. Retain request ownership protections during month, account, and client changes.
- Attendance: compact title/actions and month toolbar, summary, then records. Put policy/shift reference information behind native expandable controls after the primary data.
- Timesheet: compact period/action toolbar immediately followed by calendar. Keep submission and edit-window protections. Add a narrow-screen agenda presentation, retaining date-specific entry actions.
- Leave: compact balances and request history first. Put holiday and leave-type reference information in expandable secondary sections. Preserve permission, pagination, recovery, and approval behavior.
- Dialogs: consistent responsive sizes and grouped fields. Keep important form actions visible using the shared footer. Preserve focus trapping, return focus, validation, busy-state dismissal guards, and ownership protections. Prioritize employee creation/editing, leave application, attendance adjustment, expense submission, announcement creation, and asset forms.
- Verify functional regressions and browser layouts at desktop/tablet/mobile widths where the browser environment permits. Do not claim production or signed-in runtime proof from component tests.

## Phase 2: optional unpaid leave and comp-off

- Unpaid-leave deduction is opt-in. HR/Admin configures basic-pay basis and day divisor. Calculation uses approved unpaid leave allocated to that payroll period. Store the basis and result with payroll; closed payroll is immutable.
- Payroll treatment is selected by HR/Admin: unpaid leave reduces earnings before statutory calculation, or is a separate deduction after the existing statutory calculation.
- Comp-off eligibility inherits designation settings unless an employee override exists. Employees may request a half/full day for any worked date; manager/HR is responsible for assessing eligibility. Do not enforce weekday, holiday or roster eligibility and do not convert attendance hours to credits. Approval credits a separate balance once.
- Monthly earning limit, yearly earning limit and maximum unused balance are independently optional administrative settings.
- Credit validity begins on approval date and uses configured duration. Leave dates must fall before credit expiry. Track earned, reserved, used, and expired credits; reject duplicate crediting and overbooking. Cancellation restores the original expiry, never extends an expired credit. Limits and claim deadlines are configurable.

## Phase 3: video and pre-joining

- External notification video links open in a new tab. Private uploaded videos play inside the app; initial upload limit is 50 MB. Use a bounded media upload/playback path with audience authorization, progress and seeking rather than expanding Base64 GraphQL attachments.
- Admin configures required basic fields/documents. Invitations can be emailed by the system or copied; configurable invitation expiry defaults to 48 hours.
- Candidate experience is a private, Google Forms-style link: open, enter details/upload documents, and submit without creating an account or password. The invitation grants access only to its assigned submission, documents and feedback; it is not an employee login or an application role.
- Keep candidate answers and documents in separate staging records during review. Dedicated permissions control HR review/approval and requests for corrections. A submitted version is preserved for review; authorized corrections are resubmitted through the private-link workflow.
- HR's final Confirm joined action saves the approved information into the actual employee-related tables and sets up the employee's application account/access. Approval of information alone does not create an active employee. Make conversion atomic and idempotent; repeated confirmation must not create duplicate employees or accounts. Revoke candidate-link access after conversion. Enforce lifecycle restrictions in APIs and navigation.
- Invitation expiry controls candidate access only; it does not delete submitted information or prevent authorized HR review. Reissued correction/invitation links replace and revoke the previous link. Default invitation expiry remains 48 hours, configurable by Admin.

## Phase 4: reports and insights

- HR/Admin CSV catalogue: monthly attendance, exceptions, leave balances/transactions, payroll register, unpaid-leave calculations, employee movements, timesheet/project hours, and pending approvals; add onboarding and comp-off reports with those workflows.
- Exports cover the complete authorized filtered dataset, not a display-page limit.
- Period-filtered charts open underlying rows. Cover attendance, pending approvals, headcount/joiners/exits, payroll generated, and workflow exceptions.
- Payment occurs outside HRMS: show net salary generated, not salary paid.

## Delivery boundaries

Each phase has its own implementation plan and verification record. Source changes remain available in the current checkouts for user review. Any necessary production migration/deployment remains a separately executed operation. New business-policy choices beyond this specification must be raised rather than invented.
