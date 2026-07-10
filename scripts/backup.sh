#!/usr/bin/env bash
set -euo pipefail

# Erstellt ein komprimiertes SQL-Dump-Backup der PostgreSQL/PostGIS-Datenbank
# sowie ein Backup der hochgeladenen Dateien (Volumes).

cd "$(dirname "$0")/.."

BACKUP_DIR="./backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
mkdir -p "$BACKUP_DIR"

# .env laden, falls vorhanden - sonst gelten die Defaults aus docker-compose.yml
if [ -f .env ]; then
  set -a
  source .env
  set +a
fi
POSTGRES_USER="${POSTGRES_USER:-wienet}"
POSTGRES_DB="${POSTGRES_DB:-wienet}"

echo "-> Sichere Datenbank…"
docker compose exec -T db pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB" | gzip > "$BACKUP_DIR/db_${TIMESTAMP}.sql.gz"

echo "-> Sichere Upload-Volume…"
UPLOADS_VOLUME=$(docker volume ls --format '{{.Name}}' | grep uploads_data | head -n1)
if [ -z "$UPLOADS_VOLUME" ]; then
  echo "WARNUNG: Kein uploads_data-Volume gefunden, überspringe Upload-Backup."
else
  docker run --rm \
    -v "${UPLOADS_VOLUME}:/data:ro" \
    -v "$(realpath "$BACKUP_DIR")":/backup \
    alpine tar czf "/backup/uploads_${TIMESTAMP}.tar.gz" -C /data .
  echo "   $BACKUP_DIR/uploads_${TIMESTAMP}.tar.gz"
fi

echo "-> Backup abgeschlossen:"
echo "   $BACKUP_DIR/db_${TIMESTAMP}.sql.gz"

# Alte Backups (>30 Tage) automatisch aufräumen
find "$BACKUP_DIR" -name "*.gz" -mtime +30 -delete
