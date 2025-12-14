#!/usr/bin/env bash
set -euo pipefail

MYSQL_USER=${MYSQL_USER:-eoex}
MYSQL_PASSWORD=${MYSQL_PASSWORD:-eoex}
MYSQL_HOST=${MYSQL_HOST:-localhost}
MYSQL_DB=${MYSQL_DB:-eoex_travel}

echo "Creating database ${MYSQL_DB} if not exists..."
mysql -h "$MYSQL_HOST" -u "$MYSQL_USER" -p"$MYSQL_PASSWORD" -e "CREATE DATABASE IF NOT EXISTS ${MYSQL_DB};"

echo "Applying migrations..."
mysql -h "$MYSQL_HOST" -u "$MYSQL_USER" -p"$MYSQL_PASSWORD" "$MYSQL_DB" < "$(dirname "$0")/../migrations/001_init.sql"

echo "Done."
