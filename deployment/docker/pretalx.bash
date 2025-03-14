#!/bin/bash

# Change to the project source directory
cd /pretalx/src || exit 1

# Define default environment variables for pretalx data directory and home
export PRETALX_DATA_DIR="${PRETALX_DATA_DIR:-/data}"
export HOME=/pretalx

# Define filesystem paths for logs, media, and static assets
export PRETALX_FILESYSTEM_LOGS="${PRETALX_FILESYSTEM_LOGS:-/data/logs}"
export PRETALX_FILESYSTEM_MEDIA="${PRETALX_FILESYSTEM_MEDIA:-/data/media}"
export PRETALX_FILESYSTEM_STATIC="${PRETALX_FILESYSTEM_STATIC:-/pretalx/src/static.dist}"

# Gunicorn server configurations (worker settings, logging, etc.)
export GUNICORN_WORKERS="${GUNICORN_WORKERS:-${WEB_CONCURRENCY:-$((2 * $(nproc)))}}"
export GUNICORN_MAX_REQUESTS="${GUNICORN_MAX_REQUESTS:-1200}"
export GUNICORN_MAX_REQUESTS_JITTER="${GUNICORN_MAX_REQUESTS_JITTER:-50}"
export GUNICORN_FORWARDED_ALLOW_IPS="${GUNICORN_FORWARDED_ALLOW_IPS:-127.0.0.1}"
export GUNICORN_RELOAD="${GUNICORN_RELOAD:-false}"
export GUNICORN_LOGLEVEL="${GUNICORN_LOGLEVEL:-info}"

# Automation settings for migration and rebuild
export AUTOMIGRATE="${AUTOMIGRATE:-yes}"
export AUTOREBUILD="${AUTOREBUILD:-yes}"

# Set reload argument for Gunicorn if enabled
RELOAD_ARGUMENT=""
if [ "$GUNICORN_RELOAD" = "true" ]; then
    RELOAD_ARGUMENT="--reload"
fi

# Ensure required directories exist
mkdir -p "$PRETALX_FILESYSTEM_LOGS" "$PRETALX_FILESYSTEM_MEDIA"

# Rebuild static assets if needed
if [ "$PRETALX_FILESYSTEM_STATIC" != "/pretalx/src/static.dist" ] && [ "$AUTOREBUILD" = "yes" ]; then
    mkdir -p "$PRETALX_FILESYSTEM_STATIC"
    flock --nonblock /pretalx/.lockfile python3 -m pretalx rebuild
fi

# Handle different script arguments
case "$1" in
    cron)
        exec python3 -m pretalx runperiodic
        ;;
    all)
        exec sudo -E /usr/bin/supervisord -n -c /etc/supervisord.conf
        ;;
    webworker)
        exec gunicorn pretalx.wsgi \
            --name pretalx \
            --workers "${GUNICORN_WORKERS}" \
            --max-requests "${GUNICORN_MAX_REQUESTS}" \
            --max-requests-jitter "${GUNICORN_MAX_REQUESTS_JITTER}" \
            --forwarded-allow-ips "${GUNICORN_FORWARDED_ALLOW_IPS}" \
            $RELOAD_ARGUMENT \
            --log-level="${GUNICORN_LOGLEVEL}" \
            --bind=0.0.0.0:80
        ;;
    devel)
        python3 -m pretalx rebuild
        export GUNICORN_LOGLEVEL=debug
        export GUNICORN_RELOAD=true
        exec sudo -E /usr/bin/supervisord -n -c /etc/supervisord.conf
        ;;
    taskworker)
        exec celery -A pretalx.celery_app worker -l info
        ;;
    shell)
        exec python3 -m pretalx shell
        ;;
    upgrade)
        python3 -m pretalx rebuild
        exec python3 -m pretalx regenerate_css
        ;;
    *)
        exec python3 -m pretalx "$@"
        ;;
esac
