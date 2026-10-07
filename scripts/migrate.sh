#!/bin/bash
# Apply migrations only if a backup newer than CRAWL4AI_BACKUP_MAX_AGE_MIN (default 60) exists.
set -euo pipefail
cd "$(dirname "$(readlink -f "$0")")/.."

if [[ -n "${CRAWL4AI_ENV_FILE:-}" ]]; then
    set -a; source "$CRAWL4AI_ENV_FILE"; set +a
fi

BACKUP_DIR="${CRAWL4AI_BACKUP_DIR:-$HOME/backups}"
MAX_AGE="${CRAWL4AI_BACKUP_MAX_AGE_MIN:-60}"
PYTHON="${CRAWL4AI_VENV:-$HOME/crawl4ai-env}/bin/python"

if [[ -z "$(find "$BACKUP_DIR" -maxdepth 1 -name 'pre-migration-*.dump' -mmin "-$MAX_AGE" 2>/dev/null | head -n1)" ]]; then
    echo "No backup newer than $MAX_AGE minutes in $BACKUP_DIR. Run scripts/backup-db.sh first." >&2
    exit 1
fi

"$PYTHON" scripts/check_migrations.py
exec "$PYTHON" scripts/migrate.py
