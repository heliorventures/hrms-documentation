# Organization completion ledger

Plan: `2026-10-19-organization-completion.md`. User authorized all remaining implementation, focused checks, lower-model delegation and two review passes while unavailable for eight hours. No repeat approvals for routine reversible work. No commits/deployments/live migrations/Dart/Flutter.

Start: 2026-10-18 18:56 UTC / 2026-10-19 00:26 IST; availability window to about 02:56 UTC / 08:26 IST.

- Pre-flight: previous metadata phase and tests are recorded in its own ledger; all work remains uncommitted on feature branches. Preserve unrelated loan edits and current database HEAD 80fb0c7.
- Ruling: user explicitly requested two lower-model review passes, superseding a skill's default single final review. No additional confirmation will be requested for approved implementation/validation. Production operations remain excluded.
- Ruling: partition implementation by owned source areas and use one shared protocol contract; root coordinates shared Cargo/schema changes. This avoids conflicting edits while delivering the full feature.

## Tasks

- [x] Shared service/delegation/browser-key contracts and live policy.
- [x] Company-owned grants/relationships/commands and business adapters.
- [x] Organization directory/graph/command orchestration/inbox/reporting APIs.
- [x] Kafka/CDC/ClickHouse/OTel pipeline and safe cleanup tooling.
- [x] Existing-application Organization/manager/owner/payroll UI.
- [x] Integrated fixtures, generated contracts and browser checks.
- [x] Independent review pass 1 and confirmed fixes.
- [x] Independent review pass 2 and confirmed fixes.
- [x] Final verification, architecture HTML/runbooks and handoff.

## Implementation evidence at 19:47 UTC

- Shared service credentials and mandatory identity/link/membership epochs added; 11 security tests passed. Company key is restricted to exact service and explicit tenant IDs; route/body/audience/type are signed.
- Organization API and global graph orchestration authored with directory synchronization, source grants/relationship ACKs, minimal command intents and live policy. First reporting tests passed; all-target compilation/export in progress.
- Bound source adapters authored for leave/timesheet/performance/payroll, including principal attribution in payroll loan recovery. Initial focused all-target check passed before later canonical-manager/feedback/bootstrap refinements. Tenant agent is running updated checks and synthetic PostgreSQL tests.
- Kafka/ClickHouse/PostgreSQL actual worker and Debezium acceptance passed on dedicated synthetic containers: committed events captured, rollback excluded, replay/corrections/tombstones correct, metadata-only quarantine and recovery, source CDC role denied business table SELECT. Deployment TLS/restore are not established by this fixture.
- UI authored in existing application with feature flag; focused state/security/payload tests running. Authoritative SDL generation and browser review remain pending.
- Added verification-only company-bound client RSA mode; source company startup refuses legacy client HMAC when organization policy transport is enabled. Legacy tenant deployments remain opt-in compatible. RSA-focused checks pending.
- Reviews are still pending; no phase or feature is marked complete from authored code alone.


## Integration and review checkpoint

- Fresh organization all-target check and main/bootstrap/exporter build passed. Authoritative SDL exported with pending recovery, membership lifecycle, installed readiness, manager replacement. Organization library suite18passed/1explicitreal-PGignored; later graph/configuration race guards still require refreshed checks.
- Security suite12passed including reproduced RED then fixed service-key cross-company/cross-service reuse. Offline deployment validator3passed with canonical DER fingerprinting and 2048-bit/public-only gates. Client RSA focused tests are queued with source build work.
- UI authoritative generation and focused Organization/navigation/route suite25files/104passed; strict workspace ESLint passed. Existing Employee canonical-manager display/field ownership is being integrated from actual source SDL, with final application checks pending.
- Isolated actual HTTP chain passed using3physicallyseparateDatabases and actual0111-0117SQL: source RSA identity, bootstrap/invite/accept, membership+directory+foreignmanagerinstall, team, actual unpaidleave approval, exactreceipt oneaction, stale/forged/inactive/revoked denials. Inbox row is a declared direct-projection seam; realKafka/CDC pipeline has separate acceptance.
- Extended HTTP lifecycle passed suspend/fence/deny,resume/fence/team,detach/fence/retainedreceipts/deny. Lost-postcommitACK statusrecovery regression reproducedRED against oldbinary; sourcefix authored, freshbinary/rerun pending.
- Independent lower-model source review pass1complete: no confirmed findings, one source lookup timing concern marked NOT DEMONSTRATED. Manual lock-order/recovery audit found and fixed pending-install graph races, inactive relationship retirement and receipt reACK gaps; fresh evidence required before completion.
- Architecture HTMLv6 includes implemented service diagram, concrete migration relationships, source-confirmed lifecycle and recovery. Real isolated headlessChrome render inspected desktop layout; this is document proof, not HRMS browser acceptance.
- Remaining control-plane history and diagnostics collection wiring identified explicitly; integration agent is implementing bounded CDC retention and an allowlisted log collector template. Legacy history/log deletion remains gated.


## Recovery and second-review checkpoint

- Refreshed actual three-database HTTP fixture passed source receipt reACK recovery after simulated central ACK loss; all prior base/lifecycle/denial checks passed again.
- Second independent reviewer confirmed remote payroll prior-draft date path and performance/installation lock inversions. Payroll source fixed with focused regression; source/retirement lock order corrections and actual PostgreSQL drain tests are in progress. An aggregate-version finding was withdrawn after verifying the real monotonic outbox sequence, rather than accepting an invalid fixture as production evidence.
- Explicit source-fenced cancel-if-uncommitted is authored for reload recovery when no source receipt exists. Cancelled original command UUIDs retain a compact receipt, so late delivery cannot execute; committed results remain committed. UI focused cancellation suite20tests passed; actual source cancellation HTTP fixture awaits fresh binaries.
- Control-plane CDC/history worker, strict command cancellation audit contract, fixed-topic provenance, actual store event sequencing, sink-outage replay, actor/private field protection and actual pinned collector ingestion/redaction passed synthetic acceptance. The company pipeline historical-retention gate is being corrected to retain delayed accepted facts without granting current access.


