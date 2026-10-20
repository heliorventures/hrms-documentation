# Infrastructure ownership implementation plan

**Spec:** `../specs/2026-10-19-infrastructure-ownership-design.md`.

**Goal:** implement the user's separation of concerns, deployment/Caddy and DRY/SOLID/cleanup requirements without disturbing existing data or unrelated work.

**Constraints:** current feature branch; no automatic commits, remote repository creation, live migration/deployment, destructive data move or retirement. Native commands; no RTK/Dart/Flutter. Broad implementation, reviews and focused validation approved by the user on 2026-10-19. Existing loan changes stay intact.

- [x] Read-only inventory of current ownership, main Compose, Dockerfile, deployment/image script and Caddy entry points.
- [x] Record proposed project ownership and verified cleanup/deployment gaps in the design.
- [x] Inventory exact owned files/callers and create a move/reference manifest. Define independently executable project commands and deployment interfaces before extraction.
- [x] Create `hrms-clickhouse`: versioned schema/grants, status/checksum/locking rules, independent migration tool, server/deployment configuration and tests. Update consumers/fixtures to its canonical schema resources.
- [x] Create `hrms-kafka`: separate broker/Connect deployment, topic/ACL/connector maintenance, fixed binding/private endpoint configuration and tests. Move PostgreSQL grants/publication prerequisites to `hrms-database`.
- [x] Separate platform installation from HRMS application rollout under `hrms-documentation/deploy`; wire organization service, bound company runtimes, consumers, archive and operators. Preserve existing storage/network names through an explicit reviewed compatibility path.
- [x] Update build/archive/deployment scripts and canonical Caddy fragments. Resolve organization/tenant/Auth/gateway routing and certificate/secret propagation. Validate configuration before any opt-in restart; no live execution in this task.
- [x] Trace DRY/SOLID violations and old consumers/planners/dependencies. Refactor shared mechanics, preserve distinct domain/security rules, migrate tests/callers, then remove proven obsolete code. Active Finance/notification workers retained with explicit cutover guards.
- [x] Execute approved focused checks and independent reviews; fix all actionable source findings. Detailed evidence/limitations are in the execution ledger.
- [x] Update architecture HTML, runbooks and a per-design-phase/per-cleanup-item completion matrix with exact unperformed production gates.
- [x] Final four application images built and inspected; Rust current-target export excludes an intentionally seeded retired cache executable and required runtime libraries resolve. Current two-company Kafka/Connect/TLS/ACL/source-schema capture and all six event lifecycle fixtures pass after approved Docker recovery.
- [ ] Full application fleet/browser/metadata-Connect-TLS/identity-backfill/reconciliation/failover/restore and legacy delivery/audit replacement and retirement acceptance remain separate gates.
