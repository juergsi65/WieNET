import json
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.infrastructure import Trasse, Netzelement, NetzelementTyp, ObjektStatus

router = APIRouter(prefix="/api/map", tags=["map"])

# Zoomstufen-Gruppierung für Netzelement-Typen (siehe Vorgabe: groß/mittel/klein)
ZOOM_GROUPS = {
    "gross": list(NetzelementTyp),  # alle Typen, inkl. Hausanschluss
    "mittel": [
        NetzelementTyp.schacht, NetzelementTyp.muffe, NetzelementTyp.verteiler,
        NetzelementTyp.fcp, NetzelementTyp.kasten, NetzelementTyp.technikstandort,
    ],
    "klein": [NetzelementTyp.olt, NetzelementTyp.pon, NetzelementTyp.pop],
}


def zoom_to_group(zoom: int) -> str:
    if zoom >= 17:
        return "gross"
    if zoom >= 13:
        return "mittel"
    return "klein"


@router.get("/trassen")
def get_trassen_geojson(
    zoom: int = Query(16, ge=1, le=22),
    status_filter: Optional[str] = None,
    bbox: Optional[str] = None,  # "minLon,minLat,maxLon,maxLat"
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
):
    q = db.query(Trasse)
    if status_filter:
        q = q.filter(Trasse.status == status_filter)
    if bbox:
        min_lon, min_lat, max_lon, max_lat = map(float, bbox.split(","))
        q = q.filter(func.ST_Intersects(
            Trasse.geometrie,
            func.ST_MakeEnvelope(min_lon, min_lat, max_lon, max_lat, 4326)
        ))

    features = []
    for t in q.all():
        geom = json.loads(db.scalar(func.ST_AsGeoJSON(t.geometrie)))
        features.append({
            "type": "Feature",
            "geometry": geom,
            "properties": {
                "id": str(t.id), "name": t.name, "typ": t.typ, "status": t.status.value,
                "laenge_m": t.laenge_m, "verlegetiefe_cm": t.verlegetiefe_cm,
                "objekt_typ": "trasse", "cluster_id": str(t.cluster_id) if t.cluster_id else None,
            },
        })
    return {"type": "FeatureCollection", "features": features}


@router.get("/netzelemente")
def get_netzelemente_geojson(
    zoom: int = Query(16, ge=1, le=22),
    typ_filter: Optional[str] = None,
    bbox: Optional[str] = None,
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
):
    group = ZOOM_GROUPS[zoom_to_group(zoom)]
    q = db.query(Netzelement).filter(Netzelement.typ.in_(group))
    if typ_filter:
        q = q.filter(Netzelement.typ == typ_filter)
    if bbox:
        min_lon, min_lat, max_lon, max_lat = map(float, bbox.split(","))
        q = q.filter(func.ST_Intersects(
            Netzelement.geometrie,
            func.ST_MakeEnvelope(min_lon, min_lat, max_lon, max_lat, 4326)
        ))

    features = []
    for n in q.all():
        geom = json.loads(db.scalar(func.ST_AsGeoJSON(n.geometrie)))
        belegung_pct = None
        if n.ports_gesamt:
            belegung_pct = round(100 * (n.ports_belegt or 0) / n.ports_gesamt, 1)
        features.append({
            "type": "Feature",
            "geometry": geom,
            "properties": {
                "id": str(n.id), "name": n.name, "typ": n.typ.value, "status": n.status.value,
                "ports_gesamt": n.ports_gesamt, "ports_belegt": n.ports_belegt,
                "belegung_pct": belegung_pct, "objekt_typ": "netzelement",
            },
        })
    return {"type": "FeatureCollection", "features": features}
