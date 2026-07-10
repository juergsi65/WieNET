"""Legt beim ersten Start einen Admin-Benutzer und ein realistisches Demo-Netz an.
Idempotent: läuft bei jedem Containerstart, überspringt aber, wenn bereits Daten vorhanden sind.
"""
import random

from geoalchemy2.shape import from_shape
from shapely.geometry import Point, LineString, Polygon, MultiPolygon

from app.core.config import settings
from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models.user import User, UserRole
from app.models.infrastructure import (
    Bauabschnitt, Trasse, Rohrverband, Rohr, RohrStatus, Kabel, KabelTyp,
    RohrKabelBelegung, Netzelement, NetzelementTyp, ObjektStatus, Stoerung,
)
from app.models.admin import (
    Gebiet, GebietStatus, Cluster, ClusterStatus, Projekt, ProjektStatus,
    ProjektBauabschnitt, BauabschnittStatus, Permission, UserClusterBerechtigung,
)

# Ausgangspunkt für das Demo-Netz (frei gewählte Koordinaten, Beispielgemeinde)
BASE_LAT, BASE_LON = 48.3069, 14.2858  # Raum Oberösterreich

ROHR_FARBEN = ["#FF0000", "#0000FF", "#00A651", "#FFD700", "#FFFFFF", "#8B4513", "#808080"]


def offset(lat, lon, d_lat, d_lon):
    return lat + d_lat, lon + d_lon


