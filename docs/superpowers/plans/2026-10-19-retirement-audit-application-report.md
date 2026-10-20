# Retirement audit application implementation report — 19 October 2026

## Application changes

- Calendar/location/import callers retain their existing caller connection/transaction/savepoint while `audit_calendar` appends encrypted private audit frames. Attendance policy and expiry, employee profile changes/evidence reviews, comp-off leave cancellation, notification settings/consent and seven survey management events use the same private append port. Original actor, UUID, PostgreSQL microsecond time and before/after fields are retained; survey events accept only the seven management enum cases with static metadata.
- `append_audit_with_keyring` validates the actor against the source tenant's `user` row in the same statement, with `FOR KEY SHARE` actor locking and shared generation locking. A missing/cross-tenant actor or stale authority writes zero frames and returns an error; business transactions roll back through their existing caller error path.
- Profile change/review, approved leave/expense and common due-offboarding webhook publication use `private_webhooks::enqueue_webhooks` inside the original transaction. Notification read/unread state, preference/consent, occurrence deduplication and templates remain business state. Offboarding retains the original UUID and timestamp in `private_domain_receipt` before commit; separation FK is deferred by migration 0125.
- Survey opening and failure deduplication read/write `private_survey_execution_state` under the existing survey lock, retaining ordered `(occurred_at,id)` transition precedence and earliest opening. Management history still checks survey existence and resolver authorization; DTOs expose only action, time and the seven static messages, newest 100 ordered timestamp/UUID descending. No participation data is added.
- Analytics audit history uses the private source history client and the existing DTO field mapping. Resolver authorization remains in the existing directory management check. No organization grant is expanded.

## History transport and overlay

`kabipay-common/src/private_events/history_client.rs` reads only operator-configured `KABIPAY_PRIVATE_HISTORY_CLIENT_FILE` (maximum 64 KiB): `{schema_version:1,bindings:[{tenant_id,url,key_b64}]}`. Each binding selects a fixed HTTPS URL ending exactly `/internal/private-events/history` and a canonical 32-byte base64 HMAC key. Runtime filters cannot select credentials, sources or endpoints. Redirects and ambient HTTP proxies are disabled. Absolute bounded certificate/key files from `KABIPAY_PRIVATE_HISTORY_CLIENT_CERT_FILE` and `KABIPAY_PRIVATE_HISTORY_CLIENT_KEY_FILE` provide mTLS; optional `KABIPAY_ORGANIZATION_HTTP_CA_FILE` supplies additional verified CA roots.

Request/response HMAC proofs sign domain plus NUL plus exact JSON bytes using the agreed `kabipay-private-history-request-v1` / `kabipay-private-history-response-v1` domains. Version, tenant/generation, request UUID, age, coverage UUID and request SHA256 bindings are checked. The source authority and accepted/unrevoked/current database/schema/version/generation-bound restored initial `audit_log` export with reader switch complete are required. Runtime reads preserve permanent accepted archive access after the short destructive-authorization expiry; revocation still blocks reads. Missing history or coverage is an error.

The source pending overlay reads a repeatable-read read-only snapshot in UUID keyset pages, restricted to audit stream and `source_kind=audit_log`. It decrypts complete record frames and checks identity/tenant/time/resource/current-or-earlier generation, filters identically to remote history, deduplicates equal records, rejects observed UUID content conflicts, orders timestamp/UUID descending and returns top N. The remote API fetches only top N; no external history full scan or fabricated merged total is exposed. The facade supports current top 100/500 callers and rejects nonzero offsets. A 20-second deadline and 64-MiB byte budget surface backlog explicitly rather than returning truncated history.

## Evidence so far

- RED: direct `node hrms-svc/scripts/tests/retirement-audit-application.cjs` initially failed both legacy producer and survey execution/read boundaries. A third RED demonstrated the missing history client. `node --test` could not spawn in the sandbox (`EPERM`); executing the Node test script directly works.
- GREEN: the same direct source contract script now passes 6/6 checks, including the tenant actor SQL boundary and PostgreSQL microsecond timestamp canonicalization. These are static source checks, not database or browser proof.
- Existing survey lifecycle and attendance runtime/policy proxy tests now expect encrypted publication and local lifecycle state. The location disposable PostgreSQL fixture now uses source authority/private outbox tables and retains its invalid-actor rollback regression. The common isolated PostgreSQL transaction/savepoint test adds missing, cross-tenant and valid actor cases.
- New Rust history unit tests exercise HMAC domains/keys/tampering, configured endpoint/tenant validation, short/duplicate keys, duplicate/conflict handling and UUID tie ordering. A separate audit frame regression checks nanosecond input canonicalizes to the same PostgreSQL microsecond timestamp in decrypted bytes and envelope; legacy export bytes are untouched. The static timestamp boundary failed before this change and passed afterward.
- Rust compile and focused runtime results are recorded below; the explicit isolated common PostgreSQL atomicity test also passed.

## Files owned

