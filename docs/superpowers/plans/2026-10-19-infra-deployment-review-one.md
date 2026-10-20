# Independent bounded deployment review — 2026-10-19

Scope: the compact infrastructure evidence summary, renderer, SSH helper, release/platform shell entry points, PowerShell deployment entry points, platform Compose, root Caddy example, environment contract, Auth plane module and targeted gateway subgraph selection. Read-only source review; no tests, network requests, Docker operations or implementation edits performed. This report is the only authored artifact.

## Findings

### P1 — Organization cutover guard misses the renderer's own legacy worker

`scripts/deploy/release.sh:14-16` inspects only the literal container name `kabipay-outbox-worker`. `scripts/deploy/render.mjs:66` creates that Compose service without a `container_name`, using project `apps`; its normal generated container name is `apps-kabipay-outbox-worker-1`. Organization rendering removes the service (`render.mjs:78`), but application startup uses `compose up` without orphan removal (`release.sh:32`). Consequently a running legacy worker created by this renderer bypasses the guard and remains running alongside new company workers, risking concurrent delivery across the cutover. Inspection failure is also treated as absence.

Required correction: enumerate legacy delivery containers by exact Compose project/service labels, while covering established explicitly named legacy containers. Fail closed if inspection cannot establish the relevant state. Refuse organization rollout until operator-reviewed delivery cutover; do not solve this by indiscriminate orphan removal on the shared `apps` project.

### P1 — Company delivery services have no external egress path

Company Auth, tenant services and source outbox workers receive only the company network plus `sources` and `metadata` (`render.mjs:85,89,92,99`). The company network is internal, and platform provisioning creates both shared private networks with `--internal` (`scripts/deploy/platform.sh:36-38`). These services therefore have no ordinary external routing path. The environment contract explicitly requires existing Finance and notification delivery configuration, but the reviewed deployment contains no egress proxy or other external delivery path. External SMTP/payment/Finance/notification HTTP calls cannot succeed with this topology.

Required correction: define an explicit egress path with the intended trust boundary for roles that need external business integrations, or provision and configure a documented proxy. Verify final container routing and representative approved delivery before production cutover. This is a source-derived topology finding, not a claim that a final container experiment was run.

## Positive bounded observations

- Renderer URLs and upstream names derive from validated company identifiers and fixed service maps; no arbitrary endpoint input exists in this manifest interface.
- Organization global Auth and gateway use explicit ops deployment planes; the reviewed Auth selector excludes client routes for ops. Company gateway supplies the complete fixed tenant map.
- Public Caddy routes explicitly deny internal and organization identity paths; private source proxies publish no host ports. Application authorization on private endpoints still requires its separate service-level acceptance.
- Private key directories mount into matching Auth/service roles, while shared public verification keys remain separate. Bind mounts disable automatic host-path creation.
- SSH host/user/path validation excludes shell metacharacters. Generated release artifacts form the upload list; environment files and secret directories are not part of that list.
- Platform maintenance preserves explicit PostgreSQL/Mongo paths, external shared network ownership and Caddy volume identity; it validates Caddy before platform recreation. It does not automatically reload root Caddy during application release.

## Evidence and production boundaries

The parent reports native Caddy checks, renderer tests and mocked PowerShell release checks passing. Those results were not rerun in this review. Parent reports final Docker image/topology proof blocked by Engine HTTP 500 and awaiting coordinated approval. Container-running polling is explicitly weaker than application readiness or successful cutover.

Final image execution, final network topology/egress, private CA handshakes, final Kafka ACL/topology and CDC lifecycle, existing-data baseline/backfill, actual tenant cutover, browser acceptance, failover/restore and retirement remain distinct gates. No production rollout, retirement or rollback rehearsal was demonstrated by this review. Preserve prior release manifests/configuration and reviewed data compatibility when planning rollback; the reviewed entry points do not implement an automatic transactional rollback.

## Follow-up source review — supersedes original finding status

The original two P1 causes are **closed in source**: release now enumerates running workers using exact Compose project/service labels as well as the established explicit name; renderer adds a separate egress-capable network for each company and attaches Auth, business services and outbox. Central organization services remain on private networks. Final Docker routing/delivery evidence remains outstanding; no runtime closure is claimed.

Company private-file paths now normalize, reject overlap/containment, remain under approved application/company data roots, and undergo existing-directory plus canonical `realpath -e` checks before startup. No additional actionable path issue was found in this bounded follow-up.

Additional scope: canonical database CDC provisioning SQL/wrapper/shared boundary guard and Kafka connector renderer/template. The actual shared guard is named `cdc-boundary-guard.sql`. Company IDs, generated roles and slots bind to canonical UUIDs; schema identifiers are constrained and SQL uses quoted psql values/identifiers or `format('%I',...)`. Wrapper transactions fail on errors; guard rejects unsafe preexisting role flags, memberships, other effective database CONNECT, ownership, unexpected table privileges and publications outside the expected table boundary. It requires operator remediation rather than broad privilege revocation.

### P1 — Existing publication filters and column lists are accepted

`hrms-database/provisioning/organization/cdc-source.template.sql`, existing-publication branch, checks publication action flags and exact relation membership/count but omits `pg_publication_rel.prqual` and `prattrs`. A publication with exactly the expected two relations and an existing row filter or column list passes. Such a publication can silently omit canonical events or required event fields from logical replication. Reject non-null row filters/column lists when adopting the canonical full-table publication. No SQL execution was performed by this reviewer.

### P2 — Effective column privileges bypass the CDC role boundary guard

`hrms-database/provisioning/organization/cdc-boundary-guard.sql` checks `has_table_privilege` only. PostgreSQL column grants do not imply table-level grants. An existing role can retain SELECT on columns in unrelated user tables, or INSERT/UPDATE/REFERENCES on source columns, and pass these checks. Include effective `has_any_column_privilege` checks for unrelated readable/mutable columns and canonical source mutation columns; preserve fail-closed operator remediation.

Both findings were sent immediately to the integration owner. Kafka connector schema substitutions are bounded identifier values and role/slot UUID derivation matches provisioning. No further concrete injection issue was found in the reviewed code. Parent-reported Auth/gateway/TLS results are external evidence, not tests rerun by this review. No Docker/runtime operations or implementation changes were performed.

## Final bounded source closure

The two CDC findings above are now **closed in source** following a fresh read of the shared boundary guard and both company/control publication templates:

- Both canonical publication adoption checks explicitly reject non-null `pg_publication_rel.prqual` or `prattrs`, preventing adoption of filtered rows or restricted column sets.
- The shared guard adds effective `has_any_column_privilege` checks for SELECT/INSERT/UPDATE/REFERENCES on unrelated user relations and INSERT/UPDATE/REFERENCES on canonical source relations. Existing table-level checks remain. Unsafe grants raise exceptions; no automatic broad revocation was introduced.
- Membership rejection now covers both `member=role_id` and `roleid=role_id`, excluding a CDC role receiving other roles or being assumable by members.

All four findings raised in this review are closed at source level. No additional actionable issue was found in this final bounded read. This is not a new runtime acceptance claim. Parent reports an isolated native PostgreSQL 17 guard experiment underway; its outcome was not available or rerun by this reviewer. Such evidence must remain distinguished from pinned PostgreSQL 16/Docker deployment proof and production validation.
