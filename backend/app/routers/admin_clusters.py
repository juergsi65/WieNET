import json
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.core.geometry import geojson_to_multipolygon_ewkb

from app.core.database import get_db
from app.core.audit import log_action
from app.core.permissions import require_global_permission, user_accessible_cluster_ids
from app.models.admin import (
    Cluster, Permission, ObjektClusterZuordnung, ZuordnungsRelation,
)
from app.models.infrastructure import Trasse, Netzelement
from app.models.user import User
from app.schemas.admin_schemas import (
    ClusterCreate, ClusterOut, ClusterZuordnungsVorschau, ClusterZuordnungBestaetigen, ClusterStatsOut,
)

router = APIRouter(prefix="/api/admin/clusters", tags=["admin-cluster"])


def to_out(db: Session, c: Cluster, with_geom: bool = False) -> ClusterOut:
    geom = None
    if with_geom:
        geom = json.loads(db.scalar(func.ST_AsGeoJSON(c.geometrie)))
    return ClusterOut(
        id=c.id, name=c.name, nummer=c.nummer, beschreibung=c.beschreibung, typ=c.typ,
        status=c.status.value, flaeche_m2=c.flaeche_m2, farbe=c.farbe, prioritaet=c.prioritaet,
        gebiet_id=c.gebiet_id, project_id=c.project_id, ausbauziel=c.ausbauziel,
        anzahl_geplante_anschluesse=c.anzahl_geplante_anschluesse,
        anzahl_aktive_anschluesse=c.anzahl_aktive_anschluesse, geometrie=geom,
    )


@router.get("", response_model=list[ClusterOut])
def list_clusters(
    with_geometry: bool = True, project_id: uuid.UUID | None = None, gebiet_id: uuid.UUID | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_global_permission(Permission.daten_anzeigen)),
):
    q = db.query(Cluster)
    if project_id:
        q = q.filter(Cluster.project_id == project_id)
    if gebiet_id:
        q = q.filter(Cluster.gebiet_id == gebiet_id)

    # Sichtbarkeit einschränken: Admin sieht alle Cluster, andere Benutzer nur die,
    # für die ihnen explizit eine Berechtigung (direkt, über Projekt oder Gebiet) erteilt wurde.
    # Wurden einem Benutzer noch KEINE granularen Rechte vergeben, gelten die Rollen-Basisrechte
    # (Rückwärtskompatibilität), er sieht dann ebenfalls alle Cluster.
    erlaubte_ids = user_accessible_cluster_ids(db, user)
    if erlaubte_ids is not None:
        q = q.filter(Cluster.id.in_(erlaubte_ids))

    return [to_out(db, c, with_geometry) for c in q.order_by(Cluster.name).all()]


@router.post("", response_model=ClusterOut)
def create_cluster(
    payload: ClusterCreate, request: Request, db: Session = Depends(get_db),
    user: User = Depends(require_global_permission(Permission.cluster_erstellen)),
):
    geom = geojson_to_multipolygon_ewkb(payload.geometrie)
    flaeche = db.scalar(func.ST_Area(func.ST_Transform(geom, 3857)))

    c = Cluster(
        name=payload.name, nummer=payload.nummer, beschreibung=payload.beschreibung,
        typ=payload.typ, status=payload.status, geometrie=geom, flaeche_m2=flaeche,
        farbe=payload.farbe, prioritaet=payload.prioritaet, gebiet_id=payload.gebiet_id,
        project_id=payload.project_id, projektleiter_id=payload.projektleiter_id,
        planer_id=payload.planer_id, baufirma=payload.baufirma, start_datum=payload.start_datum,
        geplantes_ende=payload.geplantes_ende, budget=payload.budget, ausbauziel=payload.ausbauziel,
        notizen=payload.notizen,
    )
    db.add(c)
    db.commit()
    db.refresh(c)
    log_action(db, user, "cluster_erstellt", "cluster", c.id, neuer_wert=payload.name,
               cluster_id=c.id, project_id=c.project_id, area_id=c.gebiet_id, request=request)
    return to_out(db, c, with_geom=True)


@router.get("/{cluster_id}", response_model=ClusterOut)
def get_cluster(
    cluster_id: uuid.UUID, db: Session = Depends(get_db),
    _user: User = Depends(require_global_permission(Permission.daten_anzeigen)),
):
    c = db.get(Cluster, cluster_id)
    if not c:
        raise HTTPException(status_code=404, detail="Cluster nicht gefunden")
    return to_out(db, c, with_geom=True)


@router.delete("/{cluster_id}")
def delete_cluster(
    cluster_id: uuid.UUID, request: Request, db: Session = Depends(get_db),
    user: User = Depends(require_global_permission(Permission.systemeinstellungen_aendern)),
):
    c = db.get(Cluster, cluster_id)
    if not c:
        raise HTTPException(status_code=404, detail="Cluster nicht gefunden")
    db.query(ObjektClusterZuordnung).filter(ObjektClusterZuordnung.cluster_id == cluster_id).delete()
    db.query(Trasse).filter(Trasse.cluster_id == cluster_id).update({"cluster_id": None})
    db.query(Netzelement).filter(Netzelement.cluster_id == cluster_id).update({"cluster_id": None})
    db.delete(c)
    db.commit()
    log_action(db, user, "cluster_geloescht", "cluster", cluster_id, alter_wert=c.name, request=request)
    return {"status": "geloescht"}


