"""Zentrale Berechtigungsprüfung.

Admin hat immer alle Rechte. Für alle anderen Rollen wird zusätzlich zur Basisrolle
geprüft, ob eine granulare Berechtigung für das konkrete Gebiet/Cluster/Projekt vorliegt.
Das Ausblenden von Schaltflächen im Frontend ersetzt diese Prüfung NICHT - sie erfolgt
hier serverseitig bei jedem sicherheitsrelevanten Endpunkt.
"""
import uuid

from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User, UserRole
from app.models.admin import (
    Permission, UserGebietBerechtigung, UserClusterBerechtigung, UserProjektBerechtigung,
    Cluster,
)

# Basisrollen erhalten implizit einen sinnvollen Grundstock an Berechtigungen,
# sofern keine feingranulare Einschränkung existiert.
ROLLEN_BASISRECHTE = {
    UserRole.admin: set(Permission),
    UserRole.projektleiter: {
        Permission.daten_anzeigen, Permission.daten_erstellen, Permission.daten_bearbeiten,
        Permission.fotos_hochladen, Permission.dokumente_hochladen, Permission.export_durchfuehren,
        Permission.berichte_erstellen, Permission.projekte_bearbeiten, Permission.cluster_bearbeiten,
    },
    UserRole.planer: {
        Permission.daten_anzeigen, Permission.daten_erstellen, Permission.daten_bearbeiten,
        Permission.import_durchfuehren, Permission.export_durchfuehren, Permission.berichte_erstellen,
        Permission.cluster_erstellen, Permission.cluster_bearbeiten,
    },
    UserRole.techniker: {
        Permission.daten_anzeigen, Permission.fotos_hochladen, Permission.dokumente_hochladen,
    },
    UserRole.betrachter: {Permission.daten_anzeigen},
}


def user_has_global_permission(user: User, permission: Permission) -> bool:
    if user.role == UserRole.admin:
        return True
    return permission in ROLLEN_BASISRECHTE.get(user.role, set())


def user_has_cluster_permission(db: Session, user: User, cluster_id: uuid.UUID, permission: Permission) -> bool:
    if user.role == UserRole.admin:
        return True
    # explizite Clusterberechtigung hat Vorrang
    explicit = db.query(UserClusterBerechtigung).filter_by(
        user_id=user.id, cluster_id=cluster_id, permission=permission
    ).first()
    if explicit:
        return True
    # falls Nutzer projektweite Rechte für das übergeordnete Projekt des Clusters hat
    cluster = db.get(Cluster, cluster_id)
    if cluster and cluster.project_id:
        proj_perm = db.query(UserProjektBerechtigung).filter_by(
            user_id=user.id, project_id=cluster.project_id, permission=permission
        ).first()
        if proj_perm:
            return True
    if cluster and cluster.gebiet_id:
        area_perm = db.query(UserGebietBerechtigung).filter_by(
            user_id=user.id, area_id=cluster.gebiet_id, permission=permission
        ).first()
        if area_perm:
            return True
    # Wenn der Nutzer KEINE granularen Cluster-/Projekt-/Gebietsrechte besitzt,
    # gelten die Rollen-Basisrechte (Rückwärtskompatibilität für einfache Rollen ohne Scoping).
    has_any_scoped_grant = (
        db.query(UserClusterBerechtigung).filter_by(user_id=user.id).first()
        or db.query(UserProjektBerechtigung).filter_by(user_id=user.id).first()
        or db.query(UserGebietBerechtigung).filter_by(user_id=user.id).first()
    )
    if not has_any_scoped_grant:
        return permission in ROLLEN_BASISRECHTE.get(user.role, set())
    return False


def require_global_permission(permission: Permission):
    def dependency(user: User = Depends(get_current_user)) -> User:
        if not user_has_global_permission(user, permission):
            raise HTTPException(status_code=403, detail=f"Berechtigung fehlt: {permission.value}")
        return user
    return dependency


def require_cluster_permission(permission: Permission):
    def dependency(
        cluster_id: uuid.UUID,
        db: Session = Depends(get_db),
        user: User = Depends(get_current_user),
    ) -> User:
        if not user_has_cluster_permission(db, user, cluster_id, permission):
            raise HTTPException(status_code=403, detail=f"Berechtigung fehlt für dieses Cluster: {permission.value}")
        return user
    return dependency


def user_accessible_cluster_ids(db: Session, user: User) -> list[uuid.UUID] | None:
    """Gibt None zurück, wenn der Benutzer Zugriff auf ALLE Cluster hat (Admin oder keine
    granularen Einschränkungen vorhanden), sonst die Liste der explizit erlaubten Cluster-IDs."""
    if user.role == UserRole.admin:
        return None
    scoped = db.query(UserClusterBerechtigung.cluster_id).filter_by(
        user_id=user.id, permission=Permission.daten_anzeigen
    ).all()
    if not scoped:
        # Prüfen ob projekt-/gebietsweite Sicht-Rechte bestehen -> dann alle zugehörigen Cluster
        project_ids = [r[0] for r in db.query(UserProjektBerechtigung.project_id).filter_by(
            user_id=user.id, permission=Permission.daten_anzeigen).all()]
        area_ids = [r[0] for r in db.query(UserGebietBerechtigung.area_id).filter_by(
            user_id=user.id, permission=Permission.daten_anzeigen).all()]
        if not project_ids and not area_ids:
            return None  # keine granularen Einschränkungen -> Rollenrechte gelten global
        q = db.query(Cluster.id)
        clauses = []
        if project_ids:
            clauses.append(Cluster.project_id.in_(project_ids))
        if area_ids:
            clauses.append(Cluster.gebiet_id.in_(area_ids))
        from sqlalchemy import or_
        return [r[0] for r in q.filter(or_(*clauses)).all()]
    return [r[0] for r in scoped]
