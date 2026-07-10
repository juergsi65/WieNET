# WieNet

Selbstgehostete Webanwendung zur Visualisierung, Verwaltung und Analyse von Tiefbau-,
Glasfaser- und Telekommunikationsinfrastruktur - inklusive Gebiets-, Cluster- und
Projektverwaltung mit granularem Berechtigungssystem.

## Architektur

```
┌────────────────────────────────────────────────────────┐
│  Cloudflare Tunnel (optional, für externen Zugriff)     │
└────────────────────────────────────────────────────────┘
                         │
                 Host-Port 8093
                         │
        ┌────────────────────────────────┐
        │  frontend (Nginx + React/Vite)   │
        │  - liefert die statische SPA aus │
        │  - leitet /api/ intern weiter    │
        └────────────────┬─────────────────┘
                          │  (internes Docker-Netzwerk)
        ┌─────────────────▼────────────────┐
        │  backend (FastAPI, Port 8000)     │
        └─────────────────┬─────────────────┘
                          │
        ┌─────────────────▼────────────────┐
        │  db (PostgreSQL 16 + PostGIS)     │
        └───────────────────────────────────┘
```

Drei Container: `db`, `backend`, `frontend`. Der `frontend`-Container enthält seinen
eigenen Nginx, der sowohl die gebaute React-App ausliefert als auch `/api/` an das
FastAPI-Backend weiterleitet - es gibt keinen separaten Reverse-Proxy-Container.

## Schnellstart

```bash
git clone https://github.com/juergsi65/WieNet.git
cd WieNet
docker compose up -d --build
```

Das genügt für einen funktionierenden Testbetrieb: `docker-compose.yml` enthält
funktionierende Entwicklungs-Defaults (Datenbankpasswort, Secret Key, Admin-Zugang),
falls keine `.env`-Datei angelegt wird.

**Für den produktiven Einsatz** (empfohlen, insbesondere bevor der Dienst über
Cloudflare Tunnel öffentlich erreichbar ist):

```bash
cp .env.example .env
# .env öffnen und POSTGRES_PASSWORD, DATABASE_URL (gleiches Passwort!), SECRET_KEY,
# ADMIN_EMAIL, ADMIN_PASSWORD und CORS_ORIGINS auf sichere/eigene Werte setzen
docker compose up -d --build
```

Alternativ übernimmt `./scripts/install.sh` das automatisch: Docker-Installation
(falls nötig), Erzeugung einer `.env` mit zufällig generierten, zueinander passenden
Passwörtern, und den Build/Start.

Nach dem Start ist WieNet erreichbar unter: **http://<Server-IP>:8093**

Beim ersten Start passiert automatisch:
1. PostgreSQL/PostGIS wird hochgefahren (Healthcheck wartet darauf)
2. Alembic-Migrationen (`0001`, `0002`) legen das komplette Schema an
3. Ein Admin-Benutzer wird angelegt (`ADMIN_EMAIL` / `ADMIN_PASSWORD` aus `.env`)
4. Falls `SEED_DEMO_DATA=true`: realistische Demodaten werden eingespielt
   (Netzstruktur, Trassen/Rohre/Kabel, 2 Gebiete, 5 Cluster, 3 Projekte, Bauabschnitte)

## Enthaltene Funktionen

**Kernplattform:** interaktive Karte (MapLibre GL + OpenStreetMap), Trassen, Schächte,
Muffen, Verteiler/FCP, OLT/PON/Splitter, Kabel, Rohre, Hausanschlüsse; grafische
Rohrbelegungs-Querschnittsdarstellung; interaktives Netzschema; Objekt-Detailpanel;
Suche/Filter; CSV-/Excel-/GeoJSON-Import mit Vorschau und Validierung; Dashboard mit
Kennzahlen; rollenbasierte Anmeldung (JWT); Dark/Light Mode.

**Administration:** geschützter Admin-Bereich (nur Rolle Administrator); Hierarchie
Gebiet → Cluster → Projekt → Bauabschnitt; Cluster-Polygone direkt auf der Karte
zeichnen mit automatischer Erkennung aller enthaltenen/schneidenden Objekte (Vorschau
vor dem Bestätigen); Cluster- und Projekt-Dashboards; granulares, serverseitig
geprüftes Berechtigungssystem (Basisrollen plus optionale Gebiets-/Cluster-/
Projektrechte); erweiterte Benutzerverwaltung (Deaktivieren/Reaktivieren, Passwort-
Reset, Kontosperrung nach 5 Fehlversuchen); Audit-Log mit Filtern und Pagination;
Systemstatus-Seite.

### Bewusst nicht enthalten (nächste Ausbaustufe)

