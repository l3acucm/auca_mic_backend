#!/usr/bin/env bash
set -e

if [ "$TESTING" == "1" ]; then
    python3 -m pytest .
else
    python3 manage.py migrate
    exec gunicorn project.wsgi \
        --bind=0.0.0.0:8000 \
        --workers "${GUNICORN_WORKERS:-3}" \
        --timeout "${GUNICORN_TIMEOUT:-120}" \
        --access-logfile -
fi
