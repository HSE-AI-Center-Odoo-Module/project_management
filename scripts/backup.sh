#!/bin/bash
# Odoo PostgreSQL backup script
# Saves gzipped dump to /backups, keeps last 10, optionally uploads to MinIO.
# Usage: ./backup.sh
# Cron:  0 2 * * * /opt/project_management/scripts/backup.sh >> /var/log/odoo-backup.log 2>&1

set -e

# ── Config (override via environment or edit here) ─────────────────────────
BACKUP_DIR="${BACKUP_DIR:-/opt/backups/odoo}"
KEEP_LAST="${KEEP_LAST:-10}"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="${BACKUP_DIR}/backup_${TIMESTAMP}.sql.gz"

# Docker compose project (directory where docker-compose.prod.yml lives)
COMPOSE_DIR="${COMPOSE_DIR:-/opt/project_management}"
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.prod.yml}"

# MinIO / S3 settings (leave MINIO_UPLOAD=false to skip)
MINIO_UPLOAD="${MINIO_UPLOAD:-false}"
MINIO_ALIAS="${MINIO_ALIAS:-local}"          # mc alias name
MINIO_BUCKET="${MINIO_BUCKET:-odoo-backups}"
# ───────────────────────────────────────────────────────────────────────────

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting backup..."

# Create backup directory
mkdir -p "${BACKUP_DIR}"

# Load env vars from .env.prod if present
if [ -f "${COMPOSE_DIR}/.env.prod" ]; then
    set -a
    source "${COMPOSE_DIR}/.env.prod"
    set +a
fi

# Run pg_dump inside the db container
docker compose \
    -f "${COMPOSE_DIR}/${COMPOSE_FILE}" \
    exec -T db \
    pg_dump -U "${DB_USER}" "${DB_NAME}" \
    | gzip > "${BACKUP_FILE}"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Backup saved: ${BACKUP_FILE} ($(du -sh "${BACKUP_FILE}" | cut -f1))"

# Upload to MinIO if enabled
if [ "${MINIO_UPLOAD}" = "true" ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Uploading to MinIO bucket '${MINIO_BUCKET}'..."
    mc cp "${BACKUP_FILE}" "${MINIO_ALIAS}/${MINIO_BUCKET}/"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Upload complete."
fi

# Rotate: keep only last N local backups
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Rotating backups, keeping last ${KEEP_LAST}..."
ls -t "${BACKUP_DIR}"/backup_*.sql.gz 2>/dev/null \
    | tail -n +$((KEEP_LAST + 1)) \
    | xargs -r rm --
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Backup complete."
