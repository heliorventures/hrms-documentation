# Infrastructure deployment review — second pass

Review date: 2026-10-19. Scope: renderer, HRMS/platform release and install scripts, backup Compose, and organization infrastructure/phase audit. Read-only review; no commands/checks were run and no runtime claims are made.

## Findings

### High — Organization tenants can share a private-files bind path

`hrms-documentation/scripts/deploy/render.mjs:26-34` checks uniqueness for company IDs, slugs and public hosts, but only validates `privateFilesPath` syntax. It never rejects a path already assigned to another company. At `:87-97`, that value becomes a writable bind mount (`readOnly=false`) for every service in the corresponding company fleet. A manifest can therefore give two companies the same host directory and cause both fleets to read/write the same private documents. Path spellings with a trailing slash are normalized by `safePath` (`:14`) but uniqueness is not checked after normalization either.

**Root cause:** the manifest validator treats company file roots as individually valid paths without enforcing one-to-one tenant ownership. Normalize paths first and reject duplicate normalized roots before creating services. The infrastructure runbook says to map each existing company directory explicitly (`docs/deployment/organization-infrastructure.md:60`), but the renderer does not enforce that boundary.

### Low — Worker and tenant selector switches are accepted but have no effect

`build-save-upload-images.ps1` exposes `TenantId` and `WithWorker` (`:66-73`) and forwards them during `DeployAfterUpload` (`:333-349`). `deploy-on-vps.ps1` also declares both (`:15-17`) but never reads either. Rendered Compose includes worker services and release starts every generated service (`deploy/render.mjs:99,123-128`; `deploy/release.sh:31-32`), so `WithWorker` cannot control worker inclusion; tenant identity comes from the manifest, so `TenantId` cannot select a tenant. Operators can supply either switch believing it changed the rollout when it did not.

**Root cause:** obsolete CLI controls survived after the manifest and generated service inventory became authoritative. Remove them or fail explicitly with a migration message; do not silently accept ignored deployment inputs.

## Scope assessment

The reviewed source preserves the intended ownership split in the inspected flows: generated HRMS Compose is application-only; the platform helper uses an explicit platform env file and checks root mounts/Caddy volumes; the backup runner has its own Compose project and env file; and organization mode renders bound per-company services while omitting the legacy global delivery worker. The phase audit accurately keeps live rollout, current final topology, broad retirement and business/outbox records open. These are source observations only, not live deployment proof.

## Closure recheck — 2026-10-19

The two findings above are closed in the current source:

- `render.mjs:14,27,33-36` normalizes company paths, limits them to approved company-data trees and rejects equal or ancestor/descendant overlaps. The renderer emits the paths into `private-files.txt`; `release.sh:29-34` requires each path to exist and its `realpath -e` result to match before `up`, preventing deployment through symlink aliases.
- `TenantId` and `WithWorker` are absent from both deployment-script parameter lists and from forwarded arguments. Organization and legacy worker services are part of the rendered topology and are started with the generated services; treat worker installation/startup as mandatory for that deployment mode, not an optional switch.

The root reports renderer path-negative coverage, PowerShell mocked release coverage, and two Caddy parse checks passing. I did not run those checks. Final Docker image and topology proof remain blocked by Engine HTTP500; Kafka final topology and production rollout remain pending per the phase audit.
