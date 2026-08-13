# Employee Self-Service Production Readiness Design

Date: 2026-08-12

Status: Approved as the follow-up to the employee self-service audit

## Objective

Close the security, operational, and usability gaps left after the first employee self-service delivery. HR reviewers must be able to review the real proposed values and evidence without exposing them to ordinary users; decisions must be auditable and notify the requester; evidence submission must not leave inconsistent records; validation must be enforced both when a request is submitted and when it is approved; and the remaining profile and org-chart interactions must stay section-local and accessible.

## Security and data design

- Store only a masked, non-sensitive summary in `requested_payload`.
- Store the complete pending value as an authenticated encrypted envelope in a new `requested_payload_encrypted` column. Encryption is AES-256-GCM with a random nonce and a versioned application key supplied through `KABIPAY_PROFILE_CHANGE_ENCRYPTION_KEY`. Submission fails closed when the key is absent or invalid.
- Keep a temporary backward-compatible read path for pre-migration pending rows that still contain the legacy JSON payload. New writes never store raw PAN, Aadhaar, bank account, legal-name, or DOB values in JSONB.
- Return decrypted current/requested values only from an HR-authorized review-detail resolver after employee data-scope enforcement. List responses remain masked.
- Signed document URLs are generated only on demand after the existing tenant/employee/document authorization checks and are never persisted in GraphQL cache state.

## Review workflow

- Add an HR review queue with bounded pagination and optional status filtering. Each row contains employee labels, masked summary, request metadata, and evidence availability; full sensitive values are loaded only when HR opens one request.
- Approval and rejection lock the request, decrypt and revalidate the payload, update canonical data, evidence status, immutable `audit_log`, requester notification, and an `outbox_event` in one database transaction.
- Submission and cancellation also create immutable audit events. Submission notifies authorized HR users; resolution notifies the requester.
- Reviewer self-action remains forbidden.

## Validation and consistency

- Legal names have explicit length limits and DOB must be in the past and within a defensible human range.
- PAN, Aadhaar, IFSC, bank-account number, account type, and all optional string lengths are validated centrally.
- Work dates cannot be in the future; education dates and completion year remain bounded.
- Approval calls the same validator used at submission, preventing stale or malformed stored payloads from bypassing current rules.
- Evidence upload/link operations compensate on link failure by soft-deleting the newly created document record and deleting its object when supported. UI submission prevents navigation while the combined operation is in progress and reports retry-safe outcomes.

## React experience

- Add an HR Profile Review page with pending-count affordance, masked queue, detail drawer, evidence preview/download, and approve/reject controls.
- Wire document cards to the signed-read-url query with explicit loading/error states.
- Replace browser `prompt`/`confirm` usage with accessible dialogs that retain values after mutation failure.
- Reconcile every successful section mutation locally; only explicit Refresh performs background reconciliation and never unmounts the profile shell.
- Add org-chart search, expand/collapse controls, and visible data-quality warnings for missing managers and cycles.

## Testing and rollout

- Add focused Rust and React regression tests before production changes, but do not execute unit tests in this Codex session per repository instructions.
- Allowed verification is limited to schema parsing, compilation/build checks that are not unit tests, generated-contract review, and `git diff --check`.
- No commits are created by Codex. The user applies migration `0051` after deploying the new service configuration so encrypted writes cannot start without the key.

