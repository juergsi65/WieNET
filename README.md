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
3. Ein Admin-Benutzer wird angelegt (`ADMIN_EMAIL` / `ADMIN_PASSWORD` aus `.env`),
   mit erzwungener Passwortänderung beim ersten Login

Die Datenbank ist danach **leer** – es werden keinerlei Demo- oder Testdaten
angelegt. Trassen, Schächte, Kabel, Gebiete, Cluster und Projekte werden über
den Import-Assistenten oder manuell über die Admin-Oberfläche erfasst.

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
geprüftes Berechtigungssystem - **Administratoren sehen alle Cluster und Objekte,
andere Benutzer nur die ihnen explizit zugewiesenen** (gilt sowohl für die
Kartenansicht als auch für die Cluster-Verwaltung); erweiterte Benutzerverwaltung
(Deaktivieren/Reaktivieren, Passwort-Reset, Kontosperrung nach 5 Fehlversuchen);
Audit-Log mit Filtern und Pagination; Systemstatus-Seite.

**Redlining (Objekterfassung auf der Karte):** Für Benutzer mit Erstellrecht
(Administrator, Projektleiter, Planer) steht auf der Kartenansicht eine
Werkzeugleiste zur Verfügung: Trassen als Linie zeichnen (inkl. optionalem
Rohrverband mit frei wählbarer Rohranzahl, -typ und -durchmesser, branchenüblicher
Rohrfarbcodierung), sowie Schächte, Kästen, Muffen, Verteiler und FCPs als
Punktobjekte setzen. In der Rohrbelegungsansicht kann in ein freies Rohr direkt
ein Kabel eingezogen werden.

**Materialkatalog** (Adminbereich → Materialkatalog): Hersteller, Produktkategorien,
Produktfamilien, Produkte, Farben sowie Rohrverband- und Kabelvorlagen als
versionierbare Stammdaten. Enthält bereits die zwei in der Branche etablierten,
öffentlich dokumentierten Farbstandards **DIN EN 60794-1-1** (Rohr-/Aderfarben) und
**TIA-598-C** (Faserfarben) mit je 12 Grund- und 12 Streifenkombinationsfarben, ein
Hersteller-Gerüst für gabocom (gabo Systemtechnik GmbH), Hexatronic und Prysmian
Group sowie drei generische, produktneutrale Rohrverbandvorlagen (4-/7-/12-fach nach
DIN-Farbfolge). **Bewusst keine erfundenen Artikelnummern oder Produktvarianten** -
Hersteller/Produktfamilien/Produkte ohne verifizierte Quelle sind im Adminbereich
sichtbar mit „zu ergänzen" markiert und müssen von einem Administrator anhand
tatsächlicher Datenblätter vervollständigt werden. Lesen ist allen Rollen erlaubt,
Anlegen/Ändern/Löschen ist auf die Rolle Administrator beschränkt
(serverseitig geprüft über die Berechtigung `systemeinstellungen_aendern`).

**Materialauswahl im Redlining:** Beim Zeichnen einer Trasse kann zwischen „Aus
Materialkatalog" (echte Rohrverbandvorlage mit Grund-/Streifenfarbe je Rohr, direkt
per Farbvorschau auswählbar), „Generisch" (bisherige freie Rohranzahl/-typ-Eingabe,
weiterhin unterstützt) und „Kein Rohrverband" gewählt werden. Beim Einziehen eines
Kabels in ein freies Rohr steht ebenso eine Kabelvorlage aus dem Materialkatalog zur
Auswahl (Kabeltyp/Faseranzahl/Hersteller werden übernommen), alternativ weiterhin
freie Eingabe. Die Rohrquerschnittsansicht zeigt Grundfarbe, Streifenfarbe und
Farbname jedes Rohrs (aufgelöst aus dem Materialkatalog statt eines reinen
Hex-Werts), unabhängig davon farblich unterscheidbar von der Belegungsmarkierung
(weißer Punkt = Rohr belegt).

**Konfigurierbares, transaktionssicheres Nummernsystem** (Adminbereich →
Nummernkreise): pro Objekttyp (Gebiet, Cluster, Projekt, Bauabschnitt, Trasse) ein
frei definierbares Muster (z. B. `G-{sequence:03d}` oder
`{gebiet_code}-C-{sequence:03d}`) mit wählbarem Zähler-Geltungsbereich (global, je
Gebiet, je Cluster, je Projekt); höchstens ein aktives Schema je Objekttyp
(serverseitig über einen partiellen Unique-Index erzwungen), ältere Schemata bleiben
als Historie erhalten. Die Nummernvergabe selbst läuft über ein atomares
`INSERT … ON CONFLICT DO UPDATE … RETURNING` je Zählerkreis - unter Postgres'
Zeilensperren garantiert lückenlose, eindeutige Nummern auch bei gleichzeitigen
Anfragen (mit 50 parallelen Anfragen getestet: keine Duplikate, keine Lücken). Jede
vergebene Nummer wird zusätzlich in einer Historientabelle protokolliert, die auch
nach Löschung des Objekts erhalten bleibt. Gebiete und Cluster erhalten beim Anlegen
automatisch eine Nummer, sofern ein aktives Schema existiert; ohne aktives Schema
funktioniert das Anlegen unverändert ohne Nummer.

