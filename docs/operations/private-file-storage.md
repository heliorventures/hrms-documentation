# Private local file storage

The production Compose deployment uses one persistent host directory for private local files:

| Scope | Path |
| --- | --- |
| VPS host | `/opt/apps/data/private-files` |
| `kabipay-subgraphs` container | `/var/lib/kabipay/private-files` |
| `kabipay-outbox-worker` container | `/var/lib/kabipay/private-files` |

Both containers receive the same `KABIPAY_LOCAL_FILE_ROOT` value and bind mount. This is required
because subgraphs write and read local fallback files while the worker retries durable physical
deletion. The Caddy and UI containers do not mount this directory, and no route serves it as a
static directory.

## Cleanup worker lifecycle

`kabipay-outbox-worker` is part of the default production Compose set. A normal deployment such
as `./scripts/deploy-on-vps.ps1 ... -Deploy` starts it; no optional Compose profile or deployment
switch is required. The worker shares the private-file bind mount above and processes durable
cleanup tombstones with retries.

After an object write, a metadata insertion failure creates an object-only tombstone. If the
tenant database is unavailable and that tombstone cannot be recorded either, the request fails
and the service logs only an opaque correlation ID and error class. This unavoidable condition
has no durable cleanup record; operators must reconcile the failed request using the correlation
ID without recording storage coordinates in logs.

## Permissions

The deployment script creates the host directory with mode `0700`. The current service image runs
as root. If the runtime image is changed to a non-root user, change ownership to that exact numeric
UID/GID before recreating containers; do not make the directory group/world writable.

Check the host permissions:

```bash
stat -c '%a %u:%g %n' /opt/apps/data/private-files
```

Expected mode: `700`.

## Backup and restore

The existing backup runner backs up PostgreSQL and Docker image archives only. It does not back up
private local files. Use an encrypted VPS/filesystem snapshot or a separate encrypted backup job
for `/opt/apps/data/private-files`.

Take the database and private-file backup from one coordinated recovery point. For a simple file
archive, stop write-producing application containers during the snapshot window, archive the
private directory without following symlinks, take the database backup, and restart the services.
Restore the matching database and private-file snapshot together. Never copy this directory into
the UI image, Caddy document root, a public bucket, or an unencrypted backup.

## Static and runtime verification

After deployment, confirm both containers resolve the same root and the host bind source:

```bash
cd /opt/apps
docker inspect kabipay-subgraphs --format '{{range .Mounts}}{{println .Source "->" .Destination}}{{end}}'
docker inspect kabipay-outbox-worker --format '{{range .Mounts}}{{println .Source "->" .Destination}}{{end}}'
docker compose exec kabipay-subgraphs sh -lc 'test "$KABIPAY_LOCAL_FILE_ROOT" = /var/lib/kabipay/private-files && test -d "$KABIPAY_LOCAL_FILE_ROOT" && test -w "$KABIPAY_LOCAL_FILE_ROOT"'
docker compose exec kabipay-outbox-worker sh -lc 'test "$KABIPAY_LOCAL_FILE_ROOT" = /var/lib/kabipay/private-files && test -d "$KABIPAY_LOCAL_FILE_ROOT" && test -w "$KABIPAY_LOCAL_FILE_ROOT"'
```

Both `docker inspect` commands must show `/opt/apps/data/private-files` mapped to
`/var/lib/kabipay/private-files`. Do not print filenames or file contents into deployment logs.
