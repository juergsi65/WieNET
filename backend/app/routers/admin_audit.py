import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.permissions import require_global_permission
from app.models.admin import AuditLogEintrag, Permission
from app.models.user import User
from app.schemas.admin_schemas import AuditLogOut, PaginatedResponse

router = APIRouter(prefix="/api/admin/audit-log", tags=["admin-audit"])


@router.get("", response_model=PaginatedResponse)
def list_audit_log(
    page: int = 1,
    page_size: int = Query(50, le=200),
    user_id: uuid.UUID | None = None,
    aktion: str | None = None,
    objekt_typ: str | None = None,
    area_id: uuid.UUID | None = None,
    cluster_id: uuid.UUID | None = None,
    project_id: uuid.UUID | None = None,
    von: datetime | None = None,
    bis: datetime | None = None,
    db: Session = Depends(get_db),
    _user: User = Depends(require_global_permission(Permission.audit_log_anzeigen)),
):
    q = db.query(AuditLogEintrag)
    if user_id:
        q = q.filter(AuditLogEintrag.user_id == user_id)
    if aktion:
        q = q.filter(AuditLogEintrag.aktion.ilike(f"%{aktion}%"))
    if objekt_typ:
        q = q.filter(AuditLogEintrag.objekt_typ == objekt_typ)
    if area_id:
        q = q.filter(AuditLogEintrag.area_id == area_id)
    if cluster_id:
        q = q.filter(AuditLogEintrag.cluster_id == cluster_id)
    if project_id:
        q = q.filter(AuditLogEintrag.project_id == project_id)
    if von:
        q = q.filter(AuditLogEintrag.zeitpunkt >= von)
    if bis:
        q = q.filter(AuditLogEintrag.zeitpunkt <= bis)

    total = q.count()
    rows = q.order_by(AuditLogEintrag.zeitpunkt.desc()).offset((page - 1) * page_size).limit(page_size).all()

    items = []
    for r in rows:
        benutzer_name = r.user.full_name if r.user else "System"
        items.append(AuditLogOut(
            id=r.id, user_id=r.user_id, benutzer_name=benutzer_name, zeitpunkt=r.zeitpunkt,
            aktion=r.aktion, objekt_typ=r.objekt_typ, objekt_id=r.objekt_id,
            area_id=r.area_id, cluster_id=r.cluster_id, project_id=r.project_id,
            ip_adresse=r.ip_adresse, ergebnis=r.ergebnis.value, fehlerbeschreibung=r.fehlerbeschreibung,
        ))

    return PaginatedResponse(items=items, total=total, page=page, page_size=page_size)