Under `hrms-svc/crates/`: common `private_events/history_client.rs`, actor validation/test additions in `private_events/mod.rs`, `working_calendar/writes.rs`, `due_offboarding.rs`; attendance `attendance_day/repository.rs`, `attendance_day_runtime.rs` and their runtime/policy tests; employee `profile_change_service.rs`, `profile_record_service.rs`, `tests/company_locations.rs` and `tests/support/company_locations.sql`; leave `leave_service.rs`; expense `expense_service.rs`; notification `automation_settings.rs`; survey `survey_lifecycle.rs` and `survey_lifecycle_tests.rs`; analytics `analytics_service.rs` audit reader and `resolvers/types.rs` audit DTO mapping. Static contract: `scripts/tests/retirement-audit-application.cjs`.

## Explicit limitations

No production databases, source cutover, migration/restore acceptance, broker/ClickHouse/mTLS deployment, browser tests or commits were performed. The PostgreSQL execution below uses an explicitly provided disposable PG16 fixture and TEMP tables only. Source static/proxy/unit evidence and isolated TEMP-table atomicity cannot prove real survey row-lock concurrency or end-to-end read-your-write. The initial accepted export must exist before private history reads work, including fresh installations requiring verified-empty acceptance. Retained pending identities outside the remote top N are not individually checked against remote hashes; observed duplicates are checked and protected immutable history/accepted cleanup coverage remain prerequisites. Legacy analytics outbox/retry and webhook-delivery log readers are outside this agent's audit reader assignment and remain integration work for the parent/source owner.

## Coordinated Rust check

Started `cargo check -p kabipay-common -p kabipay-survey -p kabipay-attendance -p kabipay-analytics -p kabipay-expense --lib --tests --offline` in `hrms-svc`, unified exec session `20163`. It initially waited for the shared build-directory lock; the completed result is recorded below. `cargo check` alone does not emit fresh test executables; pre-existing common binaries predated these history/actor/precision changes and were not used as runtime evidence.

Rust check completed GREEN, exit 0, after 8m14 including build-lock wait. All five requested crates' library and test targets compile with the new history client, survey/attendance tests, tenant actor checks and precision regression. Output included existing analytics test fixture dead-code/unused-import warnings and the dependency `proc-macro-error2` future-compatibility warning; no compilation errors occurred. This proves compilation only, not execution. The shared target lock was held by an IDE Rust Analyzer workspace check; the parent identified and stopped that exact background check before this focused command progressed.

The initial archive runtime TTL regression was observed RED then GREEN in the direct static Node suite (6/6). Its SQL predicate was corrected after the successful five-crate compile and during fresh test compilation; no redundant full build was queued for that SQL-only change, per parent coordination.


## Fresh focused runtime execution

`cargo test -p kabipay-common -p kabipay-survey -p kabipay-attendance --lib --test attendance_day_policy --no-run --offline` completed GREEN, exit 0 (25m07 on the Windows debug build). Fresh executables from that command were run directly:

| Executable/filter | Result |
|---|---|
| `target/debug/deps/kabipay_common-0a6a7ea72ca501a6.exe private_ --nocapture` | 21 passed, 1 isolated-PG test initially ignored; includes proof/config/merge, microsecond regression, crypto framing/tamper/frozen Node vector and per-destination helper tests. |
| `target/debug/deps/kabipay_survey-845f3feffe26babf.exe survey_lifecycle --nocapture` | 9 passed; local lifecycle dedupe, scheduling/locking order, rollback propagation, static management metadata and authorization negatives. |
| `target/debug/deps/kabipay_attendance-e3e030a45c1edb94.exe attendance_day_ --nocapture` | 19 passed; expiry, correction preservation, audit failure retry, policy boundaries and authorization checks. |
| `target/debug/deps/attendance_day_policy-ece4f2432318de3d.exe --nocapture` | 18 passed; transactional encrypted audit, raw snapshot/actor preservation, failure propagation, history and preview/schedule parity. |
| Latest common executable with exact ignored `private_events::tests::postgres_transaction_savepoint_generation_and_delivery_atomicity` | 1 passed against the stable isolated PG16 fixture. |

Runtime total: 68 passed. The common PostgreSQL test creates TEMP `user`, `private_source_cutover`, `private_delivery_receipt` and `company_event_outbox` within its own transaction; it does not mutate the infrastructure fixture's `source_one` or `kabipay_ops`. It demonstrates savepoint rollback, source-generation fencing, missing/cross-tenant actor rejection and valid actor acceptance, duplicate/conflicting delivery behavior and receipt rollback when frame insertion fails. It finishes by rolling back its transaction. This is real isolated PostgreSQL evidence, not production or migration acceptance.

The first isolated PostgreSQL attempt used the parent's earlier fixture port 61302 and failed before beginning its transaction with `PoolTimedOut`, because that fixture had been replaced. Infrastructure supplied the held port 62831; the identical fresh executable and exact test then passed in 0.45 seconds. No source fix was needed for that environment failure.

The initial archive TTL follow-up changes only the source SQL predicate; it was made during the no-run build and is covered by the new static RED/GREEN TTL contract. No claim is made that these native unit tests execute the full signed history SQL/mTLS/Kafka/ClickHouse overlay path. The adapted company-location ignored PostgreSQL integration target was not built or executed by this agent's focused commands. Source checks, proxy tests and isolated atomicity retain those explicit limits.
