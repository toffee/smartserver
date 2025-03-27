#!/bin/sh
set -e

# Upgrade database
echo "Upgrading database..."
ftcli db upgrade || { echo "Failed to upgrade database!"; exit 1; }

# Run app w/ gunicorn
echo "Running app...APP_WORKERS: ${APP_WORKERS}, APP_TIMEOUT: ${APP_TIMEOUT}, SCRIPT_NAME: ${SCRIPT_NAME}"
exec gunicorn -b 0.0.0.0:5000 "fittrackee:create_app()" --error-logfile /usr/src/app/logs/gunicorn.log --workers="${APP_WORKERS:-1}" --timeout "${APP_TIMEOUT:-30}"
