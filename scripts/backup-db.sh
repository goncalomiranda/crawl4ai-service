#!/bin/bash
# Create a custom-format pg_dump backup. Usage: scripts/backup-db.sh [backup_dir]
# Reads CRAWL4AI_DB_* from the environment (or CRAWL4AI_ENV_FILE if set).
set -euo pipefail

if [[ -n "${CRAWL4AI_ENV_FILE:-}" ]]; then
    set -a; source "$CRAWL4AI_ENV_FILE"; set +a
fi

BACKUP_DIR="${1:-${CRAWL4AI_BACKUP_DIR:-$HOME/backups}}"
KEEP="${CRAWL4AI_BACKUP_KEEP:-10}"

for v in CRAWL4AI_DB_HOST CRAWL4AI_DB_PORT CRAWL4AI_DB_NAME CRAWL4AI_DB_USER CRAWL4AI_DB_PASSWORD; do
    [[ -n "${!v:-}" ]] || { echo "Missing $v" >&2; exit 1; }
done
PG_IMAGE="${CRAWL4AI_PG_IMAGE:-postgres:16-alpine}"
if command -v pg_dump >/dev/null; then
    PG_DUMP=(pg_dump)
elif command -v docker >/dev/null; then
    # No local client: run pg_dump from a throwaway container (match the server's major version).
    PG_DUMP=(docker run --rm --network host -e PGPASSWORD "$PG_IMAGE" pg_dump)
else
    echo "Neither pg_dump nor docker found; install postgresql-client or docker" >&2
    exit 1
fi

umask 077
mkdir -p "$BACKUP_DIR"
chmod 700 "$BACKUP_DIR"
OUT="$BACKUP_DIR/pre-migration-$(date +%F-%H%M%S).dump"

# Dump to stdout so the file is created by this user, not by a container.
PGPASSWORD="$CRAWL4AI_DB_PASSWORD" "${PG_DUMP[@]}" -Fc \
    -h "$CRAWL4AI_DB_HOST" -p "$CRAWL4AI_DB_PORT" -U "$CRAWL4AI_DB_USER" \
    -d "$CRAWL4AI_DB_NAME" > "$OUT" || { rm -f "$OUT"; echo "Backup failed" >&2; exit 1; }
chmod 600 "$OUT"

ls -1t "$BACKUP_DIR"/pre-migration-*.dump | tail -n +"$((KEEP + 1))" | xargs -r rm -f --
echo "$OUT"
