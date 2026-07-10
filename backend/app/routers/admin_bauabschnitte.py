import uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.audit import log_action
from app.core.permissions import require_global_permission
from app.models.admin import ProjektBauabschnitt, Permission
from app.models.user import User
from app.schemas.admin_schemas import BauabschnittCreate, BauabschnittOut

router = APIRouter(prefix="/api/admin/construction-sections", tags=["admin-bauabschnitte"])


def to_out(b: ProjektBauabschnitt) -> BauabschnittOut:
    return BauabschnittOut(
        id=b.id, name=b.name, nummer=b.nummer, status=b.status.value, project_id=b.project_id,
        cluster_id=b.cluster_id, verantwortlicher_id=b.verantwortlicher_id,
        fortschritt_pct=b.fortschritt_pct, start_datum=b.start_datum, ende_datum=b.ende_datum,
    )


@router.get("", response_model=list[BauabschnittOut])
def list_bauabschnitte(
    project_id: uuid.UUID | None = None, cluster_id: uuid.UUID | None = None,
    db: Session = Depends(get_db),
    _user: User = Depends(require_global_permission(Permission.daten_anzeigen)),
):
    q = db.query(ProjektBauabschnitt)
    if project_id:
        q = q.filter(ProjektBauabschnitt.project_id == project_id)
    if cluster_id:
        q = q.filter(ProjektBauabschnitt.cluster_id == cluster_id)
    return [to_out(b) for b in q.order_by(ProjektBauabschnitt.nummer).all()]


@router.post("", response_model=BauabschnittOut)
def create_bauabschnitt(
    payload: BauabschnittCreate, request: Request, db: Session = Depends(get_db),
    user: User = Depends(require_global_permission(Permission.projekte_bearbeiten)),
):
    b = ProjektBauabschnitt(**payload.model_dump())
    db.add(b)
    db.commit()
    db.refresh(b)
    log_action(db, user, "bauabschnitt_erstellt", "bauabschnitt", b.id, neuer_wert=payload.name,
               project_id=b.project_id, cluster_id=b.cluster_id, request=request)
    return to_out(b)


@router.patch("/{bauabschnitt_id}", response_model=BauabschnittOut)
def update_bauabschnitt(
    bauabschnitt_id: uuid.UUID, fortschritt_pct: int | None = None, status_neu: str | None = None,
    request: Request = None, db: Session = Depends(get_db),
    user: User = Depends(require_global_permission(Permission.projekte_bearbeiten)),
):
    b = db.get(ProjektBauabschnitt, bauabschnitt_id)
    if not b:
        raise HTTPException(status_code=404, detail="Bauabschnitt nicht gefunden")
    alt = f"status={b.status.value},fortschritt={b.fortschritt_pct}"
    if fortschritt_pct is not None:
        b.fortschritt_pct = fortschritt_pct
    if status_neu is not None:
        b.status = status_neu
    db.commit()
    db.refresh(b)
    log_action(db, user, "bauabschnitt_aktualisiert", "bauabschnitt", b.id, alter_wert=alt,
               neuer_wert=f"status={b.status.value},fortschritt={b.fortschritt_pct}",
               project_id=b.project_id, cluster_id=b.cluster_id, request=request)
    return to_out(b)
