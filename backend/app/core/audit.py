import uuid

from fastapi import Request
from sqlalchemy.orm import Session

from app.models.admin import AuditLogEintrag, AuditErgebnis
from app.models.user import User


def log_action(
    db: Session,
    user: User | None,
    aktion: str,
    objekt_typ: str | None = None,
    objekt_id: uuid.UUID | None = None,
    alter_wert: str | None = None,
    neuer_wert: str | None = None,
    area_id: uuid.UUID | None = None,
    cluster_id: uuid.UUID | None = None,
    project_id: uuid.UUID | None = None,
    request: Request | None = None,
    ergebnis: AuditErgebnis = AuditErgebnis.erfolg,
    fehlerbeschreibung: str | None = None,
):
    ip = request.client.host if request and request.client else None
    entry = AuditLogEintrag(
        user_id=user.id if user else None,
        aktion=aktion,
        objekt_typ=objekt_typ,
        objekt_id=objekt_id,
        alter_wert=alter_wert,
        neuer_wert=neuer_wert,
        area_id=area_id,
        cluster_id=cluster_id,
        project_id=project_id,
        ip_adresse=ip,
        ergebnis=ergebnis,
        fehlerbeschreibung=fehlerbeschreibung,
    )
    db.add(entry)
    db.commit()