def run():
    db = SessionLocal()
    try:
        if not db.query(User).filter(User.email == settings.ADMIN_EMAIL).first():
            db.add(User(
                email=settings.ADMIN_EMAIL, full_name="Administrator",
                hashed_password=hash_password(settings.ADMIN_PASSWORD), role=UserRole.admin,
            ))
            db.commit()
            print(f"[seed] Admin-Benutzer angelegt: {settings.ADMIN_EMAIL}")

        if not settings.SEED_DEMO_DATA:
            return
        if db.query(Trasse).count() > 0:
            print("[seed] Demodaten bereits vorhanden, überspringe.")
            return

        # --- Bauabschnitt ---
        bauabschnitt = Bauabschnitt(name="Bauabschnitt Nord 2026", status=ObjektStatus.geplant)
        db.add(bauabschnitt)
        db.flush()

        # --- Netzhierarchie: OLT -> 4x PON -> Splitter -> 3x FCP -> Muffen -> Hausanschlüsse ---
        olt = Netzelement(
            name="OLT-ZENTRALE-01", typ=NetzelementTyp.olt, status=ObjektStatus.aktiv,
            geometrie=from_shape(Point(BASE_LON, BASE_LAT), srid=4326),
            betreiber="Stadtwerke Demo", ports_gesamt=64, ports_belegt=41,
        )
        db.add(olt)
        db.flush()

        pons = []
        for i in range(4):
            lat, lon = offset(BASE_LAT, BASE_LON, 0.002 * (i + 1), 0.001 * i)
            pon = Netzelement(
                name=f"PON-{i+1:02d}", typ=NetzelementTyp.pon, status=ObjektStatus.aktiv,
                geometrie=from_shape(Point(lon, lat), srid=4326),
                parent_id=olt.id, ports_gesamt=32, ports_belegt=random.randint(10, 28),
            )
            db.add(pon)
            pons.append(pon)
        db.flush()

        fcps = []
        for i in range(3):
            pon = pons[i % len(pons)]
            lat, lon = offset(BASE_LAT, BASE_LON, 0.003 * (i + 2), 0.002 * (i + 1))
            splitter = Netzelement(
                name=f"SPLITTER-{i+1:02d}", typ=NetzelementTyp.splitter, status=ObjektStatus.aktiv,
                geometrie=from_shape(Point(lon, lat), srid=4326),
                parent_id=pon.id, ports_gesamt=16, ports_belegt=random.randint(4, 14),
            )
            db.add(splitter)
            db.flush()
            fcp = Netzelement(
                name=f"FCP-{i+1:02d}", typ=NetzelementTyp.fcp, status=ObjektStatus.aktiv,
                geometrie=from_shape(Point(lon + 0.0005, lat + 0.0005), srid=4326),
                parent_id=splitter.id, ports_gesamt=24, ports_belegt=random.randint(6, 20),
            )
            db.add(fcp)
            fcps.append(fcp)
        db.flush()

        # --- 10 Schächte entlang von Trassen ---
        schaechte = []
        for i in range(10):
            lat, lon = offset(BASE_LAT, BASE_LON, 0.0015 * i, 0.0009 * i)
            s = Netzelement(
                name=f"SCHACHT-{i+1:03d}", typ=NetzelementTyp.schacht, status=ObjektStatus.aktiv,
                geometrie=from_shape(Point(lon, lat), srid=4326),
            )
            db.add(s)
            schaechte.append(s)
        db.flush()

        # --- Muffen in einigen Schächten, verknüpft mit FCPs ---
        muffen = []
        for i, s in enumerate(schaechte[:5]):
            m = Netzelement(
                name=f"MUFFE-{i+1:03d}", typ=NetzelementTyp.muffe, status=ObjektStatus.aktiv,
                geometrie=s.geometrie, parent_id=fcps[i % len(fcps)].id,
            )
            db.add(m)
            muffen.append(m)
        db.flush()

        # --- Hausanschlüsse an Muffen ---
        for i in range(15):
            lat, lon = offset(BASE_LAT, BASE_LON, 0.0016 * i + 0.0003, 0.0011 * i + 0.0004)
            ha = Netzelement(
                name=f"HA-{i+1:04d}", typ=NetzelementTyp.hausanschluss,
                status=ObjektStatus.aktiv if i % 6 != 0 else ObjektStatus.geplant,
                geometrie=from_shape(Point(lon, lat), srid=4326),
                adresse=f"Musterstraße {i+1}", gemeinde="Musterstadt",
                parent_id=muffen[i % len(muffen)].id,
            )
            db.add(ha)
        db.flush()

        # --- Trassen mit Rohrverbänden, Rohren, Kabeln ---
        for t_idx in range(6):
            start_lat, start_lon = offset(BASE_LAT, BASE_LON, 0.0015 * t_idx, 0.0009 * t_idx)
            end_lat, end_lon = offset(start_lat, start_lon, 0.0015, 0.0009)
            line = LineString([(start_lon, start_lat), (end_lon, end_lat)])

            status = ObjektStatus.aktiv
            if t_idx == 4:
                status = ObjektStatus.geplant
            elif t_idx == 5:
                status = ObjektStatus.stillgelegt

            trasse = Trasse(
                name=f"Trasse {t_idx+1:02d}", typ="Haupttrasse" if t_idx < 2 else "Zubringer",
                status=status, verlegetiefe_cm=random.choice([60, 80, 120]),
                oberflaeche=random.choice(["Asphalt", "Pflaster", "Wiese"]),
                laenge_m=round(line.length * 111000, 1),  # grobe Umrechnung Grad->Meter
                geometrie=from_shape(line, srid=4326),
                bauabschnitt_id=bauabschnitt.id if t_idx == 4 else None,
            )
            db.add(trasse)
            db.flush()

            rv = Rohrverband(trasse_id=trasse.id, bezeichnung=f"RV-{t_idx+1:02d} (7 Mikrorohre)")
            db.add(rv)
            db.flush()

            rohre = []
            for r_idx in range(7):
                rohr = Rohr(
                    rohrverband_id=rv.id, nummer=r_idx + 1, farbe=ROHR_FARBEN[r_idx % len(ROHR_FARBEN)],
                    durchmesser_mm=10, typ="Mikrorohr",
                    status=RohrStatus.frei,
                )
                db.add(rohr)
                rohre.append(rohr)
            db.flush()

            # In 3-4 der 7 Rohre je Trasse ein Kabel verlegen
            besetzte = random.sample(rohre, k=random.randint(2, 5))
            for rohr in besetzte:
                kabel = Kabel(
                    bezeichnung=f"GF-{trasse.name}-{rohr.nummer:02d}", typ=KabelTyp.glasfaser,
                    fasernanzahl=random.choice([12, 24, 48, 96]),
                    belegte_fasern=0, laenge_m=trasse.laenge_m, hersteller=random.choice(["Corning", "Prysmian", "CommScope"]),
                    status=ObjektStatus.aktiv, geometrie=trasse.geometrie,
                )
                kabel.belegte_fasern = random.randint(0, kabel.fasernanzahl)
                db.add(kabel)
                db.flush()

                db.add(RohrKabelBelegung(rohr_id=rohr.id, kabel_id=kabel.id, segment_start_m=0, segment_ende_m=trasse.laenge_m))
                rohr.status = RohrStatus.belegt
            # ein Rohr blockiert markieren zur Demonstration
            if len(rohre) > 6:
                rohre[6].status = RohrStatus.blockiert

        # --- Eine Beispielstörung ---
        db.add(Stoerung(
            titel="Signalabbruch FCP-02", beschreibung="Reduzierte Signalqualität an FCP-02, Ursache wird geprüft.",
            objekt_typ="netzelement", objekt_id=fcps[1].id, offen=True,
        ))

        db.commit()

        # --- Gebiete, Cluster, Projekte, Bauabschnitte, Berechtigungen ---
        seed_admin_demo_data(db)

        print("[seed] Demodaten erfolgreich angelegt.")
    finally:
        db.close()


