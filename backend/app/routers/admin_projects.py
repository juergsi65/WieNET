import uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.audit import log_action
from app.core.permissions import require_global_permission
from app.models.admin import Projekt, Cluster, Permission, ProjektBauabschnitt, BauabschnittStatus
from app.models.infrastructure import Trasse, Netzelement, Stoerung
from app.models.user import User
from app.schemas.admin_schemas import ProjektCreate, ProjektOut

router = APIRouter(prefix="/api/admin/projects", tags=["admin-projekte"])


def to_out(db: Session, p: Projekt) -> ProjektOut:
    anzahl_cluster = db.query(Cluster).filter(Cluster.project_id == p.id).count()
    return ProjektOut(
        id=p.id, name=p.name, projektnummer=p.projektnummer, projektcode=p.projektcode,
        beschreibung=p.beschreibung, status=p.status.value, projektart=p.projektart,
        auftraggeber=p.auftraggeber, projektleiter_id=p.projektleiter_id,
        start_datum=p.start_datum, geplantes_ende=p.geplantes_ende, budget=p.budget,
        kostenstand=p.kostenstand, fortschritt_pct=p.fortschritt_pct, anzahl_cluster=anzahl_cluster,
    )


@router.get("", response_model=list[ProjektOut])
def list_projekte(
    status_filter: str | None = None, db: Session = Depends(get_db),
    _user: User = Depends(require_global_permission(Permission.daten_anzeigen)),
):
    q = db.query(Projekt)
    if status_filter:
        q = q.filter(Projekt.status == status_filter)
    return [to_out(db, p) for p in q.order_by(Projekt.name).all()]


@router.post("", response_model=ProjektOut)
def create_projekt(
    payload: ProjektCreate, request: Request, db: Session = Depends(get_db),
    user: User = Depends(require_global_permission(Permission.projekte_erstellen)),
):
    p = Projekt(**payload.model_dump())
    db.add(p)
    db.commit()
    db.refresh(p)
    log_action(db, user, "projekt_erstellt", "projekt", p.id, neuer_wert=payload.name,
               project_id=p.id, request=request)
    return to_out(db, p)


@router.get("/{project_id}", response_model=ProjektOut)
def get_projekt(
    project_id: uuid.UUID, db: Session = Depends(get_db),
    _user: User = Depends(require_global_permission(Permission.daten_anzeigen)),
):
    p = db.get(Projekt, project_id)
    if not p:
        raise HTTPException(status_code=404, detail="Projekt nicht gefunden")
    return to_out(db, p)


@router.get("/{project_id}/dashboard")
def projekt_dashboard(
    project_id: uuid.UUID, db: Session = Depends(get_db),
    _user: User = Depends(require_global_permission(Permission.daten_anzeigen)),
):
    p = db.get(Projekt, project_id)
    if not p:
        raise HTTPException(status_code=404, detail="Projekt nicht gefunden")

    clusters = db.query(Cluster).filter(Cluster.project_id == project_id).all()
    cluster_ids = [c.id for c in clusters]

    trassen_laenge = db.query(func.coalesce(func.sum(Trasse.laenge_m), 0)).filter(
        Trasse.cluster_id.in_(cluster_ids)
    ).scalar() if cluster_ids else 0

    anzahl_hausanschluesse = db.query(Netzelement).filter(
        Netzelement.cluster_id.in_(cluster_ids), Netzelement.typ == "hausanschluss"
    ).count() if cluster_ids else 0

    netz_ids = [n.id for n in db.query(Netzelement.id).filter(Netzelement.cluster_id.in_(cluster_ids)).all()] if cluster_ids else []
    offene_stoerungen = db.query(Stoerung).filter(
        Stoerung.objekt_id.in_(netz_ids), Stoerung.offen == True  # noqa: E712
    ).count() if netz_ids else 0

    bauabschnitte = db.query(ProjektBauabschnitt).filter(ProjektBauabschnitt.project_id == project_id).all()

    return {
        "projekt": to_out(db, p),
        "anzahl_cluster": len(clusters),
        "anzahl_bauabschnitte": len(bauabschnitte),
        "bauabschnitte_abgeschlossen": sum(1 for b in bauabschnitte if b.status == BauabschnittStatus.abgeschlossen),
        "trassenlaenge_m": trassen_laenge,
        "anzahl_hausanschluesse": anzahl_hausanschluesse,
        "offene_stoerungen": offene_stoerungen,
        "cluster_liste": [{"id": str(c.id), "name": c.name, "status": c.status.value} for c in clusters],
    }
