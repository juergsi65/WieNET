import json
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import func
from sqlalchemy.orm import Session
from geoalchemy2.shape import from_shape
from shapely.geometry import shape

from app.core.database import get_db
from app.core.audit import log_action
from app.core.permissions import require_global_permission
from app.models.admin import Gebiet, Cluster, Permission
from app.models.user import User
from app.schemas.admin_schemas import GebietCreate, GebietOut

router = APIRouter(prefix="/api/admin/areas", tags=["admin-gebiete"])


def to_out(db: Session, g: Gebiet, with_geom: bool = False) -> GebietOut:
    geom = None
    if with_geom and g.geometrie is not None:
        geom = json.loads(db.scalar(func.ST_AsGeoJSON(g.geometrie)))
    anzahl_cluster = db.query(Cluster).filter(Cluster.gebiet_id == g.id).count()
    return GebietOut(
        id=g.id, name=g.name, kuerzel=g.kuerzel, beschreibung=g.beschreibung,
        gebietstyp=g.gebietstyp, status=g.status.value, flaeche_m2=g.flaeche_m2,
        betreiber=g.betreiber, eigentuemer=g.eigentuemer, organisation=g.organisation,
        ansprechpartner=g.ansprechpartner, parent_id=g.parent_id, farbe=g.farbe,
        notizen=g.notizen, geometrie=geom, anzahl_cluster=anzahl_cluster,
    )


@router.get("", response_model=list[GebietOut])
def list_gebiete(
    with_geometry: bool = False,
    db: Session = Depends(get_db),
    _user: User = Depends(require_global_permission(Permission.daten_anzeigen)),
):
    return [to_out(db, g, with_geometry) for g in db.query(Gebiet).order_by(Gebiet.name).all()]


@router.post("", response_model=GebietOut)
def create_gebiet(
    payload: GebietCreate, request: Request, db: Session = Depends(get_db),
    user: User = Depends(require_global_permission(Permission.systemeinstellungen_aendern)),
):
    geom = from_shape(shape(payload.geometrie), srid=4326) if payload.geometrie else None
    flaeche = None
    if geom is not None:
        flaeche = db.scalar(func.ST_Area(func.ST_Transform(geom, 3857)))

    g = Gebiet(
        name=payload.name, kuerzel=payload.kuerzel, beschreibung=payload.beschreibung,
        gebietstyp=payload.gebietstyp, geometrie=geom, flaeche_m2=flaeche,
        betreiber=payload.betreiber, eigentuemer=payload.eigentuemer,
        organisation=payload.organisation, ansprechpartner=payload.ansprechpartner,
        parent_id=payload.parent_id, farbe=payload.farbe, notizen=payload.notizen,
    )
    db.add(g)
    db.commit()
    db.refresh(g)
    log_action(db, user, "gebiet_erstellt", "gebiet", g.id, neuer_wert=payload.name,
               area_id=g.id, request=request)
    return to_out(db, g)


@router.get("/{gebiet_id}", response_model=GebietOut)
def get_gebiet(
    gebiet_id: uuid.UUID, db: Session = Depends(get_db),
    _user: User = Depends(require_global_permission(Permission.daten_anzeigen)),
):
    g = db.get(Gebiet, gebiet_id)
    if not g:
        raise HTTPException(status_code=404, detail="Gebiet nicht gefunden")
    return to_out(db, g, with_geom=True)


@router.delete("/{gebiet_id}")
def delete_gebiet(
    gebiet_id: uuid.UUID, request: Request, db: Session = Depends(get_db),
    user: User = Depends(require_global_permission(Permission.systemeinstellungen_aendern)),
):
    g = db.get(Gebiet, gebiet_id)
    if not g:
        raise HTTPException(status_code=404, detail="Gebiet nicht gefunden")
    if db.query(Cluster).filter(Cluster.gebiet_id == gebiet_id).count() > 0:
        raise HTTPException(status_code=400, detail="Gebiet enthält noch Cluster und kann nicht gelöscht werden")
    db.delete(g)
    db.commit()
    log_action(db, user, "gebiet_geloescht", "gebiet", gebiet_id, alter_wert=g.name, request=request)
    return {"status": "geloescht"}