def rechteck(lat, lon, groesse=0.006):
    """Erzeugt ein einfaches quadratisches Polygon um einen Mittelpunkt (für Demo-Cluster/Gebiete)."""
    return MultiPolygon([Polygon([
        (lon - groesse, lat - groesse), (lon + groesse, lat - groesse),
        (lon + groesse, lat + groesse), (lon - groesse, lat + groesse),
        (lon - groesse, lat - groesse),
    ])])


def seed_admin_demo_data(db):
    if db.query(Gebiet).count() > 0:
        print("[seed] Admin-Demodaten (Gebiete/Cluster/Projekte) bereits vorhanden, überspringe.")
        return

    # --- 2 Gebiete, hierarchisch ---
    gebiet_ooe = Gebiet(
        name="Oberösterreich", kuerzel="OOE", gebietstyp="Bundesland", status=GebietStatus.aktiv,
        geometrie=from_shape(rechteck(BASE_LAT, BASE_LON, 0.03), srid=4326),
        betreiber="Stadtwerke Demo", farbe="#0ea5e9",
    )
    db.add(gebiet_ooe)
    db.flush()

    gebiet_walding = Gebiet(
        name="Ausbaugebiet Walding Nord", kuerzel="WALD-N", gebietstyp="Ausbaugebiet",
        status=GebietStatus.aktiv, parent_id=gebiet_ooe.id,
        geometrie=from_shape(rechteck(BASE_LAT, BASE_LON, 0.012), srid=4326),
        betreiber="Stadtwerke Demo", farbe="#16a34a",
    )
    db.add(gebiet_walding)
    db.flush()

    # --- 3 Projekte ---
    projekt_ftth = Projekt(
        name="FTTH Walding", projektnummer="P-2026-001", projektcode="FTTH-WALD",
        beschreibung="Glasfaserausbau Walding Nord, Phase 1", status=ProjektStatus.bau,
        projektart="FTTH-Ausbau", auftraggeber="Gemeinde Walding", betreiber="Stadtwerke Demo",
        budget=850000, kostenstand=420000, fortschritt_pct=45,
    )
    projekt_wartung = Projekt(
        name="Netzwartung Zentrum 2026", projektnummer="P-2026-002", projektcode="WART-ZENT",
        beschreibung="Laufende Wartung und Störungsbehebung im Bestandsnetz", status=ProjektStatus.betrieb,
        projektart="Wartung", auftraggeber="Stadtwerke Demo", betreiber="Stadtwerke Demo",
        budget=120000, kostenstand=38000, fortschritt_pct=30,
    )
    projekt_abgeschlossen = Projekt(
        name="FTTH Zentrum Bauabschnitt 1", projektnummer="P-2025-014", projektcode="FTTH-ZENT-1",
        beschreibung="Abgeschlossener Erstausbau im Stadtzentrum", status=ProjektStatus.abgeschlossen,
        projektart="FTTH-Ausbau", auftraggeber="Stadtwerke Demo", betreiber="Stadtwerke Demo",
        budget=600000, kostenstand=598000, fortschritt_pct=100,
    )
    db.add_all([projekt_ftth, projekt_wartung, projekt_abgeschlossen])
    db.flush()

    # --- 5 Cluster ---
    cluster_defs = [
        dict(name="Walding Nord - Baucluster 1", nummer="CL-001", typ="Baucluster",
             status=ClusterStatus.im_bau, gebiet=gebiet_walding, projekt=projekt_ftth,
             mittel=(BASE_LAT + 0.004, BASE_LON + 0.002), groesse=0.004, farbe="#f59e0b",
             ausbauziel=120, geplant=90, aktiv=54),
        dict(name="Walding Nord - Baucluster 2", nummer="CL-002", typ="Baucluster",
             status=ClusterStatus.geplant, gebiet=gebiet_walding, projekt=projekt_ftth,
             mittel=(BASE_LAT + 0.010, BASE_LON + 0.006), groesse=0.004, farbe="#eab308",
             ausbauziel=95, geplant=95, aktiv=0),
        dict(name="Zentrum FCP-Versorgungsbereich", nummer="CL-003", typ="FCP-Versorgungsbereich",
             status=ClusterStatus.abgeschlossen, gebiet=gebiet_ooe, projekt=projekt_abgeschlossen,
             mittel=(BASE_LAT - 0.005, BASE_LON - 0.004), groesse=0.005, farbe="#16a34a",
             ausbauziel=200, geplant=200, aktiv=196),
        dict(name="Störungsgebiet Zentrum Süd", nummer="CL-004", typ="Störungsgebiet",
             status=ClusterStatus.aktiv, gebiet=gebiet_ooe, projekt=projekt_wartung,
             mittel=(BASE_LAT - 0.002, BASE_LON + 0.008), groesse=0.003, farbe="#dc2626",
             ausbauziel=None, geplant=0, aktiv=40),
        dict(name="Gewerbegebiet Ost", nummer="CL-005", typ="Gewerbegebiet",
             status=ClusterStatus.geplant, gebiet=gebiet_ooe, projekt=None,
             mittel=(BASE_LAT + 0.002, BASE_LON - 0.010), groesse=0.0035, farbe="#7c3aed",
             ausbauziel=40, geplant=40, aktiv=0),
    ]

    clusters = []
    for cd in cluster_defs:
        poly = rechteck(cd["mittel"][0], cd["mittel"][1], cd["groesse"])
        c = Cluster(
            name=cd["name"], nummer=cd["nummer"], typ=cd["typ"], status=cd["status"],
            geometrie=from_shape(poly, srid=4326), farbe=cd["farbe"],
            gebiet_id=cd["gebiet"].id, project_id=cd["projekt"].id if cd["projekt"] else None,
            ausbauziel=cd["ausbauziel"], anzahl_geplante_anschluesse=cd["geplant"],
            anzahl_aktive_anschluesse=cd["aktiv"], prioritaet=random.randint(1, 5),
        )
        db.add(c)
        clusters.append(c)
    db.flush()

    # --- Bauabschnitte für das FTTH-Walding-Projekt / Baucluster 1 ---
    bauabschnitt_namen = ["Tiefbau", "Einblasen", "Spleißen", "Hausanschlüsse", "Dokumentation"]
    for i, name in enumerate(bauabschnitt_namen):
        db.add(ProjektBauabschnitt(
            name=f"Bauabschnitt {i+1} {name}", nummer=i + 1,
            status=BauabschnittStatus.abgeschlossen if i < 2 else (
                BauabschnittStatus.aktiv if i == 2 else BauabschnittStatus.geplant
            ),
            project_id=projekt_ftth.id, cluster_id=clusters[0].id,
            fortschritt_pct=100 if i < 2 else (50 if i == 2 else 0),
        ))
    db.flush()

    # --- Vorhandene Objekte teilweise Clustern zuordnen (räumlich sinnvoll, per Nähe simuliert) ---
    # Erste 3 Trassen dem Baucluster 1 zuordnen, Trasse 4 dem Baucluster 2, Rest bleibt unzugeordnet
    alle_trassen = db.query(Trasse).order_by(Trasse.name).all()
    if len(alle_trassen) >= 4:
        alle_trassen[0].cluster_id = clusters[0].id
        alle_trassen[1].cluster_id = clusters[0].id
        alle_trassen[2].cluster_id = clusters[0].id
        alle_trassen[3].cluster_id = clusters[1].id
        # Trasse 5 bleibt absichtlich ohne Zuordnung (Demonstration "Objekte ohne Zuordnung")

    alle_netzelemente = db.query(Netzelement).all()
    for i, n in enumerate(alle_netzelemente):
        if i % 3 == 0:
            n.cluster_id = clusters[0].id
        elif i % 3 == 1:
            n.cluster_id = clusters[2].id
        # jedes dritte Element bleibt ohne Cluster (Demonstration Datenqualitäts-Lücke)

    db.flush()

    # --- Benutzer mit eingeschränkten Clusterrechten anlegen ---
    if not db.query(User).filter(User.email == "planer.walding@wsmronline.uk").first():
        eingeschraenkter_user = User(
            email="planer.walding@wsmronline.uk", username="pwalding",
            vorname="Anna", nachname="Berger", full_name="Anna Berger",
            hashed_password=hash_password("changeme123"), role=UserRole.planer,
            firma="Externes Planungsbüro", abteilung="Netzplanung",
        )
        db.add(eingeschraenkter_user)
        db.flush()
        # Darf nur Cluster 1 (Baucluster 1) sehen und bearbeiten
        for perm in [Permission.daten_anzeigen, Permission.daten_bearbeiten, Permission.export_durchfuehren]:
            db.add(UserClusterBerechtigung(user_id=eingeschraenkter_user.id, cluster_id=clusters[0].id, permission=perm))
        print("[seed] Eingeschränkter Planer-Benutzer angelegt: planer.walding@wsmronline.uk / changeme123")

    db.commit()
    print("[seed] Admin-Demodaten (2 Gebiete, 3 Projekte, 5 Cluster, 5 Bauabschnitte) angelegt.")


if __name__ == "__main__":
    run()