# --- Automatische räumliche Zuordnung ---

@router.get("/{cluster_id}/zuordnung/vorschau", response_model=list[ClusterZuordnungsVorschau])
def zuordnung_vorschau(
    cluster_id: uuid.UUID, db: Session = Depends(get_db),
    _user: User = Depends(require_global_permission(Permission.cluster_bearbeiten)),
):
    """Ermittelt, welche Objekte im Clusterpolygon liegen oder es schneiden,
    ohne bereits etwas zu speichern (Schritt 'Vorschau' vor dem Bestätigen)."""
    cluster = db.get(Cluster, cluster_id)
    if not cluster:
        raise HTTPException(status_code=404, detail="Cluster nicht gefunden")

    ergebnisse = []

    netzelemente = db.query(Netzelement).filter(
        func.ST_Within(Netzelement.geometrie, cluster.geometrie)
    ).all()
    if netzelemente:
        bereits_anders = sum(1 for n in netzelemente if n.cluster_id and n.cluster_id != cluster_id)
        ergebnisse.append(ClusterZuordnungsVorschau(
            objekt_typ="netzelement", anzahl=len(netzelemente), davon_enthalten=len(netzelemente),
            davon_schneidend=0, davon_bereits_anders_zugeordnet=bereits_anders,
            beispiel_ids=[n.id for n in netzelemente[:5]],
        ))

    trassen = db.query(Trasse).filter(
        func.ST_Intersects(Trasse.geometrie, cluster.geometrie)
    ).all()
    if trassen:
        enthalten = [t for t in trassen if db.scalar(func.ST_Within(t.geometrie, cluster.geometrie))]
        schneidend = [t for t in trassen if t not in enthalten]
        bereits_anders = sum(1 for t in trassen if t.cluster_id and t.cluster_id != cluster_id)
        ergebnisse.append(ClusterZuordnungsVorschau(
            objekt_typ="trasse", anzahl=len(trassen), davon_enthalten=len(enthalten),
            davon_schneidend=len(schneidend), davon_bereits_anders_zugeordnet=bereits_anders,
            beispiel_ids=[t.id for t in trassen[:5]],
        ))

    return ergebnisse


@router.post("/{cluster_id}/zuordnung/bestaetigen")
def zuordnung_bestaetigen(
    cluster_id: uuid.UUID, payload: ClusterZuordnungBestaetigen, request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_global_permission(Permission.cluster_bearbeiten)),
):
    """Übernimmt die zuvor angezeigte Vorschau tatsächlich: setzt Hauptcluster bzw.
    legt Einträge in object_cluster_assignments für schneidende Objekte an."""
    cluster = db.get(Cluster, cluster_id)
    if not cluster:
        raise HTTPException(status_code=404, detail="Cluster nicht gefunden")

    zusammenfassung = {}

    if "netzelement" in payload.objekt_typen:
        netzelemente = db.query(Netzelement).filter(
            func.ST_Within(Netzelement.geometrie, cluster.geometrie)
        ).all()
        for n in netzelemente:
            n.cluster_id = cluster.id
        zusammenfassung["netzelement"] = len(netzelemente)

    if "trasse" in payload.objekt_typen:
        trassen = db.query(Trasse).filter(
            func.ST_Intersects(Trasse.geometrie, cluster.geometrie)
        ).all()
        anzahl_enthalten = anzahl_schneidend = 0
        for t in trassen:
            enthalten = db.scalar(func.ST_Within(t.geometrie, cluster.geometrie))
            if enthalten:
                t.cluster_id = cluster.id
                anzahl_enthalten += 1
            else:
                existing = db.query(ObjektClusterZuordnung).filter_by(
                    objekt_typ="trasse", objekt_id=t.id, cluster_id=cluster.id
                ).first()
                if not existing:
                    db.add(ObjektClusterZuordnung(
                        objekt_typ="trasse", objekt_id=t.id, cluster_id=cluster.id,
                        relation=ZuordnungsRelation.schneidet, ist_hauptcluster=False,
                    ))
                anzahl_schneidend += 1
        zusammenfassung["trasse"] = {"enthalten": anzahl_enthalten, "schneidend": anzahl_schneidend}

    db.commit()
    log_action(
        db, user, "cluster_objektzuordnung_bestaetigt", "cluster", cluster_id,
        neuer_wert=json.dumps(zusammenfassung, default=str), cluster_id=cluster_id, request=request,
    )
    return {"status": "zugeordnet", "zusammenfassung": zusammenfassung}


# --- Cluster-Dashboard / Statistiken ---

