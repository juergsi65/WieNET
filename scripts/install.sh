#!/usr/bin/env bash
set -euo pipefail

# Installationsskript für WieNet - Tiefbau-/Glasfaser-Infrastrukturplattform
# Zielumgebung: frischer Debian-12-LXC-Container auf Proxmox mit Docker + Docker Compose

echo "== WieNet: Installation =="

if [ "$EUID" -ne 0 ]; then
  echo "Bitte als root oder mit sudo ausführen."
  exit 1
fi

# 1. Docker prüfen / installieren
if ! command -v docker &> /dev/null; then
  echo "-> Docker wird installiert…"
  apt-get update
  apt-get install -y ca-certificates curl gnupg
  install -m 0755 -d /etc/apt/keyrings
  curl -fsSL https://download.docker.com/linux/debian/gpg -o /etc/apt/keyrings/docker.asc
  chmod a+r /etc/apt/keyrings/docker.asc
  echo \
    "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/debian $(. /etc/os-release && echo "$VERSION_CODENAME") stable" \
    > /etc/apt/sources.list.d/docker.list
  apt-get update
  apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
else
  echo "-> Docker ist bereits installiert."
fi

# 2. .env anlegen, falls nicht vorhanden - mit automatisch generierten, konsistenten Werten
if [ ! -f .env ]; then
  echo "-> Erstelle .env aus .env.example mit automatisch generierten sicheren Werten…"
  cp .env.example .env

  DB_PASS=$(openssl rand -hex 16)
  SECRET=$(openssl rand -hex 32)
  ADMIN_PASS=$(openssl rand -hex 10)

  sed -i "s/change_me_strong_password/${DB_PASS}/g" .env   # ersetzt sowohl POSTGRES_PASSWORD als auch DATABASE_URL konsistent
  sed -i "s/change_me_generate_with_openssl_rand_hex_32/${SECRET}/" .env
  # ADMIN_PASSWORD separat setzen (eigener Wert, nicht identisch mit DB-Passwort)
  sed -i "s/^ADMIN_PASSWORD=.*/ADMIN_PASSWORD=${ADMIN_PASS}/" .env

  echo ""
  echo "-> .env wurde mit automatisch generierten, sicheren Werten erstellt."
  echo "-> Admin-Passwort (bitte notieren): ${ADMIN_PASS}"
  echo ""
  echo "Optional: .env öffnen, um ADMIN_EMAIL oder CORS_ORIGINS (Domain) anzupassen:"
  echo "  nano .env"
  echo ""
fi

# 3. Container bauen und starten
echo "-> Baue und starte Container…"
docker compose up -d --build

echo "-> Warte auf Backend-Healthcheck…"
for i in $(seq 1 30); do
  if docker compose ps backend | grep -q "healthy"; then
    echo "Backend ist bereit."
    break
  fi
  sleep 2
done

echo ""
echo "== Installation abgeschlossen =="
echo "Die Anwendung ist lokal erreichbar unter: http://127.0.0.1:8093"
echo "Für externen Zugriff über Cloudflare Tunnel siehe README.md, Abschnitt 'Cloudflare Tunnel'."
echo "Admin-Zugang: siehe ADMIN_EMAIL / ADMIN_PASSWORD in .env"
