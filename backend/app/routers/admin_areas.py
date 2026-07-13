import json
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.core.geometry import geojson_to_multipolygon_ewkb

from app.core.database import get_db
from app.core.audit import log_action
from app.core.permissions import require_global_permission
from app.core.numbering import get_active_schema, generate_nummer, scope_key_und_kontext
from app.models.admin import Gebiet, Cluster, Permission
from app.models.user import User
from app.schemas.admin_schemas import GebietCreate, GebietUpdate, GebietOut

router = APIRouter(prefix="/api/admin/areas", tags=["admin-gebiete"])


def to_out(db: Session, g: Gebiet, with_geom: bool = False) -> GebietOut:
    geom = None
    if with_geom and g.geometrie is not None:
        geom = json.loads(db.scalar(func.ST_AsGeoJSON(g.geometrie)))
    anzahl_cluster = db.query(Cluster).filter(Cluster.gebiet_id == g.id).count()
    return GebietOut(
        id=g.id, nummer=g.nummer, name=g.name, kuerzel=g.kuerzel, beschreibung=g.beschreibung,
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
    geom = geojson_to_multipolygon_ewkb(payload.geometrie) if payload.geometrie else None
    flaeche = None
    if geom is not None:
        flaeche = db.scalar(func.ST_Area(func.ST_Transform(geom, 3857)))

    nummer = payload.nummer
    schema = get_active_schema(db, "gebiet")
    if schema:
        try:
            scope_key, kontext = scope_key_und_kontext(db, schema.scope)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=f"Nummernvergabe fehlgeschlagen: {e}")
        nummer = generate_nummer(db, schema, scope_key, kontext)

    g = Gebiet(
        nummer=nummer, name=payload.name, kuerzel=payload.kuerzel, beschreibung=payload.beschreibung,
        gebietstyp=payload.gebietstyp, geometrie=geom, flaeche_m2=flaeche,
        betreiber=payload.betreiber, eigentuemer=payload.eigentuemer,
        organisation=payload.organisation, ansprechpartner=payload.ansprechpartner,
        parent_id=payload.parent_id, farbe=payload.farbe, notizen=payload.notizen,
        erstellt_von_id=user.id,
    )
    db.add(g)
    db.commit()
    db.refresh(g)
    log_action(db, user, "gebiet_erstellt", "gebiet", g.id, neuer_wert=payload.name,
               area_id=g.id, request=request)
    return to_out(db, g)


@router.patch("/{gebiet_id}", response_model=GebietOut)
def update_gebiet(
    gebiet_id: uuid.UUID, payload: GebietUpdate, request: Request, db: Session = Depends(get_db),
    user: User = Depends(require_global_permission(Permission.systemeinstellungen_aendern)),
):
    g = db.get(Gebiet, gebiet_id)
    if not g:
        raise HTTPException(status_code=404, detail="Gebiet nicht gefunden")
    if payload.parent_id == gebiet_id:
        raise HTTPException(status_code=400, detail="Ein Gebiet kann nicht sein eigenes übergeordnetes Gebiet sein")

    alt = f"{g.name} ({g.status.value})"
    updates = payload.model_dump(exclude_unset=True)
    if "status" in updates:
        from app.models.admin import GebietStatus
        try:
            updates["status"] = GebietStatus(updates["status"])
        except ValueError:
            raise HTTPException(status_code=400, detail="Ungültiger Status")
    for field, value in updates.items():
        setattr(g, field, value)
    g.geaendert_von_id = user.id
    db.commit()
    db.refresh(g)
    log_action(db, user, "gebiet_aktualisiert", "gebiet", g.id, alter_wert=alt,
               neuer_wert=f"{g.name} ({g.status.value})", area_id=g.id, request=request)
    return to_out(db, g, with_geom=True)


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
