#!/bin/bash
cd /eventyay/src || exit 1
export EVENTYAY_DATA_DIR="${EVENTYAY_DATA_DIR:-/data}"
export HOME=/eventyay

EVENTYAY_FILESYSTEM_LOGS="${EVENTYAY_FILESYSTEM_LOGS:-/data/logs}"
EVENTYAY_FILESYSTEM_MEDIA="${EVENTYAY_FILESYSTEM_MEDIA:-/data/media}"
EVENTYAY_FILESYSTEM_STATIC="${EVENTYAY_FILESYSTEM_STATIC:-/eventyay/src/static.dist}"

GUNICORN_WORKERS="${GUNICORN_WORKERS:-${WEB_CONCURRENCY:-$((2 * $(nproc)))}}"
GUNICORN_MAX_REQUESTS="${GUNICORN_MAX_REQUESTS:-1200}"
GUNICORN_MAX_REQUESTS_JITTER="${GUNICORN_MAX_REQUESTS_JITTER:-50}"
GUNICORN_FORWARDED_ALLOW_IPS="${GUNICORN_FORWARDED_ALLOW_IPS:-127.0.0.1}"

AUTOMIGRATE="${AUTOMIGRATE:-yes}"
AUTOREBUILD="${AUTOREBUILD:-yes}"

if [ "$EVENTYAY_FILESYSTEM_LOGS" != "/data/logs" ]; then
    export EVENTYAY_FILESYSTEM_LOGS
fi
if [ "$EVENTYAY_FILESYSTEM_MEDIA" != "/data/media" ]; then
    export EVENTYAY_FILESYSTEM_MEDIA
fi
if [ "$EVENTYAY_FILESYSTEM_STATIC" != "/eventyay/src/static.dist" ]; then
    export EVENTYAY_FILESYSTEM_STATIC
fi

if [ ! -d "$EVENTYAY_FILESYSTEM_LOGS" ]; then
    mkdir "$EVENTYAY_FILESYSTEM_LOGS";
fi
if [ ! -d "$EVENTYAY_FILESYSTEM_MEDIA" ]; then
    mkdir "$EVENTYAY_FILESYSTEM_MEDIA";
fi
if [ "$EVENTYAY_FILESYSTEM_STATIC" != "/eventyay/src/static.dist" ] &&
   [ ! -d "$EVENTYAY_FILESYSTEM_STATIC" ] &&
   [ "$AUTOREBUILD" = "yes" ]; then
    mkdir -p "$EVENTYAY_FILESYSTEM_STATIC"
    flock --nonblock /eventyay/.lockfile python3 -m eventyay rebuild
fi

if [ "$1" == "cron" ]; then
    exec python3 -m eventyay runperiodic
fi

if [ "$AUTOMIGRATE" = "yes" ]; then
    python3 -m eventyay migrate --noinput
fi

if [ "$1" == "all" ]; then
    exec sudo /usr/bin/supervisord -n -c /etc/supervisord.conf
fi

if [ "$1" == "webworker" ]; then
    exec gunicorn eventyay.wsgi \
        --name eventyay \
        --workers "${GUNICORN_WORKERS}" \
        --max-requests "${GUNICORN_MAX_REQUESTS}" \
        --max-requests-jitter "${GUNICORN_MAX_REQUESTS_JITTER}" \
        --forwarded-allow-ips "${GUNICORN_FORWARDED_ALLOW_IPS}" \
        --log-level=info \
        --bind=0.0.0.0:80
fi

if [ "$1" == "taskworker" ]; then
    exec celery -A eventyay.celery_app worker -l info
fi

if [ "$1" == "shell" ]; then
    exec python3 -m eventyay shell
fi

if [ "$1" == "upgrade" ]; then
    python3 -m eventyay rebuild
    exec python3 -m eventyay regenerate_css
fi

exec python3 -m eventyay "$@"