@router.get("/{cluster_id}/stats", response_model=ClusterStatsOut)
def cluster_stats(
    cluster_id: uuid.UUID, db: Session = Depends(get_db),
    _user: User = Depends(require_global_permission(Permission.daten_anzeigen)),
):
    from app.models.infrastructure import Rohr, RohrStatus, Kabel, Stoerung, Rohrverband
    from app.models.admin import ProjektBauabschnitt, BauabschnittStatus

    cluster = db.get(Cluster, cluster_id)
    if not cluster:
        raise HTTPException(status_code=404, detail="Cluster nicht gefunden")

    trassen_q = db.query(Trasse).filter(Trasse.cluster_id == cluster_id)
    trassen_laenge = db.query(func.coalesce(func.sum(Trasse.laenge_m), 0)).filter(
        Trasse.cluster_id == cluster_id
    ).scalar()

    netz_q = db.query(Netzelement).filter(Netzelement.cluster_id == cluster_id)
    anzahl_schaechte = netz_q.filter(Netzelement.typ == "schacht").count()
    anzahl_muffen = netz_q.filter(Netzelement.typ == "muffe").count()
    anzahl_verteiler = netz_q.filter(Netzelement.typ == "verteiler").count()
    anzahl_fcp = netz_q.filter(Netzelement.typ == "fcp").count()
    anzahl_hausanschluesse = netz_q.filter(Netzelement.typ == "hausanschluss").count()

    trassen_ids = [t.id for t in trassen_q.all()]
    rohre_frei = rohre_belegt = 0
    kabellaenge = 0.0
    fasern_frei = fasern_belegt = 0
    if trassen_ids:
        rv_ids = [rv.id for rv in db.query(Rohrverband).filter(Rohrverband.trasse_id.in_(trassen_ids)).all()]
        if rv_ids:
            rohre_frei = db.query(Rohr).filter(Rohr.rohrverband_id.in_(rv_ids), Rohr.status == RohrStatus.frei).count()
            rohre_belegt = db.query(Rohr).filter(Rohr.rohrverband_id.in_(rv_ids), Rohr.status == RohrStatus.belegt).count()
        kabellaenge = db.query(func.coalesce(func.sum(Kabel.laenge_m), 0)).filter(
            func.ST_Intersects(Kabel.geometrie, cluster.geometrie)
        ).scalar() or 0
        fasern_gesamt = db.query(func.coalesce(func.sum(Kabel.fasernanzahl), 0)).filter(
            func.ST_Intersects(Kabel.geometrie, cluster.geometrie)
        ).scalar() or 0
        fasern_belegt_gesamt = db.query(func.coalesce(func.sum(Kabel.belegte_fasern), 0)).filter(
            func.ST_Intersects(Kabel.geometrie, cluster.geometrie)
        ).scalar() or 0
        fasern_belegt = fasern_belegt_gesamt
        fasern_frei = max(fasern_gesamt - fasern_belegt_gesamt, 0)

    netz_ids = [n.id for n in netz_q.all()]
    anzahl_stoerungen = db.query(Stoerung).filter(
        Stoerung.objekt_id.in_(netz_ids), Stoerung.offen == True  # noqa: E712
    ).count() if netz_ids else 0

    bauabschnitte_geplant = db.query(ProjektBauabschnitt).filter(
        ProjektBauabschnitt.cluster_id == cluster_id, ProjektBauabschnitt.status == BauabschnittStatus.geplant
    ).count()
    bauabschnitte_abgeschlossen = db.query(ProjektBauabschnitt).filter(
        ProjektBauabschnitt.cluster_id == cluster_id, ProjektBauabschnitt.status == BauabschnittStatus.abgeschlossen
    ).count()

    rohr_gesamt = rohre_frei + rohre_belegt
    fasern_gesamt_sum = fasern_frei + fasern_belegt

    return ClusterStatsOut(
        flaeche_m2=cluster.flaeche_m2,
        trassenlaenge_m=trassen_laenge or 0,
        kabellaenge_m=kabellaenge or 0,
        anzahl_schaechte=anzahl_schaechte,
        anzahl_muffen=anzahl_muffen,
        anzahl_verteiler=anzahl_verteiler,
        anzahl_fcp=anzahl_fcp,
        anzahl_hausanschluesse=anzahl_hausanschluesse,
        rohre_frei=rohre_frei,
        rohre_belegt=rohre_belegt,
        rohrbelegung_pct=round(100 * rohre_belegt / rohr_gesamt, 1) if rohr_gesamt else 0,
        fasern_frei=fasern_frei,
        fasern_belegt=fasern_belegt,
        faserauslastung_pct=round(100 * fasern_belegt / fasern_gesamt_sum, 1) if fasern_gesamt_sum else 0,
        anzahl_stoerungen=anzahl_stoerungen,
        bauabschnitte_geplant=bauabschnitte_geplant,
        bauabschnitte_abgeschlossen=bauabschnitte_abgeschlossen,
    )
