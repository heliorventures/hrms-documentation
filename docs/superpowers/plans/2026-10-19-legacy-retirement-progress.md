# Legacy retirement execution ledger

## Authorization and status

19 October2026: user approved full local migration, historical/pending-data tools, guarded retirement, independent reviews and focused checks. Seven repositories remain on `feat/organization-cross-company-management`, uncommitted. No live database/VPS/history/worker was changed; existing organization and loan work is preserved.

- [x] Bounded inventory, dedicated GPT6.1 summary and approved phase7 design/plan.
- [x] Rust/Node authenticated framing, exact raw bytes and atomic publication.
- [x] Separate PostgreSQL/Kafka/ClickHouse preparation and provisioning.
- [x] Audit producers/readers and compact survey/offboarding authority.
- [x] Company maintenance, source delivery/ownership and Finance adapter.
- [x] Private history/query, broker retry/DLQ and authorized replay.
- [x] Full raw export/restore, pending translation and guarded retirement.
- [x] Obsolete runtime entities/worker/Finance loop/deployment removal.
- [x] Independent security/correctness and DRY/SOLID reviews; findings corrected.
- [x] Final Rust/Node images, runtime artifacts and complete default Liquibase rehearsal.

These are local implementation gates. Production identity linking, receiver reconciliation, migration, certificates/grants, browser acceptance and retirement remain separate release gates.

## Replacement and retention

| Legacy item | Implemented disposition |
| --- | --- |
| Tenant audit readers/writers | Transactional encrypted append; signed source-bound protected history plus pending overlay; resolver permissions and safe DTOs retained. |
| `outbox_event` polling/claim/retry | Old worker crate/binary removed. Purpose-specific Kafka work/retry/history/DLQ and fixed source HTTPS execution replace transport state. |
| `webhook_delivery_log` | Full raw archive plus protected delivery outcomes. Subscription configuration and compact per-destination receipts remain. |
| Finance outbox/poller | Immutable delivery references; original signed Employee/Payroll protocol, readback, version/loan/FNF rules remain source-owned. |
| Business schedules | All nine moved to bound `kabipay-tenant-maintenance`. |
| Old entities/lossy producer | Obsolete audit/outbox/log/Finance entities removed. New lossy audit export denied in preparation/CLI; stored historical parsers/manifests remain readable. |
| Legacy tables/migration helpers | Opt-in0126/0127 remove exact objects after locked evidence checks, without CASCADE; nineteen raw-source migration helpers removed. Applied migrations remain reproducible. |
| Atomic publication outboxes | Existing company/metadata CDC bridge remains, with bounded coverage- and generation-checked cleanup. No second raw publication or shared source DSN. |
| Survey/domain identity, delivery/command receipts, notification read/dedupe and payroll jobs | Retained operational business and duplicate-execution state. Their authority cannot depend on remote history. |

## Fresh verification

Separate suites and overlapping Rust subsets must not be summed into a unique total. Earlier owner-report checkpoints are superseded by their final addenda.

| Boundary | Evidence and limits |
| --- | --- |
| Complete Liquibase masters | Fresh metadata41 and tenant267 changesets applied; repeat updates ran zero and retained history fingerprints. Native process exit0. Opt-in retirement is separately tested below. |
| PostgreSQL preparation/gates/retirement | Infrastructure42/42 actual PostgreSQL16 scenarios, contracts4/4. Includes terminal ownership, generation-safe GC, exact catalog removal and surviving post-retirement capture/cleanup. |
| Source bootstrap/grants | Provider49 actual PostgreSQL checks plus native wrapper mocks. Exact registration, PREPARED state, retained business grants and effective privilege negatives. |
| Composed persistence/capture | Infrastructure11/11 actual PG16/Kafka4/Debezium3.2/ClickHouse25.8: three private purposes, raw/chunk/checkpoint persistence, restart/dedupe, real verifier/filesystem restore, source acceptance and bounded cleanup retaining the tail pulse. Isolated plaintext transport does not prove production TLS/ACLs. |
| All five raw legacy tables | Coordinator actual PG source frames to production processor/real protected ClickHouse to independent file restore:8 rows/9 frames,18 replay visits; source/restore hashes match. Previously accepted manifests verified without republishing or changing acceptance. Direct hook is not Kafka transport. |
| Protected reader SQL | Actual ClickHouse audit/delivery acceptance: physical source filtering, fanout/cursors, original raw numeric bytes, archive generation lineage, stale proof and reader INSERT denial. |
| 64-bit precision | Actual CH RED rounded9007199254740993 to9007199254740992. Explicit quoted64-bit output GREEN for positions/offsets. Raw audit JSON remains a string across RPC. |
| Private HTTPS | Deployment6/6 real loopback mTLS checks using production Node clients/validators/handler: certificate/CA/hostname denial, signed scope/fixed paths, exact offsets, same-lease ack-loss probing, uncertainty and replay/coverage. Source/receiver/store state is synthetic. |
| Native Rust | Audit: five-crate check and68 runtime passes. Provider: fresh common/analytics binaries,23 distinct passes including two TEMP-PG tests. Tools:8 including three actual PG fixtures. Overlapping subsets do not prove deployed receiver effects. |
| Event units | Official refreshed event suite118/118 passed. All six historical Kafka/ClickHouse regressions passed in a new owned stack;47 evidence files and six PASS summaries independently hash-verified, and exact-owned cleanup completed. |
| Deployment | Renderer/private topology, actual Compose/Caddy parser and private-path denial, mockSSH passed. Coordinator final combined deployment suite37/37 passed after the retired-worker guard. The earlier Git Bash timeout passed isolated rerun without an implementation change. Final Ops-route removal passed13/13 focused renderer/private/real-Caddy/document checks; company paths404 on Ops before upstream while company routes remain200. No remote/application startup implied. |
| Release images | Rust image `sha256:e787e65bff9b39f7b6a7f89f5533a6d94c47cd7c67f6278c092729dc9fab0542` built successfully;25 runtime executables/libraries verified, old worker absent, maintenance rejects missing source binding. Node image `sha256:1585d2cc2f42e428f54e78239f9608fea5e49c4ab20a6c2cc35965f1f506343e` is nonroot and its private worker/query/CLI syntax and precision setting passed artifact checks. Neither check starts the full application. |
| Documents/worktrees | Current HTML/mirrors links/IDs/frozen hash passed. Seven branches verified; tracked diff checks returned0. |

