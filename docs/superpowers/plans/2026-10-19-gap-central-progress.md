# Central gap integration evidence

## Implemented

- Explicit source operation mappings for Employee/account/workflow/offboarding and payroll jobs. Added source EmployeeList/EmployeeReferences to avoid stale directory versions and EmployeeLoginProvision using the existing real source account provisioning transaction. Role administration is separate from employee administration; no arbitrary existing-user links.
- Runtime authorization has source-verified alternate target account IDs solely for self-administration guards. Company/account lock precedes affected domain rows. New creation versions are positive and serialized; no fake source users.
- Payroll job fresh-authorization route accepts only the bound Payroll service, exact immutable original intent/body hash/operation/resource/principal/source login/membership/grant and saved identity/link epochs. Old unknown epochs are not backfilled. Ops0123 adds nullable original epochs and ACCEPTED intent state.
- Operational progress exposes source-defined attendance, whole-request leave centidays and project time, with exact quantity strings/nulls. No task/productivity model is invented. Existing reporting/history now use source-marker/CDC/all-role/all-partition capture health and retained start coverage.
- Protected fixed archive-sidecar client signs exact requests using existing RS256 service credentials; central holds no encryption keys or tenant DB credentials. Current history:read ALL plus history:export ALL before/after external I/O; exact org/company/archive/epoch/range/count/field response checks; browser output is curated purpose-limited history, not arbitrary stored JSON. Retrieval uses immutable accepted archive epoch with current company access.
- Extended history browser allowlist includes exact attendance/leave/project/admin/legacy mapped fields and typed attribution, excluding original private audit bodies.
- New source capture timer and master migration includes are integrated. Production migration/deployment remains unperformed.
- Identity/policy network failures and server outages now remain retryable Internal errors; positive authority denials and malformed/substituted responses remain fail-closed.

## Executed evidence

- Shared new enum contract first RED (unknown operation), then focused protocol GREEN1.
- `cargo test -p kabipay-organization --lib --offline`: latest completed session29959 exit0,26passed/1explicit-disposable-PGignored. Includes operational exact-number/range/privatefield tests, archive identity/count/epoch tests, capture coverage tests and original job intent epoch tests. This run predates final EmployeeList/LoginProvision and network-classification edits; final repeat required.
- Prior focused job authority test80076 exit0,1passed. Earlier organization test13969 exit0,24passed/1ignored.
- Authoritative SDL first export68209 exit0 to `hrms-gateway/schemas/organization.graphql`, but lacked final source list/login enums. Latest export93044 pending Cargo queue. Do not hand-edit SDL to claim authoritative generation.
- HR source94passed/2existingS3ignored +Workflow5passed; Payroll5unit +1realPGincluding crash/commit-lease tests +Tenanthelper1passed, per their owner ledgers. HTTP fixture builds/integration still pending.
- Source designation reference query was corrected after verifying real schema uses title, not name; actual HTTP fixture now tests source references/list.

## Remaining validation/review

- Final source/central builds and full separate-company HTTP HR/job fixture, including login provisioning and non-retention of credential-bearing payloads.
- Final authoritative SDL/client generation, UI type/lint/regression/browser acceptance.
- Central end-to-end report/archive HTTP plus actual CH/marker proof, including revocation/partial coverage.
- Dedicated GPT6.1 sol evidence summariser, two independent scoped reviews and fixes.
- Reconcile working architecture HTML copies; keep frozen baseline byte-exact. Production TLS/ACL/RLS/service role grants, deployment/migrations, real historical backfill/cutover/retention and real backup/restore remain separate release gates, never claimed executed from synthetic proof.

## Final integration and closure (supersedes in-flight items above)

- Shared business-domain errors now return definitive4xx rather than ambiguous503; transport/identity outages remain retryable. A focused status classification regression passed.
- Real ClickHouse25.8 exposed tuple field pruning across views and nested aggregate alias substitution. Current supported-fact views expose explicit columns, retain nullable values through tuple-wrapped argMax, and qualify outer aggregate inputs. All3actual queries passed. The full central HTTP fixture separately confirmed nonempty exact/null fact rows.
- Real source-to-ClickHouse HTTP exposed411 when reqwest omitted an empty POST length. A new wire-level test first failed on `.body(empty)` alone, then passed with explicit `Content-Length:0`; no source payload/query/secrets are logged. Current organization suite80144 passed28tests/1default-PGignored; Tenant11passed/2special-PGignored. Reporting authorization's disposable PostgreSQL test24403 then passed separately after updating its schema fixture to current membership readiness fields.
- Final source/central fixture binaries built. Expanded three-DB HTTP68271 passed, then root independently reran85435 and observed exit0 with all foundation, HR, payroll, report/history/archive, current-denial and lifecycle assertions. Each run cleaned its own random services/database container.
- Authoritative SDL69401 with PayrollDetail generated the final UI client. UI static/build/regression evidence is in the final gap closure ledger. Live browser acceptance remains unavailable and explicitly NOTDEMONSTRATED.
- Independent review one closed G1/G2; independent review two closed R2-C1/C2 after the residual retired-Connect ordering correction. Dedicated summariser input and dated final review addenda are retained.
- Five organization crates strict all-target Clippy98645 passed with `--no-deps`; source Employee/Workflow/Payroll all-target check33633 passed with existing warnings. Broad common dependency-inclusive strict lint is not claimed clean.
- Canonical HTML v7 and both working mirrors synchronized with location-correct local links; structural/link checks passed. Frozen recorded baseline remains byte-exact. Root verified all5repositories stay on the intended feature branch and tracked diff whitespace checks exit0. Untracked files are not covered by git diff --check.
- Only the4label-verified synthetic stack containers were stopped after validation; no production service or existing-company data was changed. No commits/pushes/deployments.
