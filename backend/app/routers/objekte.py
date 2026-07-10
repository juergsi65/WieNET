import json
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.infrastructure import (
    Trasse, Netzelement, Rohr, RohrStatus, Kabel, Stoerung, Bauabschnitt, ObjektStatus
)
from app.schemas.schemas import DashboardStats, SearchResult

router = APIRouter(prefix="/api", tags=["objekte"])


@router.get("/search", response_model=list[SearchResult])
def search(q: str = Query(..., min_length=2), db: Session = Depends(get_db), _user=Depends(get_current_user)):
    like = f"%{q}%"
    results = []

    for t in db.query(Trasse).filter(Trasse.name.ilike(like)).limit(20).all():
        geom = json.loads(db.scalar(func.ST_AsGeoJSON(func.ST_Centroid(t.geometrie))))
        results.append(SearchResult(id=t.id, typ="trasse", name=t.name, geometrie=geom))

    for n in db.query(Netzelement).filter(
        or_(Netzelement.name.ilike(like), Netzelement.adresse.ilike(like))
    ).limit(20).all():
        geom = json.loads(db.scalar(func.ST_AsGeoJSON(n.geometrie)))
        results.append(SearchResult(id=n.id, typ=n.typ.value, name=n.name, geometrie=geom))

    return results


@router.get("/objekt/{objekt_typ}/{objekt_id}")
def get_objekt_detail(objekt_typ: str, objekt_id: uuid.UUID, db: Session = Depends(get_db), _user=Depends(get_current_user)):
    if objekt_typ == "trasse":
        obj = db.get(Trasse, objekt_id)
        if not obj:
            raise HTTPException(status_code=404, detail="Nicht gefunden")
        geom = json.loads(db.scalar(func.ST_AsGeoJSON(obj.geometrie)))
        return {
            "id": str(obj.id), "typ": "trasse", "name": obj.name, "status": obj.status.value,
            "verlegetiefe_cm": obj.verlegetiefe_cm, "oberflaeche": obj.oberflaeche,
            "laenge_m": obj.laenge_m, "notizen": obj.notizen, "geometrie": geom,
            "rohrverbaende": [{"id": str(r.id), "bezeichnung": r.bezeichnung, "anzahl_rohre": len(r.rohre)}
                               for r in obj.rohrverbaende],
        }
    else:
        obj = db.get(Netzelement, objekt_id)
        if not obj:
            raise HTTPException(status_code=404, detail="Nicht gefunden")
        geom = json.loads(db.scalar(func.ST_AsGeoJSON(obj.geometrie)))
        return {
            "id": str(obj.id), "typ": obj.typ.value, "name": obj.name, "status": obj.status.value,
            "adresse": obj.adresse, "gemeinde": obj.gemeinde, "baujahr": obj.baujahr,
            "betreiber": obj.betreiber, "eigentuemer": obj.eigentuemer, "hersteller": obj.hersteller,
            "modell": obj.modell, "notizen": obj.notizen, "geometrie": geom,
            "ports_gesamt": obj.ports_gesamt, "ports_belegt": obj.ports_belegt,
            "parent_id": str(obj.parent_id) if obj.parent_id else None,
        }


@router.get("/dashboard", response_model=DashboardStats)
def dashboard(db: Session = Depends(get_db), _user=Depends(get_current_user)):
    trassen_laenge = db.query(func.coalesce(func.sum(Trasse.laenge_m), 0)).scalar()
    kabel_laenge = db.query(func.coalesce(func.sum(Kabel.laenge_m), 0)).scalar()
    anzahl_schaechte = db.query(Netzelement).filter(Netzelement.typ == "schacht").count()
    anzahl_muffen = db.query(Netzelement).filter(Netzelement.typ == "muffe").count()
    anzahl_hausanschluesse = db.query(Netzelement).filter(Netzelement.typ == "hausanschluss").count()
    rohre_frei = db.query(Rohr).filter(Rohr.status == RohrStatus.frei).count()
    rohre_belegt = db.query(Rohr).filter(Rohr.status == RohrStatus.belegt).count()

    fasern_gesamt = db.query(func.coalesce(func.sum(Kabel.fasernanzahl), 0)).scalar()
    fasern_belegt = db.query(func.coalesce(func.sum(Kabel.belegte_fasern), 0)).scalar()

    offene_stoerungen = db.query(Stoerung).filter(Stoerung.offen == True).count()  # noqa: E712
    geplante_bauabschnitte = db.query(Bauabschnitt).filter(Bauabschnitt.status == ObjektStatus.geplant).count()

    return DashboardStats(
        trassen_laenge_m=trassen_laenge or 0,
        kabel_laenge_m=kabel_laenge or 0,
        anzahl_schaechte=anzahl_schaechte,
        anzahl_muffen=anzahl_muffen,
        anzahl_hausanschluesse=anzahl_hausanschluesse,
        rohre_frei=rohre_frei,
        rohre_belegt=rohre_belegt,
        fasern_frei=max((fasern_gesamt or 0) - (fasern_belegt or 0), 0),
        fasern_belegt=fasern_belegt or 0,
        offene_stoerungen=offene_stoerungen,
        geplante_bauabschnitte=geplante_bauabschnitte,
    )