## Review findings and corrections

- RSEC-1: first complete broker ownership tuple allowed on DELIVERED; terminal outcome and later ownership stay immutable. Actual SQL/signed Rust regressions cover migration and execute-before-own ordering.
- RSEC-2: trusted database/schema constrain audit rows and count; actual CH excludes another physical source sharing a company scope.
- RSEC-3: forward0125 denies new/pending/complete lossy legacy export before its shortcut; CLI OUTBOX-only. Actual PG8 and Node4 preserve existing stored history and canonical company export. Coordinator inspected the reviewer-authored correction.
- Actual CH error115 established HTTP placement of wait_end_of_query; array filters use bound JSON strings with typed extraction.
- Encrypted pulses and bounded slot refresh solve idle capture. Current-generation capture cannot delete uncaptured older-generation frames.
- Replay uses absolute source leases and preserves original event/retry identity. Raw JSON and newly created microsecond timestamps stay stable across languages/storage.
- Final scoped independent review has no remaining confirmed executable P0/P1/P2. Environment drift/grant filename corrected; evidence limits remain explicit.

## Architecture rulings

1. Exact existing CDC publication boundary; checked private discrimination and separate purpose topics/identities. Company inbox/reporting remains independent.
2. Source retains final authorization, destination secrets and business credentials. Shared workers have no company DSN and accept references, never arbitrary execution URLs.
3. Initial archive coverage is durable/revocable; live/destructive evidence is short-lived and current-generation-bound. Reviewed older archive lineage stays readable.
4. Broker ownership differs from receiver success. Unsettled executable source payload remains until settled; no generic archive restore authority inferred.
5. Compact migration/capture evidence is operational state with bounded compaction. Business state, receipts and atomic handoff remain necessary.

## Release gates

Source-owned export, pending reconciliation and capture precede accepted retirement. Accept real signing-key references, legacy uncertain outcomes, authoritative Finance receiver state, live ACL/certificates, production raw restore and current identity/grants per source. No age-only deletion, competing poller, automatic role expansion or inferred receiver success.

Complete browser/application/receiver/HA/off-host production acceptance is NOT DEMONSTRATED by local suites. Post-retirement rollback needs retained prior release artifacts, verified raw backups and reviewed source authority; simply restarting the old poller is unsafe.

Reports: `2026-10-19-retirement-{foundation,source,audit-application,infrastructure,tools,providers,deployment}-report.md`, `2026-10-19-retirement-final-review.md`, and dedicated `2026-10-19-retirement-release-summary.md`. The frozen baseline remains unchanged; current HTML/mirrors describe implementation and relationships.

## Final local closure

All eight local implementation tasks are complete. Final release build exited0; its optimized Cargo build took63m15 and retained nonblocking pre-existing leave-helper/tenant-import warnings. Complete Liquibase fresh/repeat masters exited0; prior-loan-checksum simulation was deliberately skipped in this focused rehearsal. The first PowerShell outer redirection formatted normal Liquibase stderr as an error record; separate native process capture reran successfully without source changes.

All held and regression fixtures were released by exact container identity after their owners finished. The evidence index independently verifies47 synthetic files/1,327,539bytes and six PASS scenarios; raw restore artifacts remain available locally. There are no automatic commits or live rollout/data changes.
