# Organization production review disposition

19 October 2026. The user requested re-evaluation of the preceding review and fixes for confirmed engineering issues. They confirmed that the production ops registry serves one shared fleet/VPS. Changes remain local and uncommitted; no live database query, migration, rollout, identity backfill, key change, history deletion or remote repository creation was performed.

| Review comment | Re-evaluation and action |
| --- | --- |
| A partial bound-runtime cutover could omit live tenants | Confirmed operational risk. Rendered releases now include exact company bindings and artifact hashes. A separate read-only ops operator query checks every ACTIVE/SUSPENDED tenant and current subdomain; the release requires a matching fifteen-minute inventory receipt before image loading/startup. Tenant provisioning and registry edits must stay frozen through the reviewed cutover. |
| 0125 holds locks while backfilling legacy state | Confirmed. Replaced two correlated audit queries per survey with one windowed pass, preserving values/tie-breaks. Transaction-local settings limit each lock wait to five seconds and each statement to sixty seconds; these are not a total transaction deadline. Necessary locks remain; representative data rehearsal and a maintenance window are still required. |
| 0115 rollback may refuse after organization traffic | Intentional safety boundary, not a missing rollback fix. The existing guard checks durable receipts/outbox/bootstrap/installed grants before dropping anything. Keep compatible schema or use accepted forward recovery/restore after enablement. |
| Dirty branches and new infrastructure repositories lack release provenance | Confirmed handoff work, not a runtime defect. The user owns manual commits, review, publishing and artifact versioning. No automatic commit or remote creation. |
| Original HTML still says decisions precede implementation | Corrected in both visible-text mirrors. It now distinguishes source implementation, policy sign-off and optional extensions from live acceptance. The frozen recorded baseline is unchanged. |
| Browser, existing-data upgrade, real grants/TLS/ACLs/backfill/restore remain unproven | Production acceptance work. Local unit/synthetic checks cannot attest an existing tenant's data, certificates, key custody, installed roles or business workflow results. |

## Verification

Final local verification completed on 20 October 2026: 5 source-upgrade/registry PostgreSQL cases, 42 complete preparation/retirement PostgreSQL cases, 43 deployment/document regressions, 11 default database tests and 4 retirement contract tests passed. The PowerShell deployment-wrapper regression also passed with remote actions mocked. A bounded independent source review found no additional confirmed source issue in the reviewed files. No full service/UI build or real deployment was performed.

Current results and any remaining local checks are recorded in [the implementation plan](../superpowers/plans/2026-10-19-organization-production-hardening.md). The migration regression executes the actual preparation prefix in fresh loopback PostgreSQL, including contention/atomic rollback and EXPLAIN ANALYZE scan counts. The existing full private-retirement SQL fixture separately executes complete 0124/0125 preparation and guarded retirement. The operator registry SQL is exercised in an actual read-only PostgreSQL transaction; its production libpq service/certificate connection is not invoked locally.

Inventory/native release tests use synthetic registry rows and temporary rendered files; Docker and SSH/SCP are mocked for release side effects. They prove gate behavior and rejection before startup, not actual application service readiness. The inventory receipt is trusted operator evidence against deployment mistakes, not a cryptographic authorization credential. Current runtime authorization remains independent.

## Required live release evidence

1. Review and version the complete application/infrastructure release, preserve existing root storage/network/Caddy identities and inventory every legacy worker.
2. Back up the existing tenant/ops data and archive keys; rehearse upgrade, measured lock duration, forward recovery and restore on a representative protected copy.
3. Accept actual identity/account mappings, company roles, payroll/sensitive-field policy, historical ranges, retention/freshness and recovery ownership.
4. Provision production tenant-bound runtimes, private TLS/mTLS, database/HBA/CDC/Kafka/ClickHouse grants and key custody; verify negative isolation cases.
5. Freeze provisioning/registry changes, render the exact release, generate fresh [operator inventory evidence](../../../hrms-database/provisioning/organization/README.md#shared-fleet-cutover-inventory), then follow the [ordered cutover](organization-infrastructure.md#existing-vps-cutover-separate-operator-steps).
6. Record actual company login/refresh, HR/manager/owner browser workflows, revocation, payroll crash/recovery, capture/reconciliation and off-host restore before enabling wider company access or any opt-in retirement.
