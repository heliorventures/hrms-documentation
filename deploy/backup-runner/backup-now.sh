#!/usr/bin/env bash
set -euo pipefail

log() {
  printf '[%s] %s\n' "$(date -Iseconds)" "$*"
}

fail() {
  log "ERROR: $*" >&2
  exit 1
}

bool_enabled() {
  case "${1:-}" in
    true|TRUE|1|yes|YES|y|Y) return 0 ;;
    *) return 1 ;;
  esac
}

require_env() {
  local key="$1"
  if [[ -z "${!key:-}" ]]; then
    fail "${key} is required"
  fi
}

safe_path_part() {
  printf '%s' "$1" | tr -c 'A-Za-z0-9._-/' '-'
}

write_rclone_config() {
  require_env BACKUP_BUCKET
  require_env BACKUP_S3_ACCESS_KEY_ID
  require_env BACKUP_S3_SECRET_ACCESS_KEY

  local provider="${BACKUP_S3_PROVIDER:-Cloudflare}"
  local region="${BACKUP_S3_REGION:-auto}"

  mkdir -p /backup/rclone
  cat > /backup/rclone/rclone.conf <<EOF
[backup]
type = s3
provider = ${provider}
access_key_id = ${BACKUP_S3_ACCESS_KEY_ID}
secret_access_key = ${BACKUP_S3_SECRET_ACCESS_KEY}
region = ${region}
EOF

  if [[ -n "${BACKUP_S3_ENDPOINT:-}" ]]; then
    printf 'endpoint = %s\n' "${BACKUP_S3_ENDPOINT}" >> /backup/rclone/rclone.conf
  fi

  chmod 600 /backup/rclone/rclone.conf
  export RCLONE_CONFIG=/backup/rclone/rclone.conf
}

remote_root() {
  local prefix="${BACKUP_PREFIX:-helior/hrms}"
  prefix="${prefix#/}"
  prefix="${prefix%/}"
  printf 'backup:%s/%s' "${BACKUP_BUCKET}" "$(safe_path_part "$prefix")"
}

upload_file() {
  local local_file="$1"
  local remote_file="$2"
  log "Uploading ${local_file} -> ${remote_file}"
  rclone copyto "${local_file}" "${remote_file}" --s3-no-check-bucket --transfers 1 --checkers 4
}

run_database_backup() {
  if ! bool_enabled "${BACKUP_DATABASE:-true}"; then
    log "Database backup disabled"
    return
  fi

  require_env POSTGRES_HOST
  require_env POSTGRES_PORT
  require_env POSTGRES_DB
  require_env POSTGRES_USER
  require_env POSTGRES_PASSWORD

  local stamp day_dir db_safe local_file remote_file
  stamp="$(date +%Y%m%d-%H%M%S)"
  day_dir="$(date +%Y/%m/%d)"
  db_safe="$(safe_path_part "${POSTGRES_DB}")"
  local_file="/backup/work/${db_safe}-${stamp}.dump"
  remote_file="$(remote_root)/database/${day_dir}/${db_safe}-${stamp}.dump"

  log "Starting PostgreSQL backup for ${POSTGRES_DB}"
  PGPASSWORD="${POSTGRES_PASSWORD}" pg_dump \
    -h "${POSTGRES_HOST}" \
    -p "${POSTGRES_PORT}" \
    -U "${POSTGRES_USER}" \
    -d "${POSTGRES_DB}" \
    -F c \
    --no-owner \
    --no-privileges \
    -f "${local_file}"

  gzip -f "${local_file}"
  upload_file "${local_file}.gz" "${remote_file}.gz"
  rm -f "${local_file}.gz"
  log "PostgreSQL backup complete"
}

run_image_archive_backup() {
  if ! bool_enabled "${BACKUP_IMAGE_ARCHIVES:-true}"; then
    log "Image archive backup disabled"
    return
  fi

  local image_dir="${BACKUP_IMAGE_ARCHIVE_DIR:-/backup/images}"
  if [[ ! -d "${image_dir}" ]]; then
    log "Image archive directory not found: ${image_dir}"
    return
  fi

  log "Uploading Docker image archives from ${image_dir}"
  find "${image_dir}" -type f -name 'kabipay-*.tar' -print0 | while IFS= read -r -d '' file; do
    local relative remote_file
    relative="${file#${image_dir}/}"
    remote_file="$(remote_root)/image-archives/$(safe_path_part "${relative}")"
    upload_file "${file}" "${remote_file}"
  done

  if bool_enabled "${BACKUP_PRUNE_LOCAL_IMAGE_ARCHIVES:-false}"; then
    local prune_days="${BACKUP_LOCAL_IMAGE_RETENTION_DAYS:-14}"
    log "Pruning local image archives older than ${prune_days} day(s)"
    find "${image_dir}" -type f -name 'kabipay-*.tar' -mtime "+${prune_days}" -delete
  fi

  log "Docker image archive backup complete"
}

run_retention() {
  local root db_days image_days
  root="$(remote_root)"
  db_days="${BACKUP_DATABASE_RETENTION_DAYS:-30}"
  image_days="${BACKUP_IMAGE_RETENTION_DAYS:-14}"

  if bool_enabled "${BACKUP_REMOTE_RETENTION_ENABLED:-true}"; then
    log "Applying remote database retention: ${db_days} day(s)"
    rclone delete "${root}/database" --min-age "${db_days}d" --s3-no-check-bucket || true
    rclone rmdirs "${root}/database" --leave-root --s3-no-check-bucket || true

    log "Applying remote image archive retention: ${image_days} day(s)"
    rclone delete "${root}/image-archives" --min-age "${image_days}d" --s3-no-check-bucket || true
    rclone rmdirs "${root}/image-archives" --leave-root --s3-no-check-bucket || true
  fi
}

main() {
  if ! bool_enabled "${BACKUP_ENABLED:-false}"; then
    log "Backups disabled because BACKUP_ENABLED is not true"
    exit 0
  fi

  mkdir -p /backup/work
  exec 9>/backup/work/backup.lock
  if ! flock -n 9; then
    log "Another backup is already running; skipping this run"
    exit 0
  fi

  write_rclone_config
  run_database_backup
  run_image_archive_backup
  run_retention
  log "Backup run complete"
}

main "$@"
