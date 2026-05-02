#!/bin/bash
# Odoo PostgreSQL restore script
# Usage: ./restore.sh /path/to/backup_20240101_020000.sql.gz
# WARNING: This will DROP and recreate the database. All current data will be lost.

set -e

BACKUP_FILE="$1"
COMPOSE_DIR="${COMPOSE_DIR:-/opt/project_management}"
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.prod.yml}"

if [ -z "${BACKUP_FILE}" ]; then
    echo "Usage: $0 <backup_file.sql.gz>"
    echo ""
    echo "Available backups:"
    ls -lh "${BACKUP_DIR:-/opt/backups/odoo}"/backup_*.sql.gz 2>/dev/null || echo "  (none found)"
    exit 1
fi

if [ ! -f "${BACKUP_FILE}" ]; then
    echo "Error: backup file not found: ${BACKUP_FILE}"
    exit 1
fi

# Load env vars
if [ -f "${COMPOSE_DIR}/.env.prod" ]; then
    set -a
    source "${COMPOSE_DIR}/.env.prod"
    set +a
fi

echo "============================================================"
echo "  WARNING: This will DROP database '${DB_NAME}' and restore"
echo "  from: ${BACKUP_FILE}"
echo "============================================================"
read -p "Are you sure? Type YES to continue: " CONFIRM
if [ "${CONFIRM}" != "YES" ]; then
    echo "Aborted."
    exit 0
fi

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Stopping Odoo..."
docker compose -f "${COMPOSE_DIR}/${COMPOSE_FILE}" stop odoo

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Dropping database ${DB_NAME}..."
docker compose -f "${COMPOSE_DIR}/${COMPOSE_FILE}" exec -T db \
    psql -U "${DB_USER}" -c "DROP DATABASE IF EXISTS \"${DB_NAME}\";"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Creating empty database ${DB_NAME}..."
docker compose -f "${COMPOSE_DIR}/${COMPOSE_FILE}" exec -T db \
    psql -U "${DB_USER}" -c "CREATE DATABASE \"${DB_NAME}\" OWNER \"${DB_USER}\";"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Restoring from ${BACKUP_FILE}..."
gunzip -c "${BACKUP_FILE}" | docker compose \
    -f "${COMPOSE_DIR}/${COMPOSE_FILE}" \
    exec -T db \
    psql -U "${DB_USER}" "${DB_NAME}"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting Odoo..."
docker compose -f "${COMPOSE_DIR}/${COMPOSE_FILE}" start odoo

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Restore complete."
