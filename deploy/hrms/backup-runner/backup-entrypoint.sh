#!/usr/bin/env bash
set -euo pipefail

if [[ "$#" -gt 0 ]]; then
  exec "$@"
fi

mkdir -p /backup/work /backup/rclone /run/backup-runner /var/log

BACKUP_CRON="${BACKUP_CRON:-0 2 * * *}"
BACKUP_TIMEZONE="${BACKUP_TIMEZONE:-Asia/Kolkata}"
BACKUP_RUN_ON_STARTUP="${BACKUP_RUN_ON_STARTUP:-false}"

if [[ -f "/usr/share/zoneinfo/${BACKUP_TIMEZONE}" ]]; then
  cp "/usr/share/zoneinfo/${BACKUP_TIMEZONE}" /etc/localtime
  echo "${BACKUP_TIMEZONE}" > /etc/timezone
else
  echo "WARN: timezone '${BACKUP_TIMEZONE}' not found; using container default timezone" >&2
fi

export -p > /run/backup-runner/container.env
chmod 600 /run/backup-runner/container.env

cat > /etc/crontabs/root <<EOF
SHELL=/bin/bash
PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
${BACKUP_CRON} . /run/backup-runner/container.env; /usr/local/bin/backup-now.sh >> /var/log/backup-runner.log 2>&1
EOF

echo "Backup runner scheduled with cron: ${BACKUP_CRON}"

if [[ "${BACKUP_RUN_ON_STARTUP}" == "true" ]]; then
  echo "Running startup backup because BACKUP_RUN_ON_STARTUP=true"
  /usr/local/bin/backup-now.sh
fi

exec crond -f -l 8