KML-/Shapefile-Import für Gebietsgrenzen, Polygon-Bearbeitungswerkzeuge (Teilen/
Zusammenführen), vollständiges Exportcenter (PDF-/Excel-Berichte mit mehreren
Tabellenblättern), Daten-Explorer mit speicherbaren Ansichten, Datenqualitätsprüfung,
Hintergrundjobs mit Fortschrittsanzeige, Zwei-Faktor-Authentifizierung, automatisierte
Testsuite. Das Datenbankschema ist so angelegt, dass diese Funktionen ohne erneute
Schemaänderung ergänzt werden können.

## Voraussetzungen für den Proxmox-Betrieb

- Proxmox VE mit einem Debian-12-LXC-Container (Docker-Nesting aktiviert:
  `pct set <CTID> --features nesting=1,keyctl=1`)
- Docker + Docker Compose Plugin (installiert `./scripts/install.sh` automatisch)
- Optional: bestehender Cloudflare Tunnel für externen Zugriff ohne offene Ports

## Installation auf einem frischen Debian-12-LXC-Container

```bash
apt-get update && apt-get install -y git curl sudo ca-certificates
git clone https://github.com/juergsi65/WieNet.git
cd WieNet
chmod +x scripts/*.sh
./scripts/install.sh
```

## Cloudflare Tunnel einrichten

```bash
curl -L https://pkg.cloudflare.com/cloudflare-main.gpg -o /usr/share/keyrings/cloudflare-main.gpg
echo "deb [signed-by=/usr/share/keyrings/cloudflare-main.gpg] https://pkg.cloudflare.com/cloudflared $(lsb_release -cs) main" \
  | tee /etc/apt/sources.list.d/cloudflared.list
apt-get update && apt-get install -y cloudflared

cloudflared tunnel login
cloudflared tunnel create wienet-tunnel
```

`/etc/cloudflared/config.yml`:

```yaml
tunnel: <TUNNEL-ID>
credentials-file: /root/.cloudflared/<TUNNEL-ID>.json

ingress:
  - hostname: tiefbau.wsmronline.uk
    service: http://127.0.0.1:8093
  - service: http_status:404
```

```bash
cloudflared tunnel route dns wienet-tunnel tiefbau.wsmronline.uk
systemctl enable --now cloudflared
```

Falls du bereits einen zentralen Cloudflare-Tunnel-Container für andere Dienste
(Paperless-ngx, Home Assistant, …) betreibst, genügt es, dort einen zusätzlichen
Ingress-Eintrag mit Ziel `http://<interne-ip-des-wienet-containers>:8093` zu ergänzen.

## Betrieb

```bash
docker compose ps                  # Status aller Container
docker compose logs -f backend     # Backend-Logs live verfolgen
docker compose restart backend     # Backend neu starten
./scripts/update.sh                # Update auf neueste Version (inkl. automatischem Backup)
./scripts/backup.sh                # Manuelles Backup (DB + Uploads)
./scripts/restore.sh <backup-datei># Wiederherstellung aus Backup
```

## API-Dokumentation

Nach dem Start: `http://<Server-IP>:8093/docs` (interaktive OpenAPI/Swagger-Doku).

## Sicherheitshinweise

- Passwörter ausschließlich als bcrypt-Hash gespeichert
- Authentifizierung über JWT, Ablaufzeit konfigurierbar (`ACCESS_TOKEN_EXPIRE_MINUTES`)
- Kontosperrung nach 5 fehlgeschlagenen Login-Versuchen
- Keine Ports außer 8093 werden nach außen geöffnet
- CORS auf die in `CORS_ORIGINS` konfigurierten Domains beschränkt
- Datei-Uploads auf 20 MB begrenzt und typgeprüft
- Rollenbasierte und granulare (Gebiet/Cluster/Projekt) Zugriffskontrolle wird
  serverseitig bei jedem Endpunkt geprüft, nicht nur im Frontend ausgeblendet
- Vollständiges Audit-Log für sicherheitsrelevante Aktionen

## Datenmodell

Siehe `backend/app/models/infrastructure.py` (Tiefbau-/Netzobjekte) und
`backend/app/models/admin.py` (Gebiete, Cluster, Projekte, Berechtigungen, Audit-Log).
Kernbeziehungen: `Trasse → Rohrverband → Rohr ↔ Kabel`, Netzhierarchie über
`Netzelement.parent_id` (OLT → PON → Splitter → FCP → Muffe → Hausanschluss),
Cluster-Zuordnung über `cluster_id` (Hauptcluster) bzw. `object_cluster_assignments`
(zusätzliche/schneidende Zuordnungen, ohne Geodaten zu duplizieren).