## Final implementation and verification handoff (2026-10-18 22:43 UTC)

All planned implementation work and both lower-model independent review passes are complete. No confirmed review issue remains open. This is implementation acceptance in isolated fixtures; production rollout remains gated. The canonical [HTML](../../architecture/2026-10-18-organization-cross-company-management.html) and [workspace runbook](../../runbooks/organization-workspace.md) describe actual supported operations and concrete table relationships. Earlier phase runbooks are explicitly marked historical.

### Review corrections

- R2-001: remote payroll recalculation preserves the private current source business date through prior draft/readiness reads; strict source-only regression passed.
- R2-003: source/local Performance, relationship installation, actor references and terminal retirement now share compatible lock order; actual PostgreSQL cycle/participant/rebind and lifecycle drain regressions passed.
- R2-004: pending recovery compares exact original/current authority kind, ID and version. Full successful UI pagination reconciles omitted old references without deleting new/in-flight work; policy/internal failures fail the page. Real HTTP RED then GREEN, UI31 follow-up tests and root policy-error unit tests passed.
- R2-005: current appraisal authority resolves effective canonical or actual legacy manager after END, expiry and detach, including no-review-capability historical PRIMARY. Pending FK refresh preserves submitted/future contracts. Actual PostgreSQL2/2 and ordinary Performance47 tests passed.
- R2-002 was withdrawn because the supposed aggregate-version collision bypassed the real writer monotonic-sequence invariant. It was not fixed by weakening ingestion.

### Executed evidence

| Check | Result / scope |
| --- | --- |
| Final organization lib37503 | 21passed,1explicitPGignored; includes source receipt validation, graph transition, reporting, current identity and authority/internal-error recovery tests |
| Organization/security/protocol strict all-target Clippy40256 | PASS with --no-deps; initial helper-after-test-module lint fixed by moving helper, no semantics/rule relaxation |
| Final source all-target88892 | PASS Employee/Leave/Attendance/Performance/Payroll/Tenant after final review corrections |
| Source tenant strict no-deps Clippy14642 | PASS; broader dependency lint still reports existing common crate findings |
| Additional Auth/outbox-worker/tenant-import all-target check | PASS after final changes; existing Leave dead-code and dependency future-compatibility notices remain |
| Notification all-target76668 | PASS; actual notification SQL in PostgreSQL fixture proves local baseline, foreign suppression, current local canonical and ended fallback |
| Focused Rust source suites | Common92, Attendance89, Leave55, Employee88(with2explicitPGignored), Payroll74, Performance47(with2explicitPGignored), Tenant9(with2explicitPGignored); ignored source SQL/bootstrap/lifecycle seams executed separately in synthetic PostgreSQL |
| Security/domain/client key checks | Security12, domain13, client RSA4 and canonical public-key manifest validator3 passed |
| Final actual HTTP76186 | EXIT0 after fresh org/source builds;3physicallyseparateDBs,actual0111-0117,realAuth/bootstrap/invite,companyfences/directory,managerreplacement/reverse/cycle,leaveapproval/replayonce,lostACK,cancellation/lateoriginal/auditonce,obsoleteauthority,revocation,suspend/resume/detach |
| Broker/history pipeline |17Node tests plus realKafka/PG/ClickHouse/CDC correction/replay/tombstone,sinkoutage,restrictedroles,delayedhistoricalretention and separate controlCDC sequence/replay/quarantine passed |
| Collector/assets |Pinned actual Docker-wrapper/Rust-JSON redaction acceptance, restricted CHreader/worker/operator grants, Compose validation and worker image builds passed |
| UI final full suite |27files120tests passed; additional recovery follow-up6files31tests passed; authoritative codegen,productionbuild/typecheck,strictworkspaceESLint,callercheck1044files passed |
| Gateway final |15tests and TypeScript build passed |
| Database/document structure |All7newmigrationXML parse,masterstreaminclusion and actualforwardSQLfixtures passed;HTMLanchors/sectionbalance/offlinedependencies/mirror match passed |
| Browser |Synthetic application cancellation desktop/390px walkthrough passed; actual offline HTML database diagram/nav desktop1440/mobile390 inspected with no unintended overflow/runtime errors |

The HTTP fixture declares a direct inbox-projection seed; it does not masquerade as broker delivery. Real broker acceptance is separate. Payroll/Performance/Attendance business adapters have compilation/unit/SQL evidence, not full live workflow HTTP/browser acceptance. UI mocks are not a deployed real-account test. No Liquibase existing-company upgrade/rollback/restore, productionTLS/ACLs, completehistoricalbackfill or productionavailability claim is made.

### Workspace and cleanup

- No commits,pushes,deployment,existing-companymigration,DartorFluttercommands or legacyhistorydeletion. All five repos remain on feat/organization-cross-company-management; unrelated loan diffs preserved.
- Final HTTP fixture cleaned its own random database container, processes and generated keys. After all explicit PostgreSQL proofs finished, stopped only verified Composeproject org-pipeline-accept-20261019 (postgres,kafka,clickhouse,connect). No existing services were stopped and retained evidence/storage was not deleted.
- Temporary source/test artifact storage stays ignored. Database and code diffs pass whitespace checks; legacy lint limitations remain explicit.
- Production enablement follows the workspace runbook: reviewed migrations/roles/keys/TLS/topics, source installation, coverage/backfill/reconciliation and backuprestore before history/deliverycleanup.
