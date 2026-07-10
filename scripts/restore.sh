#!/usr/bin/env bash
set -euo pipefail

# Stellt ein Datenbank-Backup wieder her.
# Nutzung: ./scripts/restore.sh backups/db_20260710_120000.sql.gz

if [ $# -ne 1 ]; then
  echo "Nutzung: $0 <pfad-zum-backup.sql.gz>"
  exit 1
fi

BACKUP_FILE="$1"
if [ ! -f "$BACKUP_FILE" ]; then
  echo "Datei nicht gefunden: $BACKUP_FILE"
  exit 1
fi
BACKUP_FILE="$(realpath "$BACKUP_FILE")"

cd "$(dirname "$0")/.."

if [ -f .env ]; then
  set -a
  source .env
  set +a
fi
POSTGRES_USER="${POSTGRES_USER:-wienet}"
POSTGRES_DB="${POSTGRES_DB:-wienet}"

echo "WARNUNG: Dies überschreibt die aktuelle Datenbank '${POSTGRES_DB}' vollständig."
read -rp "Fortfahren? [j/N] " confirm
if [[ ! "$confirm" =~ ^[jJ]$ ]]; then
  echo "Abgebrochen."
  exit 0
fi

echo "-> Stelle Datenbank wieder her…"
gunzip -c "$BACKUP_FILE" | docker compose exec -T db psql -U "$POSTGRES_USER" -d "$POSTGRES_DB"

echo "-> Backend neu starten, damit Verbindungen sauber neu aufgebaut werden…"
docker compose restart backend

echo "-> Wiederherstellung abgeschlossen."
