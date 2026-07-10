import os
import shutil

from fastapi import APIRouter, Depends
from sqlalchemy import func, text
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.permissions import require_global_permission
from app.models.admin import Permission, AuditLogEintrag
from app.models.user import User
from app.models.infrastructure import Trasse, Netzelement, Kabel

router = APIRouter(prefix="/api/admin/system", tags=["admin-system"])

APP_VERSION = "1.1.0"


@router.get("/status")
def system_status(
    db: Session = Depends(get_db),
    _user: User = Depends(require_global_permission(Permission.systemeinstellungen_aendern)),
):
    db_ok = True
    postgis_version = None
    db_size = None
    try:
        postgis_version = db.scalar(text("SELECT PostGIS_Version()"))
        db_size = db.scalar(text("SELECT pg_size_pretty(pg_database_size(current_database()))"))
    except Exception:
        db_ok = False

    anzahl_benutzer = db.query(User).count()
    anzahl_aktive_benutzer = db.query(User).filter(User.is_active == True).count()  # noqa: E712
    anzahl_objekte = db.query(Trasse).count() + db.query(Netzelement).count() + db.query(Kabel).count()

    letzter_fehler = db.query(AuditLogEintrag).filter(
        AuditLogEintrag.ergebnis == "fehler"
    ).order_by(AuditLogEintrag.zeitpunkt.desc()).first()

    upload_dir = "/app/uploads"
    upload_size_mb = None
    if os.path.isdir(upload_dir):
        total = sum(f.stat().st_size for f in __import__("pathlib").Path(upload_dir).rglob("*") if f.is_file())
        upload_size_mb = round(total / (1024 * 1024), 2)

    disk = shutil.disk_usage("/")

    return {
        "version": APP_VERSION,
        "frontend": "ok",
        "api": "ok",
        "datenbank": "ok" if db_ok else "fehler",
        "postgis_version": postgis_version,
        "datenbankgroesse": db_size,
        "upload_verzeichnis_mb": upload_size_mb,
        "datenträger_frei_gb": round(disk.free / (1024 ** 3), 1),
        "datenträger_gesamt_gb": round(disk.total / (1024 ** 3), 1),
        "anzahl_benutzer": anzahl_benutzer,
        "anzahl_aktive_benutzer": anzahl_aktive_benutzer,
        "anzahl_objekte": anzahl_objekte,
        "letzter_fehler": {
            "zeitpunkt": letzter_fehler.zeitpunkt.isoformat() if letzter_fehler else None,
            "aktion": letzter_fehler.aktion if letzter_fehler else None,
            "beschreibung": letzter_fehler.fehlerbeschreibung if letzter_fehler else None,
        } if letzter_fehler else None,
    }
