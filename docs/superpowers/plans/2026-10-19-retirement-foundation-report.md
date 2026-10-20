# Private event foundation implementation report

Status: implementation ready for independent review; latest Rust/SQL validation pending shared Cargo build. No commit, deployment or live data changes.

## Interfaces and ownership

- Exact wire/keyfile/SQL assumptions: `hrms-svc/crates/kabipay-common/src/private_events/contract.md`.
- Rust: `private_events/{mod,types,crypto}.rs`, common Cargo dependency `aes-gcm.workspace=true`, common module export. Other pre-existing common changes preserved.
- Node actual root: `hrms-svc/integrations/organization-events`; new `src/private/{contract,crypto}.mjs`, `test/private-crypto.test.mjs`, synthetic `test/private-vector.json` and explicit fixture generator.
- Public Rust APIs: `append_audit(db,&AuditRecordInput)`, `enqueue_delivery(db,&DeliveryIntentInput)` and explicit-keyring equivalents. `configured_keyring`, `AuditHistoryReader`, `read_audit_history` and history filter/page types. New reader owner must implement signed history transport and authenticated coverage/pending merge; no unsafe all-outbox overlay remains.
- Node: `parseKeyring`, `encryptFrames`, `decryptFrame`, `decryptFrames`; contract exports `HEAD_FIELDS`, `associatedData`, `sourceHash`, bounds and validators. `decryptFrame` authenticates one bounded frame without declaring complete source/hash acceptance. `decryptFrames` verifies framing and complete byte hash.

AES256-GCM authenticates immutable event/record/tenant/purpose/generation/source/resource/time/key/hash/framing head. Source generation is a required positive safe integer, not a production fallback. Both Rust producers query `private_source_cutover.producer_generation`, encrypt with that generation, then lock the same authority row with expected generation `FOR SHARE` in their publication statement. Missing/changed authority fails closed. Audit frames use one INSERT statement; delivery receipt plus all frames use one CTE statement. Delivery duplicate identity/hash/metadata/current generation is idempotent; conflict rejects. Organization is NULL only for private streams, company defaults unchanged.

Key file path comes only from trusted runtime `KABIPAY_PRIVATE_EVENT_KEYS_FILE`; no fallback keys, test environment mutation or worker URL/secret fields. Keyfile <=64KiB/256 keys; one active key per configured tenant/purpose with inactive rotation readers. Source bytes <=16MiB, frames <=256KiB/64; exact source bytes are hashed/restored, unknown audit entity/action retained. Audit input field names match legacy `before_state`/`after_state`.

## RED/GREEN evidence

Commands below run from `hrms-svc/integrations/organization-events` unless specified.

1. RED `node test/private-crypto.test.mjs`: missing `src/private/crypto.mjs` before implementation. Native `node --test` initially hit sandbox `spawn EPERM`; `--test-isolation=none` is unsupported on Node22.18, while `--experimental-test-isolation=none` works.
2. GREEN latest `node --experimental-test-isolation=none --test test/private-crypto.test.mjs`: **8 passed, 0 failed**. Exact UTF8 bytes, shared Node/Rust frozen vector, authenticated single-frame handling, every immutable head field including source generation, ciphertext/nonce/scope tamper, incomplete/duplicate framing, oversized source, rotation, bad keys, unknown fields and invalid dates covered.
3. RED calendar regression: 5 passed/1 failed (`Missing expected exception` for normalized impossible calendar date on encryption). Fixed canonical UTC date comparison; subsequent focused run green.
4. RED strict-keyfile parity regression: 7 passed/1 failed (`Missing expected exception` for unknown keyfile fields). Fixed exact property sets; latest focused run 8/8 green.
5. From `hrms-svc`, earlier `cargo test -p kabipay-common --lib private_events`: **4 passed, 0 failed**, including Node frozen fixture decryption in Rust. Session **77542** completed successfully. This predates the latest authenticated-generation producer changes and SQL test, so it is not latest-source proof. Earlier session81229 had 3/3 crypto tests green. Both emitted existing future incompatibility warning for proc-macro-error2.
6. Latest same command `cargo test -p kabipay-common --lib private_events`, exec session **50843**, completed RED: 29 test-only missing import/trait errors after the ignored PostgreSQL test was added. Corrected test module imports to bring parent API/types/SeaORM traits into scope. No subsequent Cargo build queued per coordinator handoff; latest source has not been claimed compiled or GREEN. Production module compilation reached the test-only diagnostics without a reported production error, but this is not a successful compile claim.

One broad Node run during parallel WIP was performed before coordinator requested focused checks only. Its final snapshot was 61passed/5failed; temporary log `%TEMP%/private-foundation-node-suite.log`. Failures: three acceptance fixture tests with `invalid auditPrincipal` (canonical company schema, isolated SMT contract, precreated streaming topics), process-tree cleanup `spawn EPERM`, and acceptance launcher gate test. Infrastructure/coordinator notified; these are unresolved in this foundation report, and the source was concurrently changing. No broad suite success claimed.

## Pending isolated PostgreSQL proof

Infrastructure owns a disposable native PostgreSQL17.6 fixture at `127.0.0.1:55494`, user `private_fixture`, database `postgres`, trust auth. Connection: `postgresql://private_fixture@127.0.0.1:55494/postgres`. Never apply this fixture URL to production settings. Infrastructure owns shutdown.

The ignored test `private_events::tests::postgres_transaction_savepoint_generation_and_delivery_atomicity` creates only transaction-local TEMP tables (`ON COMMIT DROP`), rolls the whole test transaction back, and requires explicit `PRIVATE_EVENT_TEST_DATABASE_URL`. It checks missing authority, audit savepoint rollback, source generation17 in the encrypted head, unknown fields restored, matching delivery dedupe, conflict rejection, failing frame insertion rolling back the receipt, and generation rollover rejecting an old intent identity.

Coordinator must rerun `cargo test -p kabipay-common --lib private_events` after the corrected test imports, then execute the freshly built test executable directly to avoid another Cargo queue:

```powershell
$env:PRIVATE_EVENT_TEST_DATABASE_URL='postgresql://private_fixture@127.0.0.1:55494/postgres'
& .\target\debug\deps\kabipay_common-1aa56dc629b7f346.exe --ignored --exact private_events::tests::postgres_transaction_savepoint_generation_and_delivery_atomicity --nocapture
```

Confirm executable hash/name from the latest Cargo output before invoking. This SQL proof is **NOT DEMONSTRATED** until executed. Latest-source Rust compilation, actual concurrent generation-change scheduling, runtime history transport/pending coverage, actual Kafka/CH isolation, full-row export/archive restore and production deployment remain separate acceptance work.
