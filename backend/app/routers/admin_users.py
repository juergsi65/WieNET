import secrets
import string
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.audit import log_action
from app.core.security import hash_password, require_roles
from app.core.permissions import require_global_permission
from app.models.user import User, UserRole
from app.models.admin import (
    Permission, UserGebietBerechtigung, UserClusterBerechtigung, UserProjektBerechtigung,
)
from app.schemas.admin_schemas import (
    UserDetailOut, UserCreateFull, UserUpdate, PasswordResetRequest, PermissionGrant,
)

router = APIRouter(prefix="/api/admin/users", tags=["admin-benutzer"])

SCOPE_MODEL = {
    "area": UserGebietBerechtigung,
    "cluster": UserClusterBerechtigung,
    "project": UserProjektBerechtigung,
}
SCOPE_FK = {"area": "area_id", "cluster": "cluster_id", "project": "project_id"}


@router.get("", response_model=list[UserDetailOut])
def list_users(
    db: Session = Depends(get_db),
    _admin: User = Depends(require_global_permission(Permission.benutzer_verwalten)),
):
    return db.query(User).order_by(User.full_name).all()


@router.post("", response_model=UserDetailOut)
def create_user(
    payload: UserCreateFull, request: Request, db: Session = Depends(get_db),
    admin: User = Depends(require_global_permission(Permission.benutzer_verwalten)),
):
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status_code=400, detail="E-Mail bereits vergeben")
    try:
        role = UserRole(payload.role)
    except ValueError:
        raise HTTPException(status_code=400, detail="Ungültige Rolle")

    user = User(
        email=payload.email, username=payload.username,
        vorname=payload.vorname, nachname=payload.nachname,
        full_name=f"{payload.vorname} {payload.nachname}",
        hashed_password=hash_password(payload.password), role=role,
        abteilung=payload.abteilung, firma=payload.firma, telefon=payload.telefon,
        notiz=payload.notiz, ablauf_datum=payload.ablauf_datum,
        muss_passwort_aendern=payload.muss_passwort_aendern,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    log_action(db, admin, "benutzer_erstellt", "benutzer", user.id, neuer_wert=user.email, request=request)
    return user


@router.patch("/{user_id}", response_model=UserDetailOut)
def update_user(
    user_id: uuid.UUID, payload: UserUpdate, request: Request, db: Session = Depends(get_db),
    admin: User = Depends(require_global_permission(Permission.benutzer_verwalten)),
):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Benutzer nicht gefunden")

    alt = f"{user.vorname} {user.nachname}, Rolle={user.role.value}"
    updates = payload.model_dump(exclude_unset=True)
    if "role" in updates and updates["role"]:
        try:
            user.role = UserRole(updates.pop("role"))
        except ValueError:
            raise HTTPException(status_code=400, detail="Ungültige Rolle")
    for field, value in updates.items():
        setattr(user, field, value)
    if user.vorname and user.nachname:
        user.full_name = f"{user.vorname} {user.nachname}"

    db.commit()
    db.refresh(user)
    log_action(db, admin, "benutzer_bearbeitet", "benutzer", user.id, alter_wert=alt,
               neuer_wert=f"{user.vorname} {user.nachname}, Rolle={user.role.value}", request=request)
    return user


@router.post("/{user_id}/deaktivieren")
def deactivate_user(
    user_id: uuid.UUID, request: Request, db: Session = Depends(get_db),
    admin: User = Depends(require_global_permission(Permission.benutzer_verwalten)),
):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Benutzer nicht gefunden")
    user.is_active = False
    db.commit()
    log_action(db, admin, "benutzer_deaktiviert", "benutzer", user.id, request=request)
    return {"status": "deaktiviert"}


@router.post("/{user_id}/reaktivieren")
def reactivate_user(
    user_id: uuid.UUID, request: Request, db: Session = Depends(get_db),
    admin: User = Depends(require_global_permission(Permission.benutzer_verwalten)),
):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Benutzer nicht gefunden")
    user.is_active = True
    user.fehlgeschlagene_logins = 0
    db.commit()
    log_action(db, admin, "benutzer_reaktiviert", "benutzer", user.id, request=request)
    return {"status": "aktiviert"}


@router.delete("/{user_id}")
def delete_user(
    user_id: uuid.UUID, request: Request, db: Session = Depends(get_db),
    admin: User = Depends(require_global_permission(Permission.benutzer_verwalten)),
):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Benutzer nicht gefunden")
    if user.id == admin.id:
        raise HTTPException(status_code=400, detail="Eigenes Konto kann nicht gelöscht werden")
    db.query(UserGebietBerechtigung).filter_by(user_id=user_id).delete()
    db.query(UserClusterBerechtigung).filter_by(user_id=user_id).delete()
    db.query(UserProjektBerechtigung).filter_by(user_id=user_id).delete()
    email = user.email
    db.delete(user)
    db.commit()
    log_action(db, admin, "benutzer_geloescht", "benutzer", user_id, alter_wert=email, request=request)
    return {"status": "geloescht"}


@router.post("/{user_id}/passwort-zuruecksetzen")
def reset_password(
    user_id: uuid.UUID, payload: PasswordResetRequest, request: Request, db: Session = Depends(get_db),
    admin: User = Depends(require_global_permission(Permission.benutzer_verwalten)),
):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Benutzer nicht gefunden")
    user.hashed_password = hash_password(payload.new_password)
    user.muss_passwort_aendern = payload.muss_passwort_aendern
    user.fehlgeschlagene_logins = 0
    db.commit()
    log_action(db, admin, "passwort_zurueckgesetzt", "benutzer", user.id, request=request)
    return {"status": "zurueckgesetzt"}


@router.post("/{user_id}/generiere-passwort")
def generate_temp_password(
    user_id: uuid.UUID, request: Request, db: Session = Depends(get_db),
    admin: User = Depends(require_global_permission(Permission.benutzer_verwalten)),
):
    """Erzeugt ein zufälliges Einmalpasswort, das dem Administrator angezeigt wird,
    damit er es dem Benutzer sicher mitteilen kann. Erzwingt Passwortänderung beim nächsten Login."""
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Benutzer nicht gefunden")
    alphabet = string.ascii_letters + string.digits
    temp_password = "".join(secrets.choice(alphabet) for _ in range(14))
    user.hashed_password = hash_password(temp_password)
    user.muss_passwort_aendern = True
    user.fehlgeschlagene_logins = 0
    db.commit()
    log_action(db, admin, "temporaeres_passwort_erzeugt", "benutzer", user.id, request=request)
    return {"temporaeres_passwort": temp_password}


# --- Granulare Berechtigungen (Gebiet/Cluster/Projekt) ---

@router.get("/{user_id}/berechtigungen")
def get_user_permissions(
    user_id: uuid.UUID, db: Session = Depends(get_db),
    _admin: User = Depends(require_global_permission(Permission.rollen_verwalten)),
):
    result = {"area": [], "cluster": [], "project": []}
    for scope, model in SCOPE_MODEL.items():
        fk = SCOPE_FK[scope]
        rows = db.query(model).filter_by(user_id=user_id).all()
        result[scope] = [{"scope_id": str(getattr(r, fk)), "permission": r.permission.value} for r in rows]
    return result


@router.post("/berechtigungen/vergeben")
def grant_permission(
    payload: PermissionGrant, request: Request, db: Session = Depends(get_db),
    admin: User = Depends(require_global_permission(Permission.rollen_verwalten)),
):
    if payload.scope_type not in SCOPE_MODEL:
        raise HTTPException(status_code=400, detail="Ungültiger scope_type (area|cluster|project)")
    model = SCOPE_MODEL[payload.scope_type]
    fk = SCOPE_FK[payload.scope_type]
    try:
        permission = Permission(payload.permission)
    except ValueError:
        raise HTTPException(status_code=400, detail="Ungültige Berechtigung")

    existing = db.query(model).filter_by(
        user_id=payload.user_id, permission=permission, **{fk: payload.scope_id}
    ).first()
    if not existing:
        db.add(model(user_id=payload.user_id, permission=permission, **{fk: payload.scope_id}))
        db.commit()
    log_action(
        db, admin, "berechtigung_vergeben", "berechtigung", payload.user_id,
        neuer_wert=f"{payload.scope_type}:{payload.scope_id}:{payload.permission}", request=request,
        **({"area_id": payload.scope_id} if payload.scope_type == "area" else {}),
        **({"cluster_id": payload.scope_id} if payload.scope_type == "cluster" else {}),
        **({"project_id": payload.scope_id} if payload.scope_type == "project" else {}),
    )
    return {"status": "vergeben"}


@router.post("/berechtigungen/entziehen")
def revoke_permission(
    payload: PermissionGrant, request: Request, db: Session = Depends(get_db),
    admin: User = Depends(require_global_permission(Permission.rollen_verwalten)),
):
    if payload.scope_type not in SCOPE_MODEL:
        raise HTTPException(status_code=400, detail="Ungültiger scope_type (area|cluster|project)")
    model = SCOPE_MODEL[payload.scope_type]
    fk = SCOPE_FK[payload.scope_type]
    try:
        permission = Permission(payload.permission)
    except ValueError:
        raise HTTPException(status_code=400, detail="Ungültige Berechtigung")

    db.query(model).filter_by(
        user_id=payload.user_id, permission=permission, **{fk: payload.scope_id}
    ).delete()
    db.commit()
    log_action(db, admin, "berechtigung_entzogen", "berechtigung", payload.user_id,
               alter_wert=f"{payload.scope_type}:{payload.scope_id}:{payload.permission}", request=request)
    return {"status": "entzogen"}