**Gebiete und Cluster bearbeiten/zusammenführen:** Gebiete und Cluster können jetzt
nachträglich umbenannt, mit Kürzel versehen, in Status/Farbe geändert und (Cluster)
einem anderen Gebiet oder Projekt zugeordnet werden (zuvor gab es dafür **keinen**
Backend-Endpunkt). Zwei oder mehr Cluster lassen sich zu einem neuen Cluster
zusammenführen: eine Vorschau zeigt vorab kombinierte Fläche (räumliche Vereinigung
der Polygone via PostGIS `ST_Union`), Anzahl betroffener Trassen/Netzelemente und
warnt, falls die gewählten Cluster unterschiedlichen Gebieten oder Projekten
angehören. Nach Bestätigung werden alle zugeordneten Objekte (Trassen, Netzelemente,
Cluster-Zuweisungen) transaktional auf den neuen Cluster umgehängt und die
Quell-Cluster gelöscht.

### Bewusst nicht enthalten (nächste Ausbaustufe)

Cluster-Teilen (Split, als Gegenstück zum Zusammenführen), automatische Clusterung
nach Adresse/Fläche/Distanz mit Vorschau, vollständige Löschfunktionen für alle
verbleibenden Objekttypen (aktuell: Cluster/Gebiete/Materialkatalog-Einträge mit
Abhängigkeitsschutz, weitere folgen), KML-/Shapefile-Import für Gebietsgrenzen,
Polygon-Bearbeitungswerkzeuge, vollständiges Exportcenter (PDF-/Excel-Berichte mit
mehreren Tabellenblättern), Daten-Explorer mit speicherbaren Ansichten,
Datenqualitätsprüfung, Hintergrundjobs mit Fortschrittsanzeige,
Zwei-Faktor-Authentifizierung, automatisierte Testsuite. Das Datenbankschema ist so
angelegt, dass diese Funktionen ohne erneute Schemaänderung ergänzt werden können.

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

- Passwörter ausschließlich als bcrypt-Hash gespeichert (`bcrypt` in
  `backend/requirements.txt` bewusst auf `4.0.1` gepinnt - neuere `bcrypt`-Versionen
  entfernen ein von `passlib` 1.7.4 zur Backend-Erkennung genutztes Attribut, wodurch
  jedes Hashing/Verifizieren inkl. Admin-Bootstrap und Login sonst mit einem Fehler
  abbricht)
- Authentifizierung über JWT, Ablaufzeit konfigurierbar (`ACCESS_TOKEN_EXPIRE_MINUTES`)
- Kontosperrung nach 5 fehlgeschlagenen Login-Versuchen
- Keine Ports außer 8093 werden nach außen geöffnet
- CORS auf die in `CORS_ORIGINS` konfigurierten Domains beschränkt
- Datei-Uploads auf 20 MB begrenzt und typgeprüft
- Rollenbasierte und granulare (Gebiet/Cluster/Projekt) Zugriffskontrolle wird
  serverseitig bei jedem Endpunkt geprüft, nicht nur im Frontend ausgeblendet
- Vollständiges Audit-Log für sicherheitsrelevante Aktionen

## Betriebshinweis: Kartendarstellung und Internetzugang

Trassen, Netzelemente und Cluster werden vollständig selbst gehostet (PostgreSQL/
PostGIS → FastAPI → Karte) und benötigen keinerlei externe Server, um zuverlässig
sichtbar zu sein. Lediglich die **Kachelbilder der Hintergrundkarte** stammen von
`tile.openstreetmap.org` und benötigen ausgehenden Internetzugang vom Browser des
Benutzers aus; ist dieser eingeschränkt, langsam oder durch eine Firewall/einen
Werbeblocker blockiert, bleibt nur der Kartenhintergrund leer/grau - eigene Daten
(Trassen, Schächte, Muffen, Verteiler, Cluster) werden davon unabhängig sofort
geladen und angezeigt. Schriftarten und die MapLibre-CSS werden mit der Anwendung
ausgeliefert und nicht mehr von externen CDNs nachgeladen.

## Datenmodell

Siehe `backend/app/models/infrastructure.py` (Tiefbau-/Netzobjekte),
`backend/app/models/admin.py` (Gebiete, Cluster, Projekte, Berechtigungen, Audit-Log)
und `backend/app/models/materials.py` (Materialkatalog: Hersteller, Produktkategorien,
Produktfamilien, Produkte, Farben, Rohrverband-/Kabelvorlagen). Kernbeziehungen:
`Trasse → Rohrverband → Rohr ↔ Kabel`, Netzhierarchie über `Netzelement.parent_id`
(OLT → PON → Splitter → FCP → Muffe → Hausanschluss), Cluster-Zuordnung über
`cluster_id` (Hauptcluster) bzw. `object_cluster_assignments` (zusätzliche/
schneidende Zuordnungen, ohne Geodaten zu duplizieren). Der Materialkatalog ist mit
der Kerninfrastruktur verknüpft: `Rohrverband.vorlage_id` → `Rohrverbandvorlage`,
`Rohr.farbe_id` → `Farbe` (das alte freie `Rohr.farbe`-Hexfeld bleibt als Fallback
für Altdaten/generisch angelegte Rohrverbände ohne Katalogbezug erhalten),
`Kabel.vorlage_id` → `Kabelvorlage`. Alle drei Fremdschlüssel sind nullable - Trassen
ohne Materialkatalog-Bezug funktionieren unverändert weiter.
