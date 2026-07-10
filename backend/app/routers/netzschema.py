import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.infrastructure import Netzelement, NetzelementTyp

router = APIRouter(prefix="/api/netzschema", tags=["netzschema"])


def build_node(el: Netzelement, db: Session) -> dict:
    belegung_pct = None
    if el.ports_gesamt:
        belegung_pct = round(100 * (el.ports_belegt or 0) / el.ports_gesamt, 1)
    return {
        "id": str(el.id),
        "name": el.name,
        "typ": el.typ.value,
        "status": el.status.value,
        "ports_gesamt": el.ports_gesamt,
        "ports_belegt": el.ports_belegt,
        "belegung_pct": belegung_pct,
        "children": [build_node(c, db) for c in
                     db.query(Netzelement).filter(Netzelement.parent_id == el.id).all()],
    }


@router.get("/baum")
def get_gesamtbaum(db: Session = Depends(get_db), _user=Depends(get_current_user)):
    """Liefert alle OLTs mit vollständiger Kinderhierarchie (OLT->PON->Splitter->FCP->Muffe->Hausanschluss)."""
    olts = db.query(Netzelement).filter(Netzelement.typ == NetzelementTyp.olt).all()
    return [build_node(o, db) for o in olts]


@router.get("/pfad/{netzelement_id}")
def get_pfad_zu_wurzel(netzelement_id: uuid.UUID, db: Session = Depends(get_db), _user=Depends(get_current_user)):
    """Liefert den kompletten Weg von einem Hausanschluss (oder beliebigem Element) bis zur OLT."""
    el = db.get(Netzelement, netzelement_id)
    if not el:
        raise HTTPException(status_code=404, detail="Element nicht gefunden")

    pfad = [el]
    current = el
    while current.parent_id:
        current = db.get(Netzelement, current.parent_id)
        if not current:
            break
        pfad.append(current)
    pfad.reverse()

    return [{"id": str(e.id), "name": e.name, "typ": e.typ.value, "status": e.status.value} for e in pfad]
