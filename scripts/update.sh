#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

echo "== WieNet: Update =="

echo "-> Sichere Datenbank vor dem Update…"
./scripts/backup.sh

echo "-> Hole neueste Quelltexte von GitHub…"
git pull

echo "-> Baue Container neu und starte sie (Alembic-Migrationen laufen automatisch)…"
docker compose up -d --build

echo "-> Fertig. Logs prüfen mit: docker compose logs -f backend"
