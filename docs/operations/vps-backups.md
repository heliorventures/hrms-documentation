# VPS backup runner

This runbook configures scheduled offsite backups from the VPS.

The backup runner is separate from tenant setup and separate from normal application deployment.

## What is backed up

The backup runner can upload:

1. PostgreSQL database dump.
2. Docker image tar archives from `/opt/apps/images`.

It uploads to an S3-compatible bucket. Cloudflare R2 is the recommended target.

Private local-fallback files under `/opt/apps/data/private-files` are **not** included by the
current backup runner. See [Private file storage](private-file-storage.md) before enabling local
fallback in production; database and private-file backups must come from the same recovery point.

## Default policy

| Setting | Default |
| --- | --- |
| Schedule | Daily at 2:00 AM India time |
| Database backup retention | 30 days |
| Docker image archive retention | 14 days |
| Local image archive deletion | Disabled |

## Sync backup runner files to VPS

From your local machine:

```powershell
Set-Location D:\work\heliorventures\hrms-documentation

.\scripts\install-backup-runner.ps1 `
  -VpsHost 159.198.70.19 `
  -VpsUser deploy `
  -SyncCompose
```

Use `-SyncCompose` when the VPS compose file does not yet include the `backup-runner` service.

## Configure VPS environment

SSH into the VPS:

```powershell
ssh deploy@159.198.70.19
```

Edit:

```bash
nano /opt/apps/.env
```

Add or update:

```env
BACKUP_ENABLED=true
BACKUP_CRON=0 2 * * *
BACKUP_TIMEZONE=Asia/Kolkata
BACKUP_RUN_ON_STARTUP=false

BACKUP_DATABASE=true
BACKUP_IMAGE_ARCHIVES=true

BACKUP_BUCKET=your-bucket-name
BACKUP_PREFIX=helior/hrms
BACKUP_S3_PROVIDER=Cloudflare
BACKUP_S3_ENDPOINT=https://<cloudflare-account-id>.r2.cloudflarestorage.com
BACKUP_S3_REGION=auto
BACKUP_S3_ACCESS_KEY_ID=<access-key>
BACKUP_S3_SECRET_ACCESS_KEY=<secret-key>

BACKUP_REMOTE_RETENTION_ENABLED=true
BACKUP_DATABASE_RETENTION_DAYS=30
BACKUP_IMAGE_RETENTION_DAYS=14
BACKUP_PRUNE_LOCAL_IMAGE_ARCHIVES=false
BACKUP_LOCAL_IMAGE_RETENTION_DAYS=14
```

For AWS S3, use:

```env
BACKUP_S3_PROVIDER=AWS
BACKUP_S3_ENDPOINT=
BACKUP_S3_REGION=ap-south-1
```

## Schedule examples

Daily at 2:00 AM:

```env
BACKUP_CRON=0 2 * * *
```

Twice daily at 2:00 AM and 2:00 PM:

```env
BACKUP_CRON=0 2,14 * * *
```

Three times daily at 2:00 AM, 10:00 AM, and 6:00 PM:

```env
BACKUP_CRON=0 2,10,18 * * *
```

## Start backup runner

On the VPS:

```bash
cd /opt/apps
docker compose --profile backup build backup-runner
docker compose --profile backup up -d backup-runner
```

Check logs:

```bash
docker logs -f backup-runner
```

## Run a backup immediately

Use this after first setup to verify bucket credentials:

```bash
cd /opt/apps
docker compose --profile backup run --rm -e BACKUP_ENABLED=true backup-runner /usr/local/bin/backup-now.sh
```

Expected result:

- One `.dump.gz` file under `<bucket>/<prefix>/database/YYYY/MM/DD/`.
- Docker image `.tar` files under `<bucket>/<prefix>/image-archives/`.

## Stop backup runner

```bash
cd /opt/apps
docker compose --profile backup stop backup-runner
```

## Restore database backup

Download the required `.dump.gz` from the bucket, then restore using `pg_restore` against the target database.

Do not restore into production without a planned maintenance window and a verified rollback path.

Typical restore shape:

```bash
gunzip -c helior-YYYYMMDD-HHMMSS.dump.gz > helior.dump
PGPASSWORD="$POSTGRES_PASSWORD" pg_restore \
  -h postgres \
  -p 5432 \
  -U "$POSTGRES_USER" \
  -d "$POSTGRES_DB" \
  --clean \
  --if-exists \
  helior.dump
```

## Operational notes

- The backup runner uses a lock file, so overlapping cron runs skip instead of running concurrently.
- The database backup uses `pg_dump -F c`, compressed afterward with gzip.
- Bucket credentials live only in `/opt/apps/.env`; do not commit real keys.
- Keep `BACKUP_PRUNE_LOCAL_IMAGE_ARCHIVES=false` until offsite backup restore has been verified.
