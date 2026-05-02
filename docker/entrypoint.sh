#!/bin/bash
set -e

# Wait for PostgreSQL to be ready
wait_for_postgres() {
    echo "Waiting for PostgreSQL at ${HOST}:${PORT}..."
    until pg_isready -h "${HOST}" -p "${PORT}" -U "${USER}" > /dev/null 2>&1; do
        sleep 2
    done
    echo "PostgreSQL is ready."
}

# Generate odoo.conf from environment variables
# $1: "stdout" — no logfile (for init/update), anything else — log to file (for server)
generate_config() {
    mkdir -p /etc/odoo /var/lib/odoo/sessions
    mkdir -p /var/log/odoo || true

    if [ "${1}" = "stdout" ]; then
        LOGFILE_LINE=""
    else
        LOGFILE_LINE="logfile = /var/log/odoo/odoo.log"
    fi

    cat > /etc/odoo/odoo.conf <<EOF
[options]
db_host = ${HOST}
db_port = ${PORT}
db_user = ${USER}
db_password = ${PASSWORD}
db_name = ${DB_NAME}

admin_passwd = ${ADMIN_PASSWORD:-admin}

addons_path = /usr/lib/python3/dist-packages/odoo/addons,/mnt/extra-addons
data_dir = /var/lib/odoo

http_port = 8069
http_interface = 0.0.0.0
proxy_mode = True

list_db = False
dbfilter = ^${DB_NAME}$

log_level = ${LOG_LEVEL:-info}
${LOGFILE_LINE}

workers = ${WORKERS:-2}
max_cron_threads = 1

limit_memory_hard = 4294967296
limit_memory_soft = 3758096384
limit_time_cpu = 600
limit_time_real = 1200
EOF
}

case "$1" in
    odoo)
        wait_for_postgres
        generate_config file
        echo "Starting Odoo server..."
        exec odoo -c /etc/odoo/odoo.conf
        ;;
    init)
        wait_for_postgres
        generate_config stdout
        echo "Initializing database ${DB_NAME}..."
        exec odoo -c /etc/odoo/odoo.conf \
            -d "${DB_NAME}" \
            -i project_management \
            --load-language=ru_RU \
            --without-demo=all \
            --stop-after-init
        ;;
    init-demo)
        wait_for_postgres
        generate_config stdout
        echo "Initializing database ${DB_NAME} with demo data..."
        exec odoo -c /etc/odoo/odoo.conf \
            -d "${DB_NAME}" \
            -i project_management \
            --load-language=ru_RU \
            --stop-after-init
        ;;
    update)
        wait_for_postgres
        generate_config stdout
        echo "Updating module project_management..."
        exec odoo -c /etc/odoo/odoo.conf \
            -d "${DB_NAME}" \
            -u project_management \
            --stop-after-init
        ;;
    shell)
        wait_for_postgres
        generate_config stdout
        echo "Starting Odoo shell..."
        exec odoo shell -c /etc/odoo/odoo.conf -d "${DB_NAME}"
        ;;
    health)
        curl -sf http://localhost:8069/web/health || exit 1
        ;;
    *)
        exec "$@"
        ;;
esac
